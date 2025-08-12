from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from app.auth.auth import get_current_user
from app.models.user import User
from app.dto.openai_dto import (
    TTSRequest, 
    ChatCompletionRequest, ChatCompletionResponse,
    STTResponse
)
from app.services.openai_service import openai_service
from typing import Optional
import tempfile
import os
from io import BytesIO
import openai
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/openai",
    tags=["OpenAI Integration"],
)


@router.post("/tts", summary="Text-to-Speech Generation")
async def generate_tts(
    request: TTSRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    Generate text-to-speech audio using OpenAI API
    
    **Features:**
    - Secure backend API (no exposed API keys)
    - Multiple voice options
    - Configurable speed and format
    - User authentication required
    
    **Voices available:**
    - alloy, echo, fable, onyx, nova, shimmer (standard voices)
    - sage, coral, verse, ballad, ash (advanced voices - requires newer models)
    """
    try:
        # Validate user permissions (you can add custom logic here)
        if not current_user:
            raise HTTPException(status_code=403, detail="Authentication required")
        
        # Generate audio using OpenAI service
        audio_content = await openai_service.generate_tts(
            text=request.text,
            voice=request.voice,
            model=request.model,
            response_format=request.response_format,
            speed=request.speed
        )
        
        # Determine MIME type based on format
        mime_types = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac"
        }
        mime_type = mime_types.get(request.response_format, "audio/mpeg")
        
        # Return streaming response
        return StreamingResponse(
            BytesIO(audio_content),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=tts_audio.{request.response_format}",
                "X-Voice-Used": request.voice,
                "X-Text-Length": str(len(request.text)),
                "X-File-Size": str(len(audio_content))
            }
        )
        
    except openai.RateLimitError:
        logger.error("OpenAI API rate limit exceeded")
        raise HTTPException(status_code=429, detail="OpenAI API rate limit exceeded. Please try again later.")
    except openai.AuthenticationError:
        logger.error("OpenAI API authentication failed")
        raise HTTPException(status_code=500, detail="OpenAI API authentication failed")
    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.post("/chat/completions", response_model=ChatCompletionResponse, summary="Chat Completion")
async def chat_completion(
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate chat completion using OpenAI API
    
    **Features:**
    - Secure backend API (no exposed API keys)
    - Support for multiple models
    - Configurable parameters
    - System prompt override
    - User authentication required
    
    **Supported Models:**
    - gpt-4o-mini (recommended for most use cases)
    - gpt-4o
    - gpt-3.5-turbo
    """
    try:
        # Validate user permissions
        if not current_user:
            raise HTTPException(status_code=403, detail="Authentication required")
        
        # Prepare messages
        messages = []
        
        # Add system prompt if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        # Add conversation messages
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Generate completion
        response = await openai_service.chat_completion(
            messages=messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=request.stream
        )
        
        # Handle streaming response
        if request.stream:
            # For streaming, we would need to implement SSE (Server-Sent Events)
            # This is a basic implementation - you might want to enhance it
            raise HTTPException(status_code=501, detail="Streaming not implemented yet")
        
        # Return structured response
        return ChatCompletionResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage=response.usage.model_dump() if response.usage else None,
            finish_reason=response.choices[0].finish_reason
        )
        
    except openai.RateLimitError:
        logger.error("OpenAI API rate limit exceeded")
        raise HTTPException(status_code=429, detail="OpenAI API rate limit exceeded. Please try again later.")
    except openai.AuthenticationError:
        logger.error("OpenAI API authentication failed")
        raise HTTPException(status_code=500, detail="OpenAI API authentication failed")
    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@router.post("/stt", response_model=STTResponse, summary="Speech-to-Text Transcription")
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    model: str = "whisper-1",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    response_format: str = "json",
    temperature: float = 0.0,
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio using OpenAI Whisper API
    
    **Features:**
    - Secure backend API (no exposed API keys)
    - Support for multiple audio formats
    - Language detection and specification
    - Custom prompts for better accuracy
    - User authentication required
    
    **Supported Audio Formats:**
    - mp3, mp4, mpeg, mpga, m4a, wav, webm
    
    **Languages:**
    - Specify in ISO-639-1 format (e.g., 'en', 'es', 'fr')
    - Leave empty for automatic detection
    """
    try:
        # Validate user permissions
        if not current_user:
            raise HTTPException(status_code=403, detail="Authentication required")
        
        # Validate file type
        allowed_extensions = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'}
        file_extension = os.path.splitext(audio_file.filename or '')[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Open the file for OpenAI API
            with open(temp_file_path, 'rb') as audio_file_obj:
                # Transcribe audio
                transcript = await openai_service.transcribe_audio(
                    audio_file=audio_file_obj,
                    model=model,
                    language=language,
                    prompt=prompt,
                    response_format=response_format,
                    temperature=temperature
                )
            
            # Extract text based on response format
            if response_format == "json" or response_format == "verbose_json":
                text = transcript.text
                detected_language = getattr(transcript, 'language', None)
                duration = getattr(transcript, 'duration', None)
            else:
                # For text, srt, vtt formats
                text = str(transcript)
                detected_language = None
                duration = None
            
            return STTResponse(
                text=text,
                language=detected_language,
                duration=duration,
                model=model
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except openai.RateLimitError:
        logger.error("OpenAI API rate limit exceeded")
        raise HTTPException(status_code=429, detail="OpenAI API rate limit exceeded. Please try again later.")
    except openai.AuthenticationError:
        logger.error("OpenAI API authentication failed")
        raise HTTPException(status_code=500, detail="OpenAI API authentication failed")
    except Exception as e:
        logger.error(f"STT transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"STT transcription failed: {str(e)}")


@router.get("/models", summary="List Available Models")
async def list_models(current_user: User = Depends(get_current_user)):
    """
    List available OpenAI models for different services
    
    **Returns information about:**
    - TTS models and voices
    - Chat completion models
    - STT models
    """
    try:
        if not current_user:
            raise HTTPException(status_code=403, detail="Authentication required")
        
        return {
            "tts": {
                "models": ["tts-1", "tts-1-hd"],
                "voices": {
                    "standard": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                    "advanced": ["sage", "coral", "verse", "ballad", "ash"]
                },
                "formats": ["mp3", "opus", "aac", "flac"],
                "speed_range": {"min": 0.25, "max": 4.0}
            },
            "chat": {
                "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                "max_tokens_range": {"min": 1, "max": 4096},
                "temperature_range": {"min": 0, "max": 2}
            },
            "stt": {
                "models": ["whisper-1"],
                "formats": ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"],
                "response_formats": ["json", "text", "srt", "verbose_json", "vtt"],
                "max_file_size": "25MB"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model information")
