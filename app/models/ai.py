from typing import List
from beanie import Document, Link


class AI(Document):
    instructions: str
    voice: str

    class Settings:
        name = "AI"
    def __repr__(self):
        return f"AI(instruction={self.instructions}, voice={self.voice})"
