from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer
from database import Base
from .user import now

class Music(Base):
    __tablename__ = "music"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    artist = Column(String(200), default="未知")
    url = Column(String(500), nullable=False)
    lyrics = Column(Text)
    cover = Column(String(500), default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)
