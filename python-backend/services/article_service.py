import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import KnowledgeArticle, UserFavorite

def _sync_rag(article_id: str, article=None):
    """同步文章到 RAG 向量库。成功→索引，失败→静默跳过（不阻塞发布流程）"""
    try:
        from services.rag_service import index_article, delete_article
        if article is None:
            # 下架/删除 → 从向量库移除
            delete_article(article_id)
        else:
            # 发布/更新 → 重建索引
            index_article(
                article_id=article.id,
                title=article.title,
                content=article.content or "",
                summary=article.summary or "",
                category=article.category.category_name if article.category else "",
                tags=article.tags or "",
                published_at=article.published_at.isoformat() if article.published_at else "",
                read_count=article.read_count or 0,
            )
    except Exception:
        pass  # RAG 未就绪时不影响正常流程

def _article_to_dict(article, user_id=None) -> dict:
    """将文章模型转换为字典，可选附带当前用户的收藏状态"""
    is_fav = False
    if user_id:
        fav = article._sa_instance_state.session.query(UserFavorite).filter(
            UserFavorite.user_id == user_id,
            UserFavorite.article_id == article.id,
        ).first()
        is_fav = fav is not None
    return {
        "id": article.id,
        "categoryId": article.category_id,
        "categoryName": article.category.category_name if article.category else None,
        "title": article.title,
        "summary": article.summary,
        "coverImage": article.cover_image,
        "tags": article.tags,
        "authorName": article.author.nickname if article.author else "系统管理员",
        "readCount": article.read_count or 0,
        "status": article.status,
        "publishedAt": article.published_at.isoformat() if article.published_at else None,
        "createdAt": article.created_at.isoformat() if article.created_at else None,
        "favoriteCount": 0,
        "isFavorited": is_fav,
    }


def paginate(db: Session, keyword="", category_id=None, status=None,
             page=1, size=10, user_id=None, sort_field="publishedAt", sort_direction="DESC"):
    """分页查询文章列表，支持关键词、分类、状态筛选和多字段排序"""
    q = db.query(KnowledgeArticle)

    if status is not None and status != "":
        q = q.filter(KnowledgeArticle.status == int(status))

    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(or_(
            KnowledgeArticle.title.like(kw),
            KnowledgeArticle.summary.like(kw),
            KnowledgeArticle.tags.like(kw),
        ))

    if category_id:
        q = q.filter(KnowledgeArticle.category_id == int(category_id))

    # 排序
    sort_col = KnowledgeArticle.published_at
    if sort_field == "readCount":
        sort_col = KnowledgeArticle.read_count
    if sort_direction.upper() == "DESC":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    total = q.count()
    safe_size = max(1, size)  # 防止除零
    pages = max(1, (total + safe_size - 1) // safe_size)
    records = q.offset((page - 1) * safe_size).limit(safe_size).all()

    return {
        "records": [_article_to_dict(a, user_id) for a in records],
        "total": total,
        "size": safe_size,
        "current": page,
        "pages": pages,
    }

def get_detail(db: Session, article_id: str, user_id=None):
    """获取文章详情，包含正文内容"""
    a = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not a:
        return None
    d = _article_to_dict(a, user_id)
    d["content"] = a.content
    return d

def increment_read(db: Session, article_id: str):
    a = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if a:
        a.read_count = (a.read_count or 0) + 1
        db.commit()

def create_article(db: Session, data: dict, author_id: int):
    a = KnowledgeArticle(
        id=str(uuid.uuid4()), category_id=data.get("categoryId") or None,
        title=data["title"], summary=data.get("summary", ""), content=data.get("content", ""),
        tags=data.get("tags", ""), author_id=author_id, status=0,
        published_at=datetime.now(timezone.utc),
    )
    db.add(a)
    db.commit()
    return a.id

def update_article(db: Session, article_id: str, data: dict):
    a = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not a:
        return False
    for field in ["title", "summary", "content", "tags", "cover_image"]:
        if field in data:
            setattr(a, field, data[field])
    if "categoryId" in data:
        a.category_id = data["categoryId"] or None
    db.commit()
    # 重新索引（内容已变）
    _sync_rag(article_id, a)
    return True

def set_status(db: Session, article_id: str, status: int):
    a = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if a:
        a.status = status
        if status == 1 and not a.published_at:
            a.published_at = datetime.now(timezone.utc)
        db.commit()
        # 发布→索引，下架→删除
        if status == 1:
            _sync_rag(article_id, a)
        else:
            _sync_rag(article_id, None)
    return a is not None

def delete(db: Session, article_id: str):
    a = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if a:
        db.delete(a)
        db.commit()
        _sync_rag(article_id, None)
    return a is not None
