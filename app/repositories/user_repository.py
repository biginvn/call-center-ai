from datetime import datetime
from beanie import PydanticObjectId
from app.models.user import User
from .base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """
    Repository chuyên xử lý truy xuất dữ liệu User
    Kế thừa các phương thức CRUD từ BaseRepository
    """
    def __init__(self):
        super().__init__(User)  # Truyền model User vào base

    # Custom methods cho User
    async def get_by_email(self, email: str) -> User | None:
        """Tìm user bằng email (unique field)"""
        return await User.find_one(User.email == email)
