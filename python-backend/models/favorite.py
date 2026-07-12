from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Index
from database import Base
from .user import now

class UserFavorite(Base):
    __tablename__ = "user_favorite"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    article_id = Column(String(64), ForeignKey("knowledge_article.id"), nullable=False)
    created_at = Column(DateTime, default=now)
    __table_args__ = (Index("uk_user_article", "user_id", "article_id", unique=True),)
