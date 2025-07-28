from beanie import init_beanie, Document
from beanie import PydanticObjectId
from app.core.config import settings
from app.models.client import Client
from app.models.user import User
from app.models.message import Message
from app.models.document import Document as DocumentModel
from app.models.ai import AI
from app.models.conversation import Conversation
from app.models.token import RefreshToken
from app.models.extension import Extension
from app.models.active import ActiveUser
from typing import TypeVar, Generic, Optional, List
import os, certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# Khởi tạo client toàn cục
client = None

T = TypeVar('T', bound=Document)

class BaseRepository(Generic[T]):
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Lấy document theo ID"""
        try:
            # Validate ObjectId format
            if not PydanticObjectId.is_valid(id):
                return None
            return await self.model_class.get(id)
        except Exception:
            return None
    
    async def get_all(self) -> List[T]:
        """Lấy tất cả documents"""
        return await self.model_class.find_all().to_list()
    
    async def create(self, **kwargs) -> T:
        """Tạo document mới"""
        document = self.model_class(**kwargs)
        await document.insert()
        return document
    
    async def update(self, id: str, **kwargs) -> Optional[T]:
        """Cập nhật document"""
        document = await self.get_by_id(id)
        if not document:
            return None
        
        for key, value in kwargs.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        await document.save()
        return document
    
    async def delete(self, id: str) -> bool:
        """Xóa document"""
        document = await self.get_by_id(id)
        if not document:
            return False
        
        await document.delete()
        return True

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
            document_models=[Client, User, Message, DocumentModel, AI, Conversation, RefreshToken, Extension, ActiveUser],
        )
        
        # Rebuild models để giải quyết forward references trong runtime
        print("Rebuilding models...")
        try:
            # Phase 1: Rebuild base models first (no dependencies)
            print("Phase 1: Rebuilding base models...")
            Client.model_rebuild()
            User.model_rebuild()
            Extension.model_rebuild()
            RefreshToken.model_rebuild()
            ActiveUser.model_rebuild()
            
            # Phase 2: Rebuild models with simple dependencies
            print("Phase 2: Rebuilding models with dependencies...")
            Message.model_rebuild()
            DocumentModel.model_rebuild()
            
            # Phase 3: Rebuild AI model (depends on Client)
            print("Phase 3: Rebuilding AI model...")
            AI.model_rebuild()
            
            # Phase 4: Rebuild Conversation last (depends on multiple models)
            print("Phase 4: Rebuilding Conversation model...")
            Conversation.model_rebuild()
            
            print("Models rebuilt successfully")
        except Exception as e:
            print(f"Warning: Model rebuild failed: {e}")
            # Try alternative rebuild approach
            print("Attempting alternative rebuild approach...")
            try:
                # Force import of all model classes to ensure they're available
                from app.models.client import Client as ClientModel
                from app.models.user import User as UserModel
                from app.models.ai import AI as AIModel
                from app.models.conversation import Conversation as ConversationModel
                
                # Rebuild in dependency order
                ClientModel.model_rebuild()
                UserModel.model_rebuild()
                AIModel.model_rebuild()
                ConversationModel.model_rebuild()
                print("Alternative rebuild successful")
            except Exception as e2:
                print(f"Alternative rebuild also failed: {e2}")
                print("Continuing without model rebuild - some features may not work correctly")
        
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