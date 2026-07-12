import httpx
from sqlalchemy.orm import Session
from models import Project


def paginate(db: Session, keyword=""):
    q = db.query(Project).filter(Project.status == 1)
    if keyword:
        q = q.filter(Project.name.contains(keyword) | Project.description.contains(keyword) | Project.tags.contains(keyword))
    items = q.order_by(Project.sort_order.asc(), Project.id.desc()).all()
    return [{"id": p.id, "name": p.name, "description": p.description, "tags": p.tags, "github_url": p.github_url, "cover": p.cover, "sort_order": p.sort_order, "status": p.status} for p in items]


def get_all(db: Session):
    return paginate(db)


def create(db: Session, data: dict):
    p = Project(name=data.get("name") or "未命名", description=data.get("description", ""), tags=data.get("tags", ""), github_url=data.get("github_url", ""), cover=data.get("cover", ""))
    db.add(p)
    db.commit()
    db.refresh(p)
    return p.id


def update(db: Session, pid: int, data: dict):
    p = db.query(Project).filter(Project.id == pid).first()
    if not p:
        return False
    for f in ["name", "description", "tags", "github_url", "cover", "status", "sort_order"]:
        if f in data and data[f] is not None:
            setattr(p, f, data[f])
    db.commit()
    return True


def delete(db: Session, pid: int):
    p = db.query(Project).filter(Project.id == pid).first()
    if p:
        db.delete(p)
        db.commit()
    return p is not None


async def fetch_readme(url: str):
    clean = url.rstrip("/").replace("https://github.com/", "")
    parts = clean.split("/")
    if len(parts) < 2:
        return None
    user, repo = parts[0], parts[1]
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as c:
        r = await c.get(f"https://raw.githubusercontent.com/{user}/{repo}/main/README.md")
        if r.status_code != 200:
            r = await c.get(f"https://raw.githubusercontent.com/{user}/{repo}/master/README.md")
        if r.status_code != 200:
            return None
        text = r.text[:2000]
        lines = [l.strip() for l in text.split('\n') if l.strip() and not l.strip().startswith(('#', '![', '[', '<')) and len(l.strip()) > 15]
        summary = ' '.join(lines)[:400]
        return {"summary": summary, "name": f"{user}/{repo}"}