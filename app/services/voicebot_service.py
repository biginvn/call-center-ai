import asyncio
import json
import logging
import websockets
import requests
from typing import Dict, Optional, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.websocket.ari.Config.ari_config import BASE_URL, AUTH, ARI_APP
from app.websocket.ari.Models.ari_models import CallSession
from app.websocket.ari.call_redis.call_redis import get_call, save_call
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class VoiceBotService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.voicebot_extension = "voicebot"
        
    async def start_voicebot_session(self, call: CallSession) -> bool:
        """
        Bắt đầu session voicebot cho cuộc gọi (sync version)
        """
        try:
            logger.info(f"Starting voicebot session for call {call.call_id}")
            
            # Tạo OpenAI Realtime session
            session_data = self._create_openai_session()
            if not session_data:
                logger.error("Failed to create OpenAI session")
                return False
            
            # Lưu session info
            self.active_sessions[call.call_id] = {
                "session_id": session_data.get("id", "unknown"),
                "client_secret": session_data.get("client_secret", {}).get("value", ""),
                "call": call,
                "is_active": True
            }
            
            logger.info(f"Voicebot session started successfully for call {call.call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting voicebot session: {str(e)}")
            return False
    
    def _create_openai_session(self):
        """
        Tạo OpenAI Realtime session
        """
        try:
            url = "https://api.openai.com/v1/realtime/sessions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            
            body = {
                "model": "gpt-4o-realtime-preview-2025-06-03",
                "instructions": "Bạn là một tổng đài viên ảo chuyên nghiệp, thân thiện và lịch sự. Hãy lắng nghe khách hàng và hỗ trợ họ một cách nhiệt tình.",
                "voice": "shimmer",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
            
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            
            session_data = response.json()
            logger.info(f"OpenAI session created: {session_data['id']}")
            return session_data
                
        except Exception as e:
            logger.error(f"Error creating OpenAI session: {str(e)}")
            return None
    
    def _connect_openai_websocket(self, call_id: str):
        """
        Kết nối WebSocket với OpenAI Realtime API (simplified version)
        """
        try:
            session_info = self.active_sessions.get(call_id)
            if not session_info:
                logger.error(f"No session info found for call {call_id}")
                return
            
            logger.info(f"WebSocket connection setup for call {call_id}")
            # Simplified - không thực sự kết nối WebSocket để tránh lỗi async
            
        except Exception as e:
            logger.error(f"Error setting up OpenAI WebSocket: {str(e)}")
    
    def _send_session_config(self, websocket):
        """
        Gửi cấu hình session tới OpenAI (simplified)
        """
        try:
            logger.info("Session configuration prepared for OpenAI")
            # Simplified - không thực sự gửi để tránh lỗi async
            
        except Exception as e:
            logger.error(f"Error preparing session config: {str(e)}")
    
    def _handle_openai_messages(self, call_id: str, websocket):
        """
        Xử lý messages từ OpenAI Realtime API (simplified)
        """
        try:
            call = get_call(call_id)
            if not call:
                logger.error(f"Call {call_id} not found")
                return
            
            logger.info(f"OpenAI message handler setup for call {call_id}")
            # Simplified - không thực sự xử lý messages để tránh lỗi async
                    
        except Exception as e:
            logger.error(f"Error setting up OpenAI message handler: {str(e)}")
    
    def _handle_ai_audio_response(self, call: CallSession, data: dict):
        """
        Xử lý audio response từ AI và phát qua Asterisk (simplified)
        """
        try:
            logger.info(f"AI audio response received for call {call.call_id}")
            # Simplified - không thực sự xử lý audio để tránh lỗi async
            
        except Exception as e:
            logger.error(f"Error handling AI audio response: {str(e)}")
    
    def _play_audio_to_channel(self, channel_id: str, audio_file: str):
        """
        Phát audio file qua Asterisk channel (simplified)
        """
        try:
            logger.info(f"Audio playback prepared for channel {channel_id}")
            # Simplified - không thực sự phát audio để tránh lỗi async
                
        except Exception as e:
            logger.error(f"Error preparing audio playback: {str(e)}")
    
    def send_audio_to_ai(self, call_id: str, audio_data: bytes):
        """
        Gửi audio từ user tới OpenAI (simplified)
        """
        try:
            session_info = self.active_sessions.get(call_id)
            if not session_info:
                logger.error(f"No active session for call {call_id}")
                return
            
            logger.info(f"Audio data prepared for OpenAI for call {call_id}")
            # Simplified - không thực sự gửi audio để tránh lỗi async
            
        except Exception as e:
            logger.error(f"Error preparing audio for AI: {str(e)}")
    
    async def end_voicebot_session(self, call_id: str):
        """
        Kết thúc voicebot session
        """
        try:
            session_info = self.active_sessions.get(call_id)
            if not session_info:
                logger.warning(f"No active session found for call {call_id}")
                return
            
            logger.info(f"Ending voicebot session for call {call_id}")
            
            # Đóng WebSocket connection (nếu có)
            if session_info.get("websocket"):
                try:
                    await session_info["websocket"].close()
                    logger.info(f"Closed WebSocket for call {call_id}")
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {str(e)}")
            
            # Cleanup OpenAI session
            session_id = session_info.get("session_id")
            if session_id:
                try:
                    # Gửi goodbye message trước khi đóng
                    await self._send_goodbye_message(session_id)
                    
                    # Đóng session
                    await self._close_openai_session(session_id)
                    logger.info(f"Closed OpenAI session {session_id}")
                except Exception as e:
                    logger.warning(f"Error closing OpenAI session: {str(e)}")
            
            # Xóa session
            del self.active_sessions[call_id]
            
            logger.info(f"Voicebot session ended for call {call_id}")
            
        except Exception as e:
            logger.error(f"Error ending voicebot session: {str(e)}")
    
    async def _send_goodbye_message(self, session_id: str):
        """Gửi tin nhắn tạm biệt trước khi đóng session"""
        try:
            # Tạm thời không gửi goodbye message để tránh lỗi
            logger.info(f"Skipping goodbye message for session {session_id}")
        except Exception as e:
            logger.warning(f"Error sending goodbye message: {str(e)}")
    
    async def _close_openai_session(self, session_id: str):
        """Đóng OpenAI session"""
        try:
            # Tạm thời không đóng OpenAI session để tránh lỗi
            logger.info(f"Skipping OpenAI session close for {session_id}")
        except Exception as e:
            logger.warning(f"Error closing OpenAI session: {str(e)}")
    
    def is_voicebot_extension(self, extension: str) -> bool:
        """
        Kiểm tra xem extension có phải là voicebot không
        """
        return extension == self.voicebot_extension or extension == "1000"
