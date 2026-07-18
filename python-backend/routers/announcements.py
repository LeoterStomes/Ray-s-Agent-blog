from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user_id
from services.announcement_service import get_list, get_all, create, update, delete
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/announcement", tags=["公告"])


class AnnouncementBody(BaseModel):
    content: str
    link: Optional[str] = ""
    sort_order: Optional[int] = 0


class AnnouncementUpdate(BaseModel):
    content: Optional[str] = None
    link: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[int] = None


@router.get("/list")
def list_announcements(db: Session = Depends(get_db)):
    return {"code": "200", "msg": "ok", "data": get_list(db)}


@router.get("/all")
def all_announcements(db: Session = Depends(get_db)):
    return {"code": "200", "msg": "ok", "data": get_all(db)}


@router.post("")
def create_announcement(body: AnnouncementBody, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    create(db, body.model_dump())
    return {"code": "200", "msg": "创建成功", "data": None}


@router.put("/{aid}")
def update_announcement(aid: int, body: AnnouncementUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    update(db, aid, {k: v for k, v in body.model_dump().items() if v is not None})
    return {"code": "200", "msg": "更新成功", "data": None}


@router.delete("/{aid}")
def delete_announcement(aid: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    delete(db, aid)
    return {"code": "200", "msg": "删除成功", "data": None}