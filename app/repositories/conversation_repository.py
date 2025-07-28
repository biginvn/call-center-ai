import json
from typing import List, Optional
import logging
from bson import ObjectId
from bson.errors import InvalidId
from app.dto.conversations.get_all_conversations_dto import (
    GetAllConversationsResponseDto,
    ConversationResponseDto,
    MessageResponseDto,
    GetConversationByIdResponseDto
)
from app.models.conversation import Conversation
from app.models.client import Client
from app.query.get_all_conversation_query import GetAllConversationQuery
from app.utils.pagination import Pagination
from app.models.message import Message
from beanie import Link

logger = logging.getLogger(__name__)

class ConversationRepository:
    @staticmethod
    def _is_valid_object_id(oid: str) -> bool:
        if not oid:
            return False
        try:
            ObjectId(oid)
            return True
        except (InvalidId, TypeError):
            return False

    @staticmethod
    async def _extract_link_model_dump(link_obj: Optional[Link]) -> Optional[dict]:
        if isinstance(link_obj, Link):
            try:
                fetched = await link_obj.fetch()
                if isinstance(fetched, Link):
                    fetched = await fetched.fetch()
                if fetched and not isinstance(fetched, Link) and hasattr(fetched, 'model_dump'):
                    data = fetched.model_dump()
                    if 'id' in data:
                        data["id"] = str(data["id"])
                    return data
            except Exception as e:
                logger.warning(f"Failed to fetch link object: {e}")
                return None
        elif link_obj and hasattr(link_obj, 'model_dump'):
            try:
                data = link_obj.model_dump()
                if 'id' in data:
                    data["id"] = str(data["id"])
                return data
            except Exception as e:
                logger.warning(f"Failed to model_dump on direct object: {e}")
                return None
        return None

    @staticmethod
    async def create_conversation(conversation: Conversation):
        try:
            if not conversation.from_user or not conversation.to_user:
                raise ValueError("From user and To user are required")
            return await conversation.insert()
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise

    @staticmethod
    async def get_all_conversations(query: GetAllConversationQuery, client_id: str) -> GetAllConversationsResponseDto:
        filters = []
        if ConversationRepository._is_valid_object_id(client_id):
            filters.append(Conversation.client_id.id == ObjectId(client_id))
        if ConversationRepository._is_valid_object_id(query.from_user_id):
            filters.append(Conversation.from_user.id == ObjectId(query.from_user_id))
        if ConversationRepository._is_valid_object_id(query.to_user_id):
            filters.append(Conversation.to_user.id == ObjectId(query.to_user_id))
        if query.type:
            filters.append(Conversation.type == query.type)

        conversations = await Conversation.find(*filters).sort("-created_at").skip(query.pagination.skip).limit(query.pagination.limit).to_list()
        total_items = await Conversation.find(*filters).count()
        query.pagination.set_total_items_and_total_pages(total_items)

        conversation_dtos = []
        for conversation in conversations:
            try:
                conv_dict = conversation.model_dump()
                conv_dict["id"] = str(conv_dict["id"])
                from_user_dict = await ConversationRepository._extract_link_model_dump(conversation.from_user)
                to_user_dict = await ConversationRepository._extract_link_model_dump(conversation.to_user)
                if not from_user_dict or not to_user_dict:
                    continue
                conv_dict["from_user"] = from_user_dict
                conv_dict["to_user"] = to_user_dict
                conversation_dtos.append(ConversationResponseDto(**conv_dict))
            except Exception as e:
                logger.error(f"Error processing conversation: {e}")
        return GetAllConversationsResponseDto(pagination=query.pagination, conversations=conversation_dtos)

    @staticmethod
    async def get_conversation_by_id(conversation_id: str) -> Optional[GetConversationByIdResponseDto]:
        if not ConversationRepository._is_valid_object_id(conversation_id):
            return None
        conversation = await Conversation.find_one({"_id": ObjectId(conversation_id)})
        if not conversation:
            return None
        try:
            conv_dict = conversation.model_dump()
            conv_dict["id"] = str(conv_dict["id"])
            from_user_dict = await ConversationRepository._extract_link_model_dump(conversation.from_user)
            to_user_dict = await ConversationRepository._extract_link_model_dump(conversation.to_user)
            if not from_user_dict or not to_user_dict:
                return None
            conv_dict["from_user"] = from_user_dict
            conv_dict["to_user"] = to_user_dict
            if conversation.messages:
                message_dtos = []
                for msg in conversation.messages:
                    try:
                        msg_dict = msg.model_dump()
                        msg_dict["id"] = str(msg_dict["id"])
                        sender_dict = await ConversationRepository._extract_link_model_dump(msg.sender_id)
                        if sender_dict:
                            msg_dict["sender_id"] = sender_dict
                            message_dtos.append(MessageResponseDto(**msg_dict))
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                conv_dict["messages"] = message_dtos
            return GetConversationByIdResponseDto(**conv_dict)
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            return None

    @staticmethod
    async def get_conversation_by_id_and_client(conversation_id: str, client_id: str) -> Optional[GetConversationByIdResponseDto]:
        if not (ConversationRepository._is_valid_object_id(conversation_id) and ConversationRepository._is_valid_object_id(client_id)):
            return None
        conversation = await Conversation.find_one(
            Conversation.id == ObjectId(conversation_id),
            Conversation.client_id.id == ObjectId(client_id)
        )
        if not conversation:
            return None
        try:
            conv_dict = conversation.model_dump()
            conv_dict["id"] = str(conv_dict["id"])
            from_user_dict = await ConversationRepository._extract_link_model_dump(conversation.from_user)
            to_user_dict = await ConversationRepository._extract_link_model_dump(conversation.to_user)
            if not from_user_dict or not to_user_dict:
                return None
            conv_dict["from_user"] = from_user_dict
            conv_dict["to_user"] = to_user_dict
            if conversation.messages:
                message_dtos = []
                for msg in conversation.messages:
                    try:
                        msg_dict = msg.model_dump()
                        msg_dict["id"] = str(msg_dict["id"])
                        sender_dict = await ConversationRepository._extract_link_model_dump(msg.sender_id)
                        if sender_dict:
                            msg_dict["sender_id"] = sender_dict
                            message_dtos.append(MessageResponseDto(**msg_dict))
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                conv_dict["messages"] = message_dtos
            return GetConversationByIdResponseDto(**conv_dict)
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            return None
