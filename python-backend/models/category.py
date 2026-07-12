from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer
from database import Base
from .user import now

class KnowledgeCategory(Base):
    __tablename__ = "knowledge_category"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_name = Column(String(100), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
