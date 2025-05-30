from typing import Optional
from beanie import Document



class AI(Document):
    instructions: str
    voice: str
    token: Optional[str] = None

    class Settings:
        name = "AI"
    def __repr__(self):
        return f"AI(instruction={self.instructions}, voice={self.voice}, token={self.token})"
