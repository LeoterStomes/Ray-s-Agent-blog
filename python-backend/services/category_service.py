from sqlalchemy.orm import Session
from models import KnowledgeCategory, KnowledgeArticle


def get_tree(db: Session):
    cats = db.query(KnowledgeCategory).filter(KnowledgeCategory.status == 1).order_by(KnowledgeCategory.sort_order.asc()).all()
    result = []
    for c in cats:
        count = db.query(KnowledgeArticle).filter(KnowledgeArticle.category_id == c.id, KnowledgeArticle.status == 1).count()
        result.append({
            "id": c.id, "categoryName": c.category_name, "description": c.description,
            "sortOrder": c.sort_order, "status": c.status, "articleCount": count,
        })
    return result


def get_all(db: Session):
    cats = db.query(KnowledgeCategory).order_by(KnowledgeCategory.sort_order.asc()).all()
    return [{"id": c.id, "categoryName": c.category_name, "description": c.description, "sortOrder": c.sort_order, "status": c.status} for c in cats]


def create(db: Session, data: dict):
    c = KnowledgeCategory(category_name=data["categoryName"], description=data.get("description", ""), sort_order=data.get("sortOrder", 0))
    db.add(c)
    db.commit()
    return c.id


def update(db: Session, cid: int, data: dict):
    c = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == cid).first()
    if not c:
        return False
    for f in ["categoryName", "description", "sortOrder"]:
        if f in data and data[f] is not None:
            setattr(c, f, data[f])
    db.commit()
    return True


def delete(db: Session, cid: int):
    c = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == cid).first()
    if c:
        db.delete(c)
        db.commit()
    return c is not None