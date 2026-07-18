"""RAG 知识库管理 API"""
import os, uuid
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from auth import get_current_user_id
from services.rag_service import index_document, delete_document, list_documents, reindex_all

router = APIRouter(prefix="/api/rag", tags=["RAG知识库"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "rag")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/import/upload")
async def import_upload(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    """上传外部文档并索引到向量库（需登录）"""
    safe_name = file.filename or "document"
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in (".pdf", ".docx", ".txt", ".md"):
        return {"code": "400", "msg": "仅支持 PDF/DOCX/TXT/MD 格式", "data": None}

    filename = f"{uuid.uuid4().hex}_{safe_name}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    n = index_document(filepath, safe_name)
    return {"code": "200", "msg": f"导入成功，{n} 个块已索引", "data": {"filename": safe_name, "chunks": n}}


@router.get("/documents")
def list_imported_docs(user_id: int = Depends(get_current_user_id)):
    """列出已导入的外部文档"""
    docs = list_documents()
    return {"code": "200", "msg": "操作成功", "data": docs}


@router.delete("/documents/{filename}")
def remove_document(
    filename: str,
    user_id: int = Depends(get_current_user_id),
):
    """删除外部文档及其向量"""
    # URL decode
    from urllib.parse import unquote
    filename = unquote(filename)
    # 同时删除文件
    for f in os.listdir(UPLOAD_DIR):
        if f.endswith(filename):
            try:
                os.remove(os.path.join(UPLOAD_DIR, f))
            except Exception:
                pass
    delete_document(filename)
    return {"code": "200", "msg": "删除成功", "data": None}


@router.post("/reindex")
def reindex(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """全量重建博客文章索引"""
    count = reindex_all(db)
    return {"code": "200", "msg": f"重建完成，{count} 个块已索引", "data": {"chunks": count}}