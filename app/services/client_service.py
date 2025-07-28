from typing import List, Optional
from app.models.client import Client
from app.repositories.client_repository import ClientRepository


class ClientService:
    def __init__(self):
        self.client_repository = ClientRepository()
    
    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """Lấy client theo ID"""
        return await self.client_repository.get_by_id(client_id)
    
    async def get_client_by_name(self, name: str) -> Optional[Client]:
        """Lấy client theo tên"""
        return await self.client_repository.get_by_name(name)
    
    async def get_all_clients(self) -> List[Client]:
        """Lấy tất cả client"""
        return await self.client_repository.get_all()
    
    async def create_client(self, name: str, description: Optional[str] = None, account_username: str = "", account_password: str = "") -> Client:
        """Tạo client mới"""
        # Kiểm tra xem tên client đã tồn tại chưa
        existing_client = await self.client_repository.get_by_name(name)
        if existing_client:
            raise ValueError(f"Client với tên '{name}' đã tồn tại")
        
        return await self.client_repository.create(name, description, account_username, account_password)
    
    async def update_client(self, client_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Client]:
        """Cập nhật thông tin client"""
        # Nếu cập nhật tên, kiểm tra tên mới có trùng không
        if name:
            existing_client = await self.client_repository.get_by_name(name)
            if existing_client and str(existing_client.id) != client_id:
                raise ValueError(f"Client với tên '{name}' đã tồn tại")
        
        return await self.client_repository.update(client_id, name, description)
    
    async def delete_client(self, client_id: str) -> bool:
        """Xóa client"""
        return await self.client_repository.delete(client_id) 