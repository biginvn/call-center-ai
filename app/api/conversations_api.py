from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from app.services.conversation_service import ConversationService
from app.query.get_all_conversation_query import GetAllConversationQuery
from app.utils.pagination import Pagination
from app.models.enums import ConversationType
from app.models.user import User
from app.auth.auth import get_current_user
from app.dto.conversations.get_all_conversations_dto import GetAllConversationsResponseDto, GetConversationByIdResponseDto

conversation_router = APIRouter(prefix="/conversations", tags=["Conversations"])
conversation_service = ConversationService()

@conversation_router.get("/", response_model=GetAllConversationsResponseDto)
async def get_all_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(10, le=100),
    from_user_id: Optional[str] = None,
    to_user_id: Optional[str] = None,
    type: Optional[ConversationType] = None,
    current_user: User = Depends(get_current_user)
):
    # Khởi tạo Pagination và Query object
    pagination = Pagination(page_number=page, page_size=size)
    query = GetAllConversationQuery(pagination=pagination)
    query.from_user_id = from_user_id
    query.to_user_id = to_user_id
    query.type = type

    # Sử dụng service với client filtering
    return await conversation_service.get_all_conversations(query, current_user)


@conversation_router.get("/{conversation_id}", response_model=GetConversationByIdResponseDto)
async def get_conversation_by_id(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    conversation = await conversation_service.get_conversation_by_id(conversation_id, current_user)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation