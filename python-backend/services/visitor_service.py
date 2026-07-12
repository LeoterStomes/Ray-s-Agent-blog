from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import VisitorLog


def stats(db: Session):
    total = db.query(VisitorLog).count()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    online = db.query(func.count(func.distinct(VisitorLog.ip))).filter(VisitorLog.visited_at >= cutoff).scalar() or 0
    return {"total": total, "online": max(online, 1)}


def ping(db: Session, ip: str, ua: str):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    exists = db.query(VisitorLog).filter(VisitorLog.ip == ip, VisitorLog.visited_at >= cutoff).first()
    if not exists:
        db.add(VisitorLog(ip=ip, user_agent=ua[:500], visited_at=datetime.now(timezone.utc)))
        db.commit()