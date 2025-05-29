from app.call_bot.call_bot import SessionRequest, SessionResponse, create_openai_session
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth.auth import get_current_user
from app.auth.exceptions import CustomHTTPException
from app.models.user import User
import os
import httpx
import logging

router = APIRouter(prefix="/realtime", tags=["OpenAI Realtime"])

logger = logging.getLogger(__name__)



@router.post("/session", response_model=SessionResponse)
async def create_session_endpoint(
    req: SessionRequest
):
    try:
        session_data = await create_openai_session(req.instructions)
        return session_data
    except Exception as e:
        logger.error(f"Error creating OpenAI session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
