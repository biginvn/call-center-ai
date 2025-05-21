from fastapi import APIRouter, status, Depends
from pydantic import BaseModel
from app.models.user import User
from app.auth.exceptions import CustomHTTPException
import logging
from typing import List, Optional
from app.auth.auth import get_current_user
from app.dependencies.active_user import remove_active_user
from app.services.extension_service import ExtensionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logout", tags=["logout"])

class UserDataResponse(BaseModel):
    username: str
    extension_number: Optional[str]

@router.patch("/", response_model=UserDataResponse)
async def update_current_user_extension(current_user: User = Depends(get_current_user)):
    old_extension_number = current_user.extension_number
    extension_service = ExtensionService()
    if old_extension_number:
            await extension_service.update_extension_availability(old_extension_number, True)  

            
    current_user.extension_number = ""
    await current_user.save()
    await remove_active_user(current_user)

    return current_user
    