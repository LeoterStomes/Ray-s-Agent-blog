from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.category_service import get_tree, get_all, create, update, delete
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/knowledge/category", tags=["分类"])


class CategoryBody(BaseModel):
    categoryName: str
    description: Optional[str] = ""
    sortOrder: Optional[int] = 0


@router.get("/tree")
def tree(db: Session = Depends(get_db)):
    return {"code": "200", "msg": "操作成功", "data": get_tree(db)}


@router.get("/all")
def all_categories(db: Session = Depends(get_db)):
    return {"code": "200", "msg": "ok", "data": get_all(db)}


@router.post("")
def create_category(body: CategoryBody, db: Session = Depends(get_db)):
    cid = create(db, body.model_dump())
    return {"code": "200", "msg": "创建成功", "data": {"id": cid}}


@router.put("/{cid}")
def update_category(cid: int, body: CategoryBody, db: Session = Depends(get_db)):
    update(db, cid, body.model_dump())
    return {"code": "200", "msg": "更新成功", "data": None}


@router.delete("/{cid}")
def delete_category(cid: int, db: Session = Depends(get_db)):
    delete(db, cid)
    return {"code": "200", "msg": "删除成功", "data": None}