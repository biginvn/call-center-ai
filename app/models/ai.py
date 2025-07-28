from typing import Optional, TYPE_CHECKING, ForwardRef
from beanie import Document, Link

if TYPE_CHECKING:
    from app.models.client import Client
else:
    # For runtime, create a forward reference
    Client = ForwardRef('Client')


class AI(Document):
    instructions: str
    voice: str
    client_id: Link[Client]
    token: Optional[str] = None

    class Settings:
        name = "AI"
    def __repr__(self):
        return f"AI(instruction={self.instructions}, voice={self.voice}, token={self.token})"
