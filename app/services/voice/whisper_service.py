import openai
import aiofiles
import logging
import os
import uuid
from typing import Optional
from app.core.config import settings
from app.models.voicebot import TranscriptionRequest, TranscriptionResponse

logger = logging.getLogger(__name__)

class WhisperSTTService:
    """Service xử lý Speech-to-Text sử dụng OpenAI Whisper API"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WHISPER_MODEL
        
    async def transcribe_audio(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """
        Chuyển đổi file audio thành văn bản sử dụng Whisper API
        
        Args:
            request: TranscriptionRequest chứa đường dẫn file và cấu hình
            
        Returns:
            TranscriptionResponse với văn bản đã chuyển đổi
        """
        try:
            logger.info(f"Bắt đầu chuyển đổi audio: {request.audio_file_path}")
            
            # Kiểm tra file tồn tại
            if not os.path.exists(request.audio_file_path):
                raise FileNotFoundError(f"File audio không tồn tại: {request.audio_file_path}")
            
            # Đọc file audio
            async with aiofiles.open(request.audio_file_path, "rb") as audio_file:
                # Gọi Whisper API
                transcript = await self.client.audio.transcriptions.create(
                    model=request.model,
                    file=audio_file,
                    language=request.language,
                    response_format="verbose_json"
                )
                
                logger.info(f"Chuyển đổi thành công: {len(transcript.text)} ký tự")
                
                return TranscriptionResponse(
                    text=transcript.text,
                    confidence=getattr(transcript, 'confidence', None),
                    language=getattr(transcript, 'language', request.language),
                    duration=getattr(transcript, 'duration', None)
                )
                
        except Exception as e:
            logger.error(f"Lỗi khi chuyển đổi audio: {str(e)}")
            raise Exception(f"Không thể chuyển đổi audio: {str(e)}")
    
    async def transcribe_audio_simple(self, audio_file_path: str, language: str = "vi") -> str:
        """
        Phương thức đơn giản để chuyển đổi audio thành text
        
        Args:
            audio_file_path: Đường dẫn file audio
            language: Ngôn ngữ (mặc định: tiếng Việt)
            
        Returns:
            Văn bản đã chuyển đổi
        """
        try:
            request = TranscriptionRequest(
                audio_file_path=audio_file_path,
                language=language,
                model=self.model
            )
            
            response = await self.transcribe_audio(request)
            return response.text
            
        except Exception as e:
            logger.error(f"Lỗi chuyển đổi audio đơn giản: {str(e)}")
            return ""
    
    async def validate_audio_file(self, file_path: str) -> bool:
        """
        Kiểm tra tính hợp lệ của file audio
        
        Args:
            file_path: Đường dẫn file audio
            
        Returns:
            True nếu file hợp lệ, False nếu không
        """
        try:
            # Kiểm tra file tồn tại
            if not os.path.exists(file_path):
                logger.warning(f"File không tồn tại: {file_path}")
                return False
            
            # Kiểm tra kích thước file (tối đa 25MB cho Whisper)
            file_size = os.path.getsize(file_path)
            max_size = 25 * 1024 * 1024  # 25MB
            
            if file_size > max_size:
                logger.warning(f"File quá lớn: {file_size} bytes (tối đa: {max_size})")
                return False
            
            # Kiểm tra định dạng file
            valid_extensions = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext not in valid_extensions:
                logger.warning(f"Định dạng file không được hỗ trợ: {file_ext}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra file audio: {str(e)}")
            return False
    
    async def get_audio_duration(self, file_path: str) -> Optional[float]:
        """
        Lấy độ dài của file audio
        
        Args:
            file_path: Đường dẫn file audio
            
        Returns:
            Độ dài audio tính bằng giây, None nếu không thể xác định
        """
        try:
            import wave
            
            with wave.open(file_path, 'rb') as audio_file:
                frames = audio_file.getnframes()
                rate = audio_file.getframerate()
                duration = frames / float(rate)
                return duration
                
        except Exception as e:
            logger.warning(f"Không thể xác định độ dài audio: {str(e)}")
            return None
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """
        Xóa file tạm thời
        
        Args:
            file_path: Đường dẫn file cần xóa
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Đã xóa file tạm: {file_path}")
        except Exception as e:
            logger.error(f"Lỗi khi xóa file tạm {file_path}: {str(e)}")
