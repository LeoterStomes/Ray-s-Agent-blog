from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import ConsultationSession, ConsultationMessage


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_session(db: Session, user_id: int, title: str, initial_message: str = ""):
    s = ConsultationSession(user_id=user_id, session_title=title[:30], started_at=_now())
    db.add(s)
    db.commit()
    db.refresh(s)
    if initial_message:
        msg = ConsultationMessage(session_id=s.id, sender_type=1, content=initial_message, created_at=_now())
        db.add(msg)
        db.commit()
    return str(s.id)


def verify_session(db: Session, session_id: int, user_id: int):
    return db.query(ConsultationSession).filter(
        ConsultationSession.id == session_id, ConsultationSession.user_id == user_id
    ).first()


def save_message(db: Session, session_id: int, sender_type: int, content: str, ai_model: str = None):
    msg = ConsultationMessage(
        session_id=session_id, sender_type=sender_type, content=content, ai_model=ai_model, created_at=_now()
    )
    db.add(msg)
    db.commit()


def get_history(db: Session, session_id: int):
    return db.query(ConsultationMessage).filter(
        ConsultationMessage.session_id == session_id
    ).order_by(ConsultationMessage.created_at.asc()).all()