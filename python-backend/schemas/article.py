from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ArticleSimpleResponse(BaseModel):
    id: str
    categoryId: Optional[int] = None
    categoryName: Optional[str] = None
    title: str
    summary: Optional[str] = None
    coverImage: Optional[str] = None
    tags: Optional[str] = None
    authorName: Optional[str] = None
    readCount: int = 0
    status: Optional[int] = None
    publishedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    favoriteCount: int = 0
    isFavorited: bool = False
    class Config:
        from_attributes = True

class ArticleDetailResponse(ArticleSimpleResponse):
    content: Optional[str] = None

class PaginatedArticles(BaseModel):
    records: List[ArticleSimpleResponse]
    total: int
    size: int
    current: int
    pages: int
