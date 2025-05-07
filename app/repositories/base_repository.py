from typing import Generic, TypeVar, Optional
from beanie import Document
from pydantic.v1 import BaseModel

T = TypeVar('T', bound=Document)  # Generic type cho Beanie Document

class BaseRepository(Generic[T]):
    """
    Lớp base chứa các phương thức CRUD chung cho tất cả repositories
    Giúp tránh lặp code giữa các repository con
    """
    def __init__(self, document_model: type[T]):
        self.model = document_model

    async def get_by_id(self, id: str) -> Optional[T]:
        """Lấy document bằng _id"""
        return await self.model.get(id)

    async def create(self, data: BaseModel) -> T:
        """Tạo mới document từ Pydantic schema"""
        return await self.model(**data.dict()).insert()

    async def update(self, id: str, data: BaseModel) -> Optional[T]:
        """Cập nhật document"""
        doc = await self.get_by_id(id)
        if doc:
            await doc.update({"$set": data.dict(exclude_unset=True)})
            return doc
        return None