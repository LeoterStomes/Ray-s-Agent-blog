import os
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Music

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "music")
os.makedirs(MUSIC_DIR, exist_ok=True)


def get_list(db: Session):
    items = db.query(Music).order_by(Music.sort_order.asc(), Music.id.desc()).all()
    return [{"id": m.id, "title": m.title, "artist": m.artist, "url": m.url, "lyrics": m.lyrics, "cover": m.cover, "sort_order": m.sort_order} for m in items]


def upload_and_create(db: Session, file_content: bytes, filename: str, title: str, artist: str):
    ext = os.path.splitext(filename)[1].lower() or ".mp3"
    fname = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(MUSIC_DIR, fname), "wb") as f:
        f.write(file_content)
    url = f"/uploads/music/{fname}"
    max_order = db.query(func.coalesce(func.max(Music.sort_order), 0)).scalar() or 0
    m = Music(title=title or filename.rsplit(".", 1)[0], artist=artist or "未知", url=url, sort_order=max_order + 1)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "title": m.title, "url": url}


def update(db: Session, mid: int, data: dict):
    m = db.query(Music).filter(Music.id == mid).first()
    if not m:
        return False
    for f in ["title", "artist", "lyrics", "sort_order"]:
        if f in data and data[f] is not None:
            setattr(m, f, data[f])
    db.commit()
    return True


def delete(db: Session, mid: int):
    m = db.query(Music).filter(Music.id == mid).first()
    if m:
        try:
            os.remove(os.path.join(MUSIC_DIR, os.path.basename(m.url)))
        except OSError:
            pass
        db.delete(m)
        db.commit()
    return m is not None