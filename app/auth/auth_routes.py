from fastapi import APIRouter, status
from pydantic import BaseModel
from app.auth.auth import create_access_token, create_refresh_token
from app.dependencies.active_user import add_active_user
from app.models.user import User
from app.models.active import ActiveUser
from app.auth.exceptions import CustomHTTPException
from app.repositories.user_repository import UserRepository  # Import mới
from datetime import datetime, timedelta
from app.core.config import settings
from jose import jwt, JWTError
from app.services.extension_service import ExtensionService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/login", tags=["login"])


class AgentLoginRequest(BaseModel):
    username: str
    password: str
    extension_number: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/agent")
async def agent_login(request: AgentLoginRequest):
    logger.info(f"Attempting login for agent: {request.username}")
    user = await UserRepository.get_user_by_username(request.username)

    if not user:
        logger.error(f"User {request.username} not found")
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if request.password != user.password:
        logger.error(f"Invalid password for {request.username}")
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role != "agent":
        logger.error(f"Role mismatch for {request.username}, expected agent")
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agents can use this endpoint",
        )

    existing_extension = await UserRepository.get_user_by_extension_number(request.extension_number)
    if existing_extension:
        logger.error(
            f"Extension number {request.extension_number} is already in use by another user"
        )
        raise CustomHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension number is already in use",
        )

    if user.extension_number == "":
        logger.info(
            f"Updating extension_number for {request.username} from {user.extension_number} to {request.extension_number}"
        )
        user = await UserRepository.update_user_extension_number(user, request.extension_number)
    await add_active_user(user)
    logger.info(f"Login successful for {request.username}")
    access_token = create_access_token(data={"sub": user.username, "token_type": "access"})
    refresh_token = create_refresh_token(data={"sub": user.username, "token_type": "refresh"})
    await UserRepository.save_refresh_token(user.username, refresh_token)
    
    extension_service = ExtensionService()
    await extension_service.update_extension_availability(
        request.extension_number, False
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "username": user.username,
        "extension_number": user.extension_number,
        "token_type": "bearer",
        "role": user.role,
    }


@router.post("/admin")
async def admin_login(request: AdminLoginRequest):
    logger.info(f"Attempting login for admin: {request.username}")
    user = await UserRepository.get_user_by_username(request.username)
    if not user:
        logger.error(f"User {request.username} not found")
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if request.password != user.password:
        logger.error(f"Invalid password for {request.username}")
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role != "admin":
        logger.error(f"Role mismatch for {request.username}, expected admin")
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can use this endpoint",
        )

    logger.info(f"Login successful for {request.username}")
    access_token = create_access_token(data={"sub": user.username, "role": "admin"})
    refresh_token = create_refresh_token(data={"sub": user.username, "role": "admin"})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }


@router.post("/refresh")
async def refresh_access_token(refresh_token: str):
    credentials_exception = CustomHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    db_token = await UserRepository.get_refresh_token(refresh_token)
    if not db_token or db_token.expires_at < datetime.utcnow():
        logger.error("Invalid or expired refresh token")
        raise credentials_exception

    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        if username is None or token_type != "refresh":
            logger.error("Invalid refresh token payload")
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    access_token = create_access_token(data={"sub": username})
    await UserRepository.delete_refresh_token(db_token)
    new_refresh_token = create_refresh_token(data={"sub": username})
    await UserRepository.save_refresh_token(username, new_refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }