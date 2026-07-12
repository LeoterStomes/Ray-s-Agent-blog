"""文章路由 — 薄层，仅做参数校验和路由，业务逻辑委托给 article_service"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from auth import get_current_user_id
from services.article_service import (
    paginate, get_detail, increment_read,
    create_article, update_article, set_status, delete as delete_article,
)

router = APIRouter(prefix="/api/knowledge/article", tags=["文章"])


class ArticleBody(BaseModel):
    title: str = "未命名"
    summary: str = ""
    content: str = ""
    tags: str = ""
    categoryId: Optional[int] = None
    coverImage: Optional[str] = None


@router.get("/page")
def article_page(
    keyword: Optional[str] = None,
    categoryId: Optional[int] = None,
    status: Optional[str] = None,
    sortField: str = "publishedAt",
    sortDirection: str = "DESC",
    currentPage: int = Query(1, alias="currentPage"),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    """分页查询文章列表"""
    result = paginate(
        db,
        keyword=keyword or "",
        category_id=categoryId,
        status=status,
        page=currentPage,
        size=size,
        sort_field=sortField,
        sort_direction=sortDirection,
    )
    return {"code": "200", "msg": "操作成功", "data": result}


@router.get("/{article_id}")
def article_detail(article_id: str, db: Session = Depends(get_db)):
    """获取文章详情"""
    data = get_detail(db, article_id)
    if not data:
        return {"code": "404", "msg": "文章不存在", "data": None}
    return {"code": "200", "msg": "操作成功", "data": data}


@router.post("/{article_id}/read")
def article_read(article_id: str, db: Session = Depends(get_db)):
    """文章阅读计数 +1"""
    increment_read(db, article_id)
    data = get_detail(db, article_id)
    if not data:
        return {"code": "404", "msg": "文章不存在", "data": None}
    return {"code": "200", "msg": "操作成功", "data": data}


@router.post("")
def create(body: ArticleBody, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """创建新文章"""
    article_id = create_article(db, {
        "categoryId": body.categoryId,
        "title": body.title,
        "summary": body.summary,
        "content": body.content,
        "tags": body.tags,
    }, author_id=user_id)
    return {"code": "200", "msg": "创建成功", "data": {"id": article_id}}


@router.put("/{article_id}")
def update(article_id: str, body: ArticleBody, db: Session = Depends(get_db)):
    """更新文章"""
    ok = update_article(db, article_id, {
        "title": body.title,
        "summary": body.summary,
        "content": body.content,
        "tags": body.tags,
        "categoryId": body.categoryId,
    })
    if not ok:
        return {"code": "404", "msg": "文章不存在", "data": None}
    return {"code": "200", "msg": "更新成功", "data": None}


@router.delete("/{article_id}")
def delete(article_id: str, db: Session = Depends(get_db)):
    """删除文章"""
    ok = delete_article(db, article_id)
    return {"code": "200", "msg": "删除成功", "data": None}


@router.post("/{article_id}/publish")
def publish(article_id: str, db: Session = Depends(get_db)):
    """发布文章"""
    ok = set_status(db, article_id, status=1)
    if not ok:
        return {"code": "404", "msg": "文章不存在", "data": None}
    return {"code": "200", "msg": "发布成功", "data": None}


@router.post("/{article_id}/offline")
def offline(article_id: str, db: Session = Depends(get_db)):
    """下架文章"""
    ok = set_status(db, article_id, status=0)
    if not ok:
        return {"code": "404", "msg": "文章不存在", "data": None}
    return {"code": "200", "msg": "已下架", "data": None}
