from pydantic import Field
from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = Field(..., env="MONGODB_URL")
    MONGODB_NAME: str = Field(..., env="callcenter")
    
    # Auth
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(..., env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    CORS_ORIGINS: list[str] = Field(["*"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_mongo_client(self):
        return AsyncIOMotorClient(self.MONGODB_URL)

    def get_database(self):
        client = self.get_mongo_client()
        return client[self.MONGODB_NAME]

settings = Settings()