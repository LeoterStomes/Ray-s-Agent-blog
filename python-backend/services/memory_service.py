"""跨会话记忆系统 — 基于 Mem0，自动提取/去重/合并事实"""
import os
os.environ["MEM0_TELEMETRY"] = "false"  # 关闭遥测
from mem0 import Memory
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL, EMBEDDING_MODEL

# ChromaDB 持久化目录
_CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# Mem0 配置
_memory_client = None


def _get_memory() -> Memory:
    global _memory_client
    if _memory_client is not None:
        return _memory_client

    config = {
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "mem0_core",
                "path": _CHROMA_DIR,
            },
        },
        "llm": {
            "provider": "openai",
            "config": {
                "api_key": AI_API_KEY,
                "model": AI_MODEL,
                "openai_base_url": f"{AI_BASE_URL}/v1",
                "temperature": 0.1,
                "max_tokens": 500,
            },
        },
        "embedder": {
            "provider": "huggingface",
            "config": {
                "model": EMBEDDING_MODEL or "BAAI/bge-small-zh-v1.5",
            },
        },
        "history_db_path": os.path.join(_CHROMA_DIR, "mem0_history.db"),
    }

    _memory_client = Memory.from_config(config)
    print("[Mem0] 记忆系统已初始化")
    return _memory_client


def add_memory(text: str, user_id: int):
    """添加对话消息到记忆（Mem0 自动提取事实、去重、合并）"""
    try:
        m = _get_memory()
        m.add(text, user_id=str(user_id))
    except Exception as e:
        print(f"[Mem0] add error: {e}")


def search_memories(user_id: int, query: str, limit: int = 5) -> list[str]:
    """搜索用户记忆，返回相关事实列表"""
    try:
        m = _get_memory()
        results = m.search(query, filters={"user_id": str(user_id)}, limit=limit)
        items = results.get("results", []) if isinstance(results, dict) else results
        memories = []
        for r in items:
            mem = r.get("memory", "") if isinstance(r, dict) else str(r)
            if mem and mem.strip():
                memories.append(mem.strip())
        return memories
    except Exception as e:
        print(f"[Mem0] search error: {e}")
        return []


def get_all_memories(user_id: int) -> list[dict]:
    """获取用户所有记忆"""
    try:
        m = _get_memory()
        return m.get_all(user_id=str(user_id))
    except Exception:
        return []


def delete_all(user_id: int):
    """删除用户所有记忆"""
    try:
        m = _get_memory()
        m.delete_all(user_id=str(user_id))
    except Exception:
        pass
