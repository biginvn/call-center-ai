# app/auth/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth.auth import create_access_token
from app.models.user import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class AgentLoginRequest(BaseModel):
    username: str
    password: str
    extensionNumber: str

class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/agent/login")
async def agent_login(request: AgentLoginRequest):
    logger.info(f"Attempting login for agent: {request.username}")
    user = await User.find_one(User.username == request.username)
    if not user:
        logger.error(f"User {request.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if request.password != user.password: 
        logger.error(f"Invalid password for {request.username}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role != "agent":
        logger.error(f"Role mismatch for {request.username}, expected agent")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agents can use this endpoint",
        )
    if not request.extensionNumber or len(request.extensionNumber) != 3:
        logger.error(f"Invalid extensionNumber for {request.username}: {request.extensionNumber}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension number must be a 3-digit number",
        )
    
    existing_extension = await User.find_one(User.extensionNumber == request.extensionNumber)
    
    if existing_extension:
        logger.error(f"Extension number {request.extensionNumber} is already in use by another user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension number is already in use",
        )
    
    if user.extensionNumber != request.extensionNumber:
        logger.info(f"Updating extensionNumber for {request.username} from {user.extensionNumber} to {request.extensionNumber}")
        user.extensionNumber = request.extensionNumber
        await user.save()
    logger.info(f"Login successful for {request.username}")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "username": user.username, "extensionNumber": user.extensionNumber, "token_type": "bearer", "role": user.role}

@router.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    logger.info(f"Attempting login for admin: {request.username}")
    user = await User.find_one(User.username == request.username)
    logger.info(f"Found user: {user}")  # Debug
    if not user:
        logger.error(f"User {request.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if request.password != user.password:  
        logger.error(f"Invalid password for {request.username}")
        print(request.password, user.password)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role != "admin":
        logger.error(f"Role mismatch for {request.username}, expected admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can use this endpoint",
        )
    logger.info(f"Login successful for {request.username}")
    access_token = create_access_token(data={"sub": user.username, "role": "admin"})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "username": user.username}
