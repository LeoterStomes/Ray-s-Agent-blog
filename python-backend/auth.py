import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> int:
    payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return int(payload["sub"])


def get_current_user_id(request: Request) -> int:
    token = request.headers.get("token") or request.headers.get("Token")
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        return verify_token(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token 已过期")
    except Exception:
        raise HTTPException(status_code=401, detail="token 无效")
