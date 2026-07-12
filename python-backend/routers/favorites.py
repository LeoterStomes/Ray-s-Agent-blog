from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user_id
from services.favorite_service import paginate, toggle, is_favorited

router = APIRouter(prefix="/api/knowledge/favorite", tags=["收藏"])


@router.get("/page")
def list_favorites(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db),
                   currentPage: int = Query(1), size: int = Query(50)):
    records, total = paginate(db, user_id, currentPage, size)
    return {"code": "200", "msg": "操作成功", "data": {"records": records, "total": total, "size": size, "current": currentPage, "pages": max(1, -(-total // size))}}


@router.post("/{article_id}")
def add_favorite(article_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    result = toggle(db, user_id, article_id)
    return {"code": "200", "msg": "收藏成功" if result == "added" else "已取消收藏", "data": None}


@router.delete("/{article_id}")
def remove_favorite(article_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    toggle(db, user_id, article_id)
    return {"code": "200", "msg": "已取消收藏", "data": None}


@router.get("/{article_id}/status")
def check_favorite(article_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    fav = is_favorited(db, user_id, article_id)
    return {"code": "200", "msg": "ok", "data": {"isFavorited": fav}}