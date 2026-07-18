from pydantic import BaseModel, Field
from typing import Optional

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str   # 注册必须提供邮箱
    nickname: Optional[str] = None

class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class PasswordUpdateRequest(BaseModel):
    oldPassword: str = ""
    password: str = Field(alias="password")

class UserResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    userType: Optional[int] = Field(None, alias="user_type")
    status: Optional[int] = None
    class Config:
        from_attributes = True
        populate_by_name = True

class UserLoginResponse(BaseModel):
    token: str
    user: UserResponse
