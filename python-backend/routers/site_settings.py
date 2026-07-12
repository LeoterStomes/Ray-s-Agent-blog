"""站点设置接口 — 背景图上传 + 获取"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from auth import get_current_user_id

router = APIRouter(prefix="/api/site", tags=["站点设置"])

BG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "background")
os.makedirs(BG_DIR, exist_ok=True)


@router.get("/background")
def get_background():
    """返回当前背景图 URL，若无自定义则返回空"""
    # 找最新的背景文件
    if not os.path.exists(BG_DIR):
        return {"code": "200", "msg": "ok", "data": {"url": "", "hasCustom": False}}
    files = [f for f in os.listdir(BG_DIR) if not f.startswith('.')]
    if not files:
        return {"code": "200", "msg": "ok", "data": {"url": "", "hasCustom": False}}
    # 返回最新的文件
    files.sort(key=lambda f: os.path.getmtime(os.path.join(BG_DIR, f)), reverse=True)
    return {"code": "200", "msg": "ok", "data": {"url": f"/uploads/background/{files[0]}", "hasCustom": True}}


@router.post("/background/upload")
async def upload_background(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    """上传自定义背景图（仅登录用户）"""
    # 清理旧背景
    if os.path.exists(BG_DIR):
        for old in os.listdir(BG_DIR):
            try:
                os.remove(os.path.join(BG_DIR, old))
            except Exception:
                pass

    # 保存新文件
    ext = os.path.splitext(file.filename or "bg.jpg")[1] or ".jpg"
    if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    filename = f"custom-bg{ext}"
    filepath = os.path.join(BG_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return {"code": "200", "msg": "上传成功", "data": {"url": f"/uploads/background/{filename}"}}


@router.post("/background/reset")
def reset_background():
    """恢复默认背景（删除自定义背景图）"""
    if os.path.exists(BG_DIR):
        for old in os.listdir(BG_DIR):
            try:
                os.remove(os.path.join(BG_DIR, old))
            except Exception:
                pass
    return {"code": "200", "msg": "已恢复默认背景", "data": None}
