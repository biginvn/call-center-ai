from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation
from app.models.user import User
from app.query.get_all_conversation_query import GetAllConversationQuery
from app.dto.conversations.get_all_conversations_dto import GetAllConversationsResponseDto, GetConversationByIdResponseDto
from app.auth.exceptions import CustomHTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.conversation_repo = ConversationRepository()
    
    @staticmethod
    def _extract_id_from_link(link_obj) -> Optional[str]:
        """Helper method để extract ID từ Link object"""
        if link_obj is None:
            return None
            
        # Case 1: Link object với ref
        if hasattr(link_obj, 'ref') and link_obj.ref:
            if hasattr(link_obj.ref, 'id'):
                return str(link_obj.ref.id)
                
        # Case 2: Direct object với id
        if hasattr(link_obj, 'id'):
            return str(link_obj.id)
            
        # Case 3: Đã là string ID
        if isinstance(link_obj, str):
            return link_obj
            
        # Case 4: Fallback - convert to string
        try:
            return str(link_obj)
        except:
            return None

    async def get_all_conversations(self, query: GetAllConversationQuery, current_user: User) -> GetAllConversationsResponseDto:
        """Lấy tất cả conversations theo client của user hiện tại"""
        try:
            # Extract client_id từ Link object
            client_id_str = self._extract_id_from_link(current_user.client_id)
            
            if not client_id_str:
                logger.warning(f"Cannot extract client_id from user {current_user.id}")
                return GetAllConversationsResponseDto(pagination=query.pagination, conversations=[])
            
            logger.info(f"Getting conversations for client_id: {client_id_str}")
            # Sử dụng method đúng để filter theo client trong database
            return await self.conversation_repo.get_all_conversations(query, client_id_str)
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            # Return empty result instead of failing
            return GetAllConversationsResponseDto(pagination=query.pagination, conversations=[])

    async def get_conversation_by_id(self, conversation_id: str, current_user: User) -> Optional[GetConversationByIdResponseDto]:
        """Lấy conversation theo ID và filter theo client của user hiện tại"""
        try:
            # Extract client_id từ Link object
            client_id_str = self._extract_id_from_link(current_user.client_id)
            
            if not client_id_str:
                logger.warning(f"Cannot extract client_id from user {current_user.id}")
                return None
            
            return await self.conversation_repo.get_conversation_by_id_and_client(conversation_id, client_id_str)
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None

    async def create_conversation(self, conversation: Conversation, current_user: User) -> Conversation:
        """Tạo conversation mới và gán client_id từ user hiện tại"""
        try:
            # Extract client_id từ Link object và assign vào conversation
            client_id_str = self._extract_id_from_link(current_user.client_id)
            
            if client_id_str:
                # Fetch client object để assign vào conversation
                from app.models.client import Client
                client = await Client.get(client_id_str)
                if client:
                    conversation.client_id = client
                    
            return await self.conversation_repo.create_conversation(conversation)
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
