from typing import List, Optional
from app.models.ai import AI
from app.models.client import Client
from app.models.user import User
from app.repositories.ai_repository import AiRepository
from app.auth.exceptions import CustomHTTPException
import logging

logger = logging.getLogger(__name__)

class AIManagementService:
    def __init__(self):
        self.ai_repo = AiRepository()

    async def get_ai_instructions(self, current_user: User) -> Optional[AI]:
        """Lấy AI instructions - tạm thời không filter theo client"""
        return await self.ai_repo.get_ai_instruction(current_user.client_id)

    async def get_all_ai_by_client(self, current_user: User) -> List[AI]:
        """Lấy tất cả AI configs - tạm thời trả về list rỗng"""
        return []

    async def update_ai_instructions(self, instructions: str, voice: str, current_user: User) -> AI:
        """Cập nhật AI instructions - tạm thời không filter theo client"""
        return await self.ai_repo.update_ai_instruction(instructions, voice, current_user.client_id)

    async def create_ai_for_client(self, instructions: str, voice: str, current_user: User) -> AI:
        """Tạo AI config mới - tạm thời tạo global AI"""
        ai = await self.ai_repo.get_ai_instruction_by_client(current_user.client_id)
        if ai:
            raise CustomHTTPException(status_code=400, detail="AI config already exists")
        client = await Client.get(current_user.client_id)
        ai_obj = AI(instructions=instructions, voice=voice, client_id=client)
        await ai_obj.insert()
        return ai_obj