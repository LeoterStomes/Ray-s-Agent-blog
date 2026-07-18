from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from .user import now


class Comment(Base):
    __tablename__ = "comment"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    article_id = Column(String(64), ForeignKey("knowledge_article.id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(BigInteger, ForeignKey("comment.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    user = relationship("User", lazy="joined")
