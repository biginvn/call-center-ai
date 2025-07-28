from app.models.user import User
from app.models.token import RefreshToken
from app.models.active import ActiveUser
from app.models.extension import Extension
from app.models.client import Client
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.config import settings
from app.auth.exceptions import CustomHTTPException
from beanie import Link

class UserRepository:
    @staticmethod
    async def get_all_users(client_id: Link[Client]) -> List[User]:
        return await User.find(User.client_id == client_id).to_list()
    
    @staticmethod
    async def get_all_users_by_client(client_id: str) -> List[User]:
        """Lấy tất cả user thuộc một client"""
        client = await Client.get(client_id)
        if not client:
            return []
        return await User.find(User.client_id == client).to_list()
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[User]:
        return await User.find_one(User.username == username)
    
    @staticmethod
    async def get_user_by_username_and_client(username: str, client_id: str) -> Optional[User]:
        """Lấy user theo username và client_id"""
        client = await Client.get(client_id)
        if not client:
            return None
        return await User.find_one(User.username == username, User.client_id == client)

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
            if any(u.id == user.id for u in active_user_doc.active_user):
                raise CustomHTTPException (
                    status_code=401,
                    detail= "User already on connection, please login another account",
                )
            
            # Nếu chưa có thì thêm vào
            
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
    async def get_active_users(client_id: Link[Client]) -> List[User]:
        extensions = await Extension.find({"available": False}).to_list()
        users = []
        
        for ext in extensions:
            print("Fetching user for extension:", ext.number)
            await ext.fetch_link(Extension.user)

            if ext.user:
                print("User found:", ext.user)
                await ext.user.fetch_link(User.client_id)
                print("User client_id:", ext.user.client_id)
                print("Client id:", client_id)
                # So sánh id của client với ref của Link
                if ext.user.client_id and str(ext.user.client_id.id) == str(client_id.ref.id):
                    users.append(ext.user)
        print("Active users found:", users)
        return users
    
    @staticmethod
    async def get_active_users_by_client(client_id: str) -> List[User]:
        """Lấy active users thuộc một client"""
        extensions = await Extension.find({"available": False}).to_list()
        users = []
        client = await Client.get(client_id)
        if not client:
            return []
            
        for ext in extensions:
            await ext.fetch_link(Extension.user)
            if ext.user:
                await ext.user.fetch_link(User.client_id)
                if ext.user.client_id and ext.user.client_id.id == client.id:
                    users.append(ext.user)
        return users

    @staticmethod
    async def get_fullname_by_extension(extension_number: str) -> Optional[str]:
        active_user_doc = await Extension.find_one({"number": extension_number})
        if not active_user_doc:
            return None
        await active_user_doc.fetch_link(Extension.user)
        return active_user_doc.user.fullname if active_user_doc.user else None
    @staticmethod
    async def get_user_by_extension(extension_number: str) -> Optional[User]:
        print("Getting user by extension", extension_number)
        temp_extension = await Extension.find_one(Extension.extension==extension_number)
        if temp_extension:
            user = await User.find_one(User.extension_number == temp_extension.number)
        else: user = await User.find_one(User.extension_number == extension_number)
        print("User found", user)
        return user
    @staticmethod
    async def create_user(client_id: str, username: str, password: str, fullname: str, email: str, role: str) -> User:
        user = User(username=username, password=password, client_id=client_id, role=role, fullname=fullname, email=email, extension_number="")
        return await user.insert()
    @staticmethod
    async def delete_user(username: str) -> None:
        user = await User.find_one(User.username == username)
        if user:
            await user.delete()