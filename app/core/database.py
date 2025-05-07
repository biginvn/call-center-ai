from beanie import init_beanie
from app.core.config import settings
from app.models.user import User
from app.models.message import Message
from app.models.document import Document
from app.models.ai import AI
from app.models.conversation import Conversation

# Khởi tạo client toàn cục
client = None

async def init_db():
    global client
    # Sử dụng client từ settings
    client = settings.get_mongo_client()
    database = client[settings.MONGODB_NAME]
    
    # Khởi tạo Beanie với database và các mô hình
    await init_beanie(
        database=database,
        document_models=[User, Message, Document, AI, Conversation],
    )
    return client

async def close_db():
    global client
    if client:
        client.close()
        client = None

def get_database():
    if client is None:
        raise RuntimeError("Database client is not initialized. Call init_db() first.")
    return client[settings.MONGODB_NAME]