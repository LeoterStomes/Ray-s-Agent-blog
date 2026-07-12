"""图形验证码接口"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from captcha_store import generate, verify
from captcha_utils import make_image

router = APIRouter(prefix="/api/captcha", tags=["验证码"])


@router.get("/generate")
def get_captcha():
    """生成验证码图片，返回 PNG 图片 + X-Captcha-Key 响应头"""
    key, code = generate()
    img_buf = make_image(code)
    return StreamingResponse(
        img_buf,
        media_type="image/png",
        headers={
            "X-Captcha-Key": key,
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@router.get("/verify")
def check_captcha(key: str = Query(...), code: str = Query(...)):
    """校验验证码（调试用，生产由 login 接口内部调用）"""
    ok = verify(key, code)
    if ok:
        return {"code": "200", "msg": "验证码正确", "data": True}
    return {"code": "400", "msg": "验证码错误或已过期", "data": False}