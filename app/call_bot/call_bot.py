import os
from app.models.conversation import Conversation
from app.models.enums import ConversationMood, ConversationStatus, ConversationType
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_service import AIService, gpt_call_analyze_response
from fastapi import Depends
from typing import List, Optional, Literal, Any
from app.auth.auth import get_current_user
from app.models.user import User
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



class FinishSessionRequest(BaseModel):
    current_user: User
    audio_url: str

async def finish_openai_bot_session(request: FinishSessionRequest):
    try:
        user = request.current_user
        audio_url = request.audio_url
        print("Finishing bot session for user:", user.username)

        # Bot user (giả định dùng 1 account cố định)
        bot_user = await UserRepository.get_user_by_username("thanh")
        if not bot_user:
            raise Exception("Bot user 'genai_bot' not found in system")

        # 1. Upload file lên S3 (nếu cần)
        ai_service = AIService()
        file_url = await ai_service.upload_record_to_s3(audio_url, user.username)
        print("File uploaded to S3:", file_url)

        # 2. Phân tích file ghi âm
        ai_response: gpt_call_analyze_response = await ai_service.analyze_call_full_one_gpt_call(
            file_url, user.username, bot_user.username
        )
        print("AI analyze response:", ai_response)

        # 3. Lưu từng message vào DB
        messages = []
        for mes in ai_response.messages:
            msg = Message(
                sender_id=mes.sender_id,
                content=mes.content,
                mood=mes.mood,
                order=mes.order,
                start_time=mes.start_time,
                end_time=mes.end_time
            )
            await msg.insert()
            messages.append(msg)

        # 4. Tạo conversation
        conversation = Conversation(
            type=ConversationType.AGENT_TO_AI,
            from_user=bot_user,
            to_user=user,
            status=ConversationStatus.CLOSED,
            record_url=file_url,
            mood=ConversationMood.UNKNOWN,
            messages=messages,
            summarize=ai_response.summarize,
            sentiment=ai_response.overall_mood,
        )
        saved_conversation = await ConversationRepository.create_conversation(conversation)
        print("Saved bot conversation successfully:", saved_conversation)

        return saved_conversation

    except Exception as e:
        print("Error in finish_openai_bot_session:", str(e))
        raise e

