from fastapi import APIRouter, Depends, HTTPException
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.voicebot_service import VoiceBotService
import logging

router = APIRouter(prefix="/voicebot", tags=["VoiceBot"])
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_voicebot_status(current_user: User = Depends(get_current_user)):
    """
    Lấy trạng thái của VoiceBot service
    """
    try:
        # Lấy voicebot service từ app state
        from app.main import app
        voicebot_service = getattr(app.state, 'voicebot_service', None)
        
        if not voicebot_service:
            raise HTTPException(status_code=503, detail="VoiceBot service not initialized")
        
        active_sessions = len(voicebot_service.active_sessions)
        
        return {
            "status": "active",
            "active_sessions": active_sessions,
            "voicebot_extension": voicebot_service.voicebot_extension,
            "message": "VoiceBot service is running"
        }
        
    except Exception as e:
        logger.error(f"Error getting voicebot status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/test")
async def test_voicebot(current_user: User = Depends(get_current_user)):
    """
    Test VoiceBot service (chỉ dành cho testing)
    """
    try:
        # Lấy voicebot service từ app state
        from app.main import app
        voicebot_service = getattr(app.state, 'voicebot_service', None)
        
        if not voicebot_service:
            raise HTTPException(status_code=503, detail="VoiceBot service not initialized")
        
        # Test tạo OpenAI session
        session_data = await voicebot_service._create_openai_session()
        
        if session_data:
            return {
                "status": "success",
                "message": "VoiceBot service test passed",
                "openai_session_id": session_data.get("id", "unknown")
            }
        else:
            return {
                "status": "error",
                "message": "Failed to create OpenAI session"
            }
            
    except Exception as e:
        logger.error(f"Error testing voicebot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/extensions")
async def get_voicebot_extensions(current_user: User = Depends(get_current_user)):
    """
    Lấy danh sách extensions có thể gọi VoiceBot
    """
    try:
        return {
            "voicebot_extensions": [
                {
                    "extension": "voicebot",
                    "number": "1000",
                    "description": "VoiceBot extension for AI calls"
                }
            ],
            "usage": "Gọi extension 1000 hoặc 'voicebot' để kết nối với AI VoiceBot"
        }
        
    except Exception as e:
        logger.error(f"Error getting voicebot extensions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
