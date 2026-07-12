from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer
from database import Base
from .user import now

class Project(Base):
    __tablename__ = "project"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    tags = Column(String(500), default="")
    github_url = Column(String(500), default="")
    cover = Column(String(500), default="")
    status = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
