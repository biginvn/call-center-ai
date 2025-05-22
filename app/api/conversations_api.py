from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from app.repositories.conversation_repository import ConversationRepository
from app.query.get_all_conversation_query import GetAllConversationQuery
from app.utils.pagination import Pagination
from app.models.enums import ConversationType
from app.dto.conversations.get_all_conversations_dto import GetAllConversationsResponseDto, GetConversationByIdResponseDto

conversation_router = APIRouter(prefix="/conversations", tags=["Conversations"])

@conversation_router.get("/", response_model=GetAllConversationsResponseDto)
async def get_all_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(10, le=100),
    from_user_id: Optional[str] = None,
    to_user_id: Optional[str] = None,
    type: Optional[ConversationType] = None,
):
    # Khởi tạo Pagination và Query object
    pagination = Pagination(page_number=page, page_size=size)
    query = GetAllConversationQuery(pagination=pagination)
    query.from_user_id = from_user_id
    query.to_user_id = to_user_id
    query.type = type

    # Truy vấn từ repository
    return await ConversationRepository.get_all_conversations(query)


@conversation_router.get("/{conversation_id}", response_model=GetConversationByIdResponseDto)
async def get_conversation_by_id(conversation_id: str):
    conversation = await ConversationRepository.get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation