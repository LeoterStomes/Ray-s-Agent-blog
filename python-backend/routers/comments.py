from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from auth import get_current_user_id
from services.comment_service import create_comment, paginate_comments, delete_comment

router = APIRouter(prefix="/api/comment", tags=["评论"])


class CommentCreateRequest(BaseModel):
    article_id: str
    content: str
    parent_id: Optional[int] = None


def get_optional_user_id(request: Request) -> int | None:
    """尝试获取当前用户 ID，未登录返回 None（不抛异常）"""
    try:
        return get_current_user_id(request)
    except Exception:
        return None


@router.get("/article/{article_id}")
def list_comments(
    article_id: str,
    page: int = Query(1),
    size: int = Query(20),
    db: Session = Depends(get_db),
):
    records, total = paginate_comments(db, article_id, page, size)
    return {
        "code": "200",
        "msg": "操作成功",
        "data": {
            "records": records,
            "total": total,
            "size": size,
            "current": page,
            "pages": max(1, -(-total // size)) if total > 0 else 0,
        },
    }


@router.post("")
def post_comment(
    body: CommentCreateRequest,
    user_id: int | None = Depends(get_optional_user_id),
    db: Session = Depends(get_db),
):
    """发表评论或回复（需登录）"""
    if user_id is None:
        return {"code": "401", "msg": "评论失败，请先登录", "data": None}
    try:
        comment = create_comment(db, user_id, body.article_id, body.content, body.parent_id)
        return {"code": "200", "msg": "评论成功", "data": comment}
    except ValueError as e:
        return {"code": "400", "msg": str(e), "data": None}


@router.delete("/{comment_id}")
def remove_comment(
    comment_id: int,
    user_id: int | None = Depends(get_optional_user_id),
    db: Session = Depends(get_db),
):
    """删除评论（本人或管理员）"""
    if user_id is None:
        return {"code": "401", "msg": "请先登录", "data": None}
    ok = delete_comment(db, user_id, comment_id)
    if ok:
        return {"code": "200", "msg": "删除成功", "data": None}
    return {"code": "403", "msg": "无权限或评论不存在", "data": None}
