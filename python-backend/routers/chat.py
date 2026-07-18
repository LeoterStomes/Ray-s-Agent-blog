import json
import asyncio
import copy
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from models import ConsultationSession, ConsultationMessage
from schemas import ChatSessionStartRequest
from auth import get_current_user_id, verify_token
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from services.agent_service import TOOLS_SCHEMA, execute_tool
from services.mcp_client import load_mcp_servers, get_mcp_tools, call_mcp_tool
from pathlib import Path

# ── 加载 MCP Server ──
_mcp_servers = load_mcp_servers()
_MCP_TOOLS = get_mcp_tools()
if _MCP_TOOLS:
    print(f"[MCP] Loaded {len(_MCP_TOOLS)} external tools from {len(_mcp_servers)} servers")
ALL_TOOLS = list(TOOLS_SCHEMA) + _MCP_TOOLS

router = APIRouter(prefix="/api/psychological-chat", tags=["AI聊天"])

# ── 加载 System Prompt ──
_PROMPT_FILE = Path(__file__).parent.parent / "system_prompt.md"

def _load_system_prompt() -> str:
    if _PROMPT_FILE.exists():
        return _PROMPT_FILE.read_text(encoding="utf-8")
    return "你是 Ray 个人博客的 AI 助手。"

# ── 加载 Skills ──
def _load_skills() -> str:
    skills_dir = Path(__file__).parent.parent / "skills"
    if not skills_dir.exists():
        return ""
    parts = []
    for f in sorted(skills_dir.glob("*.skill")):
        try:
            content = f.read_text(encoding="utf-8")
            name = f.stem.replace("-", " ").title()
            parts.append(f"## {name}\n{content}")
        except Exception:
            pass
    return "\n\n".join(parts) if parts else ""

SKILLS_TEXT = _load_skills()

SYSTEM_PROMPT = _load_system_prompt()
MAX_TOOL_ROUNDS = 20  # 兜底值，正常由 Prompt 引导模型自行决定停止时机

# 注入 Skills
if SKILLS_TEXT:
    SYSTEM_PROMPT += "\n\n## 可用专业技能 (Skills)\n"
    SYSTEM_PROMPT += "根据用户意图匹配对应 Skill，按 Skill 定义的 workflow 顺序调用工具：\n\n"
    SYSTEM_PROMPT += SKILLS_TEXT

# ── 权限控制 ──
WRITE_TOOLS = {"create_draft", "export_file"}  # 仅 admin(user_type=2) 可用的工具

def _filter_tools_for_user(db: Session, user_id: int) -> list[dict]:
    """根据用户角色过滤工具列表：admin 全部可用，普通用户移除写工具"""
    from models import User
    user = db.query(User).filter(User.id == user_id).first()
    is_admin = user and user.user_type == 2
    if is_admin:
        return TOOLS_SCHEMA  # admin 全部工具
    return [t for t in TOOLS_SCHEMA if t["function"]["name"] not in WRITE_TOOLS]

def _now():
    """返回当前本地时间（naive，MySQL 兼容）"""
    return datetime.now(timezone.utc).astimezone().replace(tzinfo=None)


@router.post("/session/start")
def start_session(
    req: ChatSessionStartRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    title = req.sessionTitle or req.initialMessage or "新对话"
    title = title[:30]

    session = ConsultationSession(
        user_id=user_id,
        session_title=title,
        started_at=_now(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    if req.initialMessage:
        msg = ConsultationMessage(
            session_id=session.id,
            sender_type=1,
            content=req.initialMessage,
            created_at=_now(),
        )
        db.add(msg)
        db.commit()

    return {"code": "200", "msg": "操作成功", "data": {"id": str(session.id)}}


# ── 会话历史 ──

@router.get("/session/list")
def list_sessions(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出当前用户的所有会话"""
    sessions = (
        db.query(ConsultationSession)
        .filter(ConsultationSession.user_id == user_id)
        .order_by(ConsultationSession.started_at.desc())
        .limit(50)
        .all()
    )
    result = []
    for s in sessions:
        # 取第一条用户消息作为预览
        first_msg = (
            db.query(ConsultationMessage)
            .filter(ConsultationMessage.session_id == s.id, ConsultationMessage.sender_type == 1)
            .order_by(ConsultationMessage.created_at.asc())
            .first()
        )
        result.append({
            "id": str(s.id),
            "title": s.session_title or "新对话",
            "preview": (first_msg.content[:60] if first_msg else ""),
            "startedAt": s.started_at.isoformat() if s.started_at else "",
        })
    return {"code": "200", "msg": "ok", "data": result}


@router.get("/session/{session_id}/messages")
def get_session_messages(
    session_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """加载某个会话的所有消息（用于恢复历史）"""
    try:
        sid_int = int(session_id)
    except (ValueError, TypeError):
        return {"code": "400", "msg": "会话ID格式错误", "data": None}

    # 验证会话属于当前用户
    session = db.query(ConsultationSession).filter(
        ConsultationSession.id == sid_int,
        ConsultationSession.user_id == user_id,
    ).first()
    if not session:
        return {"code": "404", "msg": "会话不存在", "data": None}

    messages = (
        db.query(ConsultationMessage)
        .filter(ConsultationMessage.session_id == sid_int)
        .order_by(ConsultationMessage.created_at.asc())
        .all()
    )
    result = []
    for m in messages:
        result.append({
            "role": "user" if m.sender_type == 1 else "assistant",
            "content": m.content,
            "createdAt": m.created_at.isoformat() if m.created_at else "",
        })
    return {"code": "200", "msg": "ok", "data": result}


@router.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """删除指定会话及其所有消息"""
    try:
        sid_int = int(session_id)
    except (ValueError, TypeError):
        return {"code": "400", "msg": "会话ID格式错误", "data": None}

    session = db.query(ConsultationSession).filter(
        ConsultationSession.id == sid_int,
        ConsultationSession.user_id == user_id,
    ).first()
    if not session:
        return {"code": "404", "msg": "会话不存在", "data": None}

    # 删除所有消息
    db.query(ConsultationMessage).filter(
        ConsultationMessage.session_id == sid_int
    ).delete()
    # 删除会话
    db.delete(session)
    db.commit()

    return {"code": "200", "msg": "已删除", "data": None}


@router.post("/stream")
async def stream_chat(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    try:
        body = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Windows 终端/curl 可能发送 GBK 编码的中文，尝试回退解码
        try:
            body = json.loads(raw_body.decode("gbk", errors="replace"))
        except Exception:
            body = json.loads(raw_body.decode("latin-1", errors="replace"))
    session_id = body.get("sessionId", "")
    user_message = body.get("userMessage", "")

    if not session_id or not user_message:
        return {"code": "400", "msg": "参数缺失", "data": None}

    # 校验 session_id 类型
    try:
        sid_int = int(session_id)
    except (ValueError, TypeError):
        return {"code": "400", "msg": "会话ID格式错误", "data": None}

    session = db.query(ConsultationSession).filter(
        ConsultationSession.id == sid_int,
        ConsultationSession.user_id == user_id,
    ).first()
    if not session:
        return {"code": "404", "msg": "会话不存在", "data": None}

    # Save user message
    user_msg = ConsultationMessage(
        session_id=sid_int,
        sender_type=1,
        content=user_message,
        created_at=_now(),
    )
    db.add(user_msg)
    db.commit()

    # Load history — 滑动窗口：最近5条原文 + 之前压缩为摘要
    all_history = (
        db.query(ConsultationMessage)
        .filter(ConsultationMessage.session_id == sid_int)
        .order_by(ConsultationMessage.created_at.desc())
        .all()
    )[::-1]

    from models import User
    current_user = db.query(User).filter(User.id == user_id).first()
    user_ctx = ""
    if current_user:
        if current_user.user_type == 2:
            user_ctx = (
                f"\n## 当前用户（博主/管理员）\n"
                f"用户名: {current_user.username}，昵称: {current_user.nickname or '未设置'}。\n"
                f"这是博客的站长，最高权限。像私人助理对老板：用\"您\"，专业高效，\n"
                f"主动汇报站点情况、提出运营建议、快速执行指令。"
            )
        else:
            user_ctx = (
                f"\n## 当前用户（读者）\n"
                f"用户名: {current_user.username}，昵称: {current_user.nickname or '未设置'}。\n"
                f"像热情的导览员对访客：用\"你\"，亲切友好，\n"
                f"主动推荐好文章、耐心解答问题、引导探索博客。"
            )

    now_str = _now().strftime("%Y年%m月%d日 %H:%M (星期%w)").replace('星期0','周日').replace('星期1','周一').replace('星期2','周二').replace('星期3','周三').replace('星期4','周四').replace('星期5','周五').replace('星期6','周六')
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n当前时间：{now_str}" + user_ctx},
    ]

    KEEP_RECENT = 5
    if len(all_history) > KEEP_RECENT:
        older = all_history[:-KEEP_RECENT]
        recent = all_history[-KEEP_RECENT:]
        lines = ["[历史摘要，仅供参考，只回复最新消息]"]
        for m in older:
            role = "用户" if m.sender_type == 1 else "AI"
            preview = (m.content or "")[:80].replace("\n", " ")
            lines.append(f"{role}: {preview}")
        messages.append({"role": "system", "content": "\n".join(lines)})
        for msg in recent:
            role = "user" if msg.sender_type == 1 else "assistant"
            messages.append({"role": role, "content": msg.content})
    else:
        for msg in all_history:
            role = "user" if msg.sender_type == 1 else "assistant"
            messages.append({"role": role, "content": msg.content})

    async def event_generator():
        full_content = ""
        current_messages = messages
        tool_rounds = 0

        try:
            while tool_rounds < MAX_TOOL_ROUNDS:
                tool_rounds += 1
                accumulated_tool_calls: dict[int, dict] = {}  # index -> {name, args}
                has_content = False

                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=45.0)) as client:
                    request_json = {
                        "model": AI_MODEL,
                        "messages": current_messages,
                        "stream": True,
                    }
                    # 根据用户角色过滤工具
                    if tool_rounds <= MAX_TOOL_ROUNDS:
                        user_tools = _filter_tools_for_user(db, user_id)
                        request_json["tools"] = user_tools + _MCP_TOOLS
                        request_json["tool_choice"] = "auto"

                    async with client.stream(
                        "POST",
                        f"{AI_BASE_URL}/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {AI_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json=request_json,
                    ) as response:
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {})

                                # 处理文本内容
                                content = delta.get("content", "")
                                if content:
                                    has_content = True
                                    full_content += content
                                    yield f"event: message\ndata: {json.dumps({'text': content})}\n\n"
                                    await asyncio.sleep(0.01)

                                # 处理工具调用
                                tc_list = delta.get("tool_calls")
                                if tc_list:
                                    for tc in tc_list:
                                        idx = tc.get("index", 0)
                                        if idx not in accumulated_tool_calls:
                                            accumulated_tool_calls[idx] = {
                                                "id": tc.get("id", ""),
                                                "name": "",
                                                "args": "",
                                            }
                                        entry = accumulated_tool_calls[idx]
                                        if tc.get("id"):
                                            entry["id"] = tc["id"]
                                        if tc.get("function", {}).get("name"):
                                            entry["name"] = tc["function"]["name"]
                                        if tc.get("function", {}).get("arguments"):
                                            entry["args"] += tc["function"]["arguments"]
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue

                # 如果有工具调用，执行它们
                if accumulated_tool_calls:
                    # 构建 assistant 消息（含 tool_calls）
                    assistant_msg = {"role": "assistant", "content": full_content or None}
                    tc_formatted = []
                    for idx in sorted(accumulated_tool_calls.keys()):
                        tc = accumulated_tool_calls[idx]
                        try:
                            args_parsed = json.loads(tc["args"])
                        except json.JSONDecodeError:
                            args_parsed = {}
                        tc_formatted.append({
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": tc["args"]},
                        })
                        # 发送 tool_call 事件
                        yield f"event: tool_call\ndata: {json.dumps({'tool': tc['name'], 'args': args_parsed})}\n\n"
                        await asyncio.sleep(0.01)

                    if tc_formatted:
                        assistant_msg["tool_calls"] = tc_formatted

                    # 添加到消息历史
                    current_messages = copy.deepcopy(current_messages)
                    current_messages.append(assistant_msg)

                    # 执行工具并发送 tool_result
                    tool_names = {
                        'search_articles': '搜索博客文章', 'get_article': '读取文章全文',
                        'search_web': '联网搜索', 'get_categories': '查看分类',
                        'recommend_articles': '推荐文章', 'read_url': '读取网页',
                        'read_document': '读取文档', 'summarize_url': 'AI 摘要',
                        'summarize_text': 'AI 摘要', 'export_file': '导出文件',
                        'get_recent_articles': '获取最新文章', 'create_draft': '创建草稿',
                    }
                    for idx in sorted(accumulated_tool_calls.keys()):
                        tc = accumulated_tool_calls[idx]
                        try:
                            args_parsed = json.loads(tc["args"])
                        except json.JSONDecodeError:
                            args_parsed = {}
                        # MCP 工具分发
                        if tc["name"].startswith("mcp_"):
                            result = await call_mcp_tool(tc["name"], args_parsed) or json.dumps({"error": "MCP 工具未找到"}, ensure_ascii=False)
                        else:
                            try:
                                result = await asyncio.wait_for(
                                    execute_tool(tc["name"], args_parsed, db),
                                    timeout=15.0
                                )
                            except asyncio.TimeoutError:
                                result = json.dumps({"error": "工具执行超时"}, ensure_ascii=False)
                        yield f"event: tool_result\ndata: {json.dumps({'tool': tc['name'], 'result': json.loads(result) if result else {}})}\n\n"
                        await asyncio.sleep(0.01)

                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        })

                    # 继续循环让模型处理工具结果
                    continue

                # 没有工具调用，结束循环
                break

            # 如果没有文本输出（一直调工具），强制做最后一轮总结
            if not full_content and current_messages:
                summary_msg = [{"role": "system", "content": "结合以上工具执行结果，用简体中文给出简洁的最终回答。不要调用任何工具。"}]
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=25.0)) as client:
                        async with client.stream(
                            "POST", f"{AI_BASE_URL}/v1/chat/completions",
                            headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
                            json={"model": AI_MODEL, "messages": current_messages + summary_msg, "stream": True},
                        ) as response:
                            async for line in response.aiter_lines():
                                if not line.startswith("data: "): continue
                                data_str = line[6:]
                                if data_str == "[DONE]": break
                                try:
                                    chunk = json.loads(data_str)
                                    text = chunk["choices"][0].get("delta", {}).get("content", "")
                                    if text:
                                        full_content += text
                                        yield f"event: message\ndata: {json.dumps({'text': text})}\n\n"
                                        await asyncio.sleep(0.01)
                                except: pass
                except: pass

            # 保存完整回复
            if full_content:
                save_db = SessionLocal()
                try:
                    ai_msg = ConsultationMessage(
                        session_id=sid_int,
                        sender_type=2,
                        content=full_content,
                        ai_model=AI_MODEL,
                        created_at=_now(),
                    )
                    save_db.add(ai_msg)
                    save_db.commit()
                finally:
                    save_db.close()

            yield "event: done\ndata: {}\n\n"

        except httpx.HTTPError:
            yield f"event: error\ndata: {json.dumps({'message': 'AI 服务连接异常，请稍后重试'})}\n\n"
        except Exception:
            yield f"event: error\ndata: {json.dumps({'message': '服务暂时不可用，请稍后重试'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Export endpoints ──

# 一次性下载令牌（避免 JWT 走 URL）
_download_tokens: dict[str, dict] = {}

@router.post("/export/token")
def create_export_token(
    sessionId: str,
    format: str = "txt",
    user_id: int = Depends(get_current_user_id),
):
    """生成一次性下载令牌（60秒有效，用完即删）"""
    import secrets, time
    dt = secrets.token_urlsafe(24)
    _download_tokens[dt] = {"sessionId": sessionId, "format": format, "expires": time.time() + 60}
    return {"code": "200", "msg": "ok", "data": {"downloadToken": dt}}


@router.get("/export")
def export_session(
    sessionId: str = Query(...),
    format: str = Query("txt"),
    dt: str = Query(""),
    db: Session = Depends(get_db),
):
    # 优先用一次性下载令牌，兼容旧 JWT 参数
    import time
    entry = _download_tokens.pop(dt, None) if dt else None
    if entry and time.time() < entry["expires"]:
        sessionId = entry.get("sessionId", sessionId)
        format = entry.get("format", format)
    elif dt:
        return {"code": "401", "msg": "下载链接已过期，请重新生成", "data": None}
    else:
        return {"code": "401", "msg": "请通过 Agent 页面重新导出", "data": None}

    # 校验 sessionId 类型
    try:
        sid_int = int(sessionId)
    except (ValueError, TypeError):
        return {"code": "400", "msg": "会话ID格式错误", "data": None}

    messages = (
        db.query(ConsultationMessage)
        .filter(ConsultationMessage.session_id == sid_int)
        .order_by(ConsultationMessage.created_at.asc())
        .all()
    )
    if not messages:
        return {"code": "404", "msg": "无消息记录", "data": None}

    # Build content
    lines = ["# 对话导出", f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    for msg in messages:
        role = "用户" if msg.sender_type == 1 else "AI"
        lines.append(f"## {role}")
        lines.append(msg.content)
        lines.append("")

    text = "\n".join(lines)

    if format == "txt":
        return Response(
            content=text,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=chat_export.txt"},
        )

    if format == "md":
        return Response(
            content=text,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=chat_export.md"},
        )

    if format == "html":
        html_lines = ["<!DOCTYPE html><html><head><meta charset='utf-8'><title>对话导出</title></head><body>"]
        for msg in messages:
            role = "用户" if msg.sender_type == 1 else "AI"
            html_lines.append(f"<h3>{role}</h3>")
            html_lines.append(f"<p>{msg.content.replace(chr(10), '<br>')}</p>")
        html_lines.append("</body></html>")
        return Response(
            content="\n".join(html_lines),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=chat_export.html"},
        )

    return {"code": "400", "msg": f"不支持的格式: {format}", "data": None}


# ── AI 文档生成 ──

@router.post("/generate-doc")
async def generate_doc(request: Request):
    body = await request.json()
    topic = body.get("topic", "")
    format_type = body.get("format", "txt")
    if not topic:
        return {"code": "400", "msg": "请提供主题", "data": None}

    sys_prompt = (
        "你是一个专业的内容整理助手。请根据用户提供的主题，整合、梳理并生成一份结构清晰的文档。\n"
        "输出要求：\n"
        "- 包含标题、小标题、分段内容\n"
        "- 语言简洁专业，适合阅读和存档\n"
        "- 用简体中文\n"
        "- 纯文本格式，不要用 markdown 符号"
    )
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"请帮我整理以下内容并生成文档：\n{topic}"},
    ]

    full_content = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{AI_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
                json={"model": AI_MODEL, "messages": messages, "stream": False},
            )
            data = resp.json()
            full_content = data["choices"][0]["message"]["content"]
    except Exception as e:
        return {"code": "500", "msg": f"生成失败: {str(e)}", "data": None}

    if format_type == "txt":
        return Response(content=full_content, media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=ai_doc.txt"})
    if format_type == "md":
        return Response(content=full_content, media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=ai_doc.md"})
    return {"code": "400", "msg": f"不支持的格式: {format_type}", "data": None}
