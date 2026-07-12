from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas import UserLoginRequest, UserRegisterRequest, UserUpdateRequest, PasswordUpdateRequest
from auth import get_current_user_id
from services import user_service
from captcha_store import verify as captcha_verify

router = APIRouter(prefix="/api/user", tags=["用户"])

# 可通过环境变量关闭验证码
CAPTCHA_ENABLED = __import__("os").getenv("CAPTCHA_ENABLED", "true").lower() == "true"


@router.post("/login")
def login(
    req: UserLoginRequest,
    db: Session = Depends(get_db),
):
    result, error = user_service.authenticate(db, req)
    if error:
        return {"code": "500", "msg": error, "data": None}
    return {"code": "200", "msg": "登录成功", "data": result}


@router.post("/add")
def register(
    req: UserRegisterRequest,
    db: Session = Depends(get_db),
    email_code: Optional[str] = Header(None, alias="X-Email-Code"),
):
    # 注册需要邮箱验证码
    if req.email:
        from email_store import verify_code as email_verify
        if not email_code:
            return {"code": "400", "msg": "请输入邮箱验证码", "data": None}
        if not email_verify(req.email, email_code):
            return {"code": "400", "msg": "邮箱验证码错误或已过期", "data": None}

    result, error = user_service.register(db, req)
    if error: return {"code": "500", "msg": error, "data": None}
    return {"code": "200", "msg": "注册成功", "data": result}


@router.get("/current")
def current_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = user_service.get_by_id(db, user_id)
    return {"code": "200", "msg": "ok", "data": user}


@router.put("/profile")
def update_profile(req: UserUpdateRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = user_service.update_profile(db, user_id, req)
    return {"code": "200", "msg": "个人信息更新成功", "data": user}


@router.put("/password")
def change_password(req: PasswordUpdateRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if not user_service.change_password(db, user_id, req.password):
        return {"code": "500", "msg": "用户不存在", "data": None}
    return {"code": "200", "msg": "操作成功", "data": None}


@router.get("/forget")
def forget_password(email: str, newPassword: str, db: Session = Depends(get_db)):
    from models import User
    import bcrypt
    user = db.query(User).filter(User.email == email).first()
    if not user: return {"code": "500", "msg": "邮箱未注册", "data": None}
    user.password = bcrypt.hashpw(newPassword.encode(), bcrypt.gensalt()).decode()
    db.commit()
    return {"code": "200", "msg": "操作成功", "data": None}


@router.post("/logout")
def logout():
    return {"code": "200", "msg": "退出登录成功", "data": None}


@router.get("/page")
def list_users(username: str = "", size: int = 50, db: Session = Depends(get_db)):
    records, total = user_service.list_users(db, username, size)
    return {"code": "200", "msg": "ok", "data": {"records": records, "total": total}}


@router.put("/{user_id}/status")
def update_status(user_id: int, status: int, db: Session = Depends(get_db)):
    user_service.set_status(db, user_id, status)
    return {"code": "200", "msg": "操作成功", "data": None}