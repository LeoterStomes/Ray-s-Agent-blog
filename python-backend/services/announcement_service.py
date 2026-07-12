from sqlalchemy.orm import Session
from models import Announcement


def get_list(db: Session):
    items = db.query(Announcement).filter(Announcement.status == 1).order_by(
        Announcement.sort_order.asc(), Announcement.id.desc()
    ).all()
    return [{"id": a.id, "content": a.content, "link": a.link, "sort_order": a.sort_order, "status": a.status} for a in items]


def get_all(db: Session):
    items = db.query(Announcement).order_by(Announcement.sort_order.asc(), Announcement.id.desc()).all()
    return [{"id": a.id, "content": a.content, "link": a.link, "sort_order": a.sort_order, "status": a.status, "created_at": str(a.created_at)} for a in items]


def create(db: Session, data: dict):
    a = Announcement(content=data["content"], link=data.get("link", ""), sort_order=data.get("sort_order", 0))
    db.add(a)
    db.commit()
    return a.id


def update(db: Session, aid: int, data: dict):
    a = db.query(Announcement).filter(Announcement.id == aid).first()
    if not a:
        return False
    for f in ["content", "link", "sort_order", "status"]:
        if f in data and data[f] is not None:
            setattr(a, f, data[f])
    db.commit()
    return True


def delete(db: Session, aid: int):
    a = db.query(Announcement).filter(Announcement.id == aid).first()
    if a:
        db.delete(a)
        db.commit()
    return a is not None