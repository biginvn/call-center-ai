from app.repositories.user_repository import UserRepository
from app.models.user import User
from typing import List
from app.auth.exceptions import CustomHTTPException
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def get_all_users(self, current_user: User) -> List[User]:
        if current_user.role != "admin":
            raise CustomHTTPException(
                status_code=403,
                detail="You do not have permission to get all users",
            )
        users = await self.user_repo.get_all_users()
        if not users:
            logger.error("No users found")
            raise CustomHTTPException(status_code=404, detail="No users found")
        return users

    async def get_user(self, username: str) -> User:
        user = await self.user_repo.get_user_by_username(username)
        if not user:
            logger.error(f"User {username} not found")
            raise CustomHTTPException(status_code=404, detail="User not found")
        return user

    async def get_active_users(self, current_user: User) -> List[User]:
        return await self.user_repo.get_active_users()

    async def get_fullname_by_extension(self, extension_number: str, current_user: User) -> str:
        fullname = await self.user_repo.get_fullname_by_extension(extension_number)
        if fullname is None:
            raise CustomHTTPException(
                status_code=404,
                detail=f"No active user found with extension_number {extension_number}",
            )
        return fullname