from beanie import Document, Link
from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.user import User
from app.models.enums import MessageType


class Message(Document):
    sender_id: Link[User]
    content: str
    mood: Optional[str]
    order: int
    # type: MessageType

    class Settings:
        name = "Message"
