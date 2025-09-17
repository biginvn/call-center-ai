import asyncio
import websockets
import json
import logging
import base64
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
            
            # Kết nối tới OpenAI Realtime API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
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
            
            logger.info(f"Realtime session tạo thành công: {session_id}")
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
            
            while websocket.open:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    await self._handle_realtime_message(session_id, channel_id, data)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"WebSocket connection đóng cho session: {session_id}")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Lỗi parse JSON message: {str(e)}")
                except Exception as e:
                    logger.error(f"Lỗi xử lý message: {str(e)}")
                    
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
            if not websocket or not websocket.open:
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
            
            await websocket.send(json.dumps(message))
            return True
            
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
            if not websocket or not websocket.open:
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
            
            await websocket.send(json.dumps(message))
            return True
            
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
                if websocket.open:
                    await websocket.close()
                del self.active_connections[session_id]
            
            # Xóa lịch sử hội thoại
            if session_id in self.conversation_histories:
                del self.conversation_histories[session_id]
            
            logger.info(f"Đã dọn dẹp session: {session_id}")
            
        except Exception as e:
            logger.error(f"Lỗi dọn dẹp session {session_id}: {str(e)}")
    
    async def close_session(self, session_id: str):
        """Đóng session"""
        try:
            websocket = self.active_connections.get(session_id)
            if websocket and websocket.open:
                # Gửi message để kết thúc session
                close_message = {
                    "type": "session.update",
                    "session": {
                        "modalities": [],
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
                
                await websocket.send(json.dumps(close_message))
                await asyncio.sleep(1)  # Chờ một chút để message được xử lý
                
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
                "websocket_open": websocket.open if websocket else False,
                "conversation_turns": len(self.conversation_histories.get(session_id, [])) // 2
            }
            for session_id, websocket in self.active_connections.items()
        }
