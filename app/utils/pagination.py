from pydantic import BaseModel, Field


class Pagination(BaseModel):
    page_number: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1)
    total_pages: int = Field(default=0, ge=0)
    total_items: int = Field(default=0, ge=0)

    def set_total_items_and_total_pages(self, total_items: int):
        self.total_items = total_items
        self.total_pages = (self.total_items + self.page_size - 1) // self.page_size

    @property
    def skip(self) -> int:
        return (self.page_number - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size