"""System Prompt 组装器

职责：
- 加载 prompts/*.md（frontmatter 驱动：always / triggers）
- 加载 skills/*.skill（解析 ## trigger 段，注册表化）
- 按需组装 system prompt：常驻 prompt + 触发命中的 prompt + 最多 MAX_SKILLS_PER_TURN 个 skill
- 触发匹配使用"当前消息 + 最近用户消息"合并文本；跟进消息无命中时由调用方继承上一轮匹配

设计原则：skill 不再全量注入，避免注意力稀释与指令冲突。
"""
import re
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_SKILLS_DIR = Path(__file__).parent.parent / "skills"

_prompt_registry: list[dict] = []   # {name, body, triggers, always}
_skill_registry: list[dict] = []    # {name, body, triggers}
_always_prompts: list[str] = []

MAX_SKILLS_PER_TURN = 2  # 每轮最多注入的 skill 数，防止工作流互相打架


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


def _parse_skill(text: str, stem: str) -> dict:
    """解析 .skill 文件：# 标题作为名称，## trigger 段作为触发词"""
    name = stem
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        name = m.group(1).strip()
    triggers: list[str] = []
    tm = re.search(r"^##\s*trigger\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if tm:
        triggers = [t.strip() for t in re.split(r"[、,，/\n]+", tm.group(1)) if t.strip()]
    return {"name": name, "body": text.strip(), "triggers": triggers}


def load_all():
    """启动时加载所有 prompts 与 skills（幂等）"""
    global _prompt_registry, _skill_registry, _always_prompts
    _prompt_registry, _skill_registry, _always_prompts = [], [], []

    if _PROMPTS_DIR.exists():
        for f in sorted(_PROMPTS_DIR.glob("*.md")):
            try:
                raw = f.read_text(encoding="utf-8")
                meta, body = _parse_frontmatter(raw)
                entry = {
                    "name": f.stem,
                    "body": body,
                    "triggers": meta.get("triggers", []),
                    "always": meta.get("always", False),
                }
                _prompt_registry.append(entry)
                if entry["always"]:
                    _always_prompts.append(body)
            except Exception:
                pass

    if _SKILLS_DIR.exists():
        for f in sorted(_SKILLS_DIR.glob("*.skill")):
            try:
                _skill_registry.append(_parse_skill(f.read_text(encoding="utf-8"), f.stem))
            except Exception:
                pass


def _trigger_score(triggers: list[str], text_lower: str) -> int:
    """命中触发词的总长度：更长=更具体=优先级更高"""
    return sum(len(t) for t in triggers if t and t.lower() in text_lower)


def build_system_prompt(match_text: str, inherited: dict | None = None) -> tuple[str, dict]:
    """组装 system prompt。

    match_text: 用于触发匹配的文本（当前消息 + 最近用户消息），调用方需已转小写
    inherited: 上一轮匹配结果 {"prompts": set, "skills": set}；本轮无命中时继承
    返回 (prompt_text, {"prompts": set, "skills": set})
    """
    matched_bodies = list(_always_prompts)
    matched_prompts: set[str] = set()
    matched_skills: list[tuple[int, str]] = []  # (score, name)

    # prompts：命中即注入（体量小，不设上限）
    for entry in _prompt_registry:
        if entry["always"]:
            continue
        for t in entry["triggers"]:
            if t and t.lower() in match_text:
                matched_bodies.append(entry["body"])
                matched_prompts.add(entry["name"])
                break

    # skills：按触发词特异度评分，只注入 top N
    for sk in _skill_registry:
        score = _trigger_score(sk["triggers"], match_text)
        if score > 0:
            matched_skills.append((score, sk["name"]))
    matched_skills.sort(key=lambda x: -x[0])
    selected_skills = matched_skills[:MAX_SKILLS_PER_TURN]

    # 跟进消息无命中 → 继承上一轮匹配（"继续"、"然后呢"等场景）
    if not matched_prompts and not selected_skills and inherited:
        prev_prompts = set(inherited.get("prompts", set()))
        prev_skills = set(inherited.get("skills", set()))
        for entry in _prompt_registry:
            if entry["name"] in prev_prompts and not entry["always"]:
                matched_bodies.append(entry["body"])
                matched_prompts.add(entry["name"])
        for sk in _skill_registry:
            if sk["name"] in prev_skills:
                selected_skills.append((0, sk["name"]))

    skill_names = {name for _, name in selected_skills}
    if skill_names:
        parts = [sk["body"] for sk in _skill_registry if sk["name"] in skill_names]
        matched_bodies.append(
            "## 当前任务适用技能\n按匹配到的 Skill workflow 顺序调用工具：\n\n" + "\n\n".join(parts)
        )

    return "\n\n".join(matched_bodies), {"prompts": matched_prompts, "skills": skill_names}


# 启动时加载
load_all()
print(f"[Prompt] 加载 {len(_prompt_registry)} 个 prompt ({len(_always_prompts)} 常驻) + {len(_skill_registry)} 个 skill（按需注入）")
