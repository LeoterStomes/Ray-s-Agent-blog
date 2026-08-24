---
description: 思维导图生成规则
triggers: ["脑图", "思维导图", "mindmap", "层级", "结构图"]
tools: [make_mindmap, mcp_markmap__markdown_to_mindmap]
version: 1
---

## 脑图工具规则

两个脑图工具，用途不同，严禁同时调用：

| 工具 | 用途 | 场景 |
|------|------|------|
| `make_mindmap` | 返回公开 URL + iframe 代码 | **写文章时嵌入内容**——iframe 原样写入 content |
| MCP 版 | 交互式脑图直接展示 | **对话中回答问题时**快速展示 |

- **必须实际调用工具**——说"帮你生成"但不调 = 撒谎
- 写文章时 content 必须真的包含 `<iframe src="...`

→ 详细工作流见 mindmap.skill
