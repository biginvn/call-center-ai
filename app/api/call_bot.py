from app.call_bot.call_bot import FinishSessionRequest, SessionRequest, SessionResponse, create_openai_session, finish_openai_bot_session
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth.auth import get_current_user
from app.auth.exceptions import CustomHTTPException
from app.models.user import User
from app.repositories.ai_repository import AiRepository
from app.models.ai import AI
import os
import httpx
import logging

router = APIRouter(prefix="/realtime", tags=["OpenAI Realtime"])

logger = logging.getLogger(__name__)



@router.post("/config")
async def create_session_endpoint(
    req: SessionRequest
):
    try:

        print(f"Creating OpenAI session with instructions: {req.instructions} and voice: {req.voice}")

        await AiRepository.update_ai_instruction(
        instructions=req.instructions, voice=req.voice
    )   
        return req
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

@router.get("/session", response_model=SessionResponse)
async def get_ai_token(user: User = Depends(get_current_user)):
    try:
        ai_doc = await AI.find_one()
        if not ai_doc:
            raise HTTPException(status_code=404, detail="There are no AI Config.")
        session_data = await create_openai_session(ai_doc.instructions, ai_doc.voice)
        return session_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")