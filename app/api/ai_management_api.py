from beanie import Link
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.models.ai import AI
from app.models.client import Client
from app.models.user import User
from app.services.ai_management_service import AIManagementService
from app.auth.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Management"])

# DTOs
class AIInstructionRequest(BaseModel):
    instructions: str
    voice: str
    
    class Config:
        schema_extra = {
            "example": {
                "instructions": "Bạn là tổng đài viên chuyên nghiệp, thân thiện...",
                "voice": "shimmer"
            }
        }

class AIInstructionResponse(BaseModel):
    id: str
    instructions: str
    voice: str
    client_id: Optional[Link[Client]] = None

    @classmethod
    def from_model(cls, ai: AI) -> "AIInstructionResponse":
        return cls(
            id=str(ai.id),
            instructions=ai.instructions,
            voice=ai.voice,
            client_id=ai.client_id
        )

# Service
ai_management_service = AIManagementService()

@router.get("/instructions", response_model=Optional[AIInstructionResponse])
async def get_ai_instructions(current_user: User = Depends(get_current_user)):
    """
    ## Lấy AI Instructions
    
    Lấy thông tin cấu hình AI instructions cho chatbot
    
    **Returns**: AI configuration hoặc null nếu chưa có
    """
    ai = await ai_management_service.get_ai_instructions(current_user)
    if not ai:
        return None
    return AIInstructionResponse.from_model(ai)


@router.put("/instructions", response_model=AIInstructionResponse)
async def update_ai_instructions(
    request: AIInstructionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    ## Cập nhật AI Instructions
    
    Cập nhật cấu hình AI instructions hiện có
    
    **Note**: Thao tác này sẽ thay thế hoàn toàn cấu hình cũ
    """
    ai = await ai_management_service.update_ai_instructions(
        request.instructions, 
        request.voice, 
        current_user
    )
    return AIInstructionResponse.from_model(ai) 