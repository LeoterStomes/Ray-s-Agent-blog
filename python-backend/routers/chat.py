import json
import re
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

# ── 预加载 RAG 嵌入模型，避免首次对话等待 ──
def _preload_embedding():
    try:
        from services.rag_service import _get_embedding_fn
        _get_embedding_fn()
    except Exception:
        pass
import threading
threading.Thread(target=_preload_embedding, daemon=True).start()
ALL_TOOLS = list(TOOLS_SCHEMA) + _MCP_TOOLS

router = APIRouter(prefix="/api/psychological-chat", tags=["AI聊天"])

# ── 加载 Prompts + Skills（元数据驱动）──
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_SKILLS_DIR = Path(__file__).parent.parent / "skills"

# 缓存：所有 prompt 文件的解析结果
_prompt_registry: list[dict] = []
_always_prompts: list[str] = []
_skill_text: str = ""


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 YAML 元数据头（--- ... ---），返回 (meta, body)"""
    meta, body = {}, text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            import yaml
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass
            body = parts[2].strip()
    return meta, body


def _load_prompts_and_skills():
    global _prompt_registry, _always_prompts, _skill_text

    # 加载 prompts/*.md
    if _PROMPTS_DIR.exists():
        for f in sorted(_PROMPTS_DIR.glob("*.md")):
            try:
                raw = f.read_text(encoding="utf-8")
                meta, body = _parse_frontmatter(raw)
                entry = {
                    "name": f.stem,
                    "meta": meta,
                    "body": body,
                    "triggers": meta.get("triggers", []),
                    "always": meta.get("always", False),
                }
                _prompt_registry.append(entry)
                if entry["always"]:
                    _always_prompts.append(body)
            except Exception:
                pass

    # 加载 skills/*.skill
    if _SKILLS_DIR.exists():
        parts = []
        for f in sorted(_SKILLS_DIR.glob("*.skill")):
            try:
                content = f.read_text(encoding="utf-8")
                name = f.stem.replace("-", " ").title()
                parts.append(f"## {name}\n{content}")
            except Exception:
                pass
        _skill_text = "\n\n".join(parts) if parts else ""


def _build_system_prompt(user_message: str) -> str:
    """根据用户消息动态组装 System Prompt"""
    msg_lower = user_message.lower()
    matched_bodies = list(_always_prompts)  # 始终加载的

    for entry in _prompt_registry:
        if entry["always"]:
            continue  # 已加载
        for t in entry["triggers"]:
            if t.lower() in msg_lower:
                matched_bodies.append(entry["body"])
                break

    prompt = "\n\n".join(matched_bodies)
    if _skill_text:
        prompt += "\n\n## 可用专业技能\n根据用户意图匹配对应 Skill，按 workflow 顺序调用工具：\n\n" + _skill_text
    return prompt


# 启动时加载
_load_prompts_and_skills()
print(f"[Prompt] 加载了 {len(_prompt_registry)} 个 prompt 文件 ({len(_always_prompts)} 常驻)")
MAX_TOOL_ROUNDS = 18  # 兜底值，配合连续 3 次失败断路器


async def _compress_and_store(session_id: int, user_id: int):
    """异步保存会话到 Mem0 记忆（自动提取事实/去重/合并）"""
    try:
        db = SessionLocal()
        msgs = db.query(ConsultationMessage).filter(
            ConsultationMessage.session_id == session_id
        ).order_by(ConsultationMessage.created_at.asc()).all()
        if len(msgs) < 3:
            return
        # 拼接最近 10 条消息，让 Mem0 自动提取事实
        lines = []
        for m in msgs[-10:]:
            role = "用户" if m.sender_type == 1 else "AI"
            lines.append(f"{role}: {m.content[:300]}")
        text = "\n".join(lines)
        from services.memory_service import add_memory
        add_memory(text, user_id)
    except Exception:
        pass
    finally:
        try:
            db.close()
        except Exception:
            pass


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
    db: Session = Depends(get_db), #利用fastapi 进行数据库连接的自动注入
):
    title = req.sessionTitle or req.initialMessage or "新对话"    #agent 对话的标题截取，没有标题自动用首条消息当标题
    title = title[:30]  #阶段限制，防止会话列表过大；限制30个字符

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

    # 只返回用户/AI 对话消息，工具执行记录（sender_type 3/4）不回放给前端
    messages = (
        db.query(ConsultationMessage)
        .filter(
            ConsultationMessage.session_id == sid_int,
            ConsultationMessage.sender_type.in_([1, 2]),
        )
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

    # 检索跨会话记忆
    memory_ctx = ""
    try:
        from services.memory_service import search_memories
        memories = search_memories(user_id, user_message, limit=3)
        if memories:
            memory_ctx = "\n## 历史记忆（来自你与用户之前的对话，可供参考）\n"
            memory_ctx += "以下是用户之前聊过的话题摘要，如果当前问题与之相关可以引用：\n"
            for i, m in enumerate(memories, 1):
                memory_ctx += f"{i}. {m}\n"
            memory_ctx += "注：这些是历史总结，仅供参考，不要逐条回复。\n"
    except Exception:
        pass

    messages = [
        {"role": "system", "content": _build_system_prompt(user_message) + f"\n当前时间：{now_str}" + user_ctx + memory_ctx},
    ]

    KEEP_RECENT = 5
    # 分离工具记录和对话消息
    user_ai_history = [m for m in all_history if m.sender_type in (1, 2)]
    tool_history = [m for m in all_history if m.sender_type in (3, 4)]  # 3=工具计数, 4=工具结果

    if len(user_ai_history) > KEEP_RECENT:
        older = user_ai_history[:-KEEP_RECENT]
        recent = user_ai_history[-KEEP_RECENT:]
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
        for msg in user_ai_history:
            role = "user" if msg.sender_type == 1 else "assistant"
            messages.append({"role": role, "content": msg.content})

    # 注入工具执行记录（包含搜索结果内容，让"继续"知道之前搜了什么）
    if tool_history:
        tool_ctx = "上一轮已经搜索到的信息（不要重复搜索，直接在此基础上继续）：\n" + "\n".join(m.content[:200] for m in tool_history[-8:])
        messages.insert(1, {"role": "system", "content": tool_ctx})

    async def event_generator():
        full_content = ""
        current_messages = messages
        tool_rounds = 0
        consecutive_failures = 0
        called_tools: set[str] = set()  # 去重：已调用的工具+参数
        tool_counts: dict[str, int] = {}  # 每类工具调用次数
        failed_urls: dict[str, str] = {}  # 本轮已读取失败的 URL → 错误摘要（跨工具防重试）
        URL_FETCH_TOOLS = {"read_url", "read_document", "summarize_url", "extract_images"}

        def _norm_url(u: str) -> str:
            return (u or "").rstrip("/").split("?")[0].split("#")[0][:200]
        had_any_tool_calls = False  # 本轮是否调用过任何工具
        round_tasks: list[asyncio.Task] = []  # 当前轮次的并行任务，新一轮开始前取消
        MAX_SEARCH_CALLS = 8   # 联网搜索上限
        MAX_READ_CALLS = 8     # 读网页上限
        MAX_TOTAL_TOOLS = 15   # 单轮总工具硬上限
        BATCH_TIMEOUT = 300.0   # 并行批次总超时（需容纳视频生成）

        try:
            while tool_rounds < MAX_TOOL_ROUNDS:
                tool_rounds += 1
                if consecutive_failures >= 6:
                    yield f"event: thinking\ndata: {json.dumps({'text': '多次执行出错，用已有信息整理回答'})}\n\n"
                    break
                # 状态心跳：让用户看到 Agent 正在做什么（而非长时间无反馈）
                if tool_rounds == 1:
                    yield f"event: thinking\ndata: {json.dumps({'text': '正在思考，规划下一步…'})}\n\n"
                else:
                    yield f"event: thinking\ndata: {json.dumps({'text': '已获取结果，正在整理…'})}\n\n"
                accumulated_tool_calls: dict[int, dict] = {}  # index -> {name, args}
                round_text = ""  # 本轮文本：有工具调用的轮次视为思考过程，不进最终回复

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
                        # 检查 HTTP 状态：模型服务异常时显式重试，不再静默吞掉
                        if response.status_code != 200:
                            consecutive_failures += 2
                            yield f"event: thinking\ndata: {json.dumps({'text': f'模型服务异常（HTTP {response.status_code}），正在重试…'})}\n\n"
                            continue
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {})

                                # 处理工具调用（先检测，因为有工具调用时内容要扣住）
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

                                # 处理文本内容
                                content = delta.get("content", "")
                                if content:
                                    # 过滤 DeepSeek 误输出的原始 XML 工具调用标签
                                    if '<' in content and ('name=' in content or 'string=' in content or '</' in content):
                                        content = re.sub(r'<[^>]*(?:name|string|invoke|parameter|tool_calls|function_calls|xml)[^>]*>[\s\S]*?</[^>]*>', '', content)
                                        content = re.sub(r'<[^>]*(?:tool_calls|invoke|parameter)[^>]*/?>', '', content)
                                        content = re.sub(r'</[^>]*>', '', content)
                                        content = content.strip()
                                    if content.strip():
                                        round_text += content
                                        # 工具调用过程中的文本发 thinking（折叠），不影响最终正文
                                        if accumulated_tool_calls:
                                            yield f"event: thinking\ndata: {json.dumps({'text': content})}\n\n"
                                        else:
                                            yield f"event: message\ndata: {json.dumps({'text': content})}\n\n"
                                        await asyncio.sleep(0.01)
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue

                # 如果有工具调用，执行它们
                if accumulated_tool_calls:
                    had_any_tool_calls = True
                    # 本轮文本属于思考过程，保留在对话历史中供模型参考，但不计入最终回复
                    # 构建 assistant 消息（含 tool_calls）
                    assistant_msg = {"role": "assistant", "content": round_text or None}
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
                        # tool_call 事件延迟到去重/限制检查之后再发，防止黄灯悬挂

                    if tc_formatted:
                        assistant_msg["tool_calls"] = tc_formatted

                    # 添加到消息历史
                    current_messages = copy.deepcopy(current_messages)
                    current_messages.append(assistant_msg)

                    # 执行工具（并行 + 去重 + 批次超时）
                    tool_names: dict[str, str] = {}
                    tasks_to_run: list[dict] = []

                    cap_reason = None  # 触发上限的原因；触发后剩余调用全部回填 skipped 响应，保证协议完整
                    for idx in sorted(accumulated_tool_calls.keys()):
                        tc = accumulated_tool_calls[idx]
                        try:
                            args_parsed = json.loads(tc["args"])
                        except json.JSONDecodeError:
                            args_parsed = {}

                        # 上限检查：不中断循环，确保每个 tool_call 最终都有对应 tool 响应
                        if cap_reason is None:
                            total_called = sum(tool_counts.values())
                            if total_called >= MAX_TOTAL_TOOLS:
                                cap_reason = "已达工具调用总上限"
                            elif tc["name"] == "search_web" and tool_counts.get(tc["name"], 0) >= MAX_SEARCH_CALLS:
                                cap_reason = "搜索次数已达上限"
                            elif tc["name"] in ("read_url", "extract_images") and tool_counts.get(tc["name"], 0) >= MAX_READ_CALLS:
                                cap_reason = "网页读取次数已达上限"
                            if cap_reason:
                                yield f"event: thinking\ndata: {json.dumps({'text': cap_reason + '，整理已有信息'})}\n\n"

                        if cap_reason is not None:
                            # 协议合规：被上限拦截的调用回填 tool 响应，避免悬空 tool_calls
                            current_messages.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": json.dumps({"skipped": True, "reason": cap_reason}, ensure_ascii=False),
                            })
                            continue

                        # 去重：同一工具+参数
                        # read_url 做 URL 规范化（去尾部斜杠和参数差异）
                        if tc["name"] in ("read_url", "extract_images") and "url" in args_parsed:
                            url = args_parsed["url"].rstrip("/").split("?")[0].split("#")[0]
                            dedup_key = f"{tc['name']}:{url[:120]}"
                        else:
                            dedup_key = f"{tc['name']}:{json.dumps(args_parsed, sort_keys=True, ensure_ascii=False)[:150]}"
                        if dedup_key in called_tools:
                            # 协议合规：重复调用回填 tool 响应，避免悬空 tool_calls
                            current_messages.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": json.dumps({"skipped": True, "reason": "重复调用，已忽略，请基于已有结果继续"}, ensure_ascii=False),
                            })
                            continue
                        # 跨工具失败记忆：同一链接已读取失败，禁止换工具重试
                        if tc["name"] in URL_FETCH_TOOLS and isinstance(args_parsed.get("url"), str):
                            nu = _norm_url(args_parsed["url"])
                            if nu in failed_urls:
                                current_messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc["id"],
                                    "content": json.dumps({"skipped": True, "reason": f"该链接刚刚读取失败（{failed_urls[nu]}），请勿更换工具重复尝试；请如实告知用户读取失败并给出替代方案（如请用户直接粘贴文字内容）"}, ensure_ascii=False),
                                })
                                continue
                        called_tools.add(dedup_key)
                        tool_counts[tc["name"]] = tool_counts.get(tc["name"], 0) + 1

                        # 发送 tool_call 事件
                        yield f"event: tool_call\ndata: {json.dumps({'tool': tc['name'], 'args': args_parsed})}\n\n"
                        tasks_to_run.append({"tc": tc, "args": args_parsed, "dedup_key": dedup_key})

                    if not tasks_to_run:
                        continue

                    # 取消上一轮仍未完成的任务
                    for old_task in round_tasks:
                        if not old_task.done():
                            old_task.cancel()
                    round_tasks.clear()

                    # 并行执行所有工具
                    async def _run_one(tc, args_parsed, dedup_key):
                        norm_url = _norm_url(args_parsed["url"]) if isinstance(args_parsed.get("url"), str) else None
                        if tc["name"].startswith("mcp_"):
                            result = await call_mcp_tool(tc["name"], args_parsed) or json.dumps({"error": "MCP 工具未找到"}, ensure_ascii=False)
                        else:
                            long_tools_set = {"generate_presentation", "generate_weekly_video", "search_web", "read_url", "read_document", "extract_images"}
                            t_timeout = 300.0 if tc["name"] == "generate_weekly_video" else (120.0 if tc["name"] == "generate_presentation" else (30.0 if tc["name"] in long_tools_set else 15.0))
                            # 每个工具调用使用独立 DB Session，避免并发共享请求级 Session
                            tool_db = SessionLocal()
                            task = asyncio.create_task(execute_tool(tc["name"], args_parsed, tool_db))
                            try:
                                result = await asyncio.wait_for(task, timeout=t_timeout)
                            except asyncio.TimeoutError:
                                task.cancel()
                                try:
                                    await task
                                except (asyncio.CancelledError, Exception):
                                    pass
                                result = json.dumps({"error": "工具执行超时"}, ensure_ascii=False)
                            finally:
                                tool_db.close()
                        return {"tc": tc, "result": result, "dedup_key": dedup_key, "url": norm_url}

                    round_tasks = [asyncio.create_task(_run_one(d["tc"], d["args"], d["dedup_key"])) for d in tasks_to_run]
                    try:
                        batch_results = await asyncio.wait_for(asyncio.gather(*round_tasks), timeout=BATCH_TIMEOUT)
                    except asyncio.TimeoutError:
                        # 超时：取消未完成的任务，用已完成的结果继续
                        for t in round_tasks:
                            if not t.done():
                                t.cancel()
                        batch_results = []
                        for t in round_tasks:
                            try:
                                if t.done():
                                    batch_results.append(t.result())
                            except Exception:
                                pass
                        yield f"event: thinking\ndata: {json.dumps({'text': '部分搜索超时，用已有结果整理回答'})}\n\n"

                    # 标记已完成工具的 ID
                    done_ids = set()

                    # 发送结果（成功完成的）
                    for br in (batch_results or []):
                        if br is None:
                            continue
                        tc = br["tc"]
                        result = br["result"]
                        done_ids.add(tc.get("id", ""))

                        # 跟踪连续失败
                        try:
                            r_parsed = json.loads(result) if result else {}
                            is_hard_error = "error" in r_parsed or "超时" in str(r_parsed)
                            if is_hard_error:
                                consecutive_failures += 1
                            else:
                                consecutive_failures = 0
                        except Exception:
                            pass

                        # 记录读取失败的 URL，防止模型换工具重试同一链接
                        if br.get("url"):
                            try:
                                rj = json.loads(result) if result else {}
                                err_txt = str(rj.get("error", "")) if isinstance(rj, dict) else ""
                                summ_txt = str(rj.get("summary", "")) if isinstance(rj, dict) else ""
                                if err_txt or "无法访问" in summ_txt or "请求失败" in summ_txt or "未能从页面" in summ_txt:
                                    failed_urls[br["url"]] = (err_txt or summ_txt)[:80]
                            except Exception:
                                pass

                        yield f"event: tool_result\ndata: {json.dumps({'tool': tc['name'], 'result': json.loads(result) if result else {}})}\n\n"
                        await asyncio.sleep(0.01)

                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        })

                        # 保存工具结果到 DB（让"继续"有上下文）
                        try:
                            r_preview = json.loads(result) if result else {}
                            summary = r_preview.get("results", "") or r_preview.get("content", "") or ""
                            if isinstance(summary, str) and len(summary) > 300:
                                summary = summary[:300] + "..."
                            tool_db = SessionLocal()
                            tm = ConsultationMessage(
                                session_id=sid_int, sender_type=4,
                                content=f"{tc['name']}: {summary}" if summary else tc['name'],
                                created_at=_now(),
                            )
                            tool_db.add(tm)
                            tool_db.commit()
                            tool_db.close()
                        except Exception:
                            pass

                    # 发送未完成工具的结果（被取消/超时/跳过）
                    for d in tasks_to_run:
                        tc = d["tc"]
                        if tc.get("id", "") in done_ids:
                            continue
                        yield f"event: tool_result\ndata: {json.dumps({'tool': tc['name'], 'result': {'cancelled': True, 'reason': '批次超时或新轮次取消'}})}\n\n"
                        await asyncio.sleep(0.01)
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps({"cancelled": True}),
                        })

                    # 继续循环让模型处理工具结果
                    continue

                # 没有工具调用，本轮文本就是最终回复，结束循环
                full_content += round_text
                break

            # 强制清理所有残留运行中的任务
            for t in round_tasks:
                if not t.done():
                    t.cancel()
            round_tasks.clear()

            # 有工具调用且没有文本输出 → 追加总结请求
            if had_any_tool_calls and not full_content:
                current_messages.append({"role": "user", "content": "请根据以上已经获取到的所有信息，用简体中文直接整理出最终回答。不要搜索、不要调用工具、不要描述你的执行过程，直接给用户有用的结论。"})
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, read=40.0)) as client:
                        async with client.stream(
                            "POST", f"{AI_BASE_URL}/v1/chat/completions",
                            headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
                            json={"model": AI_MODEL, "messages": current_messages, "stream": True, "tool_choice": "none"},
                        ) as response:
                            if response.status_code != 200:
                                raise httpx.HTTPError(f"force summary request failed: HTTP {response.status_code}")
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
                                except Exception:
                                    pass
                except Exception as e:
                    import traceback
                    print(f"[Agent] Force summary failed: {e}")
                    traceback.print_exc()
                    full_content = ""

            # 兜底：如果全程没产出任何内容，发一条提示
            if not full_content:
                full_content = "抱歉，处理你的请求时遇到了问题，请稍后重试。"
                yield f"event: message\ndata: {json.dumps({'text': full_content})}\n\n"

            # 保存工具执行记录（让后续"继续"知道之前做了什么）
            if had_any_tool_calls:
                save_db = SessionLocal()
                try:
                    tool_summary_parts = []
                    for tool_name, count in sorted(tool_counts.items()):
                        tool_summary_parts.append(f"{tool_name}: {count}次")
                    tool_summary = "已执行工具：" + "、".join(tool_summary_parts)
                    tool_msg = ConsultationMessage(
                        session_id=sid_int, sender_type=3,  # 3=工具记录
                        content=tool_summary, created_at=_now(),
                    )
                    save_db.add(tool_msg)
                    save_db.commit()
                finally:
                    save_db.close()

            # 保存前清理 XML 工具调用残留（不伤 HTML 标签）
            full_content = re.sub(r'<\s*(?:tool_calls|invoke|parameter|function_calls)\b[^>]*>[\s\S]*?</\s*(?:tool_calls|invoke|parameter|function_calls)\s*>', '', full_content or '')
            full_content = re.sub(r'<\s*(?:tool_calls|invoke|parameter|function_calls)\b[^>]*/?>', '', full_content)
            full_content = re.sub(r'<\s*/\s*(?:tool_calls|invoke|parameter|function_calls)\s*>', '', full_content)

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

                # 异步压缩会话记忆（fire-and-forget，不阻塞响应）
                try:
                    asyncio.create_task(_compress_and_store(sid_int, user_id))
                except Exception:
                    pass

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
