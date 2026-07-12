"""邮箱验证码存储 + 发送频率限制"""
import time
import random
import threading

# { email: {"code": "123456", "expires_at": 1234567890} }
_codes: dict[str, dict] = {}
# { ip: [timestamp1, timestamp2, ...] }
_attempts: dict[str, list[float]] = {}
_lock = threading.Lock()
_CODE_TTL = 300      # 验证码 5 分钟有效
_RATE_WINDOW = 300   # 频率统计窗口 5 分钟
_RATE_LIMIT = 3      # 窗口内超过 3 次触发图形验证码


def generate_code() -> str:
    return "".join(random.choices("0123456789", k=6))


def can_send(ip: str) -> bool:
    """检查 IP 是否还能直接发送（未触发频率限制）"""
    with _lock:
        _cleanup_attempts()
        ts = _attempts.get(ip, [])
        return len(ts) < _RATE_LIMIT


def record_attempt(ip: str):
    """记录一次发送尝试"""
    with _lock:
        _cleanup_attempts()
        _attempts.setdefault(ip, []).append(time.time())


def store_code(email: str) -> str:
    """生成并存储验证码，返回 code"""
    code = generate_code()
    with _lock:
        _codes[email] = {"code": code, "expires_at": time.time() + _CODE_TTL}
        _cleanup_codes()
    return code


def verify_code(email: str, code: str) -> bool:
    """校验邮箱验证码，成功则删除"""
    with _lock:
        entry = _codes.pop(email, None)
        _cleanup_codes()
        if not entry:
            return False
        if time.time() > entry["expires_at"]:
            return False
        return entry["code"] == code.strip()


def _cleanup_codes():
    now = time.time()
    expired = [k for k, v in _codes.items() if v["expires_at"] < now]
    for k in expired:
        del _codes[k]


def _cleanup_attempts():
    now = time.time()
    for ip in list(_attempts.keys()):
        _attempts[ip] = [t for t in _attempts[ip] if now - t < _RATE_WINDOW]
        if not _attempts[ip]:
            del _attempts[ip]