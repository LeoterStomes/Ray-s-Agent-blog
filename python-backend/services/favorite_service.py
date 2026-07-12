from sqlalchemy.orm import Session
from models import UserFavorite, KnowledgeArticle


def paginate(db: Session, user_id: int, page=1, size=50):
    q = db.query(UserFavorite).filter(UserFavorite.user_id == user_id).order_by(UserFavorite.id.desc())
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    records = []
    for fav in items:
        a = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == fav.article_id).first()
        if a:
            records.append({
                "id": a.id, "title": a.title, "summary": a.summary,
                "categoryName": a.category.category_name if a.category else None,
                "favoriteCount": 0, "isFavorited": True,
            })
    return records, total


def toggle(db: Session, user_id: int, article_id: str):
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id, UserFavorite.article_id == article_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return "removed"
    fav = UserFavorite(user_id=user_id, article_id=article_id)
    db.add(fav)
    db.commit()
    return "added"


def is_favorited(db: Session, user_id: int, article_id: str):
    return db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id, UserFavorite.article_id == article_id
    ).first() is not None