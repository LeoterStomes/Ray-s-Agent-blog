import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rate_limit import RateLimitMiddleware

from database import SessionLocal, engine, Base
from models import *  # noqa — 确保所有模型注册到 Base
Base.metadata.create_all(bind=engine)

from services.visitor_service import stats as visitor_stats_func, ping as visitor_ping_func
from routers import users, articles, categories, favorites, chat, files, announcements, music, projects, captcha, email, site_settings, comments, rag, api_manager

_ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:4321,http://localhost:3000,http://127.0.0.1:4321",
).split(",")

app = FastAPI(title="Ray的垃圾站 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(users.router)
app.include_router(articles.router)
app.include_router(categories.router)
app.include_router(favorites.router)
app.include_router(chat.router)
app.include_router(files.router)
app.include_router(announcements.router)
app.include_router(music.router)
app.include_router(projects.router)
app.include_router(captcha.router)
app.include_router(email.router)
app.include_router(site_settings.router)
app.include_router(comments.router)
app.include_router(rag.router)
app.include_router(api_manager.router)

uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/api/health")
def health():
    return {"code": "200", "msg": "ok", "data": None}


@app.get("/api/visitor/stats")
def visitor_stats():
    db = SessionLocal()
    try:
        return {"code": "200", "msg": "ok", "data": visitor_stats_func(db)}
    finally:
        db.close()


@app.post("/api/visitor/ping")
async def visitor_ping(request: Request):
    db = SessionLocal()
    try:
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")[:500]
        visitor_ping_func(db, ip, ua)
    finally:
        db.close()
    return {"code": "200", "msg": "ok", "data": None}
