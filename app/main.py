from fastapi import FastAPI, Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db, close_db, get_database
from app.core.config import settings
from app.models.user import User
from app.auth.auth_routes import router as auth_router
from app.api.get_user import router as user_router
from app.api.logout import router as logout_router
from app.api.post_conversation import router as conversation_router
from app.middeware.check_token import check_token_middleware
from app.api.post_upload_file import router as upload_router

app = FastAPI()

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


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


app.middleware("http")(check_token_middleware)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(logout_router)
app.include_router(conversation_router)
app.include_router(upload_router)


@app.get("/")
async def hello_world():
    return {"message": "Hello World"}
