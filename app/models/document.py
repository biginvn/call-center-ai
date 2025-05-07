from datetime import datetime
from beanie import Document
from typing import Optional


class Document(Document):
    title: str
    storage_url: str
    upload_time: Optional[datetime] = None

    class Settings:
        name = "Document"
