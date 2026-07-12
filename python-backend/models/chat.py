from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, ForeignKey
from database import Base
from .user import now

class ConsultationSession(Base):
    __tablename__ = "consultation_session"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    session_title = Column(String(200))
    started_at = Column(DateTime, default=now)
    last_emotion_analysis = Column(Text)
    last_emotion_updated_at = Column(DateTime)

class ConsultationMessage(Base):
    __tablename__ = "consultation_message"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("consultation_session.id"), nullable=False, index=True)
    sender_type = Column(Integer, nullable=False)
    message_type = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    emotion_tag = Column(String(50))
    ai_model = Column(String(50))
    created_at = Column(DateTime, default=now)
