from beanie import Document, Link
from datetime import datetime
from typing import List, Optional
from app.models.user import User
from app.models.message import Message
from app.models.enums import ConversationType
from app.models.enums import ConversationMood
from app.models.enums import ConversationStatus


class Conversation(Document):
    status: ConversationStatus
    type: ConversationType
    recordUrl: Optional[str]
    summarize: Optional[str]
    fromUser: Link[User]
    toUser: Link[User]
    messages: List[Link[Message]]
    mood: ConversationMood
    sentiment: Optional[str]

    class Settings:
        name = "Conversation"
