from app.models.extension import Extension
from typing import Optional, List
from app.models.user import User

class ExtensionRepository:
    @staticmethod
    async def get_all_extensions() -> List[Extension]:
        return await Extension.find_all().to_list()

    @staticmethod
    async def get_extension_by_number(number: str) -> Optional[Extension]:
        return await Extension.find_one(Extension.number == number)

    @staticmethod
    async def update_extension_availability(extension: Extension, available: bool, user:User) -> Extension:
        extension.user = user
        extension.available = available
        return await extension.save()
