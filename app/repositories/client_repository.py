from typing import List, Optional

from fastapi import HTTPException
from app.models.ai import AI
from app.models.client import Client
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository[Client]):
    
    def __init__(self):
        super().__init__(Client)
    
    async def get_by_name(self, name: str) -> Optional[Client]:
        """Lấy client theo tên"""
        return await Client.find_one(Client.name == name)
    
    async def get_all(self) -> List[Client]:
        """Lấy tất cả client"""
        return await Client.find_all().to_list()
    
    async def create(self, name: str, description: Optional[str] = None, account_username: str =None, account_password: str = None) -> Client:
        """Tạo client mới"""
        user = await User.find_one(User.username == account_username)
        if user:
            raise HTTPException(status_code=400, detail="Account username already exists")
        client = Client(name=name, description=description)

        new_client  = await client.insert()
        ai = AI(instructions="", voice="", client_id=new_client)
        await ai.insert()
        user = User(username=account_username, password=account_password, client_id=new_client, role="admin", fullname=name, email="mock@email.com", extension_number="1001")
        await user.insert()
        return new_client
    
    async def update(self, client_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Client]:
        """Cập nhật thông tin client"""
        client = await self.get_by_id(client_id)
        if not client:
            return None
            
        if name is not None:
            client.name = name
        if description is not None:
            client.description = description
            
        await client.save()
        return client
    
    async def delete(self, client_id: str) -> bool:
        """Xóa client"""
        client = await self.get_by_id(client_id)
        if not client:
            return False
            
        await client.delete()
        await AI.find_one(AI.client_id == client).delete()
        await User.find_one(User.client_id == client).delete()

        return True 