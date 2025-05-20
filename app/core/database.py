from beanie import init_beanie
from app.core.config import settings
from app.models.user import User
from app.models.message import Message
from app.models.document import Document
from app.models.ai import AI
from app.models.conversation import Conversation
from app.models.token import RefreshToken
from app.models.extension import Extension
from app.models.active import ActiveUser
import os, certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# Khởi tạo client toàn cục
client = None

async def init_db():
    global client
    try:
        # Sử dụng client từ settings
        client = settings.get_mongo_client()
        database = client[settings.MONGODB_NAME]
        
        # Log connection info
        print(f"Connecting to MongoDB at {settings.MONGODB_URL}")
        print(f"Using database: {settings.MONGODB_NAME}")
        
        # Khởi tạo Beanie với database và các mô hình
        await init_beanie(
            database=database,
            document_models=[User, Message, Document, AI, Conversation, RefreshToken, Extension, ActiveUser],
        )
        print("Database initialized successfully")
        
        # Verify connection
        await database.command("ping")
        print("Database connection verified")
        
        return client
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

async def close_db():
    global client
    if client:
        client.close()
        client = None

def get_database():
    if client is None:
        raise RuntimeError("Database client is not initialized. Call init_db() first.")
    return client[settings.MONGODB_NAME]