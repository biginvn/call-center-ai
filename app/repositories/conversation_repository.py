from typing import List, Optional
import logging
from bson import ObjectId
from app.dto.conversations.get_all_conversations_dto import (
    GetAllConversationsResponseDto,
    ConversationResponseDto,
    UserResponseDto,
    MessageResponseDto,
    GetConversationByIdResponseDto
)
from app.models.conversation import Conversation
from app.query.get_all_conversation_query import GetAllConversationQuery
from app.utils.pagination import Pagination
from app.models.message import Message
from beanie import Link

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
    async def get_all_conversations(query: GetAllConversationQuery) -> GetAllConversationsResponseDto:
        filters = []

        if query.from_user_id:
            filters.append(Conversation.from_user.id == query.from_user_id)
        if query.to_user_id:
            filters.append(Conversation.to_user.id == query.to_user_id)
        if query.type:
            filters.append(Conversation.type == query.type)

        # Get conversations with pagination
        conversations = await Conversation.find(*filters).sort("-created_at").skip(query.pagination.skip).limit(query.pagination.limit).to_list()
        
        # Calculate total items
        total_items = await Conversation.find(*filters).count()
        query.pagination.set_total_items_and_total_pages(total_items)
        
        # Convert conversations to ConversationResponseDto
        conversation_dtos = []
        for conversation in conversations:
            # Convert to dictionary
            conv_dict = conversation.dict()
            
            # Convert IDs to strings
            conv_dict["id"] = str(conv_dict["id"])
            
            # Convert from_user and to_user
            if isinstance(conversation.from_user, Link):
                from_user = await conversation.from_user.fetch()
                if from_user:
                    from_user_dict = from_user.dict()
                    from_user_dict["id"] = str(from_user_dict["id"])
                    conv_dict["from_user"] = from_user_dict
            
            if isinstance(conversation.to_user, Link):
                to_user = await conversation.to_user.fetch()
                if to_user:
                    to_user_dict = to_user.dict()
                    to_user_dict["id"] = str(to_user_dict["id"])
                    conv_dict["to_user"] = to_user_dict
            
            conversation_dto = ConversationResponseDto(**conv_dict)
            conversation_dtos.append(conversation_dto)
        
        return GetAllConversationsResponseDto(
            pagination=query.pagination,
            conversations=conversation_dtos
        )

    @staticmethod
    async def get_conversation_by_id(conversation_id: str) -> Optional[GetConversationByIdResponseDto]:
        conversation = await Conversation.find_one({"_id": ObjectId(conversation_id)})
        if conversation is None:
            return None
            
        # Convert to dictionary
        conv_dict = conversation.dict()
        
        # Convert IDs to strings
        conv_dict["id"] = str(conv_dict["id"])
        
        # Convert from_user and to_user
        if isinstance(conversation.from_user, Link):
            from_user = await conversation.from_user.fetch()
            if from_user:
                from_user_dict = from_user.dict()
                from_user_dict["id"] = str(from_user_dict["id"])
                conv_dict["from_user"] = from_user_dict
        
        if isinstance(conversation.to_user, Link):
            to_user = await conversation.to_user.fetch()
            if to_user:
                to_user_dict = to_user.dict()
                to_user_dict["id"] = str(to_user_dict["id"])
                conv_dict["to_user"] = to_user_dict
        
        # Convert messages
        if conversation.messages:
            # print(f"conversation.messages={conversation.messages}")
            message_dtos = []
            for msg in conversation.messages:
                msg_dict = msg.dict()
                msg_dict["id"] = str(msg_dict["id"])
                if isinstance(msg.sender_id, Link):
                    sender = await msg.sender_id.fetch()
                    if sender:
                        sender_dict = sender.dict()
                        sender_dict["id"] = str(sender_dict["id"])
                        msg_dict["sender_id"] = sender_dict
                print("append message", msg_dict["content"])
                message_dtos.append(MessageResponseDto(**msg_dict))
            conv_dict["messages"] = message_dtos
        
        return GetConversationByIdResponseDto(**conv_dict)
