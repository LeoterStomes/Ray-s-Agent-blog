"""简易内存速率限制中间件"""
import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# 配置：每个 IP 每窗口允许的请求数
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/user/login": (10, 60),       # 登录: 10次/分钟
    "/api/user/add": (3, 300),         # 注册: 3次/5分钟
    "/api/user/forget": (1, 60),       # 密码重置: 1次/分钟（已被移除，保留以防恢复）
    "/api/email/send-code": (3, 300),  # 发验证码: 3次/5分钟
}

_window: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/")
        limit = RATE_LIMITS.get(path)
        if not limit:
            return await call_next(request)

        max_req, window = limit
        ip = request.client.host if request.client else "unknown"
        key = f"{ip}:{path}"
        now = time.time()
        bucket = _window[key]

        # 清理过期记录
        _window[key] = [t for t in bucket if now - t < window]
        bucket = _window[key]

        if len(bucket) >= max_req:
            return JSONResponse(
                {"code": "429", "msg": "请求过于频繁，请稍后再试", "data": None},
                status_code=429,
            )

        bucket.append(now)
        return await call_next(request)
