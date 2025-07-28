from beanie import Link
from app.models.ai import AI
from app.models.client import Client
from app.repositories.base_repository import get_database
from typing import Optional, List

class AiRepository:

    @staticmethod
    async def get_ai_instruction(client_id: Link[Client]) -> AI:
        return await AI.find_one(AI.client_id == client_id)
    
    @staticmethod
    async def get_ai_instruction_by_client(client_id: Link[Client]) -> Optional[AI]:
        """Lấy AI instruction theo client"""
        return await AI.find_one(AI.client_id == client_id)
    
    @staticmethod
    async def get_all_ai_by_client(client_id: str) -> List[AI]:
        """Lấy tất cả AI configs thuộc một client"""
        client = await Client.get(client_id)
        if not client:
            return []
        return await AI.find(AI.client_id == client).to_list()

    @staticmethod
    async def update_ai_instruction(instructions: str, voice: str, client_id: Link[Client]) -> AI:
        ai_obj = await AI.find_one(AI.client_id == client_id)
        if not ai_obj:
            ai_obj = AI(instructions=instructions, voice=voice, client_id=client_id)
        else:
            ai_obj.instructions = instructions
            ai_obj.voice = voice
            ai_obj.client_id = client_id
        await ai_obj.save()
        return ai_obj
    
    @staticmethod
    async def update_ai_instruction_by_client(client_id: str, instructions: str, voice: str) -> Optional[AI]:
        """Cập nhật AI instruction theo client"""
        client = await Client.get(client_id)
        if not client:
            return None
            
        ai_obj = await AI.find_one(AI.client_id == client)
        if not ai_obj:
            # Tạo mới nếu chưa có
            ai_obj = AI(instructions=instructions, voice=voice, client_id=client)
        else:
            ai_obj.instructions = instructions
            ai_obj.voice = voice
        await ai_obj.save()
        return ai_obj
    
    @staticmethod
    async def create_ai_for_client(client_id: str, instructions: str, voice: str) -> Optional[AI]:
        """Tạo AI config mới cho client"""
        client = await Client.get(client_id)
        if not client:
            return None
            
        ai_obj = AI(instructions=instructions, voice=voice, client_id=client)
        await ai_obj.insert()
        return ai_obj
