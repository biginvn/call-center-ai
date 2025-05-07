from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient

from app.models.user import User
from app.models.ai import AI
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document


