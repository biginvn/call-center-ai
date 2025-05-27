import json
from typing import List
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
from datetime import datetime

logger = logging.getLogger(__name__)

s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


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

    async def transcribe_wav_from_s3(self, s3_url: str) -> str:
        """
        Tải file WAV từ S3 bucket và chuyển thành text bằng OpenAI Whisper.

        Args:
            s3_url (str): URL của file WAV trên S3.

        Returns:
            str: Nội dung text của record.

        """
        # Tải file từ S3
        temp_file_path = None
        try:
            # Lấy key từ s3_url
            s3_key = s3_url.replace(f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/", "")
            logger.info(f"Generating presigned URL for S3: {s3_key}")
            
            # Tạo presigned URL
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.S3_BUCKET, 'Key': s3_key},
                ExpiresIn=3600  # Hết hạn sau 1 giờ
            )
            
            # Tải file từ presigned URL
            response = requests.get(presigned_url, stream=True)
            response.raise_for_status()
            
            # Lưu file tạm
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"temp_{os.urandom(8).hex()}.wav")
            with open(temp_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Kiểm tra file
            file_size = os.path.getsize(temp_file_path)
            if file_size == 0:
                logger.error("Downloaded WAV file is empty")
                raise HTTPException(status_code=400, detail="Downloaded WAV file is empty")
        
        except Exception as e:
            logger.error(f"Error downloading from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error downloading from S3: {str(e)}")

        try:
            with open(temp_file_path, "rb") as audio_file:
                logger.info("Transcribing WAV file")
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )
                if not transcription.strip():
                    logger.warning("Transcription is empty")
                return transcription
        except Exception as e:
            logger.error(f"Error transcribing WAV: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error transcribing WAV: {str(e)}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        try:
            logger.info("Summarizing text")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that summarizes text concisely.",
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following text in no more than {max_length} words:\n\n{text}",
                    },
                ],
                max_tokens=max_length // 1,
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error summarizing text: {str(e)}",
            )
    async def split_message(self, s3_url: str, from_user: User, to_user: User) -> List[Message]:
        try:
            # Tải file từ S3
            audio_file = requests.get(s3_url)
            if audio_file.status_code != 200:
                raise HTTPException(status_code=400, detail="Không tải được file audio từ S3.")

            # Gọi API OpenAI để transcript
            transcription = self.openai_client.audio.transcriptions.create(
                model="gpt-4o-transcribe", 
                file=("audio.wav", audio_file.content),
                response_format="text",
                prompt=(
                    "Đây là cuộc gọi giữa một nhân viên (to_user) và một khách hàng (from_user). "
                    "Hãy ghi lại hội thoại theo đúng thứ tự thời gian. "
                    "Mỗi lời nói của từng người phải được tách riêng thành một mục, dù có nói ngắn, nói chen ngang hay chưa nói hết câu.\n\n"
                    "Tuyệt đối không được gộp 2 lời nói vào một mục. Nếu một người chen ngang khi người kia đang nói, hãy coi đó là một lời nói riêng, ghi đúng thứ tự thời gian.\n\n"
                    "Mỗi mục nên bao gồm:\n"
                    "- \"order\": số thứ tự phát ngôn (tăng dần từ 1)\n"
                    "- \"speaker\": \"from_user\" hoặc \"to_user\"\n"
                    "- \"message\": nội dung lời nói\n"
                    "- \"mood\": \"positive\", \"neutral\" hoặc \"negative\"\n\n"
                    "Trả kết quả dưới dạng JSON list hợp lệ, không in gì thêm ngoài JSON list."
                )
                ,
                temperature=0.0,
            )

            # Parse JSON từ OpenAI
            print("TRANSCRIPTION:", transcription)

            try:
                parsed = json.loads(transcription.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON transcription: {e}")
                raise HTTPException(status_code=500, detail="Phản hồi từ AI không đúng định dạng JSON.")



            saved_messages: List[Message] = []

            for item in parsed:
                speaker = item.get("speaker")
                sender = from_user if speaker == "from_user" else to_user
                message = Message(
                    sender_id=sender,
                    content=item.get("message", ""),
                    mood=item.get("mood"),
                    order=item.get("order")
                )
                await message.insert()
                saved_messages.append(message)

            print("Saved messages:", saved_messages)
            return saved_messages

        except Exception as e:
            logger.error(f"Error splitting message: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error splitting message: {str(e)}")