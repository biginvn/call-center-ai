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




@router.post("/finish")
async def finish_session_endpoint(
    current_user: User = Depends(get_current_user),
    audio_url: str = ""
):

    await finish_openai_bot_session(current_user, audio_url, current_user.client_id)
    return {"message": "Session finished successfully"}

@router.get("/session", response_model=SessionResponse)
async def get_ai_token(current_user: User = Depends(get_current_user)):
    try:
        # Check usage limit
        client = current_user.client_id
        if hasattr(client, 'fetch'): # Ensure client is fully fetched if it's a Link
             # Note: By default fetching might be needed if not auto-fetched in dependency
             # However, current_user setup usually fetches linked docs or we manually fetch.
             # In user_api get_all_users does fetch. In get_current_user it might not deep fetch.
             # Safest is to rely on what's available or fetch if needed.
             # But here current_user.client_id is likely a Link or the object.
             # Let's assume we might need to fetch if it's a Link and not loaded.
             # Beanie Link handling:
             pass 

        # Reload client to get latest usage
        if current_user.client_id and hasattr(current_user.client_id, "id"):
             # It acts like an object
             from app.models.client import Client
             client = await Client.get(current_user.client_id.id)
             if client.voicebot_usage_limit != -1 and client.voicebot_usage_total >= client.voicebot_usage_limit:
                 raise HTTPException(status_code=403, detail="Voicebot usage limit exceeded")

        ai_doc = await AiRepository.get_ai_instruction(current_user.client_id)
        if not ai_doc:
            raise HTTPException(status_code=404, detail="There are no AI Config.")
        session_data = await create_openai_session(ai_doc.instructions, ai_doc.voice)
        return session_data
    
    except HTTPException as ne:
        raise ne
    except Exception as e:
        logger.error(f"Error getting AI token: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")