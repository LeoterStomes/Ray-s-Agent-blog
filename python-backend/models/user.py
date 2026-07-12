from sqlalchemy import Column, BigInteger, String, DateTime, Integer
from datetime import datetime, timezone
from database import Base

def now(): return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "user"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    nickname = Column(String(100))
    avatar = Column(String(500))
    email = Column(String(100))
    phone = Column(String(20))
    bio = Column(String(200))
    user_type = Column(Integer, default=1)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
