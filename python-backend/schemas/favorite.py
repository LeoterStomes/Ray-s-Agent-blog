from pydantic import BaseModel
from typing import Optional, List

class FavoriteResponse(BaseModel):
    id: str
    slug: Optional[str] = None
    title: str
    summary: Optional[str] = None
    categoryName: Optional[str] = None
    favoriteCount: int = 0
    isFavorited: bool = True
    class Config:
        from_attributes = True

class PaginatedFavorites(BaseModel):
    records: List[FavoriteResponse]
    total: int
    size: int
    current: int
    pages: int
