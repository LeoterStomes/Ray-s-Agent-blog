from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from services.music_service import get_list, upload_and_create, update, delete
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/music", tags=["音乐"])


class MusicUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    lyrics: Optional[str] = None
    sort_order: Optional[int] = None


@router.get("/list")
def list_music(db: Session = Depends(get_db)):
    return {"code": "200", "msg": "ok", "data": get_list(db)}


@router.post("/upload")
async def upload(file: UploadFile = File(...), title: str = Form(""), artist: str = Form("未知"),
                 lyrics: str = Form(""), db: Session = Depends(get_db)):
    content = await file.read()
    raw_name = file.filename or "未知"
    # Auto-parse Artist - Title
    detected_title = title or raw_name.rsplit(".", 1)[0]
    detected_artist = artist
    if not title and not artist and " - " in raw_name.rsplit(".", 1)[0]:
        parts = raw_name.rsplit(".", 1)[0].split(" - ", 1)
        detected_artist = parts[0].strip()
        detected_title = parts[1].strip()
    result = upload_and_create(db, content, raw_name, detected_title, detected_artist)
    return {"code": "200", "msg": "上传成功", "data": result}


@router.put("/{mid}")
def update_music(mid: int, body: MusicUpdate, db: Session = Depends(get_db)):
    update(db, mid, {k: v for k, v in body.model_dump().items() if v is not None})
    return {"code": "200", "msg": "更新成功", "data": None}


@router.delete("/{mid}")
def delete_music(mid: int, db: Session = Depends(get_db)):
    delete(db, mid)
    return {"code": "200", "msg": "删除成功", "data": None}