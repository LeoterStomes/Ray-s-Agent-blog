---
description: 搜索策略和停止条件——如何高效搜索（百度AI搜索优先，中文最优）
triggers: ["搜索", "搜一下", "查", "找", "有没有", "什么是", "怎么", "最新", "热点", "趋势", "本周", "最近"]
tools: [search_web, search_articles, read_url]
links:
  - researcher.skill
  - multi-search.skill
  - rag-kb.skill
version: 1
---

## 搜索策略

### 搜索优先级
1. **博客内容** → 先用 `search_articles`（RAG 语义搜索，覆盖博客文章 + 外部参考文档）
2. **外部信息** → 只有以下情况才用 `search_web`：
   - 用户明确要查博客外的内容（"网上搜一下"、"最新的新闻"、"最近一周"）
   - search_articles 返回空或完全不相关
   - 需要实时数据（天气、股价、热点事件）

### 关键词提取
从用户话里提炼关键词，**重点提取时间范围**，不要机械重复原话：
- "前2个月" → 推算日期范围，如现在是7月则搜 `May June 2026`
- "本周" → 搜 `this week July 2026`
- "GitHub" → 搜 `github trending` 不加多余修饰词
- "AI agent" → 精准搜 `AI agent framework github 2026`
- 不要用引号、不要用 site: 限定、不要搜中文除非用户明确要中文内容
- **搜索词控制在 5-8 个单词**，太长的搜索词返**回结果差

### 限制
- 联网搜索**最多 8 次**，读网页**最多 8 个**。达到上限立即停，整理已有信息。
- 两次搜索无满意结果 → 告知"这个方向信息比较少"，不无限换词重试。
- **搜 3-5 次必须停！** 之后立即整理已有结果，输出最终回答。不许说"再搜一次"、"换个关键词"、"让我试试"。
- 后台限制严格——超限后工具会被拒绝，届时你将无法输出任何内容。所以务必在前 3-5 次搜索内拿到足够信息。

### 图片搜索
- 用 `extract_images` 从网页提取真实图片（优先 og:image）
- 可直接构造 URL：`https://opengraph.githubassets.com/1/{owner}/{repo}`、`https://picsum.photos/800/600`
- 搜图加 `site:weibo.com` 或 `site:zhihu.com` 找社交平台图片

→ 搜索工作流见 researcher.skill、multi-search.skill
→ RAG 搜索见 rag-kb.skill
