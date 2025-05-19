from app.models.user import User
from fastapi import HTTPException
from app.auth.exceptions import CustomHTTPException
from app.repositories.user_repository import UserRepository

async def add_active_user(user: User):
    return await UserRepository.add_active_user(user)

async def remove_active_user(user: User):
    active_user_doc = await UserRepository.remove_active_user(user)
    if not active_user_doc:
        raise CustomHTTPException(status_code=404, detail="No active user list found")
    return active_user_doc

async def get_active_users():
    return await UserRepository.get_active_users()

async def get_fullname_by_extension(extension_number: str) -> str:
    fullname = await UserRepository.get_fullname_by_extension(extension_number)
    if fullname is None:
        raise CustomHTTPException(status_code=404, detail=f"No active user found with extension_number {extension_number}")
    return fullname