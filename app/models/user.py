from beanie import Document
from datetime import datetime
from pydantic import EmailStr
from typing import Optional


class User(Document):
    username: str
    fullname: str
    email: EmailStr
    password: str
    role: str
    extension_number: str
    last_login: Optional[datetime] = None

    class Settings:
        name = "User"

    def __str__(self):
        return f"User(id={self.id}, User(username={self.username}, fullname={self.fullname},email={self.email}, password={self.password}, role={self.role}, extension_number={self.extension_number}, lastLogin={self.last_login})"