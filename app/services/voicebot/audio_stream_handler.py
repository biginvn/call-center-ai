import asyncio
import websockets
import logging
import base64
import struct
import uuid
from typing import Dict, Optional, Callable
from app.services.ai.realtime_service import OpenAIRealtimeService
from app.services.ari.ari_client import ARIClient

logger = logging.getLogger(__name__)

class AudioStreamHandler:
    """Handler xử lý audio streaming giữa Asterisk và OpenAI Realtime API"""
    
    def __init__(self, ari_client: ARIClient, realtime_service: OpenAIRealtimeService):
        self.ari_client = ari_client
        self.realtime_service = realtime_service
        
        # Quản lý audio streams
        self.active_streams: Dict[str, dict] = {}  # channel_id -> stream_info
        self.audio_buffers: Dict[str, list] = {}   # channel_id -> audio_chunks
        
        # Cấu hình audio
        self.sample_rate = 16000  # 16kHz cho OpenAI Realtime API
        self.channels = 1         # Mono
        self.bits_per_sample = 16 # 16-bit PCM
        self.chunk_size = 1024    # Kích thước chunk audio
        
    async def start_audio_stream(self, channel_id: str, session_id: str) -> bool:
        """
        Bắt đầu audio stream cho channel
        
        Args:
            channel_id: ID của channel Asterisk
            session_id: ID của realtime session
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            logger.info(f"Bắt đầu audio stream cho channel: {channel_id}")
            
            # Tạo WebSocket connection tới Asterisk để nhận audio stream
            ws_url = f"ws://{self.ari_client.host}:{self.ari_client.port}/ari/channels/{channel_id}/externalMedia"
            
            # Kết nối tới Asterisk WebSocket
            asterisk_ws = await websockets.connect(ws_url)
            
            # Lưu thông tin stream
            stream_info = {
                "session_id": session_id,
                "asterisk_ws": asterisk_ws,
                "is_active": True
            }
            self.active_streams[channel_id] = stream_info
            self.audio_buffers[channel_id] = []
            
            # Đăng ký audio handler cho realtime service
            self.realtime_service.register_audio_handler(
                channel_id, 
                self._handle_ai_audio_output
            )
            
            # Bắt đầu xử lý audio streams
            asyncio.create_task(self._process_asterisk_audio(channel_id))
            asyncio.create_task(self._process_ai_audio(channel_id))
            
            logger.info(f"Audio stream đã bắt đầu cho channel: {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi bắt đầu audio stream cho channel {channel_id}: {str(e)}")
            return False
    
    async def _process_asterisk_audio(self, channel_id: str):
        """Xử lý audio từ Asterisk và gửi tới OpenAI Realtime API"""
        try:
            stream_info = self.active_streams.get(channel_id)
            if not stream_info:
                logger.error(f"Không tìm thấy stream info cho channel: {channel_id}")
                return
            
            asterisk_ws = stream_info["asterisk_ws"]
            session_id = stream_info["session_id"]
            
            logger.info(f"Bắt đầu xử lý audio từ Asterisk cho channel: {channel_id}")
            
            while stream_info["is_active"] and asterisk_ws.open:
                try:
                    # Nhận audio data từ Asterisk
                    audio_data = await asterisk_ws.recv()
                    
                    # Chuyển đổi audio data thành format phù hợp
                    processed_audio = await self._process_audio_data(audio_data)
                    
                    if processed_audio:
                        # Gửi tới OpenAI Realtime API
                        await self.realtime_service.send_audio_data(session_id, processed_audio)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"Asterisk WebSocket đóng cho channel: {channel_id}")
                    break
                except Exception as e:
                    logger.error(f"Lỗi xử lý audio từ Asterisk: {str(e)}")
                    break
            
            logger.info(f"Kết thúc xử lý audio từ Asterisk cho channel: {channel_id}")
            
        except Exception as e:
            logger.error(f"Lỗi trong _process_asterisk_audio: {str(e)}")
    
    async def _process_ai_audio(self, channel_id: str):
        """Xử lý audio từ AI và gửi tới Asterisk"""
        try:
            stream_info = self.active_streams.get(channel_id)
            if not stream_info:
                logger.error(f"Không tìm thấy stream info cho channel: {channel_id}")
                return
            
            logger.info(f"Bắt đầu xử lý audio từ AI cho channel: {channel_id}")
            
            # Audio từ AI sẽ được xử lý trong _handle_ai_audio_output
            # Đây chỉ là placeholder để duy trì task
            
            while stream_info["is_active"]:
                await asyncio.sleep(0.1)
            
            logger.info(f"Kết thúc xử lý audio từ AI cho channel: {channel_id}")
            
        except Exception as e:
            logger.error(f"Lỗi trong _process_ai_audio: {str(e)}")
    
    async def _process_audio_data(self, raw_audio_data: bytes) -> Optional[bytes]:
        """
        Xử lý audio data từ Asterisk
        
        Args:
            raw_audio_data: Audio data thô từ Asterisk
            
        Returns:
            Processed audio data hoặc None nếu lỗi
        """
        try:
            # Asterisk có thể gửi audio ở format khác nhau
            # Cần chuyển đổi thành PCM16 16kHz mono cho OpenAI Realtime API
            
            # Tạm thời return raw data, có thể cần xử lý thêm
            return raw_audio_data
            
        except Exception as e:
            logger.error(f"Lỗi xử lý audio data: {str(e)}")
            return None
    
    async def _handle_ai_audio_output(self, audio_data: str):
        """
        Xử lý audio output từ AI
        
        Args:
            audio_data: Base64 encoded audio data từ OpenAI Realtime API
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Tìm channel_id từ audio handler
            channel_id = None
            for ch_id, handler in self.realtime_service.audio_handlers.items():
                if handler == self._handle_ai_audio_output:
                    channel_id = ch_id
                    break
            
            if not channel_id:
                logger.error("Không tìm thấy channel_id cho AI audio output")
                return
            
            # Gửi audio tới Asterisk để phát
            await self._send_audio_to_asterisk(channel_id, audio_bytes)
            
        except Exception as e:
            logger.error(f"Lỗi xử lý AI audio output: {str(e)}")
    
    async def _send_audio_to_asterisk(self, channel_id: str, audio_data: bytes):
        """
        Gửi audio data tới Asterisk để phát
        
        Args:
            channel_id: ID của channel
            audio_data: Audio data cần phát
        """
        try:
            stream_info = self.active_streams.get(channel_id)
            if not stream_info:
                logger.error(f"Không tìm thấy stream info cho channel: {channel_id}")
                return
            
            asterisk_ws = stream_info["asterisk_ws"]
            
            if asterisk_ws.open:
                # Gửi audio data tới Asterisk WebSocket
                await asterisk_ws.send(audio_data)
                logger.debug(f"Đã gửi audio data tới Asterisk cho channel: {channel_id}")
            else:
                logger.warning(f"Asterisk WebSocket đã đóng cho channel: {channel_id}")
                
        except Exception as e:
            logger.error(f"Lỗi gửi audio tới Asterisk: {str(e)}")
    
    async def stop_audio_stream(self, channel_id: str):
        """
        Dừng audio stream cho channel
        
        Args:
            channel_id: ID của channel
        """
        try:
            stream_info = self.active_streams.get(channel_id)
            if not stream_info:
                logger.warning(f"Không tìm thấy stream info để dừng cho channel: {channel_id}")
                return
            
            # Đánh dấu stream không còn active
            stream_info["is_active"] = False
            
            # Đóng Asterisk WebSocket
            asterisk_ws = stream_info.get("asterisk_ws")
            if asterisk_ws and asterisk_ws.open:
                await asterisk_ws.close()
            
            # Xóa khỏi danh sách active streams
            if channel_id in self.active_streams:
                del self.active_streams[channel_id]
            
            if channel_id in self.audio_buffers:
                del self.audio_buffers[channel_id]
            
            # Xóa audio handler
            if channel_id in self.realtime_service.audio_handlers:
                del self.realtime_service.audio_handlers[channel_id]
            
            logger.info(f"Đã dừng audio stream cho channel: {channel_id}")
            
        except Exception as e:
            logger.error(f"Lỗi dừng audio stream cho channel {channel_id}: {str(e)}")
    
    def get_active_streams_count(self) -> int:
        """Lấy số lượng audio streams đang hoạt động"""
        return len(self.active_streams)
    
    def get_active_streams_info(self) -> Dict[str, dict]:
        """Lấy thông tin các audio streams đang hoạt động"""
        return {
            channel_id: {
                "session_id": stream_info["session_id"],
                "is_active": stream_info["is_active"],
                "asterisk_ws_open": stream_info["asterisk_ws"].open if stream_info["asterisk_ws"] else False
            }
            for channel_id, stream_info in self.active_streams.items()
        }
    
    async def cleanup_all_streams(self):
        """Dọn dẹp tất cả audio streams"""
        try:
            for channel_id in list(self.active_streams.keys()):
                await self.stop_audio_stream(channel_id)
            
            logger.info("Đã dọn dẹp tất cả audio streams")
            
        except Exception as e:
            logger.error(f"Lỗi dọn dẹp audio streams: {str(e)}")
