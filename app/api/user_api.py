from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import List
from app.auth.auth import get_current_user
from app.services.user_service import UserService
from app.models.user import User
from app.auth.exceptions import CustomHTTPException
from app.repositories.user_repository import UserRepository
from app.services.extension_service import ExtensionService
from app.dependencies.active_user import add_active_user, remove_active_user
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])

class UserDataResponse(BaseModel):
    username: str
    extension_number: str | None
    role: str
    fullname: str | None

@router.get("/all", response_model=List[UserDataResponse])
async def get_all_users(current_user: User = Depends(get_current_user)):
    logger.info("Fetching all users")
    user_service = UserService()
    users = await user_service.get_all_users(current_user)
    return [
        UserDataResponse(
            username=user.username,
            extension_number=user.extension_number,
            role=user.role,
            fullname=user.fullname,
        )
        for user in users
    ]

@router.get("/", response_model=UserDataResponse)
async def get_user(current_user: User = Depends(get_current_user)):
    logger.info(f"Fetching user data for: {current_user.username}")
    user_service = UserService()
    user = await user_service.get_user(current_user.username)
    return UserDataResponse(
        username=user.username,
        extension_number=user.extension_number,
        role=user.role,
        fullname=user.fullname,
    )

@router.get("/active")
async def list_active_users(current_user: User = Depends(get_current_user)):
    logger.info("Fetching active users")
    user_service = UserService()
    users = await user_service.get_active_users(current_user)
    return {"active_users": users}

@router.get("/active/{extension_number}")
async def get_fullname(extension_number: str, current_user: User = Depends(get_current_user)):
    logger.info(f"Fetching fullname for extension: {extension_number}")
    user_service = UserService()
    fullname = await user_service.get_fullname_by_extension(extension_number, current_user)
    return {"fullname": fullname, "extension_number": extension_number}

class ConnectRequest (BaseModel):
    username: str
    extension: str

@router.post("/connect")
async def on_connect_user(request:ConnectRequest):
    user = await UserRepository.get_user_by_username(request.username)
    if user:
        user = await UserRepository.update_user_extension_number(user, request.extension)
    extension_service = ExtensionService()
    await extension_service.update_extension_availability(request.extension, False)
    await add_active_user(user)
    return "User connected successfully"

@router.post("/disconnect")
async def on_connect_user(request:ConnectRequest):
    user = await UserRepository.get_user_by_username(request.username)
    await UserRepository.update_user_extension_number(user, "")
    extension_service = ExtensionService()
    await extension_service.update_extension_availability(request.extension, True)
    await remove_active_user(user)
    return "user disconnected"