from beanie import Document
from typing import Optional


class Client(Document):
    name: str
    description: Optional[str] = None
    voicebot_usage_limit: int = -1  # -1 means unlimited
    voicebot_usage_total: int = 0

    class Settings:
        name = "Client"

    def __str__(self):
        return f"Client(id={self.id}, name={self.name}, description={self.description})" 