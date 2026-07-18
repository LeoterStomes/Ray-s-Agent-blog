from sqlalchemy.orm import Session
from models import Comment, User


def _comment_to_dict(c: Comment) -> dict:
    return {
        "id": c.id,
        "articleId": c.article_id,
        "content": c.content,
        "parentId": c.parent_id,
        "createdAt": c.created_at.isoformat() if c.created_at else "",
        "updatedAt": c.updated_at.isoformat() if c.updated_at else "",
        "user": {
            "id": c.user.id,
            "nickname": c.user.nickname or c.user.username,
            "avatar": c.user.avatar or "",
        } if c.user else None,
        "replies": [],
    }


def create_comment(db: Session, user_id: int, article_id: str, content: str, parent_id: int = None) -> dict:
    """创建评论或回复。返回评论 dict（含 user）。"""
    if not content or not content.strip():
        raise ValueError("评论内容不能为空")
    if not article_id:
        raise ValueError("文章 ID 不能为空")

    # 如果是回复，验证父评论存在且属于同一文章
    if parent_id:
        parent = db.query(Comment).filter(Comment.id == parent_id).first()
        if not parent:
            raise ValueError("父评论不存在")
        if parent.article_id != article_id:
            raise ValueError("父评论不属于该文章")

    comment = Comment(
        user_id=user_id,
        article_id=article_id,
        content=content.strip(),
        parent_id=parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    # 重新查询以加载 relationship
    comment = db.query(Comment).filter(Comment.id == comment.id).first()
    return _comment_to_dict(comment)


def paginate_comments(db: Session, article_id: str, page: int = 1, size: int = 20) -> tuple:
    """分页获取文章评论。返回 (records, total)。"""
    if not article_id:
        return [], 0

    # 只查顶层评论
    q = db.query(Comment).filter(
        Comment.article_id == article_id,
        Comment.parent_id.is_(None),
    ).order_by(Comment.created_at.desc())

    total = q.count()
    top_comments = q.offset((page - 1) * size).limit(size).all()

    if not top_comments:
        return [], total

    # 批量查所有子回复
    parent_ids = [c.id for c in top_comments]
    replies = db.query(Comment).filter(
        Comment.parent_id.in_(parent_ids)
    ).order_by(Comment.created_at.asc()).all()

    # 按 parent_id 分组
    reply_map: dict = {}
    for r in replies:
        reply_map.setdefault(r.parent_id, []).append(_comment_to_dict(r))

    records = []
    for c in top_comments:
        d = _comment_to_dict(c)
        d["replies"] = reply_map.get(c.id, [])
        records.append(d)

    return records, total


def delete_comment(db: Session, user_id: int, comment_id: int) -> bool:
    """删除评论（本人或 admin）。返回 True=成功，False=无权限或不存在。"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return False

    # 权限检查：本人 或 admin (user_type=2)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    if comment.user_id != user_id and user.user_type != 2:
        return False

    # 级联删除子回复
    db.query(Comment).filter(Comment.parent_id == comment_id).delete()
    db.delete(comment)
    db.commit()
    return True


def count_comments(db: Session, article_id: str) -> int:
    """获取文章评论总数（含回复）"""
    return db.query(Comment).filter(Comment.article_id == article_id).count()
