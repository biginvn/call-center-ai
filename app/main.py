from fastapi import FastAPI, Depends
from app.core.database import init_db, close_db, get_database
from app.core.config import settings
from app.models.user import User
from app.auth.auth_routes import router as auth_router

app = FastAPI()


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
