from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.auth.auth import create_access_token, get_current_user
from app.core.database import init_db, close_db, get_database
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class AgentLoginRequest(BaseModel):
    username: str
    password: str
    extensionNumber: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.on_event("startup")
async def startup_event():
    await init_db()


@router.on_event("shutdown")
async def shutdown_event():
    await close_db()


@router.post("/login/agent")
async def agent_login(request: AgentLoginRequest):
    user = await User.find_one(User.username == request.username)
    
    if user.role != "agent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an agent",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.extensionNumber:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension number is required",
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/admin")
async def admin_login(request: AdminLoginRequest):
    user = await User.find_one(User.username == request.username)
   
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can use this endpoint",
        )
    access_token = create_access_token(data={"sub": user.username, "role": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}
