from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096, description="Text to convert to speech")
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer", "sage", "coral", "verse", "ballad", "ash", "cedar", "marin"] = Field(..., description="Voice to use for TTS")
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


# Realtime API DTOs for GA version
class RealtimeAudioOutput(BaseModel):
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer", "sage", "coral", "verse", "ballad", "ash", "cedar", "marin"] = Field(default="marin", description="Voice to use for audio output")


class RealtimeAudio(BaseModel):
    output: RealtimeAudioOutput = Field(..., description="Audio output configuration")


class RealtimeSessionConfig(BaseModel):
    type: Literal["realtime"] = Field(default="realtime", description="Session type must be 'realtime'")
    model: str = Field(default="gpt-realtime", description="Model to use for the realtime session")
    audio: Optional[RealtimeAudio] = Field(None, description="Audio configuration")
    instructions: Optional[str] = Field(None, description="Instructions for the AI assistant")
    voice: Optional[str] = Field(None, description="Legacy voice parameter (use audio.output.voice instead)")
    input_audio_format: Optional[str] = Field(None, description="Input audio format")
    output_audio_format: Optional[str] = Field(None, description="Output audio format")
    input_audio_transcription: Optional[Dict] = Field(None, description="Input audio transcription settings")
    turn_detection: Optional[Dict] = Field(None, description="Turn detection configuration")
    tools: Optional[List[Dict]] = Field(None, description="Tools available to the assistant")
    tool_choice: Optional[str] = Field(None, description="Tool choice strategy")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_response_output_tokens: Optional[int] = Field(None, description="Maximum tokens in response")


class RealtimeSessionRequest(BaseModel):
    session: RealtimeSessionConfig = Field(..., description="Session configuration")


class RealtimeClientSecret(BaseModel):
    value: str = Field(..., description="The ephemeral client secret token")
    expires_at: Optional[int] = Field(None, description="Unix timestamp when the token expires")


class RealtimeSessionResponse(BaseModel):
    value: str = Field(..., description="The ephemeral client secret value for direct client use")
    expires_at: Optional[int] = Field(None, description="Unix timestamp when the session expires")
    session_id: Optional[str] = Field(None, description="Unique session identifier")
