from fastapi import APIRouter, status, Depends
from pydantic import BaseModel
from app.models.user import User
from app.auth.exceptions import CustomHTTPException
import logging
from typing import List
from app.auth.auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


class UserDataResponse(BaseModel):
    username: str
    extension_number: str
    role: str
    fullname: str


@router.get("/all", response_model=List[UserDataResponse])
async def get_all_users(current_user: User = Depends(get_current_user)):
    logger.info("Fetching all users")
    users = await User.find_all().to_list()
    if not users:
        logger.error("No users found")
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found",
        )
    return [
        UserDataResponse(
            username=user.username,
            extension_number=user.extension_number,
            role=user.role,
        )
        for user in users
    ]


@router.get("/", response_model=UserDataResponse)
async def get_user(current_user: User = Depends(get_current_user)):
    username = current_user.username    
    logger.info(f"Fetching user data for: {username}")
    user = await User.find_one(User.username == username)
    if not user:
        logger.error(f"User {username} not found")
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserDataResponse(
        username=user.username,
        extension_number=user.extension_number,
        role=user.role,
        fullname=user.fullname,
    )
