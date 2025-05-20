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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(60 * 24 * 7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    CORS_ORIGINS: list[str] = Field(["*"], env="CORS_ORIGINS")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")

    # AWS S3
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(..., env="AWS_REGION")
    S3_BUCKET: str = Field(..., env="S3_BUCKET")
    REDIS_HOST: str = Field(..., env="REDIS_HOST")
    REDIS_PORT: int = Field(..., env="REDIS_PORT")
    
    # RECORDING AUTHEN
    AUTH_USERNAME: str = Field(..., env="AUTH_USERNAME")
    AUTH_PASSWORD: str = Field(..., env="AUTH_PASSWORD")
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_mongo_client(self):
        return AsyncIOMotorClient(self.MONGODB_URL)

    def get_database(self):
        client = self.get_mongo_client()
        return client[self.MONGODB_NAME]

settings = Settings()
