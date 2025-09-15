import asyncio
import logging
from typing import Dict, Optional
from app.services.ari.ari_client import ARIClient
from app.services.voicebot.call_handler import CallHandler
from app.models.voicebot import VoiceBotStatus

logger = logging.getLogger(__name__)

class VoiceBotService:
    """Service chính quản lý VoiceBot với OpenAI Realtime API"""
    
    def __init__(self):
        self.ari_client = ARIClient()
        self.call_handler = CallHandler(self.ari_client)
        self.is_running = False
        self.start_time = None
        
    async def start(self) -> bool:
        """
        Khởi động VoiceBot service
        
        Returns:
            True nếu khởi động thành công, False nếu không
        """
        try:
            logger.info("Đang khởi động VoiceBot service...")
            
            # Kết nối tới ARI
            if await self.ari_client.connect():
                logger.info("Kết nối ARI thành công")
                self.is_running = True
                self.start_time = asyncio.get_event_loop().time()
                
                logger.info("VoiceBot service đã khởi động thành công")
                return True
            else:
                logger.error("Không thể kết nối tới ARI")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi khởi động VoiceBot service: {str(e)}")
            return False
    
    async def stop(self):
        """Dừng VoiceBot service"""
        try:
            logger.info("Đang dừng VoiceBot service...")
            
            self.is_running = False
            
            # Dọn dẹp tất cả cuộc gọi đang hoạt động
            await self.call_handler.cleanup_all_calls()
            
            # Ngắt kết nối ARI
            await self.ari_client.disconnect()
            
            logger.info("VoiceBot service đã dừng")
            
        except Exception as e:
            logger.error(f"Lỗi dừng VoiceBot service: {str(e)}")
    
    async def cleanup_all_calls(self):
        """Dọn dẹp tất cả cuộc gọi đang hoạt động"""
        try:
            active_calls = list(self.call_handler.active_calls.keys())
            for channel_id in active_calls:
                await self.call_handler.cleanup_call(channel_id)
            
            logger.info(f"Đã dọn dẹp {len(active_calls)} cuộc gọi")
            
        except Exception as e:
            logger.error(f"Lỗi dọn dẹp cuộc gọi: {str(e)}")
    
    def get_status(self) -> VoiceBotStatus:
        """
        Lấy trạng thái của VoiceBot
        
        Returns:
            VoiceBotStatus object
        """
        try:
            uptime = None
            if self.start_time:
                uptime_seconds = asyncio.get_event_loop().time() - self.start_time
                uptime = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s"
            
            return VoiceBotStatus(
                is_connected=self.ari_client.is_connected,
                active_calls=self.call_handler.get_active_calls_count(),
                total_calls_today=0,  # Có thể implement tracking sau
                uptime=uptime,
                last_error=None,  # Có thể implement error tracking sau
                version="1.0.0"
            )
            
        except Exception as e:
            logger.error(f"Lỗi lấy trạng thái VoiceBot: {str(e)}")
            return VoiceBotStatus(
                is_connected=False,
                active_calls=0,
                total_calls_today=0,
                uptime=None,
                last_error=str(e),
                version="1.0.0"
            )
    
    def get_active_calls_info(self) -> Dict[str, dict]:
        """Lấy thông tin các cuộc gọi đang hoạt động"""
        return self.call_handler.get_active_calls_info()
    
    def get_realtime_sessions_info(self) -> Dict[str, dict]:
        """Lấy thông tin các realtime sessions đang hoạt động"""
        return self.call_handler.realtime_service.get_active_sessions_info()
    
    def get_audio_streams_info(self) -> Dict[str, dict]:
        """Lấy thông tin các audio streams đang hoạt động"""
        return self.call_handler.audio_stream_handler.get_active_streams_info()
    
    async def health_check(self) -> bool:
        """
        Kiểm tra sức khỏe của VoiceBot service
        
        Returns:
            True nếu service hoạt động tốt, False nếu không
        """
        try:
            # Kiểm tra kết nối ARI
            ari_healthy = await self.ari_client.health_check()
            
            # Kiểm tra service đang chạy
            service_running = self.is_running
            
            return ari_healthy and service_running
            
        except Exception as e:
            logger.error(f"Lỗi health check: {str(e)}")
            return False
    
    async def restart(self) -> bool:
        """
        Khởi động lại VoiceBot service
        
        Returns:
            True nếu khởi động lại thành công, False nếu không
        """
        try:
            logger.info("Đang khởi động lại VoiceBot service...")
            
            # Dừng service
            await self.stop()
            
            # Chờ một chút
            await asyncio.sleep(2)
            
            # Khởi động lại
            return await self.start()
            
        except Exception as e:
            logger.error(f"Lỗi khởi động lại VoiceBot service: {str(e)}")
            return False
