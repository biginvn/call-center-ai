import openai
import aiofiles
import logging
import os
import uuid
from typing import Optional
from app.core.config import settings
from app.models.voicebot import TTSRequest, TTSResponse, VoiceType

logger = logging.getLogger(__name__)

class OpenAITTSService:
    """Service xử lý Text-to-Speech sử dụng OpenAI TTS API"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.TTS_MODEL
        self.default_voice = settings.TTS_VOICE
        self.output_dir = settings.RECORDING_DIR
        
        # Tạo thư mục output nếu chưa tồn tại
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """
        Chuyển đổi văn bản thành giọng nói sử dụng OpenAI TTS API
        
        Args:
            request: TTSRequest chứa văn bản và cấu hình
            
        Returns:
            TTSResponse với đường dẫn file audio đã tạo
        """
        try:
            logger.info(f"Bắt đầu tổng hợp giọng nói: {len(request.text)} ký tự")
            
            # Tạo tên file duy nhất
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            file_path = os.path.join(self.output_dir, filename)
            
            # Gọi OpenAI TTS API
            response = await self.client.audio.speech.create(
                model=request.model,
                voice=request.voice.value,
                input=request.text,
                speed=request.speed
            )
            
            # Lưu audio response vào file
            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in response.iter_bytes():
                    await f.write(chunk)
            
            # Lấy thông tin file
            file_size = os.path.getsize(file_path)
            duration = await self._get_audio_duration(file_path)
            
            logger.info(f"Tổng hợp giọng nói thành công: {file_path}")
            
            return TTSResponse(
                audio_file_path=file_path,
                duration=duration,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Lỗi khi tổng hợp giọng nói: {str(e)}")
            raise Exception(f"Không thể tổng hợp giọng nói: {str(e)}")
    
    async def synthesize_speech_simple(self, text: str, voice: VoiceType = VoiceType.ALLOY) -> str:
        """
        Phương thức đơn giản để chuyển đổi text thành giọng nói
        
        Args:
            text: Văn bản cần chuyển đổi
            voice: Loại giọng nói
            
        Returns:
            Đường dẫn file audio đã tạo
        """
        try:
            request = TTSRequest(
                text=text,
                voice=voice,
                model=self.model,
                speed=1.0
            )
            
            response = await self.synthesize_speech(request)
            return response.audio_file_path
            
        except Exception as e:
            logger.error(f"Lỗi tổng hợp giọng nói đơn giản: {str(e)}")
            return None
    
    async def _get_audio_duration(self, file_path: str) -> Optional[float]:
        """
        Lấy độ dài của file audio MP3
        
        Args:
            file_path: Đường dẫn file audio
            
        Returns:
            Độ dài audio tính bằng giây, None nếu không thể xác định
        """
        try:
            # Sử dụng mutagen để đọc metadata MP3
            from mutagen.mp3 import MP3
            
            audio = MP3(file_path)
            duration = audio.info.length
            return duration
            
        except ImportError:
            logger.warning("Mutagen không được cài đặt, không thể xác định độ dài audio")
            return None
        except Exception as e:
            logger.warning(f"Không thể xác định độ dài audio: {str(e)}")
            return None
    
    async def create_welcome_message(self, custom_message: Optional[str] = None) -> str:
        """
        Tạo tin nhắn chào mừng
        
        Args:
            custom_message: Tin nhắn tùy chỉnh
            
        Returns:
            Đường dẫn file audio chào mừng
        """
        welcome_text = custom_message or "Xin chào! Tôi là trợ lý AI. Bạn có thể nói chuyện với tôi."
        return await self.synthesize_speech_simple(welcome_text, VoiceType.ALLOY)
    
    async def create_goodbye_message(self, custom_message: Optional[str] = None) -> str:
        """
        Tạo tin nhắn tạm biệt
        
        Args:
            custom_message: Tin nhắn tùy chỉnh
            
        Returns:
            Đường dẫn file audio tạm biệt
        """
        goodbye_text = custom_message or "Cảm ơn bạn đã gọi. Chúc bạn một ngày tốt lành!"
        return await self.synthesize_speech_simple(goodbye_text, VoiceType.ALLOY)
    
    async def create_error_message(self, error_type: str = "general") -> str:
        """
        Tạo tin nhắn lỗi
        
        Args:
            error_type: Loại lỗi
            
        Returns:
            Đường dẫn file audio lỗi
        """
        error_messages = {
            "general": "Xin lỗi, tôi gặp một chút khó khăn. Bạn có thể nói lại được không?",
            "timeout": "Tôi không nghe thấy gì. Bạn có thể nói lại được không?",
            "network": "Xin lỗi, kết nối có vấn đề. Vui lòng thử lại sau.",
            "processing": "Tôi đang xử lý. Vui lòng chờ một chút."
        }
        
        error_text = error_messages.get(error_type, error_messages["general"])
        return await self.synthesize_speech_simple(error_text, VoiceType.ALLOY)
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """
        Xóa file tạm thời
        
        Args:
            file_path: Đường dẫn file cần xóa
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Đã xóa file TTS tạm: {file_path}")
        except Exception as e:
            logger.error(f"Lỗi khi xóa file TTS tạm {file_path}: {str(e)}")
    
    def get_available_voices(self) -> list:
        """
        Lấy danh sách các giọng nói có sẵn
        
        Returns:
            Danh sách các giọng nói
        """
        return [voice.value for voice in VoiceType]
    
    async def validate_text_length(self, text: str) -> bool:
        """
        Kiểm tra độ dài văn bản có hợp lệ không
        
        Args:
            text: Văn bản cần kiểm tra
            
        Returns:
            True nếu hợp lệ, False nếu không
        """
        # OpenAI TTS giới hạn 4096 ký tự
        max_length = 4096
        return len(text) <= max_length
    
    async def split_long_text(self, text: str, max_length: int = 4000) -> list:
        """
        Chia văn bản dài thành các đoạn nhỏ hơn
        
        Args:
            text: Văn bản cần chia
            max_length: Độ dài tối đa mỗi đoạn
            
        Returns:
            Danh sách các đoạn văn bản
        """
        if len(text) <= max_length:
            return [text]
        
        # Chia theo câu
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
