from sqlalchemy import Column, BigInteger, String, DateTime, Integer
from database import Base
from .user import now

class Announcement(Base):
    __tablename__ = "announcement"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    content = Column(String(500), nullable=False)
    link = Column(String(500), default="")
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, default=now)
