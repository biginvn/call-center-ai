from beanie import Document
from typing import Optional


class Client(Document):
    name: str
    description: Optional[str] = None

    class Settings:
        name = "Client"

    def __str__(self):
        return f"Client(id={self.id}, name={self.name}, description={self.description})" 