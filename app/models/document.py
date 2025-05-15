from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field

class Document(Document):
    file_name: str  # Tên file gốc (ví dụ: "KGVH HCM.docx")
    file_path: str  # Đường dẫn file (ví dụ: "/uploads/123e4567-e89b-12d3-a456-426614174000.docx")
    file_size: int  # Kích thước file (bytes)
    type: str      # Loại MIME hoặc định dạng (ví dụ: "application/pdf")
    upload_time: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "Document"
        # indexes = [
        #     Indexed("file_name"),
        #     Indexed("upload_time"),
        # ]
        
    def __str__(self):
        return f"Document(file_name={self.file_name}, file_path={self.file_path}, file_size={self.file_size}, type={self.type}, upload_time={self.upload_time})"