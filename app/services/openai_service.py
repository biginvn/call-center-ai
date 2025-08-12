from openai import AsyncOpenAI
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_tts(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        response_format: str = "mp3",
        speed: float = 1.0
    ) -> bytes:
        """
        Generate text-to-speech audio using OpenAI API
        """
        try:
            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format,
                speed=speed
            )
            
            # Get the audio content as bytes
            audio_content = b""
            for chunk in response.iter_bytes():
                audio_content += chunk
            return audio_content
            
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            raise
    
    async def transcribe_audio(
        self,
        audio_file,
        model: str = "whisper-1",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: float = 0
    ):
        """
        Transcribe audio using OpenAI Whisper API
        """
        try:
            transcript = await self.client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature
            )
            
            return transcript
            
        except Exception as e:
            logger.error(f"STT transcription failed: {str(e)}")
            raise
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ):
        """
        Generate chat completion using OpenAI API
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            raise


# Singleton instance
openai_service = OpenAIService()
