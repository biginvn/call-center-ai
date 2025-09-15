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
        Bắt đầu session voicebot cho cuộc gọi
        """
        try:
            logger.info(f"Starting voicebot session for call {call.call_id}")
            
            # Tạo OpenAI Realtime session
            session_data = await self._create_openai_session()
            if not session_data:
                logger.error("Failed to create OpenAI session")
                return False
            
            # Lưu session info
            self.active_sessions[call.call_id] = {
                "session_id": session_data.id,
                "client_secret": session_data.client_secret.value,
                "call": call,
                "is_active": True
            }
            
            # Kết nối WebSocket với OpenAI
            await self._connect_openai_websocket(call.call_id)
            
            logger.info(f"Voicebot session started successfully for call {call.call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting voicebot session: {str(e)}")
            return False
    
    async def _create_openai_session(self):
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
            
            async with requests.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()
                
                session_data = response.json()
                logger.info(f"OpenAI session created: {session_data['id']}")
                return session_data
                
        except Exception as e:
            logger.error(f"Error creating OpenAI session: {str(e)}")
            return None
    
    async def _connect_openai_websocket(self, call_id: str):
        """
        Kết nối WebSocket với OpenAI Realtime API
        """
        try:
            session_info = self.active_sessions.get(call_id)
            if not session_info:
                logger.error(f"No session info found for call {call_id}")
                return
            
            # WebSocket URL cho OpenAI Realtime
            ws_url = f"wss://api.openai.com/v1/realtime/sessions/{session_info['session_id']}"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            # Kết nối WebSocket
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                session_info["websocket"] = websocket
                
                # Gửi session configuration
                await self._send_session_config(websocket)
                
                # Bắt đầu xử lý messages
                await self._handle_openai_messages(call_id, websocket)
                
        except Exception as e:
            logger.error(f"Error connecting to OpenAI WebSocket: {str(e)}")
    
    async def _send_session_config(self, websocket):
        """
        Gửi cấu hình session tới OpenAI
        """
        try:
            config_message = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "Bạn là một tổng đài viên ảo chuyên nghiệp. Hãy trả lời ngắn gọn và hữu ích.",
                    "voice": "shimmer",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    }
                }
            }
            
            await websocket.send(json.dumps(config_message))
            logger.info("Session configuration sent to OpenAI")
            
        except Exception as e:
            logger.error(f"Error sending session config: {str(e)}")
    
    async def _handle_openai_messages(self, call_id: str, websocket):
        """
        Xử lý messages từ OpenAI Realtime API
        """
        try:
            call = get_call(call_id)
            if not call:
                logger.error(f"Call {call_id} not found")
                return
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                message_type = data.get("type")
                
                if message_type == "response.audio.delta":
                    # Xử lý audio response từ AI
                    await self._handle_ai_audio_response(call, data)
                    
                elif message_type == "conversation.item.input_audio_transcription.completed":
                    # Xử lý transcription của user
                    transcription = data.get("transcription", "")
                    logger.info(f"User said: {transcription}")
                    
                elif message_type == "error":
                    logger.error(f"OpenAI error: {data}")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"OpenAI WebSocket connection closed for call {call_id}")
        except Exception as e:
            logger.error(f"Error handling OpenAI messages: {str(e)}")
    
    async def _handle_ai_audio_response(self, call: CallSession, data: dict):
        """
        Xử lý audio response từ AI và phát qua Asterisk
        """
        try:
            audio_data = data.get("delta", "")
            if not audio_data:
                return
            
            # Decode base64 audio data
            import base64
            audio_bytes = base64.b64decode(audio_data)
            
            # Lưu audio tạm thời
            temp_file = f"/tmp/voicebot_response_{call.call_id}.wav"
            with open(temp_file, "wb") as f:
                f.write(audio_bytes)
            
            # Phát audio qua Asterisk channel
            if call.agent_chan:
                await self._play_audio_to_channel(call.agent_chan, temp_file)
            
        except Exception as e:
            logger.error(f"Error handling AI audio response: {str(e)}")
    
    async def _play_audio_to_channel(self, channel_id: str, audio_file: str):
        """
        Phát audio file qua Asterisk channel
        """
        try:
            # Sử dụng ARI để phát audio
            response = requests.post(
                f"{BASE_URL}/channels/{channel_id}/play",
                auth=AUTH,
                params={
                    "media": f"sound:{audio_file}",
                    "lang": "en"
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Playing audio to channel {channel_id}")
            else:
                logger.error(f"Failed to play audio: {response.text}")
                
        except Exception as e:
            logger.error(f"Error playing audio to channel: {str(e)}")
    
    async def send_audio_to_ai(self, call_id: str, audio_data: bytes):
        """
        Gửi audio từ user tới OpenAI
        """
        try:
            session_info = self.active_sessions.get(call_id)
            if not session_info or not session_info.get("websocket"):
                logger.error(f"No active session for call {call_id}")
                return
            
            websocket = session_info["websocket"]
            
            # Encode audio thành base64
            import base64
            audio_b64 = base64.b64encode(audio_data).decode()
            
            # Gửi audio tới OpenAI
            message = {
                "type": "input_audio_buffer.append",
                "audio": audio_b64
            }
            
            await websocket.send(json.dumps(message))
            logger.info(f"Audio sent to OpenAI for call {call_id}")
            
        except Exception as e:
            logger.error(f"Error sending audio to AI: {str(e)}")
    
    async def end_voicebot_session(self, call_id: str):
        """
        Kết thúc voicebot session
        """
        try:
            session_info = self.active_sessions.get(call_id)
            if not session_info:
                return
            
            # Đóng WebSocket connection
            if session_info.get("websocket"):
                await session_info["websocket"].close()
            
            # Xóa session
            del self.active_sessions[call_id]
            
            logger.info(f"Voicebot session ended for call {call_id}")
            
        except Exception as e:
            logger.error(f"Error ending voicebot session: {str(e)}")
    
    def is_voicebot_extension(self, extension: str) -> bool:
        """
        Kiểm tra xem extension có phải là voicebot không
        """
        return extension == self.voicebot_extension or extension == "1000"
