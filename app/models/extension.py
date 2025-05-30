from beanie import Document, Link
from typing import Optional
from app.models.user import User


class Extension(Document):
    extension: str
    number: str
    available: bool = True
    user: Optional[Link[User]] = None
    
    class Settings:
        name = "Extension"
        
    def __str__(self):
        return f"Extension(extension={self.extension}, number={self.number}, available={self.available}, user={self.user})"