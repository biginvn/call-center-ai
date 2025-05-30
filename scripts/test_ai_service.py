import json
from typing import List, Optional
from pydantic import BaseModel
from app.models.message import Message
from app.models.user import User
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.document import Document
from app.repositories.user_repository import UserRepository
from openai import OpenAI
import boto3
import requests
import logging
import os
import tempfile
import uuid
import pytz
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


class gpt_call_analyze_response(BaseModel):
    summarize: str
    messages: list[Message]
    overall_mood: str


class AIService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.user_repo = UserRepository()
        self.ari_username = settings.AUTH_USERNAME
        self.ari_password = settings.AUTH_PASSWORD


    async def analyze_call_full_one_gpt_call(self,
        url: Optional[str] = None,
        caller_ext: Optional[str] = None, 
        agent_ext: Optional[str] = None
    ) -> gpt_call_analyze_response:
        """
        Gọi GPT chỉ 1 lần: đưa file WAV và yêu cầu GPT:
        - Transcribe
        - Tóm tắt
        - Tách hội thoại thành message

        Trả về dict gồm: transcription, summary, messages[]
        """
        
        from_user = await self.user_repo.get_user_by_extension('111')
        to_user = await self.user_repo.get_user_by_extension('112')
        # Bước 1: Tải file WAV từ S3
        if not url:
            raise ValueError("Cần cung cấp ít nhất một trong hai: url hoặc local_path.")

        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception("Không tải được file từ URL.")
            file_data = ("audio.wav", response.content)

            # Prompt duy nhất
            prompt = (
                    "Bạn sẽ nhận được một file ghi âm cuộc gọi giữa 2 người: from_user (khách hàng) và to_user (nhân viên).\n"
                    "Hãy xử lý và trả về dữ liệu dưới dạng một JSON object hợp lệ, có đúng **4 trường** như sau:\n\n"
                    "**Kiểu dữ liệu mong muốn:**\n"
                    "{\n"
                    '  "summary": string,                  # Tóm tắt nội dung cuộc gọi trong tối đa 100 từ\n'
                    '  "messages": [                       # Danh sách lời nói theo thứ tự thời gian\n'
                    "    {\n"
                    '      "order": int,                  # Số thứ tự câu nói (tăng dần từ 1)\n'
                    '      "speaker": "from_user" | "to_user",  # Ai là người nói\n'
                    '      "message": string,             # Nội dung lời nói\n'
                    '      "mood": "positive" | "neutral" | "negative"  # Tâm trạng người nói\n'
                    '      "time_talking": int  # Thời gian tính bằng giây kể từ lúc bắt đầu câu nói tới lúc kết thúc câu nói của người đang nói trong đoạn hội thoại\n'
                    "    },\n"
                    "    ...\n"
                    "  ],\n"
                    '  "overall_mood": "positive" | "neutral" | "negative"  # Tổng quan cảm xúc dựa trên nội dung nói chuyện của khách hàng, không tính nhân viên\n'
                    "}\n\n"
                    "**Yêu cầu quan trọng:**\n"
                    "- Mỗi lời nói phải là một object riêng biệt, không gộp.\n"
                    "- Giữ nguyên đúng thứ tự thời gian.\n"
                    "- Không chèn bất kỳ text nào bên ngoài JSON object.\n\n"
                    "- Nếu đoạn hội thoại quá ngắn (dưới 4 câu hoặc nhỏ hơn 10 giây) thì trả về JSON của message như phía dưới:   #Vẫn ưu tiên xử lý được dữ liệu và ra được tóm tắt hơn\n"
                    "{\n"
                    '  "summary": "Cuộc hội thoại không mang ý nghĩa, không thể tóm tắt.",\n'
                    '  "messages": [\n'
                    "    {\n"
                    '      "order": 1,\n'
                    '      "speaker": "from_user",\n'
                    '      "message": "Không thể nghe được nội dung hoặc nội dung không có ý nghĩa",\n'
                    '      "mood": "neutral"\n'
                    '      "time_talking": 0\n'
                    "    },\n"
                    "  ],\n"
                    '  "overall_mood": "neutral"\n'
                    "}\n\n"
                    "**Ví dụ minh họa:**\n"
                    "{\n"
                    '  "summary": "Khách hàng hỏi về đơn hàng và được nhân viên xác nhận trạng thái giao hàng.",\n'
                    '  "messages": [\n'
                    "    {\n"
                    '      "order": 1,\n'
                    '      "speaker": "to_user",\n'
                    '      "message": "Xin chào quý khách ạ.",\n'
                    '      "mood": "neutral"\n'
                    '      "time_talking": 0-1\n'
                    "    },\n"
                    "    {\n"
                    '      "order": 2,\n'
                    '      "speaker": "from_user",\n'
                    '      "message": "Xin chào, bạn có thể giúp tôi kiểm tra đơn hàng 123 được không ạ, tôi rất cảm ơn bạn.",\n'
                    '      "mood": "positive"\n'
                    '      "time_talking": 1-5\n'
                    "    },\n"
                    "    {\n"
                    '      "order": 3,\n'
                    '      "speaker": "to_user",\n'
                    '      "message": "Vâng, anh/chị vui lòng chờ em kiểm tra.",\n'
                    '      "mood": "neutral"\n'
                    '      "time_talking": 7-11\n'
                    "    }\n"
                    "  ],\n"
                    '  "overall_mood": "positive"\n'
                    "}\n"
                )


            # Gọi GPT 1 lần duy nhất (Whisper + chức năng mở rộng)
            response = self.openai_client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=file_data,
                response_format="text",
                prompt=prompt,
                temperature=0,
            )
            response_text = response  

            print("Response from GPT:", response_text)

            try:
                parse_json = json.loads(response_text.strip())
            except json.JSONDecodeError as e:
                print("❌ JSON decode error:", str(e))
                with open("logs.txt", "w", encoding="utf-8") as f:
                    f.write(response_text)
                raise Exception("⚠️ Lỗi parse JSON. Nội dung gốc đã được ghi vào logs.txt")
            
            messages = []
            for msg in parse_json["messages"]:
                if msg["speaker"] == "from_user":
                    sender_id = from_user.id
                elif msg["speaker"] == "to_user":
                    sender_id = to_user.id
                else:
                    raise Exception(f"Unknown speaker: {msg['speaker']}")
                messages.append(
                    Message(
                        order=msg["order"],
                        sender_id=sender_id,
                        content=msg["message"],
                        mood=msg["mood"],
                        time=str(msg["time_talking"]),
                    )
                )
                

            ai_response = gpt_call_analyze_response(
                summarize=parse_json["summary"],
                messages=messages,
                overall_mood=parse_json["overall_mood"],
            )
            return ai_response

        except Exception as e:
            print(e)
            raise e
        
        
async def main():
    ai_service = AIService()

    # Thay đổi URL và extensions theo dữ liệu thật hoặc để test
    url = "https://internship-nixxis.s3.ap-southeast-1.amazonaws.com/records/54259aab-c02c-47b7-bd5b-281999e44c54.wav"
    caller_ext = "test1"
    agent_ext = "test2"

    try:
        result = await ai_service.analyze_call_full_one_gpt_call(
            url=url,
            caller_ext=caller_ext,
            agent_ext=agent_ext
        )
        print("=== Tổng kết cuộc gọi ===")
        print("Tóm tắt:", result.summarize)
        print("Tổng mood:", result.overall_mood)
        print("Chi tiết tin nhắn:")
        for msg in result.messages:
            print(f"[{msg.order}] ({msg.mood}) [{msg.time}] {msg.content}")

    except Exception as e:
        print("Có lỗi xảy ra:", e)

if __name__ == "__main__":
    asyncio.run(main())