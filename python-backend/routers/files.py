import os
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import get_current_user_id

router = APIRouter(prefix="/api/file", tags=["文件"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
AVATAR_DIR = os.path.join(UPLOAD_DIR, "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_AGENT_FILE_SIZE = 20 * 1024 * 1024  # 20MB

@router.post("/simple/upload/image")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "avatar.jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"code": "400", "msg": "仅支持 jpg/png/gif/webp 格式", "data": None}

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(AVATAR_DIR, filename)

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        return {"code": "400", "msg": "文件不超过 5MB", "data": None}
    with open(filepath, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/avatars/{filename}"

    # Update user avatar
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.avatar = avatar_url
        db.commit()

    return {"code": "200", "msg": "上传成功", "data": {"url": avatar_url}}


AGENT_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "agent")
os.makedirs(AGENT_UPLOAD_DIR, exist_ok=True)

@router.post("/upload/agent")
async def upload_agent_file(file: UploadFile = File(...)):
    """Agent 文件上传 — 支持 PDF/DOCX/图片/文本等"""
    content = await file.read()
    if len(content) > MAX_AGENT_FILE_SIZE:
        return {"code": "400", "msg": "文件不超过 20MB", "data": None}
    ext = os.path.splitext(file.filename or "file")[1].lower()
    safe_name = file.filename or "file"
    filename = f"{uuid.uuid4().hex}_{safe_name}"
    filepath = os.path.join(AGENT_UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    url = f"/uploads/agent/{filename}"
    return {"code": "200", "msg": "上传成功", "data": {"url": url, "name": safe_name, "size": len(content)}}
