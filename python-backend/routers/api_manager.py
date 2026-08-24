"""API Key 管理 —— 读写 .env 文件"""
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user_id
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/admin/api-keys", tags=["API管理"])

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")

# 哪些 key 是 API 相关的（显示在管理面板）
API_KEYS = [
    {"key": "AI_API_KEY", "label": "DeepSeek API Key", "group": "AI"},
    {"key": "AI_BASE_URL", "label": "DeepSeek 接口地址", "group": "AI"},
    {"key": "AI_MODEL", "label": "DeepSeek 模型名", "group": "AI"},
    {"key": "BAIDU_API_KEY", "label": "百度千帆搜索 Key", "group": "搜索"},
    {"key": "SMTP_HOST", "label": "邮箱 SMTP 服务器", "group": "邮件"},
    {"key": "SMTP_PORT", "label": "邮箱 SMTP 端口", "group": "邮件"},
    {"key": "SMTP_USER", "label": "发件邮箱地址", "group": "邮件"},
    {"key": "SMTP_PASSWORD", "label": "邮箱授权码", "group": "邮件"},
    {"key": "SMTP_FROM_NAME", "label": "发件人名称", "group": "邮件"},
    {"key": "APP_ID", "label": "飞书 App ID", "group": "飞书"},
    {"key": "APP_SECRET", "label": "飞书 App Secret", "group": "飞书"},
]

# 敏感 key 值脱敏显示
SENSITIVE_KEYS = {"AI_API_KEY", "BAIDU_API_KEY", "SMTP_PASSWORD", "APP_SECRET", "JWT_SECRET"}


def _read_env() -> dict[str, str]:
    """读取 .env 为 dict"""
    result = {}
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip()
    return result


def _write_env(data: dict[str, str]):
    """将 dict 写回 .env（保留注释和空行）"""
    if not os.path.exists(_ENV_PATH):
        return
    with open(_ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k = stripped.split("=", 1)[0].strip()
        if k in data:
            lines[i] = f"{k}={data[k]}\n"
            updated.add(k)

    # 追加新 key
    for k, v in data.items():
        if k not in updated:
            lines.append(f"{k}={v}\n")

    with open(_ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


class ApiKeyUpdate(BaseModel):
    key: str
    value: str


@router.get("")
def list_keys(user_id: int = Depends(get_current_user_id)):
    """列出所有 API 相关配置"""
    env = _read_env()
    items = []
    for ak in API_KEYS:
        raw = env.get(ak["key"], "")
        display = "***" + raw[-4:] if raw and ak["key"] in SENSITIVE_KEYS else raw
        items.append({
            "key": ak["key"],
            "label": ak["label"],
            "group": ak["group"],
            "value": display,
            "is_sensitive": ak["key"] in SENSITIVE_KEYS,
        })
    return {"code": "200", "msg": "ok", "data": {"items": items}}


@router.put("")
def update_key(body: ApiKeyUpdate, user_id: int = Depends(get_current_user_id)):
    """更新单个配置项"""
    env = _read_env()
    env[body.key] = body.value
    _write_env(env)
    return {"code": "200", "msg": f"{body.key} 已更新（需重启后端生效）", "data": None}
