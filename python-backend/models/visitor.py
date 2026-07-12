from sqlalchemy import Column, BigInteger, String, DateTime
from database import Base
from .user import now

class VisitorLog(Base):
    __tablename__ = "visitor_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ip = Column(String(45))
    user_agent = Column(String(500))
    visited_at = Column(DateTime, default=now)
