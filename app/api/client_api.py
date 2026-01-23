from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.models.client import Client
from app.services.client_service import ClientService
from app.auth.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/clients", tags=["clients"])

class UpdateClientLimitRequest(BaseModel):
    voicebot_usage_limit: int

class AddClientUsageRequest(BaseModel):
    duration: int

@router.put("/{client_id}/limit")
async def update_client_limit(
    client_id: str, 
    request: UpdateClientLimitRequest,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "system":
         raise HTTPException(status_code=403, detail="Not authorized")
    
    client = await Client.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.voicebot_usage_limit = request.voicebot_usage_limit
    await client.save()
    
    return {"message": "Client limit updated successfully", "voicebot_usage_limit": client.voicebot_usage_limit}

    return {"message": "Client limit updated successfully", "voicebot_usage_limit": client.voicebot_usage_limit}

@router.post("/{client_id}/usage")
async def add_client_usage(
    client_id: str,
    request: AddClientUsageRequest,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "system":
         raise HTTPException(status_code=403, detail="Not authorized")
    
    client = await Client.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.voicebot_usage_total += request.duration
    await client.save()
    
    return {
        "message": "Client usage updated successfully", 
        "voicebot_usage_total": client.voicebot_usage_total,
        "added_duration": request.duration
    }

# DTOs
class ClientCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    account_username: Optional[str] = None
    account_password: Optional[str] = None
    

class ClientUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ClientResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    voicebot_usage_limit: int 
    voicebot_usage_total: int

    @classmethod
    def from_model(cls, client: Client) -> "ClientResponse":
        return cls(
            id=str(client.id),
            name=client.name,
            description=client.description,
            voicebot_usage_limit=client.voicebot_usage_limit,
            voicebot_usage_total=client.voicebot_usage_total
        )

# Service
client_service = ClientService()

@router.get("/all", response_model=List[ClientResponse])
async def get_all_clients(current_user: User = Depends(get_current_user)):
    """
    ## Lấy tất cả clients
    
    **Quyền**: Chỉ admin mới được xem danh sách clients
    
    **Returns**: Danh sách tất cả clients trong hệ thống
    """
    if current_user.role != "system":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền xem danh sách clients")
    
    clients = await client_service.get_all_clients()
    return [ClientResponse.from_model(client) for client in clients]

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    """
    ## Lấy thông tin chi tiết một client
    
    **Quyền**: Admin có thể xem tất cả, user chỉ xem client của mình
    """
    # Admin có thể xem tất cả, user chỉ xem client của mình
    if current_user.role != "system":
        # Tạm thời cho phép - sẽ implement client checking sau
        pass
    
    client = await client_service.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client không tồn tại")
    
    return ClientResponse.from_model(client)

@router.post("/create", response_model=ClientResponse)
async def create_client(
    request: ClientCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    ## Tạo client mới
    
    **Quyền**: Chỉ admin mới được tạo client
    
    **Example Request**:
    ```json
    {
        "name": "Công ty ABC",
        "description": "Client dành cho công ty ABC"
    }
    ```
    """
    if current_user.role != "system":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền tạo client")
    if not request.account_username or not request.account_password:
        raise HTTPException(status_code=403, detail="Account username and password are required")
    try:
        client = await client_service.create_client(request.name, request.description, request.account_username, request.account_password)
        return ClientResponse.from_model(client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    request: ClientUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    ## Cập nhật thông tin client
    
    **Quyền**: Chỉ admin mới được cập nhật client
    """
    if current_user.role != "system":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền cập nhật client")
    
    try:
        client = await client_service.update_client(
            client_id, 
            request.name, 
            request.description
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client không tồn tại")
        
        return ClientResponse.from_model(client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    ## Xóa client
    
    **Quyền**: Chỉ admin mới được xóa client
    
    **Warning**: Thao tác này sẽ xóa client và có thể ảnh hưởng đến data liên quan
    """
    if current_user.role != "system":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền xóa client")
    
    success = await client_service.delete_client(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client không tồn tại")
    
    return {"message": "Client đã được xóa thành công"} 