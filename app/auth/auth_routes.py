from fastapi import APIRouter, status
from pydantic import BaseModel
from app.auth.auth import create_access_token, create_refresh_token
from app.models.user import User
from app.auth.exceptions import CustomHTTPException
from app.models.token import RefreshToken
from datetime import datetime, timedelta
from app.core.config import settings
from jose import jwt, JWTError
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
    user = await User.find_one(User.username == request.username)
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
    # if not request.extension_number or len(request.extension_number) != 3:
    #     logger.error(
    #         f"Invalid extension_number for {request.username}: {request.extension_number}"
    #     )
    #     raise CustomHTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Extension number must be a 3-digit number",
    #     )

    existing_extension = await User.find_one(
        User.extension_number == request.extension_number
    )

    if existing_extension:
        logger.error(
            f"Extension number {request.extension_number} is already in use by another user"
        )
        raise CustomHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension number is already in use",
        )

    if user.extension_number != request.extension_number:
        logger.info(
            f"Updating extension_number for {request.username} from {user.extension_number} to {request.extension_number}"
        )
        user.extension_number = request.extension_number
        await user.save()

    logger.info(f"Login successful for {request.username}")
    access_token = create_access_token(data={"sub": user.username, "token_type": "access"})
    refresh_token = create_refresh_token(data={"sub": user.username, "token_type": "refresh"})
    db_refresh_token = RefreshToken(
        refresh_token=refresh_token,
        username=user.username,
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    await db_refresh_token.insert()
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
    user = await User.find_one(User.username == request.username)
    logger.info(f"Found user: {user}")
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

    db_token = await RefreshToken.find_one(RefreshToken.refresh_token == refresh_token)

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
    except jwt.JWTError:
        raise credentials_exception
    access_token = create_access_token(data={"sub": username})
    await db_token.delete()

    new_refresh_token = create_refresh_token(data={"sub": username})
    db_new_token = RefreshToken(
        refresh_token=new_refresh_token,
        username=username,
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    await db_new_token.insert()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
