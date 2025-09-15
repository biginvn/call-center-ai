from fastapi import FastAPI, Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from app.repositories.base_repository import init_db, close_db, get_database
from app.core.config import settings
from app.models.user import User
from app.auth.auth_routes import router as auth_router
from app.api.user_api import router as user_router
from app.api.logout import router as logout_router
from app.api.conversations_api import conversation_router as conversation_router
from app.api.call_bot import router as call_bot_router
from app.api.extension_api import router as extension_router
from app.api.client_api import router as client_router
from app.api.ai_management_api import router as ai_management_router
from app.middeware.check_token import check_token_middleware
import threading
from app.websocket.ws_monitor import run_ws_monitor
from app.services.voicebot.voicebot_service import VoiceBotService
from app.api.ai_api import router as upload_router
from app.api.voicebot_api import router as voicebot_router
from app.api.crawl_api import router as crawl_router
from app.api.openai_api import router as openai_router

app = FastAPI(
    title="Call Center AI API",
    description="""
    ## Call Center AI API với Multi-Client Support
    
    ### Hướng dẫn Authentication:
    1. **Login**: Sử dụng `/login/admin` hoặc `/login/agent` để lấy access_token
    2. **Authorize**: Click nút **Authorize** ở góc phải, nhập token (KHÔNG cần prefix 'Bearer')
    3. **Test APIs**: Sau khi authorize, tất cả APIs sẽ tự động include token
    
    ### Tài khoản mặc định:
    - **Admin**: username=`admin`, password=`123456`
    - **Agent**: username=`khoa`, password=`123456`, extension=`112`
    
    ### Multi-Client Features:
    - **Clients Management**: CRUD operations cho clients (admin only)
    - **AI Management**: Quản lý AI instructions per client
    - **Data Isolation**: Users chỉ xem data của client họ
    """,
    version="2.0.0",
    swagger_ui_init_oauth=None,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
    }
)

# Security scheme cho Bearer token
security = HTTPBearer()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Call Center AI API",
        version="2.0.0",
        description="Call Center AI API với Multi-Client Support",
        routes=app.routes,
    )
    
    # Thêm security definition
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Nhập JWT token (KHÔNG cần prefix 'Bearer')"
        }
    }
    
    # Thêm global security requirement để Swagger tự động đính kèm token
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Loại bỏ security requirement cho các auth routes
    for path_item in openapi_schema["paths"]:
        if path_item.startswith("/login") or path_item.startswith("/") and path_item == "/":
            for method in openapi_schema["paths"][path_item]:
                if isinstance(openapi_schema["paths"][path_item][method], dict):
                    openapi_schema["paths"][path_item][method]["security"] = []
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Cấu hình CORS cho phép tất cả origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các origin
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các method: GET, POST, PUT, DELETE, ...
    allow_headers=["*"],  # Cho phép tất cả các headers
)


@app.on_event("startup")
async def startup_event():
    await init_db()
    
    # Khởi tạo VoiceBot Service với OpenAI Realtime API
    voicebot_service = VoiceBotService()
    app.state.voicebot_service = voicebot_service
    
    # Khởi động VoiceBot service
    if await voicebot_service.start():
        print("✅ VoiceBot Service với OpenAI Realtime API đã khởi động thành công")
    else:
        print("❌ Lỗi khởi động VoiceBot Service")
    
    # Khởi tạo WebSocket monitor
    ws_thread = threading.Thread(target=run_ws_monitor, daemon=True)
    ws_thread.start()
    print("WS thread started")


@app.on_event("shutdown")
async def shutdown_event():
    # Dừng VoiceBot service
    if hasattr(app.state, 'voicebot_service'):
        await app.state.voicebot_service.stop()
        print("VoiceBot Service đã dừng")
    
    await close_db()


app.middleware("http")(check_token_middleware)
app.include_router(call_bot_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(logout_router)
app.include_router(upload_router)
app.include_router(voicebot_router)
app.include_router(conversation_router)
app.include_router(client_router)
app.include_router(ai_management_router)
app.include_router(extension_router)
app.include_router(crawl_router)
app.include_router(openai_router)

@app.get("/", tags=["Health Check"])
async def hello_world():
    """
    ## Health Check Endpoint
    Kiểm tra server có hoạt động không
    """
    return {"message": "Call Center AI Server is running! 🚀"}

@app.get("/voicebot/status", tags=["VoiceBot"])
async def get_voicebot_status():
    """
    ## VoiceBot Status
    Kiểm tra trạng thái VoiceBot với OpenAI Realtime API
    """
    if hasattr(app.state, 'voicebot_service'):
        voicebot_service = app.state.voicebot_service
        status = voicebot_service.get_status()
        return {
            "status": "success",
            "data": {
                "is_connected": status.is_connected,
                "active_calls": status.active_calls,
                "total_calls_today": status.total_calls_today,
                "uptime": status.uptime,
                "version": status.version,
                "last_error": status.last_error
            }
        }
    else:
        return {
            "status": "error",
            "message": "VoiceBot service chưa được khởi tạo"
        }

@app.get("/voicebot/health", tags=["VoiceBot"])
async def voicebot_health_check():
    """
    ## VoiceBot Health Check
    Kiểm tra sức khỏe của VoiceBot service
    """
    if hasattr(app.state, 'voicebot_service'):
        voicebot_service = app.state.voicebot_service
        is_healthy = await voicebot_service.health_check()
        return {
            "status": "success" if is_healthy else "error",
            "healthy": is_healthy,
            "message": "VoiceBot service hoạt động tốt" if is_healthy else "VoiceBot service có vấn đề"
        }
    else:
        return {
            "status": "error",
            "healthy": False,
            "message": "VoiceBot service chưa được khởi tạo"
        }
