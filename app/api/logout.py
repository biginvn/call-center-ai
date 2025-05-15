from fastapi import APIRouter, status, Depends
from pydantic import BaseModel
from app.models.user import User
from app.auth.exceptions import CustomHTTPException
import logging
from typing import List, Optional
from app.auth.auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logout", tags=["logout"])

class UserDataResponse(BaseModel):
    username: str
    extension_number: Optional[str]

@router.patch("/", response_model=UserDataResponse)
async def update_current_user_extension(current_user: User = Depends(get_current_user)):
    logger.info(f"Updating extension number for user: {current_user.id}")

    current_user.extension_number = ""
    await current_user.save()

    return current_user
    