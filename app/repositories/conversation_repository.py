from typing import List, Optional
import logging

from app.dto.conversations.get_all_conversations_dto import GetAllConversationsResponseDto
from app.models.conversation import Conversation
from app.query.get_all_conversation_query import GetAllConversationQuery
from app.utils.pagination import Pagination

logger = logging.getLogger(__name__)

class ConversationRepository:
    @staticmethod
    async def create_conversation(conversation: Conversation):
        try:
            logger.info(f"Creating conversation with from_user: {conversation.from_user}")
            logger.info(f"To user: {conversation.to_user}")
            
            # Verify the conversation object
            if not conversation.from_user:
                raise ValueError("From user is required")
            if not conversation.to_user:
                raise ValueError("To user is required")
                
            # Insert the conversation
            saved_conversation = await conversation.insert()
            logger.info(f"Conversation saved successfully: {saved_conversation}")
            return saved_conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    @staticmethod 
    async def get_conversation_by_id(conversation_id: str) -> Optional[Conversation]:
        return await Conversation.find_one(Conversation.id == conversation_id).populate("from_user", "to_user")

    @staticmethod
    async def get_all_conversations(query: GetAllConversationQuery) -> List[GetAllConversationsResponseDto]:
        filters = []

        if query.from_user_id:
            filters.append(Conversation.from_user.id == query.from_user_id)
        if query.to_user_id:
            filters.append(Conversation.to_user.id == query.to_user_id)
        if query.type:
            filters.append(Conversation.type == query.type)

        conversations_query = Conversation.find(*filters).sort("-created_at")
        conversations_query = conversations_query.skip(query.pagination.skip).limit(query.pagination.limit)
        conversations = await conversations_query.to_list()
        total_items = await conversations_query.count()
        query.pagination.set_total_items_and_total_pages(total_items)
        return GetAllConversationsResponseDto(pagination=query.pagination, conversations=conversations)

    