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
            
            # Với voicebot, chúng ta cần tạo một channel khác để bridge
            # và sử dụng external media để stream audio
            
            # Tạo external media channel cho voicebot
            voicebot_channel_id = await self._create_voicebot_channel()
            if not voicebot_channel_id:
                logger.error(f"Không thể tạo voicebot channel cho: {channel_id}")
                return False
            
            # Tạo bridge để kết nối caller và voicebot
            bridge_id = await self._create_bridge()
            if not bridge_id:
                logger.error(f"Không thể tạo bridge cho: {channel_id}")
                return False
            
            # Thêm cả hai channels vào bridge
            await self._add_channel_to_bridge(bridge_id, channel_id)
            await self._add_channel_to_bridge(bridge_id, voicebot_channel_id)
            
            # Lưu thông tin stream
            stream_info = {
                "session_id": session_id,
                "voicebot_channel_id": voicebot_channel_id,
                "bridge_id": bridge_id,
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
            
            session_id = stream_info["session_id"]
            recording_name = stream_info["recording_name"]
            
            logger.info(f"Bắt đầu xử lý audio từ Asterisk cho channel: {channel_id}")
            
            # Với recording approach, chúng ta sẽ nhận audio data qua HTTP API
            # Tạm thời sử dụng polling để lấy audio data
            while stream_info["is_active"]:
                try:
                    # TODO: Implement cách lấy audio data từ recording
                    # Có thể sử dụng HTTP API để lấy audio chunks
                    await asyncio.sleep(0.1)  # Polling interval
                    
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
            
            if not raw_audio_data or len(raw_audio_data) == 0:
                logger.debug("Nhận được audio data rỗng")
                return None
            
            # Log thông tin audio data để debug
            logger.debug(f"Nhận audio data: {len(raw_audio_data)} bytes")
            
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
            if not audio_data:
                logger.warning("Nhận được audio data rỗng từ AI")
                return
                
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            logger.debug(f"Decoded AI audio: {len(audio_bytes)} bytes")
            
            # Tìm channel_id từ audio handler
            channel_id = None
            for ch_id, handler in self.realtime_service.audio_handlers.items():
                if handler == self._handle_ai_audio_output:
                    channel_id = ch_id
                    break
            
            if not channel_id:
                logger.error("Không tìm thấy channel_id cho AI audio output")
                return
            
            # Kiểm tra stream có còn active không
            stream_info = self.active_streams.get(channel_id)
            if not stream_info or not stream_info.get("is_active", False):
                logger.warning(f"Stream không còn active cho channel: {channel_id}")
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
            if not audio_data or len(audio_data) == 0:
                logger.warning(f"Audio data rỗng cho channel: {channel_id}")
                return
                
            stream_info = self.active_streams.get(channel_id)
            if not stream_info:
                logger.error(f"Không tìm thấy stream info cho channel: {channel_id}")
                return
            
            # Sử dụng ARI HTTP API để phát audio
            # Tạm thời lưu audio data vào file và phát qua ARI
            import tempfile
            import os
            
            # Tạo file tạm để lưu audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Upload file lên Asterisk và phát
                sound_name = f"temp_audio_{channel_id}_{int(asyncio.get_event_loop().time())}"
                upload_success = await self.ari_client.upload_sound_file(temp_file_path, sound_name)
                
                if upload_success:
                    # Phát audio file
                    play_success = await self.ari_client.play_media(channel_id, f"sound:{sound_name}")
                    if play_success:
                        logger.debug(f"Đã phát {len(audio_data)} bytes audio data cho channel: {channel_id}")
                    else:
                        logger.error(f"Không thể phát audio cho channel: {channel_id}")
                else:
                    logger.error(f"Không thể upload audio file cho channel: {channel_id}")
                    
            finally:
                # Xóa file tạm
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Không thể xóa file tạm: {str(e)}")
                
        except Exception as e:
            logger.error(f"Lỗi gửi audio tới Asterisk cho channel {channel_id}: {str(e)}")
    
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
            
            # Dừng recording nếu có
            recording_name = stream_info.get("recording_name")
            if recording_name:
                await self.ari_client.stop_recording(recording_name)
                logger.info(f"Đã dừng recording: {recording_name}")
            
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
                "recording_name": stream_info.get("recording_name", "N/A")
            }
            for channel_id, stream_info in self.active_streams.items()
        }
    
    def is_stream_active(self, channel_id: str) -> bool:
        """Kiểm tra xem audio stream có đang hoạt động không"""
        stream_info = self.active_streams.get(channel_id)
        if not stream_info:
            return False
        return stream_info.get("is_active", False) and stream_info.get("recording_name") is not None
    
    async def cleanup_all_streams(self):
        """Dọn dẹp tất cả audio streams"""
        try:
            for channel_id in list(self.active_streams.keys()):
                await self.stop_audio_stream(channel_id)
            
            logger.info("Đã dọn dẹp tất cả audio streams")
            
        except Exception as e:
            logger.error(f"Lỗi dọn dẹp audio streams: {str(e)}")
    
    async def _create_voicebot_channel(self) -> Optional[str]:
        """Tạo external media channel cho voicebot với đủ tham số bắt buộc cho ARI externalMedia"""
        try:
            url = f"{self.ari_client.base_url}/channels/externalMedia"
            data = {
                "app": "nixxis",  # ARI app name, chỉnh nếu cần
                "external_host": "127.0.0.1:4569",  # host:port, chỉnh port nếu cần
                "format": "slin16",
                "encapsulation": "rtp",
                "transport": "udp",
                # "connection_type": "client",  # optional
                # "direction": "both",          # optional
                # "channelId": f"voicebot-{int(asyncio.get_event_loop().time())}"  # optional
            }
            async with self.ari_client.session.post(url, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    channel_id = result.get("id")
                    logger.info(f"Đã tạo voicebot channel: {channel_id}")
                    return channel_id
                else:
                    try:
                        text = await response.text()
                        logger.error(f"Lỗi tạo voicebot channel: {response.status} - {text}")
                    except Exception:
                        logger.error(f"Lỗi tạo voicebot channel: {response.status} - (không đọc được response body)")
                    return None
        except Exception as e:
            logger.error(f"Lỗi tạo voicebot channel: {str(e)}")
            return None
    
    async def _create_bridge(self) -> Optional[str]:
        """Tạo bridge để kết nối channels"""
        try:
            url = f"{self.ari_client.base_url}/bridges"
            data = {"type": "mixing"}
            
            async with self.ari_client.session.post(url, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    bridge_id = result.get("id")
                    logger.info(f"Đã tạo bridge: {bridge_id}")
                    return bridge_id
                else:
                    logger.error(f"Lỗi tạo bridge: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Lỗi tạo bridge: {str(e)}")
            return None
    
    async def _add_channel_to_bridge(self, bridge_id: str, channel_id: str) -> bool:
        """Thêm channel vào bridge"""
        try:
            url = f"{self.ari_client.base_url}/bridges/{bridge_id}/addChannel"
            data = {"channel": channel_id}
            
            async with self.ari_client.session.post(url, json=data) as response:
                if response.status == 204:
                    logger.info(f"Đã thêm channel {channel_id} vào bridge {bridge_id}")
                    return True
                else:
                    logger.error(f"Lỗi thêm channel vào bridge: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Lỗi thêm channel vào bridge: {str(e)}")
            return False
