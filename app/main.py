from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db, close_db, get_database
import asyncio

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
    # Kiểm tra kết nối
    try:
        db = get_database()
        await db.command("ping")
        print("Kết nối tới MongoDB Atlas thành công!")
    except Exception as e:
        print(f"Lỗi kết nối tới MongoDB Atlas: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
    print("Đã đóng kết nối tới MongoDB Atlas.")

@app.get("/")
async def hello_world():
    return {"message": "Hello World"}
