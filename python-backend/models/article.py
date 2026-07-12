from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from .user import now

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_article"
    id = Column(String(64), primary_key=True)
    category_id = Column(BigInteger, ForeignKey("knowledge_category.id"))
    title = Column(String(200), nullable=False)
    summary = Column(String(1000))
    content = Column(Text)
    cover_image = Column(String(500))
    tags = Column(String(500))
    author_id = Column(BigInteger, ForeignKey("user.id"))
    read_count = Column(Integer, default=0)
    status = Column(Integer, default=0)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
    category = relationship("KnowledgeCategory", lazy="joined")
    author = relationship("User", lazy="joined")
