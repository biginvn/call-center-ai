# app/main.py
from fastapi import FastAPI
from app.core.database import init_db, close_db, get_database
import asyncio

app = FastAPI()

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
