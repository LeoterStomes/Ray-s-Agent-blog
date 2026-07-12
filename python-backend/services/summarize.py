"""Summarize URLs/text using DeepSeek API — 替代 brew summarize"""
import re, json, httpx
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL


async def summarize_url(url: str, max_length: int = 500) -> str:
    """Fetch a URL, extract text, and return an AI-generated summary."""
    # 1. Fetch content
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                return f"无法访问该页面 (HTTP {r.status_code})"
            content_type = r.headers.get("content-type", "").lower()
            raw = r.text
    except Exception as e:
        return f"请求失败: {e}"

    # 2. Extract text
    text = _extract_text(raw, content_type, r.content)

    if not text or len(text) < 50:
        return "未能从页面提取到足够的文本内容"

    # 3. Truncate for API
    text = text[:4000]

    # 4. Call DeepSeek to summarize
    try:
        async with httpx.AsyncClient(timeout=30.0) as c:
            resp = await c.post(
                f"{AI_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": f"你是一个摘要助手。用简体中文将以下内容总结为{max_length}字以内的摘要。保留关键信息、数据和观点。直接输出摘要，不要前缀。"},
                        {"role": "user", "content": text},
                    ],
                    "max_tokens": max_length * 2,
                    "temperature": 0.3,
                },
            )
            data = resp.json()
            summary = data["choices"][0]["message"]["content"].strip()
            return summary
    except Exception as e:
        # Fallback: return extracted text
        return text[:max_length] + "..."


async def summarize_text(content: str, max_length: int = 300) -> str:
    """Summarize plain text using DeepSeek."""
    content = content[:4000]
    try:
        async with httpx.AsyncClient(timeout=30.0) as c:
            resp = await c.post(
                f"{AI_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": f"用简体中文总结为{max_length}字以内摘要，保留关键信息。直接输出摘要。"},
                        {"role": "user", "content": content},
                    ],
                    "max_tokens": max_length * 2,
                    "temperature": 0.3,
                },
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return content[:max_length] + "..."


def _extract_text(html: str, content_type: str, raw_bytes: bytes) -> str:
    """Extract readable text from HTML or plain content."""
    if "text/plain" in content_type:
        return raw_bytes.decode("utf-8", errors="ignore")

    # HTML extraction
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<nav[^>]*>.*?</nav>', '', text, flags=re.DOTALL)
    text = re.sub(r'<footer[^>]*>.*?</footer>', '', text, flags=re.DOTALL)
    text = re.sub(r'<header[^>]*>.*?</header>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
