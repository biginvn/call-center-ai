from beanie import Document, Link
from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.user import User
from app.models.enums import MessageType


class RefreshToken(Document):
    refresh_token: str = Field(..., unique=True)
    username: str
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "refresh_tokens"
