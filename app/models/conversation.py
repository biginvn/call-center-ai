from beanie import Document, Link
from datetime import datetime
from typing import List, Optional
from app.models.user import User
from app.models.message import Message
from app.models.enums import ConversationType
from app.models.enums import ConversationMood
from app.models.enums import ConversationStatus
from pydantic import Field


class Conversation(Document):
    status: ConversationStatus
    type: ConversationType
    record_url: Optional[str]
    summarize: Optional[str]
    from_user: Link[User]
    to_user: Link[User]
    messages: Optional[List[Message]]
    mood: ConversationMood
    sentiment: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "Conversation"
        indexes = [
            "created_at"
        ]

    def __str__(self):
        return f"Conversation(type={self.type}, from_user={self.from_user}, to_user={self.to_user}, status={self.status}, summarize={self.summarize})"