"""RAG 知识库核心服务
- ChromaDB 向量存储
- 文本嵌入 + 切片 + 索引 + 搜索 + 删除
- 支持博客文章 + 外部文档双源
"""
import os, re, json
from typing import Optional
from sqlalchemy.orm import Session

# ChromaDB 存储目录
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# 嵌入配置（通过 config.py 环境变量覆盖）
from config import EMBEDDING_PROVIDER, EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL

_client = None
_embed_fn = None


def _get_embedding_fn():
    """延迟加载嵌入函数，按配置选择后端"""
    global _embed_fn
    if _embed_fn is not None:
        return _embed_fn

    if EMBEDDING_PROVIDER == "local":
        # 本地 BGE 中文模型（优先用国内镜像）
        import os as _os
        if not _os.environ.get("HF_ENDPOINT"):
            _os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL or "BAAI/bge-small-zh-v1.5")
        _embed_fn = lambda texts: model.encode(list(texts), normalize_embeddings=True).tolist()
        print(f"[RAG] 本地嵌入模型已加载: {EMBEDDING_MODEL or 'BAAI/bge-small-zh-v1.5'}")
    else:
        # OpenAI 兼容 API（openai / 硅基流动 / 本地 Ollama 等）
        from openai import OpenAI
        client = OpenAI(api_key=EMBEDDING_API_KEY, base_url=EMBEDDING_BASE_URL)
        def _embed_openai(texts):
            resp = client.embeddings.create(model=EMBEDDING_MODEL or "text-embedding-3-small", input=list(texts))
            return [d.embedding for d in resp.data]
        _embed_fn = _embed_openai
        print(f"[RAG] 云嵌入 API 已配置: {EMBEDDING_BASE_URL} / {EMBEDDING_MODEL}")

    return _embed_fn


def _get_client():
    """延迟加载 ChromaDB 客户端"""
    global _client
    if _client is not None:
        return _client
    import chromadb
    os.makedirs(CHROMA_DIR, exist_ok=True)
    _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


# ── 文本切片 ──
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """中文文本切片：按段落优先，长段落按句子切"""
    if not text or not text.strip():
        return []
    # 先按段落
    paragraphs = re.split(r'\n{2,}', text.strip())
    chunks = []
    current = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current) + len(p) <= chunk_size:
            current = (current + "\n" + p).strip()
        else:
            if current:
                chunks.append(current)
            # 长段落按句子切
            if len(p) > chunk_size:
                sentences = re.split(r'(?<=[。！？!?])\s*', p)
                current = ""
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    if len(current) + len(s) <= chunk_size:
                        current = (current + s).strip()
                    else:
                        if current:
                            chunks.append(current)
                        current = s
                if current:
                    # not added yet, will be added after loop
                    pass
            else:
                current = p
    if current:
        chunks.append(current)
    # 带重叠
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            over = chunks[i-1][-overlap:] + chunks[i]
            overlapped.append(over)
        return overlapped
    return chunks


# ── HTML → 纯文本 ──
def _html_to_text(html: str) -> str:
    """复用 export_service 逻辑：HTML 标签 → 纯文本"""
    t = html or ""
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'</p>', '\n', t)
    t = re.sub(r'</h[1-6]>', '\n', t)
    t = re.sub(r'</li>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'&nbsp;', ' ', t)
    t = re.sub(r'&lt;', '<', t)
    t = re.sub(r'&gt;', '>', t)
    t = re.sub(r'&amp;', '&', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r' {2,}', ' ', t)
    return t.strip()


# ── 集合名 ──
ARTICLES_COLLECTION = "blog_articles"
DOCS_COLLECTION = "imported_docs"


def _ensure_collection(name: str):
    client = _get_client()
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name, metadata={"hnsw:space": "cosine"})


# ── 文章索引 ──
def index_article(article_id: str, title: str, content: str, summary: str = "",
                  category: str = "", tags: str = "", published_at: str = "", read_count: int = 0):
    """索引单篇文章到向量库（先删旧再写新）"""
    delete_article(article_id)

    # 拼接文本：标题 + 摘要 + 正文
    text = f"{title}\n{summary}\n{_html_to_text(content)}"
    chunks = chunk_text(text)
    if not chunks:
        return 0

    embed = _get_embedding_fn()
    vectors = embed(chunks)

    coll = _ensure_collection(ARTICLES_COLLECTION)
    ids = [f"{article_id}_chunk_{i}" for i in range(len(chunks))]
    metas = [{
        "article_id": article_id,
        "title": title,
        "category": category,
        "tags": tags,
        "published_at": published_at,
        "read_count": read_count,
        "chunk_index": i,
        "source_type": "article",
        "url": f"/blog/{article_id}",
    } for i in range(len(chunks))]

    coll.add(ids=ids, embeddings=vectors, documents=chunks, metadatas=metas)
    return len(chunks)


def delete_article(article_id: str):
    """从向量库删除文章的所有块"""
    try:
        coll = _ensure_collection(ARTICLES_COLLECTION)
        # 按 article_id 过滤删除
        results = coll.get(where={"article_id": article_id})
        if results and results["ids"]:
            coll.delete(ids=results["ids"])
    except Exception:
        pass


# ── 外部文档索引 ──
def index_document(filepath: str, filename: str) -> int:
    """索引外部文档（PDF/DOCX/TXT）到向量库"""
    ext = os.path.splitext(filename)[1].lower()
    text = ""
    try:
        if ext == ".pdf":
            from PyPDF2 import PdfReader
            import io
            with open(filepath, "rb") as f:
                pages = [p.extract_text() or "" for p in PdfReader(io.BytesIO(f.read())).pages[:20]]
            text = "\n".join(pages)
        elif ext == ".docx":
            from docx import Document
            import io
            with open(filepath, "rb") as f:
                text = "\n".join(p.text for p in Document(io.BytesIO(f.read())).paragraphs if p.text.strip())
        elif ext in (".txt", ".md", ".csv"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            return 0
    except Exception:
        return 0

    if not text.strip():
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0

    embed = _get_embedding_fn()
    vectors = embed(chunks)

    doc_id_base = filename.rsplit(".", 1)[0]
    coll = _ensure_collection(DOCS_COLLECTION)
    # 先清旧
    try:
        old = coll.get(where={"filename": filename})
        if old and old["ids"]:
            coll.delete(ids=old["ids"])
    except Exception:
        pass

    ids = [f"doc_{doc_id_base}_chunk_{i}" for i in range(len(chunks))]
    metas = [{
        "filename": filename,
        "chunk_index": i,
        "source_type": "uploaded_doc",
    } for i in range(len(chunks))]

    coll.add(ids=ids, embeddings=vectors, documents=chunks, metadatas=metas)
    return len(chunks)


def delete_document(filename: str):
    """删除外部文档的所有块"""
    try:
        coll = _ensure_collection(DOCS_COLLECTION)
        results = coll.get(where={"filename": filename})
        if results and results["ids"]:
            coll.delete(ids=results["ids"])
    except Exception:
        pass


# ── 搜索 ──
def search_articles(query: str, limit: int = 5) -> list[dict]:
    """语义搜索博客文章，返回 [{article_id, title, chunk_text, score, url, category, ...}]"""
    if not query or not query.strip():
        return []
    try:
        embed = _get_embedding_fn()
        qv = embed([query.strip()])[0]
        coll = _ensure_collection(ARTICLES_COLLECTION)
        results = coll.query(query_embeddings=[qv], n_results=min(limit, 20))
    except Exception:
        return []

    if not results or not results.get("ids") or not results["ids"][0]:
        return []

    out = []
    seen = set()
    for i, mid in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
        doc = results["documents"][0][i] if results.get("documents") else ""
        aid = meta.get("article_id", "")
        if aid in seen:
            continue
        seen.add(aid)
        out.append({
            "article_id": aid,
            "title": meta.get("title", ""),
            "category": meta.get("category", ""),
            "tags": meta.get("tags", ""),
            "chunk_text": doc[:300] if doc else "",
            "score": round(1 - results["distances"][0][i], 4) if results.get("distances") else 0,
            "url": meta.get("url", f"/blog/{aid}"),
            "published_at": meta.get("published_at", ""),
        })
        if len(out) >= limit:
            break
    return out


def search_documents(query: str, limit: int = 5) -> list[dict]:
    """语义搜索外部导入文档"""
    if not query or not query.strip():
        return []
    try:
        embed = _get_embedding_fn()
        qv = embed([query.strip()])[0]
        coll = _ensure_collection(DOCS_COLLECTION)
        results = coll.query(query_embeddings=[qv], n_results=min(limit, 20))
    except Exception:
        return []

    if not results or not results.get("ids") or not results["ids"][0]:
        return []

    out = []
    for i, mid in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
        doc = results["documents"][0][i] if results.get("documents") else ""
        out.append({
            "filename": meta.get("filename", ""),
            "chunk_text": doc[:300] if doc else "",
            "score": round(1 - results["distances"][0][i], 4) if results.get("distances") else 0,
        })
    return out


def search_all(query: str, limit: int = 5) -> list[dict]:
    """搜索全部知识库（文章 + 外部文档）"""
    articles = search_articles(query, limit)
    docs = search_documents(query, limit)
    return articles + docs


# ── 管理 ──
def reindex_all(db: Optional[Session] = None):
    """全量重建博客文章索引（需要传入 db session）"""
    if db is None:
        return 0
    from models import KnowledgeArticle
    articles = db.query(KnowledgeArticle).filter(KnowledgeArticle.status == 1).all()
    count = 0
    for a in articles:
        n = index_article(
            article_id=a.id,
            title=a.title,
            content=a.content or "",
            summary=a.summary or "",
            category=a.category.category_name if a.category else "",
            tags=a.tags or "",
            published_at=a.published_at.isoformat() if a.published_at else "",
            read_count=a.read_count or 0,
        )
        count += n
    print(f"[RAG] 全量重建完成：{len(articles)} 篇文章 → {count} 个块")
    return count


def list_documents() -> list[dict]:
    """列出所有已导入的外部文档"""
    try:
        coll = _ensure_collection(DOCS_COLLECTION)
        data = coll.get()
        if not data or not data.get("metadatas"):
            return []
        seen = {}
        for m in data["metadatas"]:
            fn = m.get("filename", "")
            if fn and fn not in seen:
                seen[fn] = {"filename": fn}
        return list(seen.values())
    except Exception:
        return []