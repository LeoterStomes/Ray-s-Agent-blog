"""验证码存储 — 内存字典 + 过期时间，无需 Redis"""
import time
import uuid
import threading

# { key: {"code": "A3xK", "expires_at": 1234567890.0} }
_store: dict[str, dict] = {}
_lock = threading.Lock()
_TTL = 300  # 5 分钟


def generate() -> tuple[str, str]:
    """生成一个验证码，返回 (key, code_text)"""
    from captcha_utils import random_code

    key = uuid.uuid4().hex[:16]
    code = random_code()
    with _lock:
        _store[key] = {"code": code, "expires_at": time.time() + _TTL}
        _cleanup_expired()
    return key, code


def verify(key: str, code: str) -> bool:
    """校验验证码，无论成功与否都删除"""
    with _lock:
        entry = _store.pop(key, None)
        _cleanup_expired()
        if not entry:
            return False
        if time.time() > entry["expires_at"]:
            return False
        return entry["code"].upper() == code.upper().strip()


def _cleanup_expired():
    """清除过期的验证码"""
    now = time.time()
    expired = [k for k, v in _store.items() if v["expires_at"] < now]
    for k in expired:
        del _store[k]