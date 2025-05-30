from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from pydantic import BaseModel
from app.models.document import Document
from dotenv import load_dotenv
from datetime import datetime
from app.auth.exceptions import CustomHTTPException
from app.auth.auth import get_current_user
from app.models.user import User
from app.repositories.ai_repository import AiRepository
import logging
import os
import uuid
import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")


router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", "wav"}
MAX_FILE_SIZE = 20 * 1024 * 1024

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET]):
    logger.error("Missing AWS environment variables")
    raise ValueError(
        "AWS environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET) must be set in .env"
    )
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


class DocumentResponse(BaseModel):
    document_id: str
    file_name: str
    file_path: str
    file_size: int
    type: str
    upload_time: datetime


class InstructionRequest(BaseModel):
    instruction: str
    voice: str


def is_allowed_file(file_name: str) -> bool:
    return os.path.splitext(file_name)[1].lower() in ALLOWED_EXTENSIONS


@router.post(
    "/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    logger.info(f"Received file: {file.filename}, size: {file.size} bytes")

    role = current_user.role
    if role not in ["admin", "superuser"]:
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to upload files",
        )

    if not is_allowed_file(file.filename):
        raise CustomHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_size = file.size
    if file_size > MAX_FILE_SIZE:
        raise CustomHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024)} MB",
        )

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    try:
        file_content = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=unique_filename,
            Body=file_content,
            ContentType=file.content_type or "application/octet-stream",
        )
        # Tạo URL công khai cho file
        file_url = (
            f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        )
    except Exception as e:
        logger.error(f"Error uploading file to S3: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file to S3: {str(e)}",
        )

    document = Document(
        document_id=str(uuid.uuid4()),
        file_name=file.filename,
        file_path=file_url,  # Đường dẫn tương đối
        file_size=file_size,
        type=file.content_type or "application/octet-stream",
        uploaded_at=datetime.utcnow(),
    )
    await document.insert()

    # Trả về response
    return DocumentResponse(
        document_id=str(document.id),
        file_name=document.file_name,
        file_path=document.file_path,
        file_size=document.file_size,
        type=document.type,
        upload_time=document.upload_time,
    )


@router.get("/dowload/{document_id}")
async def dowloand_document(
    document_id: str, current_user: User = Depends(get_current_user)
):
    document = await Document.get(document_id)

    role = current_user.role
    if role not in ["admin"]:
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to download files",
        )
    if not document:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    file_url = document.file_path

    file_key = file_url.split("/")[-1]
    signed_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": file_key},
        ExpiresIn=3600,  # URL sẽ hết hạn sau 1 giờ
    )

    return {"download_url": signed_url}


