from typing import List, Optional
from datetime import datetime
from app.models.conversation import Conversation
from app.utils.pagination import Pagination
from pydantic import BaseModel, ConfigDict, field_validator


class UserResponseDto(BaseModel):
    id: str
    username: str
    fullname: str
    email: str
    role: str
    # extension_number: str


class MessageResponseDto(BaseModel):
    id: str
    sender_id: UserResponseDto
    content: str
    mood: Optional[str]
    order: int
    start_time: Optional[int]
    end_time: Optional[int]



class ConversationResponseDto(BaseModel):
    id: str
    status: str
    type: str
    record_url: Optional[str]
    summarize: Optional[str]
    from_user: UserResponseDto
    to_user: UserResponseDto
    # messages: List[MessageResponseDto]
    mood: str
    sentiment: Optional[str]
    created_at: datetime


class GetAllConversationsResponseDto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    pagination: Pagination
    conversations: List[ConversationResponseDto]



class GetConversationByIdResponseDto(BaseModel):
    id: str
    status: str
    type: str
    record_url: Optional[str]
    summarize: Optional[str]
    from_user: UserResponseDto
    to_user: UserResponseDto
    messages: List[MessageResponseDto]
    mood: str
    sentiment: Optional[str]
    created_at: datetime
