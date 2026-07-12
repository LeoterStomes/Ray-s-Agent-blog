"""邮箱验证码接口 — 含频率限制，超限触发图形验证码"""
from fastapi import APIRouter, Request, Header
from typing import Optional
from pydantic import BaseModel
from email_store import can_send, record_attempt, store_code, verify_code
from email_utils import send_code
from captcha_store import verify as captcha_verify
from config import SMTP_ENABLED

router = APIRouter(prefix="/api/email", tags=["邮箱验证"])


class SendCodeBody(BaseModel):
    email: str


class VerifyCodeBody(BaseModel):
    email: str
    code: str


@router.post("/send-code")
def send_verification_code(
    req: SendCodeBody,
    request: Request,
    captcha_key: Optional[str] = Header(None, alias="X-Captcha-Key"),
    captcha_code: Optional[str] = Header(None, alias="X-Captcha-Code"),
):
    if not SMTP_ENABLED:
        return {"code": "503", "msg": "邮件服务未配置", "data": None}

    email = req.email.strip().lower()
    if not email or "@" not in email:
        return {"code": "400", "msg": "请输入有效的邮箱地址", "data": None}

    ip = request.client.host if request.client else "unknown"

    # 检查频率限制
    if not can_send(ip):
        # 需要图形验证码
        if not captcha_key or not captcha_code:
            return {
                "code": "429",
                "msg": "发送过于频繁，请输入图形验证码",
                "data": {"requireCaptcha": True},
            }
        if not captcha_verify(captcha_key, captcha_code):
            return {
                "code": "429",
                "msg": "图形验证码错误或已过期",
                "data": {"requireCaptcha": True},
            }

    # 生成验证码并发送
    code = store_code(email)
    send_code(email, code)
    record_attempt(ip)

    return {
        "code": "200",
        "msg": "验证码已发送",
        "data": {"requireCaptcha": False},
    }


@router.post("/verify-code")
def check_verification_code(body: VerifyCodeBody):
    email = body.email.strip().lower()
    if verify_code(email, body.code):
        return {"code": "200", "msg": "验证码正确", "data": True}
    return {"code": "400", "msg": "验证码错误或已过期", "data": False}
