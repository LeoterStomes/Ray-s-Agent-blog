# Ray的垃圾站 — 全栈个人博客

基于 **Astro 5 + Vue 3 + FastAPI + DeepSeek AI** 的全栈个人博客系统，内置 **AI Agent**（可观测深度思考）+ **RAG 知识库** + **跨会话记忆（Mem0）**。

## 功能

### 博客
- 文章发布/编辑（富文本编辑器，支持 Markdown 快捷输入和图片粘贴）
- 分类/标签系统
- 文章目录导航（深色主题，IntersectionObserver 滚动高亮）
- 推荐文章、阅读统计
- 评论系统（嵌套回复，登录后可评论）
- 全局搜索（Ctrl+K 快捷键）
- 收藏功能

### AI Agent（16 个内置工具）
- **深度思考流式可见**：解析模型 `reasoning_content`，以 thinking 事件实时推送；前端思考卡片流式时自动展开、结束后自动折叠
- **RAG 语义搜索**：基于 ChromaDB + BGE 中文嵌入，理解问题含义
- **知识库搜索**：一次搜索覆盖博客文章 + 外部参考文档（PDF/DOCX/TXT），交叉验证
- **外部文档导入**：管理后台「知识库」上传参考文档，自动切片入库
- **联网搜索**：DuckDuckGo → Bing → SearXNG 多引擎故障转移
- **文件读取**：读取网页 / PDF / DOCX，AI 摘要，生成思维导图
- **文章草稿**：AI 辅助写作，创建/编辑文章
- **文件导出**：PDF / Word(DOCX) / TXT / HTML
- **PPT / 视频生成**：python-pptx 演示文稿（dark / tech / warm 三套主题）+ 视频合成
- **可视化对话**：浮窗 + 全屏 Agent 页面，工具调用实时卡片展示，思考过程实时滚动
- **MCP 外部服务**：5 个 MCP Server（高德地图 / 八字算命 / deepwiki / 飞书 / markmap 脑图）
- **Skills 按需注入**：11 个专业技能注册表化，按触发词特异度取 top-2 注入（闲聊 prompt 体积从 ~29KB 降至 1.5KB），跟进消息自动继承上一轮命中
- **权限控制**：Admin 可写（创建草稿/导出/PPT），普通用户只读
- **会话管理**：历史对话/删除/跨页面恢复
- **跨会话记忆**：Mem0 自动提取事实、去重合并、结构化更新（"不喜欢 Python 了"旧记忆自动失效），对话开始前注入历史事实

### 用户系统
- JWT 登录认证
- 邮箱验证码注册（QQ/163/Gmail 等）
- 图形验证码防刷
- Admin/普通用户角色
- API 速率限制 + 请求频率限制

### 其他
- 音乐播放器（跨页面持久化）
- 站点公告
- 项目管理
- 访客统计
- 自定义壁纸上传
- 深色/浅色模式切换（默认深色）
- 面板毛玻璃效果调节
- 樱花粒子特效

## 技术栈

| 层 | 技术 |
|------|------|
| 前端框架 | Astro 5（SSR）+ Vue 3.5 + TypeScript |
| CSS | Tailwind CSS 3 |
| 后端框架 | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 |
| 数据库 | MySQL 8 |
| 向量数据库 | ChromaDB（RAG 语义搜索 + Mem0 记忆存储） |
| 嵌入模型 | BAAI/bge-small-zh-v1.5（中文优化，可切 API） |
| AI 模型 | SiliconFlow `deepseek-ai/DeepSeek-V4-Flash`（兼容 OpenAI 协议） |
| 跨会话记忆 | Mem0（自动事实提取/去重/合并） |
| 认证 | JWT + bcrypt |
| 邮件 | SMTP (QQ/163/Gmail) |
| MCP | JSON-RPC 2.0 (stdio + HTTP/SSE) |
| 文档处理 | PyPDF2 / python-docx / python-pptx / fpdf2 / Pillow |

## 项目结构

```
├── astro-blog/                # 前端
│   ├── src/
│   │   ├── pages/             # 21 个页面（index/blog/[slug]/agent/editor/auth/admin/*/profile/projects/favorites/about/404）
│   │   ├── components/
│   │   │   ├── astro/         # Astro 组件
│   │   │   └── vue/           # 39 个 Vue 组件（Agent/ThinkingCard/ToolCallCard/评论区/搜索等）
│   │   ├── layouts/           # BaseLayout/AdminLayout/AuthLayout/BlogPostLayout
│   │   ├── lib/               # api.ts / constants.ts / store.ts / toolNames.ts（工具名→前端展示映射）
│   │   └── styles/            # 全局样式
│   └── package.json
│
├── python-backend/            # 后端
│   ├── routers/               # 14 个路由模块
│   ├── services/              # 业务逻辑层（17 个模块）
│   │   ├── agent_service.py   # Agent 工具定义（16 个内置工具）与执行
│   │   ├── prompt_builder.py  # System Prompt 按需组装（prompts 注册表 + skill top-2 注入）
│   │   ├── rag_service.py     # RAG 知识库（ChromaDB + 嵌入 + 切片）
│   │   ├── memory_service.py  # Mem0 跨会话记忆
│   │   ├── mcp_client.py      # MCP 外部服务客户端（stdio + HTTP/SSE）
│   │   ├── export_service.py  # PDF/DOCX/TXT/HTML 导出
│   │   ├── slide_service.py   # PPT 生成（python-pptx，三套主题）
│   │   ├── video_service.py   # 视频合成（Edge TTS + FFmpeg + Pillow）
│   │   └── summarize.py       # AI 摘要服务
│   ├── models/                # 10 个数据模型
│   ├── schemas/               # Pydantic Schema
│   ├── prompts/               # 8 个提示词模块（frontmatter 驱动：always/triggers）
│   ├── skills/                # 11 个 Agent 技能文件（## trigger 触发词驱动）
│   ├── chroma_db/             # ChromaDB 向量库持久化目录（RAG + Mem0）
│   ├── uploads/               # 上传文件/导出发布产物
│   ├── main.py                # 入口 + CORS + 限流中间件
│   ├── config.py              # 配置（数据库/JWT/AI/SMTP/CORS/Embedding）
│   ├── rate_limit.py          # API 速率限制中间件
│   └── .env                   # 环境变量（不提交 Git）
│
├── start-backend.bat          # 后端启动（reload 排除运行时目录 + 崩溃自动重启）
├── start-frontend.bat         # 前端启动
├── README.md
└── CHANGELOG.md
```

## 提示词体系（按需注入）

```
prompts/*.md       ← 8 个独立模块，frontmatter 声明 always / triggers，常驻 + 触发命中组装
skills/*.skill     ← 11 个专项技能（写作/搜索/RAG/导出/PPT/周报/白皮书等），## trigger 触发词
chat.py 运行时     ← 按"当前消息 + 最近 2 条消息"匹配，特异度取 top-2；每轮注入当前时间/用户身份；
                     跟进消息（"继续"等）继承上一轮命中的 prompt/skill（按会话缓存）
```

> 已常驻 prompt：core（核心规则）、privacy（安全边界）、citation（引用规范）；
> 按需触发 prompt：blog-features / search-guide / tools-reference / mindmap-guide / ppt-guide。

## 配置说明

所有配置项在 `python-backend/.env` 中（复制 `.env.example` 并修改）。

### 必填

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | MySQL 连接串 | `mysql+pymysql://root:password@localhost:3306/blog_db?charset=utf8mb4` |
| `JWT_SECRET` | JWT 签名密钥 | `python -c "import secrets; print(secrets.token_urlsafe(32))"` 生成 |
| `AI_API_KEY` | SiliconFlow API Key | `sk-xxx`，从 [siliconflow.cn](https://siliconflow.cn) 获取 |
| `AI_BASE_URL` | API 地址 | `https://api.siliconflow.cn` |
| `AI_MODEL` | 模型名称 | `deepseek-ai/DeepSeek-V4-Flash`（支持 `reasoning_content` 深度思考流） |

> 同样兼容 OpenAI / DeepSeek 官方端点（`https://api.deepseek.com` + `deepseek-chat`），只需换 BASE_URL/MODEL。

### RAG 嵌入（可选，默认本地 BGE）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EMBEDDING_PROVIDER` | `local`（BGE 本地）/ `openai`（API） | `local` |
| `EMBEDDING_MODEL` | 模型名 | `BAAI/bge-small-zh-v1.5` |
| `EMBEDDING_API_KEY` | 云端嵌入 Key（provider=openai 时必填） | 空 |

> 国内首次启动会自动使用 `hf-mirror.com` 下载模型（~400MB）。

### 邮件验证码（注册必配）

| 变量 | 说明 | QQ邮箱示例 |
|------|------|-----------|
| `SMTP_HOST` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SMTP_USER` | 发件邮箱 | `your-email@qq.com` |
| `SMTP_PASSWORD` | **授权码**（非邮箱密码） | 去 [mail.qq.com](https://mail.qq.com) → 设置 → 账户 → 生成授权码 |
| `SMTP_FROM_NAME` | 发件人名称 | `Ray的垃圾站` |

### 可选

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CORS_ORIGINS` | 允许的前端域名（逗号分隔） | `http://localhost:4321,http://localhost:3000` |
| `PUBLIC_API_BASE` | 前端 SSR 调用的 API 地址 | `http://localhost:1235` |
| `MCP_SERVERS_0`~`MCP_SERVERS_19` | MCP 外部服务配置（JSON，支持 stdio/HTTP） | 空 |

## 快速开始

### 前置条件
- Node.js >= 18
- Python >= 3.10
- MySQL >= 8.0

### 1. 配置数据库

```sql
CREATE DATABASE blog_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

启动后端时自动创建所有表（`Base.metadata.create_all`），数据库表：

| 表 | 模型 | 说明 |
|------|------|------|
| `user` | User | 用户（含 user_type 角色） |
| `knowledge_article` | KnowledgeArticle | 文章 |
| `knowledge_category` | KnowledgeCategory | 分类 |
| `user_favorite` | UserFavorite | 收藏 |
| `consultation_session` | ConsultationSession | Agent 会话 |
| `consultation_message` | ConsultationMessage | Agent 消息（含工具执行记录，sender_type 区分） |
| `comment` | Comment | 评论（含嵌套回复） |
| `announcement` | Announcement | 公告 |
| `music` | Music | 音乐 |
| `project` | Project | 项目 |
| `visitor_log` | VisitorLog | 访客记录 |

### 2. 后端

```bash
cd python-backend
pip install -r requirements.txt
cp .env.example .env  # 编辑 .env 填入真实配置
python -m uvicorn main:app --host 0.0.0.0 --port 1235 --reload --reload-exclude "*uploads*" --reload-exclude "*chroma_db*" --reload-exclude "*logs*" --reload-exclude "*__pycache__*"
# Windows: 双击 start-backend.bat（崩溃 3 秒自动重启）
```

### 3. 前端

```bash
cd astro-blog
npm install
npm run dev  # 端口 4321
# Windows: 双击 start-frontend.bat
```

### 4. RAG 知识库初始化

启动后端后，登录管理后台 → 知识库 → 点击「重建博客索引」将已有文章导入向量库。之后发布/更新文章会自动同步。

### 5. 可选：MCP 外部服务

在 `.env` 中配置（编号 `MCP_SERVERS_0` 到 `MCP_SERVERS_19`）：

```bash
# Stdio 传输（本地进程）
MCP_SERVERS_0={"name":"bazi","command":"npx","args":"-y bazi-mcp"}

# HTTP/SSE 传输（远程 API）
MCP_SERVERS_1={"name":"amap","url":"https://mcp.amap.com/mcp?key=YOUR_KEY"}
```

不配置 MCP 则仅使用内置 16 个工具。

## API 端点

| 模块 | 前缀 | 说明 |
|------|------|------|
| 用户 | `/api/user` | 登录/注册/个人信息/改密 |
| 文章 | `/api/knowledge/article` | CRUD + 分页/发布/下架 |
| 分类 | `/api/knowledge/category` | 分类树 |
| 收藏 | `/api/knowledge/favorite` | 收藏/取消 |
| 评论 | `/api/comment` | 文章评论/回复 |
| AI 聊天 | `/api/psychological-chat` | 会话/流式对话（SSE：thinking/tool_call/tool_result/message/done）/导出/删除 |
| RAG 知识库 | `/api/rag` | 文档导入/索引重建 |
| 邮箱 | `/api/email` | 验证码发送/校验 |
| 验证码 | `/api/captcha` | 图形验证码 |
| 文件 | `/api/file` | 头像/Agent 文件上传 |
| 站点 | `/api/site` | 背景图管理 |
| 访客 | `/api/visitor` | 统计/ping |
| 公告 | `/api/announcement` | 公告 CRUD |
| 音乐 | `/api/music` | 音乐 CRUD |
| 项目 | `/api/project` | 项目 CRUD |
| 管理 | `/api/admin/api-keys` | API Key 管理 |

在线文档：后端启动后访问 `http://localhost:1235/docs`（Swagger UI）。

## 安全

- 所有敏感信息在 `.env` 中（已加入 `.gitignore`，含 README/CHANGELOG 均不入库）
- `.env.example` 提供配置模板，真值永不提交
- JWT 24h 过期，聊天导出使用一次性下载令牌
- Admin/普通用户工具权限隔离（`create_draft`/`export_file` 仅 admin）
- Admin 管理页面客户端权限守卫
- 邮箱验证码注册 + 频率限制 + 图形验证码防刷
- 登录/注册 API 速率限制
- Admin 写操作 API 全部鉴权
- 文件上传大小限制（头像 5MB，Agent 20MB）
- Agent 安全边界：不向读者透露技术架构/站长信息/敏感配置

## 常见问题

| 问题 | 原因与解法 |
|------|-----------|
| Agent 工具调用全部 502 | 旧版 uvicorn reload 会因上传文件重启 worker；现已在启动命令排除 uploads/chroma_db/logs/__pycache__，请用 `start-backend.bat` 启动 |
| 对话无回复但没报错 | 模型服务 4xx/5xx 现会显式重试并提示，不再静默吞掉；检查 AI_API_KEY/BASE_URL/MODEL 配置 |
| 思考过程不显示 | 需要支持 `reasoning_content` 的模型（DeepSeek-V4-Flash 默认返回）；前端 ThinkingCard 自动展开 |
| 首次对话很慢 | BGE 嵌入模型首次启动需后台预加载（~400MB），之后秒回 |