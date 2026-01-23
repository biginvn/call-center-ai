from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from app.auth.auth import get_current_user
from app.services.user_service import UserService
from app.models.user import User
from app.models.client import Client
from app.auth.exceptions import CustomHTTPException
from app.repositories.user_repository import UserRepository
from app.services.extension_service import ExtensionService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])

class UserDataResponse(BaseModel):
    username: str
    extension_number: str | None
    role: str
    fullname: str | None
    client_name: str

class VoicebotLimitResponse(BaseModel):
    voicebot_usage_limit: int  # -1 means unlimited
    voicebot_usage_total: int
    remaining_time: int | None  # None if unlimited, otherwise remaining seconds
    is_unlimited: bool

class AddUsageRequest(BaseModel):
    duration: int  # Thời gian cần thêm (giây). Có thể âm để giảm usage
class CreateUserRequest(BaseModel):
    username: str
    password: str = "123456"
    fullname: str
    email: str = "mock@email.com"
    role: str   = "agent"

@router.get("/all", response_model=List[UserDataResponse])
async def get_all_users(current_user: User = Depends(get_current_user)):
    logger.info("Fetching all users")
    user_service = UserService()
    users = await user_service.get_all_users(current_user)
    for user in users:
        await user.fetch_link(User.client_id)
    return [
        UserDataResponse(
            username=user.username,
            extension_number=user.extension_number,
            role=user.role,
            fullname=user.fullname,
            client_name=user.client_id.name
        )
        for user in users
    ]

@router.get("/", response_model=UserDataResponse)
async def get_user(current_user: User = Depends(get_current_user)):
    logger.info(f"Fetching user data for: {current_user.username}")
    user_service = UserService()
    user = await user_service.get_user(current_user.username)
    await user.fetch_link(User.client_id)
    return UserDataResponse(
        username=user.username,
        extension_number=user.extension_number,
        role=user.role,
        fullname=user.fullname,
        client_name=user.client_id.name
    )

@router.get("/limit", response_model=VoicebotLimitResponse)
async def get_user_voicebot_limit(current_user: User = Depends(get_current_user)):
    """
    ## Lấy thông tin voicebot time limit của user hiện tại
    
    **Quyền**: Tất cả user đều có thể xem limit của chính họ
    
    **Returns**: 
    - `voicebot_usage_limit`: Giới hạn thời gian (giây). -1 = không giới hạn
    - `voicebot_usage_total`: Tổng thời gian đã sử dụng (giây)
    - `remaining_time`: Thời gian còn lại (giây). null nếu không giới hạn
    - `is_unlimited`: true nếu không giới hạn
    """
    logger.info(f"Fetching voicebot limit for user: {current_user.username}")
    
    # Fetch client information
    await current_user.fetch_link(User.client_id)
    if not current_user.client_id:
        raise HTTPException(status_code=404, detail="User không có client_id")
    
    # Get client with latest usage data
    client = await Client.get(current_user.client_id.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client không tồn tại")
    
    is_unlimited = client.voicebot_usage_limit == -1
    remaining_time = None if is_unlimited else max(0, client.voicebot_usage_limit - client.voicebot_usage_total)
    
    return VoicebotLimitResponse(
        voicebot_usage_limit=client.voicebot_usage_limit,
        voicebot_usage_total=client.voicebot_usage_total,
        remaining_time=remaining_time,
        is_unlimited=is_unlimited
    )

@router.post("/usage", response_model=dict)
async def add_user_usage(
    request: AddUsageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    ## Thêm usage cho user hiện tại
    
    **Quyền**: Tất cả user đều có thể thêm usage cho chính họ
    
    **Request Body**:
    - `duration`: Thời gian cần thêm (giây). Có thể là số âm để giảm usage
    
    **Returns**: 
    - `message`: Thông báo kết quả
    - `voicebot_usage_total`: Tổng usage sau khi cập nhật
    - `added_duration`: Thời gian đã thêm/giảm
    - `remaining_time`: Thời gian còn lại (nếu có limit)
    
    **Ví dụ**:
    - Thêm 300 giây: `{"duration": 300}`
    - Giảm 100 giây: `{"duration": -100}`
    """
    logger.info(f"Adding usage for user: {current_user.username}, duration: {request.duration}")
    
    # Fetch client information
    await current_user.fetch_link(User.client_id)
    if not current_user.client_id:
        raise HTTPException(status_code=404, detail="User không có client_id")
    
    # Get client
    client = await Client.get(current_user.client_id.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client không tồn tại")
    
    # Cập nhật usage
    old_usage = client.voicebot_usage_total
    client.voicebot_usage_total += request.duration
    
    # Đảm bảo usage không âm
    if client.voicebot_usage_total < 0:
        client.voicebot_usage_total = 0
    
    await client.save()
    
    # Tính remaining_time
    is_unlimited = client.voicebot_usage_limit == -1
    remaining_time = None if is_unlimited else max(0, client.voicebot_usage_limit - client.voicebot_usage_total)
    
    logger.info(f"Updated usage: {old_usage} -> {client.voicebot_usage_total}")
    
    return {
        "message": "Usage đã được cập nhật thành công",
        "voicebot_usage_total": client.voicebot_usage_total,
        "added_duration": request.duration,
        "remaining_time": remaining_time
    }

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
    await extension_service.update_extension_availability(request.extension, False, user)
    return "User connected successfully"

@router.post("/disconnect")
async def on_connect_user(request:ConnectRequest):
    user = await UserRepository.get_user_by_username(request.username)
    await UserRepository.update_user_extension_number(user, "")
    extension_service = ExtensionService()
    await extension_service.update_extension_availability(request.extension, True, None)
    return "user disconnected"

@router.post("/create")
async def create_user(request:CreateUserRequest, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not authorized to create users")
    user = await UserRepository.create_user(current_user.client_id, request.username, request.password, request.fullname, request.email, request.role)
    return user

@router.delete("/delete/{username}")
async def delete_user(username: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not authorized to delete users")
    await UserRepository.delete_user(username)
    return "User deleted successfully"