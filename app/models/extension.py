from beanie import Document


class Extension(Document):
    extension: str
    number: str
    
    class Settings:
        name = "Extension"
        
    def __str__(self):
        return f"Extension(extension={self.extension}, number={self.number})"