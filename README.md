# Ray的垃圾站 — 全栈个人博客

基于 Astro 5 + Vue 3 + FastAPI + DeepSeek AI 的全栈个人博客系统，内置 **AI Agent** + **RAG 知识库**。

## 功能

### 博客
- 文章发布/编辑（富文本编辑器，支持 Markdown 快捷输入和图片粘贴）
- 分类/标签系统
- 文章目录导航（深色主题，IntersectionObserver 滚动高亮）
- 推荐文章、阅读统计
- 评论系统（嵌套回复，登录后可评论）
- 全局搜索（Ctrl+K 快捷键）
- 收藏功能

### AI Agent（14 个内置工具）
- **RAG 语义搜索**：基于 ChromaDB + BGE 中文嵌入，理解问题含义
- **知识库搜索**：一次搜索覆盖博客文章 + 外部参考文档（PDF/DOCX/TXT），交叉验证
- **外部文档导入**：管理后台「知识库」上传参考文档，自动切片入库
- **联网搜索**：Bing → DuckDuckGo 多引擎故障转移
- **文件读写**：读取网页/PDF/DOCX，AI 摘要，生成思维导图
- **文章草稿**：AI 辅助写作，创建/编辑文章
- **文件导出**：PDF / Word(DOCX) / TXT / HTML
- **可视化对话**：浮窗 + 全屏 Agent 页面，工具调用实时卡片展示
- **MCP 外部服务**：5 个 MCP Server（高德地图/八字算命/飞书/markmap 脑图/Wikipedia）
- **Skills 系统**：8 个专业技能引导模型按流程调用工具
- **权限控制**：Admin 可写（创建草稿/导出），普通用户只读
- **会话管理**：历史对话/删除/跨页面恢复

### 用户系统
- JWT 登录认证
- 邮箱验证码注册（QQ/163/Gmail 等）
- 图形验证码防刷
- Admin/普通用户角色
- API 速率限制（登录 10次/分，注册 3次/5分）

### 其他
- 音乐播放器（跨页面持久化）
- 站点公告
- 项目管理
- 访客统计
- 自定义壁纸上传
- 深色/浅色模式切换
- 面板毛玻璃效果调节
- 樱花粒子特效

## 技术栈

| 层 | 技术 |
|------|------|
| 前端框架 | Astro 5 + Vue 3 + TypeScript |
| CSS | Tailwind CSS 3 |
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2 |
| 数据库 | MySQL 8 |
| 向量数据库 | ChromaDB（RAG 语义搜索） |
| 嵌入模型 | BAAI/bge-small-zh-v1.5（中文优化） |
| AI 模型 | DeepSeek (function calling) |
| 认证 | JWT + bcrypt |
| 邮件 | SMTP (QQ/163/Gmail) |
| MCP | JSON-RPC 2.0 (stdio + HTTP/SSE) |
| 文档处理 | PyPDF2 / python-docx / fpdf2 |

## 项目结构

```
├── astro-blog/                # 前端
│   ├── src/
│   │   ├── pages/             # 18 个页面（含 /agent、/admin/*、/editor）
│   │   ├── components/
│   │   │   ├── astro/         # 4 个 Astro 组件
│   │   │   └── vue/           # 30+ 个 Vue 组件（Agent 可视化/评论/搜索等）
│   │   ├── layouts/           # 4 个布局
│   │   ├── lib/               # 工具函数/API/状态管理/工具名映射
│   │   └── styles/            # 全局样式
│   └── package.json
│
├── python-backend/            # 后端
│   ├── routers/               # 14 个路由模块
│   ├── services/              # 业务逻辑层（11 个模块）
│   │   ├── agent_service.py   # Agent 工具定义（14个内置工具）
│   │   ├── rag_service.py     # RAG 知识库（ChromaDB + 嵌入 + 切片）
│   │   ├── mcp_client.py      # MCP 外部服务客户端
│   │   ├── export_service.py  # PDF/DOCX/TXT/HTML 导出
│   │   └── summarize.py       # AI 摘要服务
│   ├── models/                # 10 个数据模型
│   ├── schemas/               # 6 个 Pydantic Schema
│   ├── skills/                # 8 个 Agent Skill 文件
│   ├── chroma_db/             # ChromaDB 向量库持久化目录
│   ├── system_prompt.md       # Agent 系统提示词（Markdown，热加载）
│   ├── main.py                # 入口 + CORS + 限流中间件
│   ├── config.py              # 配置（数据库/JWT/AI/SMTP/CORS/Embedding）
│   ├── rate_limit.py          # API 速率限制中间件
│   └── .env                   # 环境变量（不提交 Git）
│
├── README.md
├── CHANGELOG.md
└── CLAUDE.md
```

## 提示词体系

```
system_prompt.md     ← 基础规则，最高优先级。改完热加载，不用重启
skills/*.skill       ← 专项工作流（写作/搜索/RAG/导出等），服从 .md
chat.py 动态注入     ← 当前时间、用户身份，每次请求更新
```

## 配置说明

所有配置项在 `python-backend/.env` 中（复制 `.env.example` 并修改）。

### 必填

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | MySQL 连接串 | `mysql+pymysql://root:password@localhost:3306/blog_db?charset=utf8mb4` |
| `JWT_SECRET` | JWT 签名密钥 | `python -c "import secrets; print(secrets.token_urlsafe(32))"` 生成 |
| `AI_API_KEY` | DeepSeek API Key | `sk-xxx`，从 [platform.deepseek.com](https://platform.deepseek.com) 获取 |
| `AI_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `AI_MODEL` | 模型名称 | `deepseek-chat` |

### RAG 嵌入（可选，默认本地 BGE）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EMBEDDING_PROVIDER` | `local`（BGE 本地）/ `openai`（API） | `local` |
| `EMBEDDING_MODEL` | 模型名 | `BAAI/bge-small-zh-v1.5` |

> 国内用户首次启动会自动使用 `hf-mirror.com` 下载模型。

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
| `CORS_ORIGINS` | 允许的前端域名（逗号分隔） | `http://localhost:4321` |
| `PUBLIC_API_BASE` | 前端 SSR 调用的 API 地址 | `http://localhost:1235` |
| `MCP_SERVERS_0`~`MCP_SERVERS_19` | MCP 外部服务配置 | 空 |

## 快速开始

### 前置条件
- Node.js >= 18
- Python >= 3.9
- MySQL >= 8.0

### 1. 配置数据库

```sql
CREATE DATABASE blog_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

启动后端时会自动创建所有表（`Base.metadata.create_all`），数据库表：

| 表 | 模型 | 说明 |
|------|------|------|
| `user` | User | 用户（含 user_type 角色） |
| `knowledge_article` | KnowledgeArticle | 文章 |
| `knowledge_category` | KnowledgeCategory | 分类 |
| `user_favorite` | UserFavorite | 收藏 |
| `consultation_session` | ConsultationSession | Agent 会话 |
| `consultation_message` | ConsultationMessage | Agent 消息 |
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
python -m uvicorn main:app --host 0.0.0.0 --port 1235 --reload
# Windows: 双击 start-backend.bat
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

在 `.env` 中配置（编号格式 `MCP_SERVERS_0` 到 `MCP_SERVERS_19`）：

```bash
# Stdio 传输（本地进程）
MCP_SERVERS_0={"name":"bazi","command":"npx","args":"-y bazi-mcp"}

# HTTP/SSE 传输（远程 API）
MCP_SERVERS_1={"name":"amap","url":"https://mcp.amap.com/mcp?key=YOUR_KEY"}
```

不配置 MCP 则仅使用内置 14 个工具。

## API 端点

| 模块 | 前缀 | 说明 |
|------|------|------|
| 用户 | /api/user | 登录/注册/个人信息/改密 |
| 文章 | /api/knowledge/article | CRUD + 分页/发布/下架 |
| 分类 | /api/knowledge/category | 分类树 |
| 收藏 | /api/knowledge/favorite | 收藏/取消 |
| 评论 | /api/comment | 文章评论/回复 |
| AI 聊天 | /api/psychological-chat | 会话/流式对话/导出/删除 |
| RAG 知识库 | /api/rag | 文档导入/索引重建 |
| 邮箱 | /api/email | 验证码发送/校验 |
| 验证码 | /api/captcha | 图形验证码 |
| 文件 | /api/file | 头像/Agent文件上传 |
| 站点 | /api/site | 背景图管理 |
| 访客 | /api/visitor | 统计/ping |

## 安全

- 所有敏感信息在 `.env` 中（已加入 `.gitignore`）
- `.env.example` 提供配置模板，真值永不提交
- JWT 24h 过期，聊天导出使用一次性下载令牌
- Admin/普通用户工具权限隔离
- Admin 管理页面客户端权限守卫
- 邮箱验证码注册 + 频率限制（3次/5分）+ 图形验证码防刷
- 登录/注册 API 速率限制
- Admin 写操作 API 全部鉴权
- 文件上传大小限制（头像 5MB，Agent 20MB）
