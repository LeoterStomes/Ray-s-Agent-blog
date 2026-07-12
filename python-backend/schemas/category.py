from pydantic import BaseModel
from typing import Optional

class CategoryResponse(BaseModel):
    id: int
    categoryName: Optional[str] = None
    description: Optional[str] = None
    sortOrder: Optional[int] = None
    status: Optional[int] = None
    articleCount: int = 0
    class Config:
        from_attributes = True
