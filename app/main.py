from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db, close_db, get_database
from app.core.config import settings
from app.models.user import User
from app.auth.auth_routes import router as auth_router

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


app.include_router(auth_router)


@app.get("/")
async def hello_world():
    return {"message": "Hello World"}
