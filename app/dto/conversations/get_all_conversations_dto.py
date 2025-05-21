from typing import List
from app.models.conversation import Conversation
from app.utils.pagination import Pagination
from pydantic import BaseModel, ConfigDict


class GetAllConversationsResponseDto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    pagination: Pagination
    conversations: List[Conversation]