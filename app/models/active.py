from beanie import Document,Link
from typing import Optional, List
from app.models.user import User

class ActiveUser(Document):
    active_user: Optional[List[User]] = None

    class Settings:
        name = "ActiveUser"
        
    def __str__(self):
        return f"ActiveUser(active_user={self.active_user})"