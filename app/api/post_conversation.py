from fastapi import APIRouter, status
from pydantic import BaseModel
from app.auth.auth import create_access_token, create_refresh_token
from app.models.user import User
from app.auth.exceptions import CustomHTTPException
from app.models.token import RefreshToken
from datetime import datetime, timedelta
from app.core.config import settings
from jose import jwt, JWTError
from app.models.conversation import Conversation
from app.models.enums import ConversationStatus, ConversationType, ConversationMood
from typing import Optional, List
from beanie import Link

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])

class StartConversationCreate(BaseModel):
    status: ConversationStatus
    # type: ConversationType
    # record_url: Optional[str] = None
    # summarize: Optional[str] = None
    from_user_extension: str
    to_user_extension: str
    # message_ids: Optional[List[str]] = None
    # mood: Optional[ConversationMood] = None
    # sentiment: Optional[str] = None
    
# class EndConversationUpdate(BaseModel):
#     summarize: Optional[str] = None
#     sentiment: Optional[str] = None
    
class ConversationResponse(BaseModel):
    id: str
    status: ConversationStatus
    # type: ConversationType
    # record_url: Optional[str]
    # summarize: Optional[str]
    from_user_extension: str
    to_user_extension: str
    # message_ids: Optional[List[str]]
    # mood: Optional[ConversationMood]
    # sentiment: Optional[str]
    
@router.post("/start", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(conversation_data: StartConversationCreate):
    logger.info(f"Starting conversation with data: {conversation_data}")
    
    from_user = await User.find_one(User.extension_number == conversation_data.from_user_extension)
    if not from_user:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with extension number {conversation_data.from_user_extension} not found"
        )
    to_user = await User.find_one(User.extension_number == conversation_data.to_user_extension)
    if not to_user:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with extension number {conversation_data.to_user_extension} not found"
        )
        
    conversation = Conversation(
        status=ConversationStatus.START,
        # type="A->A",
        # record_url=conversation_data.record_url,
        # summarize=None,
        from_user=Link(from_user, document_class=User),
        to_user=Link(to_user, document_class=User),
        # messages="",
        # mood=conversation_data.mood,
        # sentiment=conversation_data.sentiment
    )
    
    await conversation.insert()
    
    return ConversationResponse(
        id=str(conversation.id),
        from_user_extension=conversation_data.from_user_extension,
        to_user_extension=conversation_data.to_user_extension,
        status=ConversationStatus.START,
    )
    
# @router.patch("/{conversation_id}/end", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
# async def end_conversation(conversation_data: StartConversationCreate):
#     conversation = await Conversation.