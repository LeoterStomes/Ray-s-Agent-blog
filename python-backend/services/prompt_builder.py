"""System Prompt 组装器

职责：
- 加载 prompts/*.md（frontmatter 驱动：always / triggers）
- 加载 skills/*.skill（解析 ## trigger / ## description 段，注册表化）
- 组装 system prompt：常驻 prompt + 命中触发的 prompt + 技能目录（常驻）
- 技能不再关键字注入正文，改为「技能目录常驻 + agent 调用 use_skill 按需加载」

设计原则：技能全文不注入，避免注意力稀释与指令冲突；agent 依据目录自主判断后按需拉取。
"""
import re
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_SKILLS_DIR = Path(__file__).parent.parent / "skills"

_prompt_registry: list[dict] = []   # {name, body, triggers, always}
_skill_registry: list[dict] = []    # {name, stem, body, triggers, description}
_always_prompts: list[str] = []


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
    """解析 .skill 文件：# 标题作为名称，## trigger 段作为触发词，## description 段作为一句话说明"""
    name = stem
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        name = m.group(1).strip()
    triggers: list[str] = []
    tm = re.search(r"^##\s*trigger\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if tm:
        triggers = [t.strip() for t in re.split(r"[、,，/\n]+", tm.group(1)) if t.strip()]
    description = ""
    dm = re.search(r"^##\s*description\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if dm:
        description = dm.group(1).strip()
    return {"name": name, "stem": stem, "body": text.strip(), "triggers": triggers, "description": description}


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


def build_skill_index() -> str:
    """技能目录（紧凑）：常驻注入 system prompt，供 agent 判断后按需 use_skill 加载"""
    if not _skill_registry:
        return ""
    lines = [
        "## 可用技能目录",
        "下面是你可用的技能。先判断当前任务是否需要某个技能：需要时调用 `use_skill` 工具加载它的完整流程与规则（一次加载一个），不需要则忽略。",
        "",
    ]
    for sk in _skill_registry:
        desc = sk["description"] or "、".join(sk["triggers"][:5])
        lines.append(f"- **{sk['name']}**（`{sk['stem']}`）—— {desc}")
    return "\n".join(lines)


def get_skill_body(name: str) -> str | None:
    """按名称/文件名返回 skill 完整内容（供 use_skill 工具调用）"""
    if not name:
        return None
    key = name.strip().lower()
    for sk in _skill_registry:
        if key in (sk["name"].lower(), sk["stem"].lower()):
            return sk["body"]
    # 模糊匹配：名称或文件名包含关键词，且唯一时返回
    hits = [sk for sk in _skill_registry if key in sk["name"].lower() or key in sk["stem"].lower()]
    if len(hits) == 1:
        return hits[0]["body"]
    return None


def build_system_prompt(match_text: str, inherited: dict | None = None) -> tuple[str, dict]:
    """组装 system prompt。

    match_text: 用于 prompt 触发匹配的文本（当前消息 + 最近用户消息），调用方需已转小写
    inherited: 上一轮匹配结果 {"prompts": set}；本轮无命中时继承
    返回 (prompt_text, {"prompts": set, "skills": set})；skills 恒为空（技能改为 use_skill 按需加载）
    """
    matched_bodies = list(_always_prompts)
    matched_prompts: set[str] = set()

    # prompts：命中即注入（体量小，不设上限）
    for entry in _prompt_registry:
        if entry["always"]:
            continue
        for t in entry["triggers"]:
            if t and t.lower() in match_text:
                matched_bodies.append(entry["body"])
                matched_prompts.add(entry["name"])
                break

    # 跟进消息无命中 → 继承上一轮 prompt 匹配（"继续"、"然后呢"等场景）
    if not matched_prompts and inherited:
        prev_prompts = set(inherited.get("prompts", set()))
        for entry in _prompt_registry:
            if entry["name"] in prev_prompts and not entry["always"]:
                matched_bodies.append(entry["body"])
                matched_prompts.add(entry["name"])

    # 技能目录常驻注入（技能正文由 agent 按需 use_skill 加载）
    matched_bodies.append(build_skill_index())

    return "\n\n".join(matched_bodies), {"prompts": matched_prompts, "skills": set()}


# 启动时加载
load_all()
print(f"[Prompt] 加载 {len(_prompt_registry)} 个 prompt ({len(_always_prompts)} 常驻) + {len(_skill_registry)} 个 skill（目录常驻，use_skill 按需加载）")
