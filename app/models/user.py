from beanie import Document
from datetime import datetime
from pydantic import EmailStr
from typing import Optional


class User(Document):
    username: str
    email: EmailStr
    password: str
    role: str
    extensionNumber: str
    lastLogin: Optional[datetime] = None

    class Settings:
        name = "User"

    def __str__(self):
        return f"User(username={self.username}, email={self.email}, password={self.password}, role={self.role}, extensionNumber={self.extensionNumber}, status={self.status}, lastLogin={self.lastLogin})"