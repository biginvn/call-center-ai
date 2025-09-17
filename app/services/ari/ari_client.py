import aiohttp
import asyncio
import websockets
import json
import logging
from typing import Dict, Callable, Optional, Any
from app.core.config import settings
from app.models.voicebot import ARIEvent

logger = logging.getLogger(__name__)

class ARIClient:
    """Client để kết nối và tương tác với Asterisk ARI"""
    
    def __init__(self):
        self.host = settings.ARI_HOST
        self.port = settings.ARI_PORT
        self.username = settings.ARI_USERNAME
        self.password = settings.ARI_PASSWORD
        self.app_name = settings.ARI_APP_NAME
        
        self.base_url = f"http://{self.host}:{self.port}/ari"
        self.ws_url = f"ws://{self.host}:{self.port}/ari/events"
        
        self.auth = aiohttp.BasicAuth(self.username, self.password)
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.event_handlers: Dict[str, Callable] = {}
        self.is_connected = False
        self.is_running = False
        
    async def connect(self) -> bool:
        """
        Kết nối tới ARI WebSocket và HTTP session
        
        Returns:
            True nếu kết nối thành công, False nếu không
        """
        try:
            logger.info(f"Đang kết nối tới ARI tại {self.host}:{self.port}")
            
            # Tạo HTTP session
            self.session = aiohttp.ClientSession(auth=self.auth)
            
            # Kiểm tra kết nối HTTP
            async with self.session.get(f"{self.base_url}/applications") as response:
                if response.status == 200:
                    logger.info("Kết nối HTTP ARI thành công")
                else:
                    logger.error(f"Lỗi kết nối HTTP ARI: {response.status}")
                    return False
            
            # Kết nối WebSocket
            self.websocket = await websockets.connect(
                f"{self.ws_url}?api_key={self.username}:{self.password}&app={self.app_name}"
            )
            
            self.is_connected = True
            logger.info("Kết nối WebSocket ARI thành công")
            
            # Bắt đầu lắng nghe events
            asyncio.create_task(self._listen_for_events())
            
            return True
            
        except Exception as e:
            logger.error(f"Lỗi kết nối ARI: {str(e)}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Ngắt kết nối khỏi ARI"""
        try:
            self.is_running = False
            self.is_connected = False
            
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            if self.session:
                await self.session.close()
                self.session = None
            
            logger.info("Đã ngắt kết nối ARI")
            
        except Exception as e:
            logger.error(f"Lỗi khi ngắt kết nối ARI: {str(e)}")
    
    async def _listen_for_events(self):
        """Lắng nghe events từ ARI WebSocket"""
        try:
            self.is_running = True
            
            while self.is_running and self.websocket:
                try:
                    message = await self.websocket.recv()
                    event_data = json.loads(message)
                    
                    # Tạo ARIEvent object
                    ari_event = ARIEvent(
                        event_type=event_data.get('type', 'unknown'),
                        data=event_data,
                        channel_id=event_data.get('channel', {}).get('id') if 'channel' in event_data else None
                    )
                    
                    # Gọi handler tương ứng
                    await self._handle_event(ari_event)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection đã đóng")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Lỗi parse JSON event: {str(e)}")
                except Exception as e:
                    logger.error(f"Lỗi xử lý event: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Lỗi trong _listen_for_events: {str(e)}")
        finally:
            self.is_running = False
    
    async def _handle_event(self, event: ARIEvent):
        """Xử lý event từ ARI"""
        try:
            event_type = event.event_type
            
            # Gọi handler tương ứng nếu có
            if event_type in self.event_handlers:
                handler = self.event_handlers[event_type]
                await handler(event)
            else:
                logger.debug(f"Không có handler cho event: {event_type}")
                
        except Exception as e:
            logger.error(f"Lỗi xử lý event {event.event_type}: {str(e)}")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Đăng ký handler cho loại event cụ thể
        
        Args:
            event_type: Loại event (ví dụ: 'StasisStart', 'ChannelHangupRequest')
            handler: Function để xử lý event
        """
        self.event_handlers[event_type] = handler
        logger.info(f"Đã đăng ký handler cho event: {event_type}")
    
    async def answer_channel(self, channel_id: str) -> bool:
        """
        Trả lời cuộc gọi
        
        Args:
            channel_id: ID của channel
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            url = f"{self.base_url}/channels/{channel_id}/answer"
            async with self.session.post(url) as response:
                if response.status == 204:
                    logger.info(f"Đã trả lời channel: {channel_id}")
                    return True
                else:
                    logger.error(f"Lỗi trả lời channel {channel_id}: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Lỗi khi trả lời channel {channel_id}: {str(e)}")
            return False
    
    async def play_media(self, channel_id: str, media_uri: str) -> bool:
        """
        Phát media file
        
        Args:
            channel_id: ID của channel
            media_uri: URI của media file (sound:, recording:, v.v.)
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            url = f"{self.base_url}/channels/{channel_id}/play"
            data = {"media": media_uri}
            
            async with self.session.post(url, json=data) as response:
                if response.status == 201:
                    logger.info(f"Đã phát media {media_uri} trên channel {channel_id}")
                    return True
                else:
                    logger.error(f"Lỗi phát media {media_uri}: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Lỗi khi phát media {media_uri}: {str(e)}")
            return False
    
    async def record_channel(self, channel_id: str, name: str, max_duration: int = 30) -> bool:
        """
        Bắt đầu ghi âm channel
        
        Args:
            channel_id: ID của channel
            name: Tên file ghi âm
            max_duration: Thời gian ghi âm tối đa (giây)
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            url = f"{self.base_url}/channels/{channel_id}/record"
            data = {
                "name": name,
                "format": "wav",
                "maxDurationSeconds": max_duration,
                "terminateOn": "none"
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 201:
                    logger.info(f"Đã bắt đầu ghi âm channel {channel_id}: {name}")
                    return True
                else:
                    logger.error(f"Lỗi bắt đầu ghi âm {name}: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Lỗi khi ghi âm channel {channel_id}: {str(e)}")
            return False
    
    async def stop_recording(self, recording_name: str) -> bool:
        """
        Dừng ghi âm
        
        Args:
            recording_name: Tên file ghi âm
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            url = f"{self.base_url}/recordings/live/{recording_name}/stop"
            
            async with self.session.post(url) as response:
                if response.status == 204:
                    logger.info(f"Đã dừng ghi âm: {recording_name}")
                    return True
                else:
                    logger.error(f"Lỗi dừng ghi âm {recording_name}: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Lỗi khi dừng ghi âm {recording_name}: {str(e)}")
            return False
    
    async def hangup_channel(self, channel_id: str, reason: str = "normal") -> bool:
        """
        Cúp máy channel
        
        Args:
            channel_id: ID của channel
            reason: Lý do cúp máy
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            # Kiểm tra channel có tồn tại không trước khi cúp máy
            channel_info = await self.get_channel_info(channel_id)
            if not channel_info:
                logger.warning(f"Channel {channel_id} không tồn tại hoặc đã bị cúp máy")
                return True  # Coi như thành công vì channel đã không còn tồn tại
            
            url = f"{self.base_url}/channels/{channel_id}"
            params = {"reason": reason}
            
            async with self.session.delete(url, params=params) as response:
                if response.status == 204:
                    logger.info(f"Đã cúp máy channel {channel_id}: {reason}")
                    return True
                elif response.status == 404:
                    logger.warning(f"Channel {channel_id} không tồn tại (404)")
                    return True  # Coi như thành công vì channel đã không còn tồn tại
                else:
                    logger.error(f"Lỗi cúp máy channel {channel_id}: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Lỗi khi cúp máy channel {channel_id}: {str(e)}")
            return False
    
    async def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin channel
        
        Args:
            channel_id: ID của channel
            
        Returns:
            Thông tin channel hoặc None nếu lỗi
        """
        try:
            url = f"{self.base_url}/channels/{channel_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Lỗi lấy thông tin channel {channel_id}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông tin channel {channel_id}: {str(e)}")
            return None
    
    async def upload_sound_file(self, file_path: str, sound_name: str) -> bool:
        """
        Upload file âm thanh lên Asterisk
        
        Args:
            file_path: Đường dẫn file local
            sound_name: Tên sound trong Asterisk
            
        Returns:
            True nếu thành công, False nếu không
        """
        try:
            url = f"{self.base_url}/sounds/{sound_name}"
            
            with open(file_path, 'rb') as f:
                files = {'file': f}
                async with self.session.post(url, data=files) as response:
                    if response.status == 201:
                        logger.info(f"Đã upload sound file: {sound_name}")
                        return True
                    else:
                        logger.error(f"Lỗi upload sound file {sound_name}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Lỗi khi upload sound file {sound_name}: {str(e)}")
            return False
    
    async def get_applications(self) -> Optional[Dict[str, Any]]:
        """
        Lấy danh sách applications
        
        Returns:
            Danh sách applications hoặc None nếu lỗi
        """
        try:
            url = f"{self.base_url}/applications"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Lỗi lấy danh sách applications: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách applications: {str(e)}")
            return None
    
    async def health_check(self) -> bool:
        """
        Kiểm tra sức khỏe kết nối ARI
        
        Returns:
            True nếu kết nối tốt, False nếu không
        """
        try:
            if not self.session:
                return False
                
            url = f"{self.base_url}/applications"
            async with self.session.get(url) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Lỗi health check ARI: {str(e)}")
            return False
