from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096, description="Text to convert to speech")
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer", "sage", "coral", "verse", "ballad", "ash"] = Field(..., description="Voice to use for TTS")
    model: str = Field(default="tts-1", description="TTS model to use")
    response_format: str = Field(default="mp3", description="Audio format")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed")
    instructions: Optional[str] = Field(None, description="Additional instructions for voice generation")


class TTSResponse(BaseModel):
    audio_url: str = Field(..., description="URL to access the generated audio")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    voice_used: str = Field(..., description="Voice that was used")
    text_length: int = Field(..., description="Length of input text")
    file_size: Optional[int] = Field(None, description="Audio file size in bytes")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    max_tokens: int = Field(default=2000, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    system_prompt: Optional[str] = Field(None, description="System prompt override")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChatCompletionResponse(BaseModel):
    content: str = Field(..., description="Generated response content")
    model: str = Field(..., description="Model used for generation")
    usage: Optional[Dict] = Field(None, description="Token usage information")
    finish_reason: Optional[str] = Field(None, description="Reason for completion finish")


class STTRequest(BaseModel):
    model: str = Field(default="whisper-1", description="Speech-to-text model to use")
    language: Optional[str] = Field(None, description="Language of the audio (ISO-639-1 format)")
    prompt: Optional[str] = Field(None, description="Optional text to guide the model's style")
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] = Field(default="json", description="Response format")
    temperature: float = Field(default=0, ge=0, le=1, description="Sampling temperature")


class STTResponse(BaseModel):
    text: str = Field(..., description="Transcribed text")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    model: str = Field(..., description="Model used for transcription")
