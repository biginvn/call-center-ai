from beanie import Document
from datetime import datetime
from pydantic import EmailStr
from typing import Optional


class User(Document):
    username: str
    email: EmailStr
    password: str
    role: str
    extension_number: str
    last_login: Optional[datetime] = None

    class Settings:
        name = "User"

    def __str__(self):
        return f"User(username={self.username}, email={self.email}, password={self.password}, role={self.role}, extension_number={self.extension_number}, lastLogin={self.last_login})"