from app.call_bot.call_bot import FinishSessionRequest, SessionRequest, SessionResponse, create_openai_session, finish_openai_bot_session
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth.auth import get_current_user
from app.auth.exceptions import CustomHTTPException
from app.models.user import User
from app.repositories.ai_repository import AiRepository
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
        await AiRepository.update_ai_instruction(
        instructions=req.instructions, voice=req.voice
    )   
        print(f"Creating OpenAI session with instructions: {req.instructions} and voice: {req.voice}")
        session_data = await create_openai_session(req.instructions, req.voice)
        return session_data
    except Exception as e:
        logger.error(f"Error creating OpenAI session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




@router.post("/finish")
async def finish_session_endpoint(
    current_user: User = Depends(get_current_user),
    audio_url: str = ""
):
    await finish_openai_bot_session(current_user, audio_url)
    return {"message": "Session finished successfully"}