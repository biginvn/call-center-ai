from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class CallStatus(str, Enum):
    """Trạng thái cuộc gọi"""
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_PROGRESS = "in_progress"
    RECORDING = "recording"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    HANGUP = "hangup"
    ERROR = "error"

class AudioFormat(str, Enum):
    """Định dạng audio"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"

class VoiceType(str, Enum):
    """Loại giọng nói cho TTS"""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"

class CallSession(BaseModel):
    """Model cho session cuộc gọi"""
    session_id: str = Field(..., description="ID duy nhất của session")
    channel_id: str = Field(..., description="ID của channel Asterisk")
    caller_number: Optional[str] = Field(None, description="Số điện thoại người gọi")
    status: CallStatus = Field(CallStatus.RINGING, description="Trạng thái cuộc gọi")
    start_time: datetime = Field(default_factory=datetime.now, description="Thời gian bắt đầu cuộc gọi")
    end_time: Optional[datetime] = Field(None, description="Thời gian kết thúc cuộc gọi")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Lịch sử hội thoại")
    error_message: Optional[str] = Field(None, description="Thông báo lỗi nếu có")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AudioRecording(BaseModel):
    """Model cho bản ghi âm"""
    recording_id: str = Field(..., description="ID duy nhất của bản ghi")
    session_id: str = Field(..., description="ID của session cuộc gọi")
    file_path: str = Field(..., description="Đường dẫn file audio")
    duration: Optional[float] = Field(None, description="Độ dài bản ghi (giây)")
    format: AudioFormat = Field(AudioFormat.WAV, description="Định dạng file")
    created_at: datetime = Field(default_factory=datetime.now, description="Thời gian tạo")
    transcribed_text: Optional[str] = Field(None, description="Văn bản đã chuyển đổi")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TranscriptionRequest(BaseModel):
    """Request cho việc chuyển đổi giọng nói thành văn bản"""
    audio_file_path: str = Field(..., description="Đường dẫn file audio")
    language: Optional[str] = Field("vi", description="Ngôn ngữ (mặc định: tiếng Việt)")
    model: str = Field("whisper-1", description="Model Whisper sử dụng")

class TranscriptionResponse(BaseModel):
    """Response cho việc chuyển đổi giọng nói thành văn bản"""
    text: str = Field(..., description="Văn bản đã chuyển đổi")
    confidence: Optional[float] = Field(None, description="Độ tin cậy")
    language: Optional[str] = Field(None, description="Ngôn ngữ được phát hiện")
    duration: Optional[float] = Field(None, description="Độ dài audio")

class TTSRequest(BaseModel):
    """Request cho việc chuyển đổi văn bản thành giọng nói"""
    text: str = Field(..., description="Văn bản cần chuyển đổi")
    voice: VoiceType = Field(VoiceType.ALLOY, description="Loại giọng nói")
    model: str = Field("tts-1", description="Model TTS sử dụng")
    speed: float = Field(1.0, description="Tốc độ nói (0.25 - 4.0)")

class TTSResponse(BaseModel):
    """Response cho việc chuyển đổi văn bản thành giọng nói"""
    audio_file_path: str = Field(..., description="Đường dẫn file audio đã tạo")
    duration: Optional[float] = Field(None, description="Độ dài audio")
    file_size: Optional[int] = Field(None, description="Kích thước file (bytes)")

class ChatGPTRequest(BaseModel):
    """Request cho ChatGPT"""
    message: str = Field(..., description="Tin nhắn từ người dùng")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Lịch sử hội thoại")
    system_prompt: Optional[str] = Field(None, description="Prompt hệ thống tùy chỉnh")
    max_tokens: int = Field(150, description="Số token tối đa")
    temperature: float = Field(0.7, description="Nhiệt độ cho response")

class ChatGPTResponse(BaseModel):
    """Response từ ChatGPT"""
    response: str = Field(..., description="Phản hồi từ AI")
    usage: Optional[Dict[str, Any]] = Field(None, description="Thông tin sử dụng token")
    model: str = Field(..., description="Model được sử dụng")

class VoiceBotConfig(BaseModel):
    """Cấu hình cho VoiceBot"""
    welcome_message: str = Field("Xin chào! Tôi là trợ lý AI. Bạn có thể nói chuyện với tôi.", description="Tin nhắn chào mừng")
    goodbye_message: str = Field("Cảm ơn bạn đã gọi. Chúc bạn một ngày tốt lành!", description="Tin nhắn tạm biệt")
    max_conversation_turns: int = Field(20, description="Số lượt hội thoại tối đa")
    silence_timeout: int = Field(5, description="Thời gian im lặng tối đa (giây)")
    recording_timeout: int = Field(30, description="Thời gian ghi âm tối đa (giây)")
    enable_conversation_logging: bool = Field(True, description="Bật ghi log hội thoại")

class ARIEvent(BaseModel):
    """Model cho ARI events"""
    event_type: str = Field(..., description="Loại event")
    timestamp: datetime = Field(default_factory=datetime.now, description="Thời gian event")
    data: Dict[str, Any] = Field(..., description="Dữ liệu event")
    channel_id: Optional[str] = Field(None, description="ID channel liên quan")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class VoiceBotStatus(BaseModel):
    """Trạng thái tổng thể của VoiceBot"""
    is_connected: bool = Field(..., description="Kết nối ARI")
    active_calls: int = Field(0, description="Số cuộc gọi đang hoạt động")
    total_calls_today: int = Field(0, description="Tổng số cuộc gọi hôm nay")
    uptime: Optional[str] = Field(None, description="Thời gian hoạt động")
    last_error: Optional[str] = Field(None, description="Lỗi cuối cùng")
    version: str = Field("1.0.0", description="Phiên bản VoiceBot")
