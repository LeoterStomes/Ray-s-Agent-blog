"""
应用配置模块
============
所有敏感配置均通过环境变量读取，不提供默认值以确保安全。
运行前请先复制 .env.example 为 .env 并填入真实值。
"""
import os
from pathlib import Path

# 自动加载同目录下的 .env 文件
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv 未安装时静默跳过，依赖系统环境变量

# ========================================
# 数据库配置 | Database Configuration
# ========================================
# 格式: mysql+pymysql://<用户名>:<密码>@<主机>:<端口>/<数据库名>?charset=utf8mb4
# 示例: mysql+pymysql://root:mypassword@localhost:3307/blog_db?charset=utf8mb4
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL 环境变量未设置，请参考 .env.example 配置")

# ========================================
# JWT 认证配置 | JWT Authentication
# ========================================
# JWT_SECRET: 用于签发和验证 JWT 的密钥，必须保密
#   生成方式: python -c "import secrets; print(secrets.token_urlsafe(32))"
# JWT_ALGORITHM: 签名算法，默认 HS256
# JWT_EXPIRATION_HOURS: Token 有效期（小时），默认 24 小时
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET 环境变量未设置，请参考 .env.example 配置")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# ========================================
# AI API 配置 | AI API Configuration
# ========================================
# AI_API_KEY: DeepSeek API 密钥，从 https://platform.deepseek.com/ 获取
# AI_BASE_URL: API 基础地址，默认 DeepSeek 官方地址
# AI_MODEL: 使用的模型名称，默认 deepseek-chat
AI_API_KEY = os.getenv("AI_API_KEY")
if not AI_API_KEY:
    raise RuntimeError("AI_API_KEY 环境变量未设置，请参考 .env.example 配置")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")

# ========================================
# RAG 嵌入模型配置 | Embedding Configuration
# ========================================
# EMBEDDING_PROVIDER: "local" 使用本地 BGE 模型（免费，需 sentence-transformers）
#                     "openai" 使用 OpenAI 兼容 API（需 EMBEDDING_API_KEY）
# EMBEDDING_MODEL: 本地默认 BAAI/bge-small-zh-v1.5（中文优化，~400MB）
#                  云默认 text-embedding-3-small
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

# ========================================
# 邮件 SMTP 配置 | Email SMTP Configuration
# ========================================
# SMTP 服务器地址和端口
#   QQ邮箱: smtp.qq.com:587
#   163邮箱: smtp.163.com:465
#   126邮箱: smtp.126.com:465
#   Gmail:  smtp.gmail.com:587
#   Outlook: smtp-mail.outlook.com:587
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")   # QQ邮箱需用授权码，非邮箱密码
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Ray的垃圾站")
SMTP_ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)