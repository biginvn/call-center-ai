import asyncio
import websockets
import json
import logging
import base64
import requests
import os
from typing import Dict, Callable
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIRealtimeService:
    """Service xử lý OpenAI Realtime API cho speech-to-speech conversation"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o-realtime-preview-2024-12-17"
        self.base_url = "wss://api.openai.com/v1/realtime"
        
        # Quản lý các kết nối realtime
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.conversation_histories: Dict[str, list] = {}
        self.audio_handlers: Dict[str, Callable] = {}
        
        # Backend URL để lấy ephemeral token
        self.backend_url = os.getenv("BACKEND_URL", "https://callpilot.bigin.top/api")
        
        # Lưu login session để logout
        self._login_session = None
        
        # Cấu hình
        self.system_prompt = """Bạn là một trợ lý AI thông minh và hữu ích. 

Hướng dẫn quan trọng:
- Giữ câu trả lời ngắn gọn và súc tích (tối đa 2-3 câu) vì đây là cuộc gọi điện thoại
- Nói chuyện một cách tự nhiên và thân thiện
- Trả lời bằng tiếng Việt trừ khi được yêu cầu khác
- Nếu không hiểu câu hỏi, hãy yêu cầu người dùng nói rõ hơn
- Luôn lịch sự và chuyên nghiệp
- Tránh đưa ra lời khuyên y tế, pháp lý hoặc tài chính quan trọng
- Nếu cần thông tin chi tiết, hãy đề xuất người dùng liên hệ với chuyên gia
- Khi người dùng nói lời tạm biệt, hãy chúc họ một ngày tốt lành và kết thúc cuộc trò chuyện"""
    
    async def _get_ephemeral_token(self) -> str:
        """Lấy ephemeral session token (enToken) từ backend"""
        try:
            logger.info(f"Bắt đầu lấy ephemeral token từ backend: {self.backend_url}")
            
            session = requests.Session()
            session.timeout = 10  # 10 giây timeout
            
            username = os.getenv("OPENAI_SESSION_USER", "volkan")
            password = os.getenv("OPENAI_SESSION_PASS", "volkan123")
            extension_number = os.getenv("OPENAI_SESSION_EXTENSION", "116")
            
            logger.info(f"Đang login với username: {username}, extension: {extension_number}")
            
            # 1. Login để lấy session
            login_resp = session.post(
                f"{self.backend_url}/login/admin", 
                json={
                    "username": username,
                    "password": password
                },
                timeout=10
            )
            login_resp.raise_for_status()
            login_data = login_resp.json()
            access_token = login_data.get("access_token")
            logger.info("Login thành công")
            
            if not access_token:
                raise Exception("Không nhận được access_token từ login response")
            
            # 2. Lấy ephemeral token với Bearer token
            logger.info("Đang lấy ephemeral token...")
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            session_resp = session.get(
                f"{self.backend_url}/realtime/session",
                headers=headers,
                timeout=10
            )
            session_resp.raise_for_status()
            
            response_data = session_resp.json()
            en_token = response_data["client_secret"]["value"]
            
            logger.info(f"Đã lấy ephemeral token thành công: {en_token[:20]}...")
            
            # Lưu session để logout sau
            self._login_session = session
            return en_token
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout khi lấy ephemeral token: {str(e)}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Lỗi kết nối khi lấy ephemeral token: {str(e)}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error khi lấy ephemeral token: {str(e)}")
            raise
        except KeyError as e:
            logger.error(f"Không tìm thấy client_secret trong response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Lỗi lấy ephemeral token: {str(e)}")
            raise
    
    async def _logout_session(self):
        """Logout khỏi backend session"""
        try:
            if self._login_session:
                logger.info("Đang logout khỏi backend...")
                logout_resp = self._login_session.post(
                    f"{self.backend_url}/logout",
                    timeout=10
                )
                logout_resp.raise_for_status()
                logger.info("Logout thành công")
                self._login_session = None
        except Exception as e:
            logger.warning(f"Lỗi logout: {str(e)}")
    
    async def create_realtime_session(self, session_id: str, channel_id: str) -> bool:
        """
        Tạo session realtime mới cho cuộc gọi
        
        Args:
            session_id: ID của session
            channel_id: ID của channel Asterisk
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            logger.info(f"Tạo realtime session: {session_id} cho channel {channel_id}")
            
            # Thử lấy ephemeral token từ backend, nếu fail thì dùng API key
            use_ephemeral = True
            try:
                en_token = await self._get_ephemeral_token()
                auth_token = en_token
                logger.info("Sử dụng ephemeral token")
            except Exception as e:
                logger.warning(f"Không thể lấy ephemeral token, sử dụng API key: {str(e)}")
                auth_token = self.api_key
                use_ephemeral = False
                logger.info("Sử dụng API key")
            
            # Kết nối tới OpenAI Realtime API
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            websocket = await websockets.connect(
                self.base_url,
                additional_headers=headers
            )
            
            self.active_connections[session_id] = websocket
            self.conversation_histories[session_id] = []
            
            # Khởi tạo session
            await self._initialize_session(websocket, session_id)
            
            # Bắt đầu lắng nghe messages
            asyncio.create_task(self._listen_for_messages(session_id, channel_id))
            
            token_type = "ephemeral token" if use_ephemeral else "API key"
            logger.info(f"Realtime session tạo thành công với {token_type}: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi tạo realtime session {session_id}: {str(e)}")
            return False
    
    async def _initialize_session(self, websocket: websockets.WebSocketServerProtocol, session_id: str):
        """Khởi tạo session với OpenAI Realtime API"""
        try:
            # Gửi session configuration
            config_message = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": self.system_prompt,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 200
                    },
                    "tools": [],
                    "tool_choice": "auto",
                    "temperature": 0.7,
                    "max_response_output_tokens": 150
                }
            }
            
            await websocket.send(json.dumps(config_message))
            logger.info(f"Đã gửi config cho session: {session_id}")
            
        except Exception as e:
            logger.error(f"Lỗi khởi tạo session {session_id}: {str(e)}")
    
    async def _listen_for_messages(self, session_id: str, channel_id: str):
        """Lắng nghe messages từ OpenAI Realtime API"""
        try:
            websocket = self.active_connections.get(session_id)
            if not websocket:
                logger.error(f"Không tìm thấy websocket cho session: {session_id}")
                return
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    await self._handle_realtime_message(session_id, channel_id, data)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"WebSocket connection đóng cho session: {session_id}")
                    break
                except websockets.exceptions.WebSocketException as e:
                    logger.error(f"WebSocket exception: {str(e)}")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Lỗi parse JSON message: {str(e)}")
                except Exception as e:
                    logger.error(f"Lỗi xử lý message: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Lỗi trong _listen_for_messages: {str(e)}")
        finally:
            await self._cleanup_session(session_id)
    
    async def _handle_realtime_message(self, session_id: str, channel_id: str, data: dict):
        """Xử lý message từ OpenAI Realtime API"""
        try:
            message_type = data.get("type")
            
            if message_type == "conversation.item.input_audio_buffer.committed":
                # Audio input đã được xử lý
                logger.debug(f"Audio input committed cho session: {session_id}")
                
            elif message_type == "conversation.item.input_audio_buffer.speech_started":
                # Bắt đầu nói
                logger.info(f"Người dùng bắt đầu nói - session: {session_id}")
                
            elif message_type == "conversation.item.input_audio_buffer.speech_stopped":
                # Kết thúc nói
                logger.info(f"Người dùng kết thúc nói - session: {session_id}")
                
            elif message_type == "conversation.item.transcript.completed":
                # Transcript hoàn thành
                transcript = data.get("transcript", "")
                logger.info(f"Transcript: {transcript}")
                
                # Cập nhật lịch sử hội thoại
                if session_id in self.conversation_histories:
                    self.conversation_histories[session_id].append({
                        "role": "user",
                        "content": transcript
                    })
                
            elif message_type == "conversation.item.response.output_audio_buffer.speech_started":
                # AI bắt đầu nói
                logger.info(f"AI bắt đầu nói - session: {session_id}")
                
            elif message_type == "conversation.item.response.output_audio_buffer.audio":
                # Audio output từ AI
                audio_data = data.get("data")
                if audio_data and channel_id in self.audio_handlers:
                    # Gọi handler để phát audio
                    await self.audio_handlers[channel_id](audio_data)
                
            elif message_type == "conversation.item.response.output_audio_buffer.speech_stopped":
                # AI kết thúc nói
                logger.info(f"AI kết thúc nói - session: {session_id}")
                
            elif message_type == "conversation.item.response.completed":
                # Response hoàn thành
                response_text = data.get("response", {}).get("output", "")
                logger.info(f"AI response: {response_text}")
                
                # Cập nhật lịch sử hội thoại
                if session_id in self.conversation_histories:
                    self.conversation_histories[session_id].append({
                        "role": "assistant",
                        "content": response_text
                    })
                
            elif message_type == "error":
                # Lỗi từ API
                error_info = data.get("error", {})
                logger.error(f"Lỗi từ OpenAI Realtime API: {error_info}")
                
            else:
                logger.debug(f"Message type không xử lý: {message_type}")
                
        except Exception as e:
            logger.error(f"Lỗi xử lý realtime message: {str(e)}")
    
    async def send_audio_data(self, session_id: str, audio_data: bytes) -> bool:
        """
        Gửi audio data tới OpenAI Realtime API
        
        Args:
            session_id: ID của session
            audio_data: Audio data (PCM16 format)
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            websocket = self.active_connections.get(session_id)
            if not websocket:
                logger.error(f"WebSocket không khả dụng cho session: {session_id}")
                return False
            
            # Encode audio data thành base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            message = {
                "type": "conversation.item.input_audio_buffer.append",
                "item": {
                    "type": "input_audio_buffer",
                    "audio": audio_base64
                }
            }
            
            try:
                await websocket.send(json.dumps(message))
                return True
            except websockets.exceptions.ConnectionClosed:
                logger.error(f"WebSocket connection đã đóng cho session: {session_id}")
                return False
            except Exception as e:
                logger.error(f"Lỗi gửi audio data: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Lỗi gửi audio data: {str(e)}")
            return False
    
    async def send_text_message(self, session_id: str, text: str) -> bool:
        """
        Gửi text message tới OpenAI Realtime API
        
        Args:
            session_id: ID của session
            text: Text message
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            websocket = self.active_connections.get(session_id)
            if not websocket:
                logger.error(f"WebSocket không khả dụng cho session: {session_id}")
                return False
            
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text
                        }
                    ]
                }
            }
            
            try:
                await websocket.send(json.dumps(message))
                return True
            except websockets.exceptions.ConnectionClosed:
                logger.error(f"WebSocket connection đã đóng cho session: {session_id}")
                return False
            except Exception as e:
                logger.error(f"Lỗi gửi text message: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Lỗi gửi text message: {str(e)}")
            return False
    
    def register_audio_handler(self, channel_id: str, handler: Callable):
        """
        Đăng ký handler để xử lý audio output
        
        Args:
            channel_id: ID của channel
            handler: Function để xử lý audio data
        """
        self.audio_handlers[channel_id] = handler
        logger.info(f"Đã đăng ký audio handler cho channel: {channel_id}")
    
    async def _cleanup_session(self, session_id: str):
        """Dọn dẹp session"""
        try:
            # Đóng WebSocket connection
            if session_id in self.active_connections:
                websocket = self.active_connections[session_id]
                try:
                    await websocket.close()
                except Exception as e:
                    logger.warning(f"Lỗi đóng websocket: {str(e)}")
                del self.active_connections[session_id]
            
            # Xóa lịch sử hội thoại
            if session_id in self.conversation_histories:
                del self.conversation_histories[session_id]
            
            logger.info(f"Đã dọn dẹp session: {session_id}")
            
            # Logout khỏi backend
            await self._logout_session()
            
        except Exception as e:
            logger.error(f"Lỗi dọn dẹp session {session_id}: {str(e)}")
    
    async def close_session(self, session_id: str):
        """Đóng session"""
        try:
            websocket = self.active_connections.get(session_id)
            if websocket:
                # Gửi message để kết thúc session
                close_message = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text"],  # Chỉ giữ text modality khi đóng
                        "instructions": "",
                        "voice": "alloy",
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {
                            "model": "whisper-1"
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 200
                        },
                        "tools": [],
                        "tool_choice": "auto",
                        "temperature": 0.7,
                        "max_response_output_tokens": 150
                    }
                }
                
                try:
                    await websocket.send(json.dumps(close_message))
                    await asyncio.sleep(1)  # Chờ một chút để message được xử lý
                except Exception as e:
                    logger.warning(f"Lỗi gửi close message: {str(e)}")
                
            await self._cleanup_session(session_id)
            
        except Exception as e:
            logger.error(f"Lỗi đóng session {session_id}: {str(e)}")
    
    def get_conversation_history(self, session_id: str) -> list:
        """Lấy lịch sử hội thoại"""
        return self.conversation_histories.get(session_id, [])
    
    def get_active_sessions_count(self) -> int:
        """Lấy số lượng session đang hoạt động"""
        return len(self.active_connections)
    
    def get_active_sessions_info(self) -> Dict[str, dict]:
        """Lấy thông tin các session đang hoạt động"""
        return {
            session_id: {
                "websocket_open": websocket is not None,
                "conversation_turns": len(self.conversation_histories.get(session_id, [])) // 2
            }
            for session_id, websocket in self.active_connections.items()
        }
