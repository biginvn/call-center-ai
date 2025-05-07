from typing import List
from beanie import Document, Link


class AI(Document):
    prompt: str
    documents: List[Link[Document]]

    class Settings:
        name = "AI"
