from beanie import Document
from datetime import datetime
from pydantic import EmailStr, Field


class User(Document):
    username: str
    email: EmailStr
    passwordHash: str
    role: str
    extensionNumber: str
    status: str
    lastLogin: datetime = None

    class Settings:
        name = "User"
