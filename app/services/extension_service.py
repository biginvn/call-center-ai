from app.repositories.extension_repository import ExtensionRepository
from app.models.extension import Extension
from typing import List
from app.auth.exceptions import CustomHTTPException
import logging

logger = logging.getLogger(__name__)

class ExtensionService:
    def __init__(self):
        self.extension_repo = ExtensionRepository()

    async def get_all_extensions(self) -> List[Extension]:
        extensions = await self.extension_repo.get_all_extensions()
        if not extensions:
            logger.error("No extensions found")
            raise CustomHTTPException(status_code=404, detail="No extensions found")
        return extensions

    async def get_extension_by_number(self, number: str) -> Extension:
        extension = await self.extension_repo.get_extension_by_number(number)
        if not extension:
            logger.error(f"Extension {number} not found")
            raise CustomHTTPException(status_code=404, detail="Extension not found")
        return extension

    async def update_extension_availability(self, number: str, available: bool) -> Extension:
        extension = await self.get_extension_by_number(number)
        updated_extension = await self.extension_repo.update_extension_availability(extension, available)
        logger.info(f"Extension {number} updated to available={available}")
        return updated_extension
