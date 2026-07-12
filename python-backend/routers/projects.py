from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.project_service import paginate, get_all, create, update, delete, fetch_readme
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/project", tags=["项目"])


class ProjectBody(BaseModel):
    name: str = ""
    description: Optional[str] = ""
    tags: Optional[str] = ""
    github_url: Optional[str] = ""
    cover: Optional[str] = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    github_url: Optional[str] = None
    cover: Optional[str] = None
    status: Optional[int] = None
    sort_order: Optional[int] = None


@router.get("/list")
def list_projects(keyword: str = "", db: Session = Depends(get_db)):
    return {"code": "200", "msg": "ok", "data": paginate(db, keyword)}


@router.get("/all")
def all_projects(db: Session = Depends(get_db)):
    return {"code": "200", "msg": "ok", "data": get_all(db)}


@router.get("/fetch-readme")
async def readme(url: str = Query(...)):
    result = await fetch_readme(url)
    if not result:
        return {"code": "404", "msg": "无法获取 README", "data": None}
    return {"code": "200", "msg": "ok", "data": result}


@router.post("")
def create_project(body: ProjectBody, db: Session = Depends(get_db)):
    cid = create(db, body.model_dump())
    return {"code": "200", "msg": "创建成功", "data": {"id": cid}}


@router.put("/{pid}")
def update_project(pid: int, body: ProjectUpdate, db: Session = Depends(get_db)):
    update(db, pid, {k: v for k, v in body.model_dump().items() if v is not None})
    return {"code": "200", "msg": "更新成功", "data": None}


@router.delete("/{pid}")
def delete_project(pid: int, db: Session = Depends(get_db)):
    delete(db, pid)
    return {"code": "200", "msg": "删除成功", "data": None}