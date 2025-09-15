import asyncio
import logging
import uuid
import os
from datetime import datetime
from typing import Dict, Optional
from app.services.ari.ari_client import ARIClient
from app.services.ai.realtime_service import OpenAIRealtimeService
from app.services.voicebot.audio_stream_handler import AudioStreamHandler
from app.models.voicebot import (
    CallSession, CallStatus, AudioRecording
)

logger = logging.getLogger(__name__)

class CallHandler:
    """Handler xử lý các sự kiện cuộc gọi và quản lý hội thoại voicebot"""
    
    def __init__(self, ari_client: ARIClient):
        self.ari_client = ari_client
        self.realtime_service = OpenAIRealtimeService()
        self.audio_stream_handler = AudioStreamHandler(ari_client, self.realtime_service)
        
        # Quản lý các cuộc gọi đang hoạt động
        self.active_calls: Dict[str, CallSession] = {}
        
        # Cấu hình
        self.max_conversation_turns = 20
        self.silence_timeout = 5
        
        # Đăng ký event handlers
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Đăng ký các event handlers với ARI client"""
        self.ari_client.register_event_handler('StasisStart', self.handle_stasis_start)
        self.ari_client.register_event_handler('ChannelHangupRequest', self.handle_channel_hangup)
        self.ari_client.register_event_handler('ChannelDtmfReceived', self.handle_dtmf_received)
    
    async def handle_stasis_start(self, event):
        """Xử lý khi cuộc gọi được chuyển vào Stasis"""
        try:
            event_data = event.data
            channel_id = event_data.get('channel', {}).get('id')
            args = event_data.get('args', [])
            
            if not channel_id:
                logger.error("Không tìm thấy channel_id trong StasisStart event")
                return
            
            logger.info(f"Cuộc gọi mới vào Stasis: {channel_id}, args: {args}")
            
            # Kiểm tra xem có phải là voicebot call không
            if 'voicebot' in args:
                await self.start_voicebot_session(channel_id, event_data)
            else:
                logger.info(f"Cuộc gọi không phải voicebot: {channel_id}")
                
        except Exception as e:
            logger.error(f"Lỗi xử lý StasisStart: {str(e)}")
    
    async def start_voicebot_session(self, channel_id: str, event_data: dict):
        """Khởi tạo session voicebot cho cuộc gọi"""
        try:
            # Tạo session mới
            session_id = str(uuid.uuid4())
            caller_info = event_data.get('channel', {})
            caller_number = caller_info.get('caller', {}).get('number', 'Unknown')
            
            session = CallSession(
                session_id=session_id,
                channel_id=channel_id,
                caller_number=caller_number,
                status=CallStatus.RINGING
            )
            
            self.active_calls[channel_id] = session
            logger.info(f"Tạo session voicebot: {session_id} cho channel {channel_id}")
            
            # Trả lời cuộc gọi
            if await self.ari_client.answer_channel(channel_id):
                session.status = CallStatus.ANSWERED
                logger.info(f"Đã trả lời cuộc gọi: {channel_id}")
                
                # Tạo OpenAI Realtime session
                if await self.realtime_service.create_realtime_session(session_id, channel_id):
                    logger.info(f"Tạo OpenAI Realtime session thành công: {session_id}")
                    
                    # Bắt đầu audio stream
                    if await self.audio_stream_handler.start_audio_stream(channel_id, session_id):
                        session.status = CallStatus.IN_PROGRESS
                        logger.info(f"Bắt đầu audio stream cho channel: {channel_id}")
                        
                        # Gửi tin nhắn chào mừng
                        await self.send_welcome_message(session_id)
                    else:
                        logger.error(f"Không thể bắt đầu audio stream cho channel: {channel_id}")
                        session.status = CallStatus.ERROR
                        session.error_message = "Không thể bắt đầu audio stream"
                else:
                    logger.error(f"Không thể tạo OpenAI Realtime session: {session_id}")
                    session.status = CallStatus.ERROR
                    session.error_message = "Không thể tạo OpenAI Realtime session"
            else:
                logger.error(f"Không thể trả lời cuộc gọi: {channel_id}")
                session.status = CallStatus.ERROR
                session.error_message = "Không thể trả lời cuộc gọi"
                
        except Exception as e:
            logger.error(f"Lỗi khởi tạo voicebot session: {str(e)}")
            if channel_id in self.active_calls:
                self.active_calls[channel_id].status = CallStatus.ERROR
                self.active_calls[channel_id].error_message = str(e)
    
    async def send_welcome_message(self, session_id: str):
        """Gửi tin nhắn chào mừng qua Realtime API"""
        try:
            welcome_text = "Xin chào! Tôi là trợ lý AI. Bạn có thể nói chuyện với tôi."
            await self.realtime_service.send_text_message(session_id, welcome_text)
            logger.info(f"Đã gửi tin nhắn chào mừng cho session: {session_id}")
        except Exception as e:
            logger.error(f"Lỗi gửi tin nhắn chào mừng: {str(e)}")
    
    async def send_goodbye_message(self, session_id: str):
        """Gửi tin nhắn tạm biệt qua Realtime API"""
        try:
            goodbye_text = "Cảm ơn bạn đã gọi. Chúc bạn một ngày tốt lành!"
            await self.realtime_service.send_text_message(session_id, goodbye_text)
            logger.info(f"Đã gửi tin nhắn tạm biệt cho session: {session_id}")
        except Exception as e:
            logger.error(f"Lỗi gửi tin nhắn tạm biệt: {str(e)}")
    
    
    async def handle_channel_hangup(self, event):
        """Xử lý khi channel bị cúp máy"""
        try:
            event_data = event.data
            channel_id = event_data.get('channel', {}).get('id')
            
            if channel_id:
                logger.info(f"Channel bị cúp máy: {channel_id}")
                await self.cleanup_call(channel_id)
                
        except Exception as e:
            logger.error(f"Lỗi xử lý channel hangup: {str(e)}")
    
    async def handle_playback_finished(self, event):
        """Xử lý khi phát audio hoàn thành"""
        try:
            event_data = event.data
            playback_id = event_data.get('playback', {}).get('id')
            logger.debug(f"Playback hoàn thành: {playback_id}")
            
        except Exception as e:
            logger.error(f"Lỗi xử lý playback finished: {str(e)}")
    
    async def handle_dtmf_received(self, event):
        """Xử lý khi nhận DTMF"""
        try:
            event_data = event.data
            channel_id = event_data.get('channel', {}).get('id')
            digit = event_data.get('digit')
            
            if channel_id and digit:
                logger.info(f"Nhận DTMF {digit} từ channel {channel_id}")
                # Có thể xử lý logic DTMF ở đây
                
        except Exception as e:
            logger.error(f"Lỗi xử lý DTMF: {str(e)}")
    
    async def cleanup_call(self, channel_id: str):
        """Dọn dẹp tài nguyên cuộc gọi"""
        try:
            if channel_id in self.active_calls:
                session = self.active_calls[channel_id]
                session.status = CallStatus.HANGUP
                session.end_time = datetime.now()
                
                logger.info(f"Dọn dẹp cuộc gọi: {channel_id}")
                
                # Gửi tin nhắn tạm biệt trước khi đóng
                await self.send_goodbye_message(session.session_id)
                
                # Đóng OpenAI Realtime session
                await self.realtime_service.close_session(session.session_id)
                
                # Dừng audio stream
                await self.audio_stream_handler.stop_audio_stream(channel_id)
                
                # Xóa khỏi danh sách active calls
                del self.active_calls[channel_id]
            
            # Cúp máy channel
            await self.ari_client.hangup_channel(channel_id)
            
        except Exception as e:
            logger.error(f"Lỗi dọn dẹp cuộc gọi {channel_id}: {str(e)}")
    
    def get_active_calls_count(self) -> int:
        """Lấy số lượng cuộc gọi đang hoạt động"""
        return len(self.active_calls)
    
    def get_active_calls_info(self) -> Dict[str, dict]:
        """Lấy thông tin các cuộc gọi đang hoạt động"""
        return {
            channel_id: {
                "session_id": session.session_id,
                "caller_number": session.caller_number,
                "status": session.status,
                "start_time": session.start_time.isoformat(),
                "conversation_turns": len(session.conversation_history) // 2
            }
            for channel_id, session in self.active_calls.items()
        }
    
    async def cleanup_all_calls(self):
        """Dọn dẹp tất cả cuộc gọi đang hoạt động"""
        try:
            active_calls = list(self.active_calls.keys())
            for channel_id in active_calls:
                await self.cleanup_call(channel_id)
            
            logger.info(f"Đã dọn dẹp {len(active_calls)} cuộc gọi")
            
        except Exception as e:
            logger.error(f"Lỗi dọn dẹp cuộc gọi: {str(e)}")
