import bcrypt
from sqlalchemy.orm import Session
from models import User
from schemas import UserLoginRequest, UserRegisterRequest, UserUpdateRequest, UserResponse
from auth import create_token

def authenticate(db: Session, req: UserLoginRequest):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not bcrypt.checkpw(req.password.encode(), user.password.encode()):
        return None, "用户名或密码错误"
    if user.status == 0:
        return None, "账号已被禁用"
    token = create_token(user.id)
    return {"token": token, "user": UserResponse.model_validate(user).model_dump(by_alias=True)}, None

def register(db: Session, req: UserRegisterRequest):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        return None, "用户名已存在"
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user = User(username=req.username, password=hashed, nickname=req.nickname, email=req.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user).model_dump(by_alias=True), None

def get_by_id(db: Session, uid: int):
    user = db.query(User).filter(User.id == uid).first()
    return UserResponse.model_validate(user).model_dump(by_alias=True) if user else None

def update_profile(db: Session, uid: int, req: UserUpdateRequest):
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        return None
    for field in ["nickname", "email", "phone", "bio"]:
        val = getattr(req, field, None)
        if val is not None:
            setattr(user, field, val)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user).model_dump(by_alias=True)

def change_password(db: Session, uid: int, new_pw: str):
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        return False
    user.password = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    db.commit()
    return True

def list_users(db: Session, username: str = "", size: int = 50):
    q = db.query(User)
    if username:
        q = q.filter(User.username.contains(username) | User.nickname.contains(username))
    users = q.order_by(User.id.desc()).limit(size).all()
    total = db.query(User).count()
    records = [UserResponse.model_validate(u).model_dump(by_alias=True) for u in users]
    return records, total

def set_status(db: Session, uid: int, status: int):
    user = db.query(User).filter(User.id == uid).first()
    if user:
        user.status = status
        db.commit()
    return user is not None
