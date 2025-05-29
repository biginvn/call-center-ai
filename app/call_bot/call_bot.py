import os
from typing import List, Optional, Literal, Any
import httpx
from app.core.config import settings
from pydantic import BaseModel


# --- Submodels ---
class InputAudioTranscription(BaseModel):
    model: str


class ClientSecret(BaseModel):
    value: str
    expires_at: int


class TurnDetection(BaseModel):
    create_response: Optional[bool] = True
    interrupt_response: Optional[bool] = True
    eagerness: Optional[Literal["low", "medium", "high", "auto"]] = "auto"  # only for semantic_vad
    prefix_padding_ms: Optional[int] = 300  # only for server_vad
    silence_duration_ms: Optional[int] = 500
    threshold: Optional[float] = 0.5


# --- Request and Response models ---
class SessionRequest(BaseModel):
    instructions: str = ""


class SessionResponse(BaseModel):
    id: str
    object: str
    model: str
    modalities: List[str]
    instructions: Optional[str]
    voice: Optional[str]
    input_audio_format: Optional[str]
    output_audio_format: Optional[str]
    input_audio_transcription: Optional[InputAudioTranscription]
    turn_detection: Optional[TurnDetection]  # now correctly typed
    tools: Optional[List[Any]] = []
    tool_choice: Literal["none", "auto", "required", "manual"]
    temperature: float
    max_response_output_tokens: str
    client_secret: ClientSecret


# --- Main session creation ---
async def create_openai_session(instructions: str = "") -> SessionResponse:
    url = "https://api.openai.com/v1/realtime/sessions"

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "gpt-4o-mini-realtime-preview-2024-12-17",
        "voice": "verse",
    }

    if instructions:
        body["instructions"] = instructions

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return SessionResponse(**response.json())  # Parse into model
