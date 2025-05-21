from app.models.user import User
from app.models.token import RefreshToken
from app.models.active import ActiveUser
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.config import settings

class UserRepository:
    @staticmethod
    async def get_all_users() -> List[User]:
        return await User.find_all().to_list()
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[User]:
        return await User.find_one(User.username == username)

    @staticmethod
    async def get_user_by_extension_number(extension_number: str) -> Optional[User]:
        return await User.find_one(User.extension_number == extension_number)

    @staticmethod
    async def update_user_extension_number(user: User, extension_number: str) -> User:
        user.extension_number = extension_number
        return await user.save()

    @staticmethod
    async def save_refresh_token(username: str, refresh_token: str) -> RefreshToken:
        db_refresh_token = RefreshToken(
            refresh_token=refresh_token,
            username=username,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return await db_refresh_token.insert()

    @staticmethod
    async def get_refresh_token(refresh_token: str) -> Optional[RefreshToken]:
        return await RefreshToken.find_one(RefreshToken.refresh_token == refresh_token)

    @staticmethod
    async def delete_refresh_token(refresh_token: RefreshToken) -> None:
        await refresh_token.delete()

    @staticmethod
    async def get_active_user_list() -> Optional[ActiveUser]:
        return await ActiveUser.find_one()

    @staticmethod
    async def add_active_user(user: User) -> ActiveUser:
        active_user_doc = await ActiveUser.find_one()
        if not active_user_doc:
            active_user_doc = ActiveUser(active_user=[user])
            await active_user_doc.insert()
        else:
            if not any(u.id == user.id for u in active_user_doc.active_user):
                active_user_doc.active_user.append(user)
                await active_user_doc.save()
        return active_user_doc

    @staticmethod
    async def remove_active_user(user: User) -> Optional[ActiveUser]:
        active_user_doc = await ActiveUser.find_one()
        if not active_user_doc:
            return None
        active_user_doc.active_user = [u for u in active_user_doc.active_user if u.id != user.id]
        await active_user_doc.save()
        return active_user_doc

    @staticmethod
    async def get_active_users() -> List[User]:
        active_user_doc = await ActiveUser.find_one()
        return active_user_doc.active_user if active_user_doc else []

    @staticmethod
    async def get_fullname_by_extension(extension_number: str) -> Optional[str]:
        active_user_doc = await ActiveUser.find_one()
        if not active_user_doc:
            return None
        for user in active_user_doc.active_user:
            if user.extension_number == extension_number:
                return user.fullname
        return None
    @staticmethod
    async def get_user_by_extension(extension_number: str) -> Optional[User]:
        print("Getting user by extension", extension_number)
        user = await User.find_one(User.extension_number == extension_number)
        print("User found", user)
        return user if user else None