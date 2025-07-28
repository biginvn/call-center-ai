from beanie import Document, Link
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
from app.models.user import User
from app.models.enums import MessageType


class Message(Document):
    sender_id: Link[User]
    content: str
    mood: Optional[str] = None
    order: int
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    # type: MessageType

    class Settings:
        name = "Message"
