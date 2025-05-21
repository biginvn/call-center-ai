from typing import List, Optional
import logging

from app.dto.conversations.get_all_conversations_dto import (
    GetAllConversationsResponseDto,
    ConversationResponseDto,
    UserResponseDto,
    MessageResponseDto
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
        # logger.info(f"Found {len(conversations)} conversations")
        
        # Convert to dictionaries and then to DTOs
        conversation_dtos = []
        for conv in conversations:
            try:
                # Convert to dictionary
                conv_dict = conv.dict()
                # logger.info(f"Converted conversation to dict: {conv_dict}")
                
                # Convert IDs to strings
                conv_dict["id"] = str(conv_dict["id"])
                
                # Convert from_user and to_user
                if isinstance(conv.from_user, Link):
                    # logger.info(f"Fetching from_user: {conv.from_user}")
                    from_user = await conv.from_user.fetch()
                    if from_user:
                        from_user_dict = from_user.dict()
                        from_user_dict["id"] = str(from_user_dict["id"])
                        conv_dict["from_user"] = from_user_dict
                        # logger.info(f"Fetched from_user: {from_user_dict}")
                
                if isinstance(conv.to_user, Link):
                    # logger.info(f"Fetching to_user: {conv.to_user}")
                    to_user = await conv.to_user.fetch()
                    if to_user:
                        to_user_dict = to_user.dict()
                        to_user_dict["id"] = str(to_user_dict["id"])
                        conv_dict["to_user"] = to_user_dict
                        # logger.info(f"Fetched to_user: {to_user_dict}")
                
                # Convert messages
                if conv.messages:
                    message_dtos = []
                    for msg in conv.messages:
                        if isinstance(msg, Link):
                            # logger.info(f"Fetching message: {msg}")
                            message = await msg.fetch()
                            if message:
                                msg_dict = message.dict()
                                msg_dict["id"] = str(msg_dict["id"])
                                if isinstance(message.sender_id, Link):
                                    # logger.info(f"Fetching message sender: {message.sender_id}")
                                    sender = await message.sender_id.fetch()
                                    if sender:
                                        sender_dict = sender.dict()
                                        sender_dict["id"] = str(sender_dict["id"])
                                        msg_dict["sender_id"] = sender_dict
                                        # logger.info(f"Fetched message sender: {sender_dict}")
                                message_dtos.append(msg_dict)
                    conv_dict["messages"] = message_dtos
                
                # Convert to DTO
                conversation_dto = ConversationResponseDto(**conv_dict)
                conversation_dtos.append(conversation_dto)
                # logger.info(f"Successfully converted conversation to DTO: {conversation_dto}")
                
            except Exception as e:
                logger.error(f"Error converting conversation {conv.id}: {str(e)}")
                continue
        
        # Calculate total items
        total_items = await Conversation.find(*filters).count()
        query.pagination.set_total_items_and_total_pages(total_items)
        
        return GetAllConversationsResponseDto(
            pagination=query.pagination,
            conversations=conversation_dtos
        )

    @staticmethod
    async def get_conversation_by_id(conversation_id: str) -> Optional[Conversation]:
        conversation = await Conversation.find_one(Conversation.id == conversation_id)
        if conversation:
            try:
                # Convert to dictionary
                conv_dict = conversation.dict()
                logger.info(f"Converted conversation to dict: {conv_dict}")
                
                # Convert IDs to strings
                conv_dict["id"] = str(conv_dict["id"])
                
                # Convert from_user and to_user
                if isinstance(conversation.from_user, Link):
                    logger.info(f"Fetching from_user: {conversation.from_user}")
                    from_user = await conversation.from_user.fetch()
                    if from_user:
                        from_user_dict = from_user.dict()
                        from_user_dict["id"] = str(from_user_dict["id"])
                        conv_dict["from_user"] = from_user_dict
                        logger.info(f"Fetched from_user: {from_user_dict}")
                
                if isinstance(conversation.to_user, Link):
                    logger.info(f"Fetching to_user: {conversation.to_user}")
                    to_user = await conversation.to_user.fetch()
                    if to_user:
                        to_user_dict = to_user.dict()
                        to_user_dict["id"] = str(to_user_dict["id"])
                        conv_dict["to_user"] = to_user_dict
                        logger.info(f"Fetched to_user: {to_user_dict}")
                
                # Convert messages
                if conversation.messages:
                    message_dtos = []
                    for msg in conversation.messages:
                        if isinstance(msg, Link):
                            logger.info(f"Fetching message: {msg}")
                            message = await msg.fetch()
                            if message:
                                msg_dict = message.dict()
                                msg_dict["id"] = str(msg_dict["id"])
                                if isinstance(message.sender_id, Link):
                                    logger.info(f"Fetching message sender: {message.sender_id}")
                                    sender = await message.sender_id.fetch()
                                    if sender:
                                        sender_dict = sender.dict()
                                        sender_dict["id"] = str(sender_dict["id"])
                                        msg_dict["sender_id"] = sender_dict
                                        logger.info(f"Fetched message sender: {sender_dict}")
                                message_dtos.append(msg_dict)
                    conv_dict["messages"] = message_dtos
                
                return ConversationResponseDto(**conv_dict)
            except Exception as e:
                logger.error(f"Error converting conversation {conversation_id}: {str(e)}")
                return None
        return None

