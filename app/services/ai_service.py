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
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MESSAGE_PROMPT = ("Bạn sẽ nhận được một file ghi âm cuộc gọi giữa 2 người: from_user (khách hàng) và to_user (nhân viên).\n"
    "Hãy phân tích toàn bộ file và trả về dữ liệu dưới dạng một JSON object hợp lệ, có đúng **4 trường** như sau:\n\n"

    "**Định dạng JSON mong muốn:**\n"
    "{\n"
    '  "summary": string,                  # Tóm tắt nội dung cuộc gọi trong tối đa 100 từ\n'
    '  "messages": [                       # Danh sách câu nói theo thứ tự thời gian\n'
    "    {\n"
    '      "order": int,                  # Số thứ tự câu nói (tăng dần từ 1)\n'
    '      "speaker": "from_user" | "to_user",  # Ai là người nói\n'
    '      "message": string,             # Nội dung lời nói\n'
    '      "mood": "positive" | "neutral" | "negative",  # Tâm trạng người nói\n'
    '      "start_time": string,          # Thời điểm bắt đầu câu nói, định dạng "mm:ss"\n'
    '      "end_time": string             # Thời điểm kết thúc câu nói, định dạng "mm:ss"\n'
    "    },\n"
    "    ...\n"
    "  ],\n"
    '  "overall_mood": "positive" | "neutral" | "negative"  # Tổng quan cảm xúc toàn cuộc gọi của khách hàng\n'
    "}\n\n"

    "**Yêu cầu quan trọng:**\n"
    "- `start_time` và `end_time` phải là thời gian **thực tế trong file audio**, phản ánh chính xác **lúc bắt đầu và kết thúc mỗi câu nói**.\n"
    "- Ví dụ: nếu 10 giây đầu không có ai nói gì, thì câu đầu tiên sẽ bắt đầu từ \"00:10\", không phải \"00:00\".\n"
    "- Mỗi câu nói phải là một object riêng biệt, đúng thứ tự thời gian.\n"
    "- Tuyệt đối không chèn bất kỳ văn bản nào bên ngoài JSON object.\n\n"

    "**Trường hợp đặc biệt:**\n"
    "- Nếu cuộc gọi quá ngắn (dưới 4 câu hoặc dưới 10 giây), hãy trả về như sau:\n"
    "{\n"
    '  "summary": "Cuộc hội thoại không mang ý nghĩa, không thể tóm tắt.",\n'
    '  "messages": [\n'
    "    {\n"
    '      "order": 1,\n'
    '      "speaker": "from_user",\n'
    '      "message": "Không thể nghe được nội dung hoặc nội dung không có ý nghĩa",\n'
    '      "mood": "neutral",\n'
    '      "start_time": "00:10",\n'
    '      "end_time": "00:11"\n'
    "    }\n"
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
    '      "mood": "neutral",\n'
    '      "start_time": "00:08",\n'
    '      "end_time": "00:10"\n'
    "    },\n"
    "    {\n"
    '      "order": 2,\n'
    '      "speaker": "from_user",\n'
    '      "message": "Tôi muốn kiểm tra đơn hàng 123.",\n'
    '      "mood": "positive",\n'
    '      "start_time": "00:10",\n'
    '      "end_time": "00:15"\n'
    "    }\n"
    "  ],\n"
    '  "overall_mood": "positive"\n'
    "}\n")

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

    async def upload_record_to_s3(self, record_url: str, username: str) -> Document:
        # Tải file từ URL
        try:
            logger.info(f"Downloading WAV from: {record_url}")
            response = requests.get(
                record_url,
                auth=(self.ari_username, self.ari_password),
                stream=True,
                verify=False,
            )
            response.raise_for_status()

            # Kiểm tra Content-Type và đuôi file
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("audio/wav") and not record_url.endswith(
                ".wav"
            ):
                logger.error(f"Invalid file format: {content_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only WAV files are allowed",
                )

            # Kiểm tra kích thước file
            file_size = int(response.headers.get("Content-Length", 0))
            if file_size > 20 * 1024 * 1024:  # 20 MB
                logger.error(f"File size {file_size} exceeds limit")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds the limit of 20 MB",
                )

            file_content = response.content
            unique_filename = f"records/{uuid.uuid4()}.wav"

        except requests.RequestException as e:
            logger.error(f"Error downloading WAV: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error downloading WAV: {str(e)}",
            )

        # Upload lên S3
        try:
            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=unique_filename,
                Body=file_content,
                ContentType="audio/wav",
            )
            file_url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading to S3: {str(e)}",
            )

        document = Document(
            document_id=str(uuid.uuid4()),
            file_name=f"record_{unique_filename.split('/')[-1]}",
            file_path=file_url,
            file_size=file_size,
            type="audio/wav",
            uploaded_at=datetime.utcnow(),
            uploaded_by=username,
        )
        try:
            await document.insert()
        except Exception as e:
            logger.error(f"Error saving document to MongoDB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving document to MongoDB: {str(e)}",
            )

        return file_url


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
        
        from_user = await self.user_repo.get_user_by_extension(caller_ext)
        to_user = await self.user_repo.get_user_by_extension(agent_ext)
        # Bước 1: Tải file WAV từ S3
        if not url:
            raise ValueError("Cần cung cấp ít nhất một trong hai: url hoặc local_path.")

        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception("Không tải được file từ URL.")
            ext = os.path.splitext(url)[1].lower()  # lấy phần mở rộng, chuyển thành chữ thường
            if ext == ".wav":
                file_data = ("audio.wav", response.content)
            elif ext == ".webm":
                file_data = ("audio.webm", response.content)
            else:
                # nếu file không phải wav hoặc webm thì có thể báo lỗi hoặc xử lý mặc định
                raise Exception(f"Định dạng file không được hỗ trợ: {ext}")
            # Gọi GPT 1 lần duy nhất (Whisper + chức năng mở rộng)
            response = self.openai_client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=file_data,
                response_format="text",
                prompt=MESSAGE_PROMPT,
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
                        start_time=mmss_to_seconds(msg["start_time"]),
                        end_time=mmss_to_seconds(msg["end_time"]),
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


def mmss_to_seconds(mmss: str) -> int:
            minutes, seconds = map(int, mmss.strip().split(":"))
            return minutes * 60 + seconds
