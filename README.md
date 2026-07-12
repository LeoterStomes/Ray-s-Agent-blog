# Ray的垃圾站 — 全栈个人博客

基于 Astro + Vue 3 + FastAPI + DeepSeek AI 的全栈个人博客系统，内置 **AI Agent** 助手。

## 功能

### 博客
- 文章发布/编辑（富文本编辑器，支持 Markdown 快捷输入和图片粘贴）
- 分类/标签系统
- 文章目录导航（CSDN 风格深色主题）
- 推荐文章、阅读统计

### AI Agent
- **12 个内置工具**：搜索文章/读取全文/联网搜索/推荐/创建草稿/导出文件/AI摘要等
- **可视化对话**：浮窗 + 全屏 Agent 页面，工具调用实时卡片展示
- **MCP 外部服务**：支持 stdio/HTTP 双传输，可接入第三方 MCP Server
- **Skills 系统**：7 个专业技能引导模型按流程调用工具
- **权限控制**：Admin 可写（创建草稿/导出），普通用户只读
- **会话管理**：历史对话/删除/跨页面恢复

### 用户系统
- JWT 登录认证
- 邮箱验证码注册（QQ/163/Gmail 等）
- 图形验证码防刷
- Admin/普通用户角色

### 其他
- 音乐播放器（跨页面持久化）
- 站点公告
- 项目管理
- 收藏功能
- 访客统计
- 自定义壁纸上传
- 深色模式

## 技术栈

| 层 | 技术 |
|------|------|
| 前端框架 | Astro 5 + Vue 3 + TypeScript |
| CSS | Tailwind CSS 3 |
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2 |
| 数据库 | MySQL 8 |
| AI 模型 | DeepSeek (function calling) |
| 认证 | JWT + bcrypt |
| 邮件 | SMTP (QQ/163/Gmail) |
| MCP | JSON-RPC 2.0 (stdio + HTTP/SSE) |
| 文档处理 | PyPDF2 / python-docx / fpdf2 |

## 项目结构

```
├── astro-blog/                # 前端
│   ├── src/
│   │   ├── pages/             # 16 个页面路由（含 /agent）
│   │   ├── components/
│   │   │   ├── astro/         # 4 个 Astro 组件
│   │   │   └── vue/           # 30+ 个 Vue 组件（含 Agent 可视化）
│   │   ├── layouts/           # 4 个布局
│   │   ├── lib/               # 工具函数/API/状态管理
│   │   └── styles/            # 全局样式
│   └── package.json
│
├── python-backend/            # 后端
│   ├── routers/               # 12 个路由模块
│   ├── services/              # 业务逻辑层
│   │   ├── agent_service.py   # Agent 工具定义 (12个)
│   │   ├── mcp_client.py      # MCP 外部服务客户端
│   │   ├── export_service.py  # PDF/DOCX/TXT 导出
│   │   └── summarize.py       # AI 摘要服务
│   ├── models/                # 9 个数据模型
│   ├── schemas/               # 6 个 Pydantic Schema
│   ├── skills/                # 7 个 Agent Skill 文件
│   ├── main.py                # 入口
│   ├── config.py              # 配置
│   └── .env                   # 环境变量（不提交 Git）
│
├── README.md
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

### 邮件验证码（注册必配）

| 变量 | 说明 | QQ邮箱示例 |
|------|------|-----------|
| `SMTP_HOST` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SMTP_USER` | 发件邮箱 | `your-email@qq.com` |
| `SMTP_PASSWORD` | **授权码**（非邮箱密码） | 去 [mail.qq.com](https://mail.qq.com) → 设置 → 账户 → 生成授权码 |
| `SMTP_FROM_NAME` | 发件人名称 | `Ray的垃圾站` |

> 支持 QQ邮箱 / 163 / 126 / Gmail / Outlook。不同邮箱的 HOST 和 PORT 见 `.env.example`。

### 可选

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CORS_ORIGINS` | 允许的前端域名（逗号分隔） | `http://localhost:4321` |
| `CAPTCHA_ENABLED` | 是否启用图形验证码 | `true` |
| `MCP_SERVERS` | MCP 外部服务配置（每行一个 JSON） | 空（仅内置工具） |

## 快速开始

### 前置条件
- Node.js >= 18
- Python >= 3.9
- MySQL >= 8.0

### 1. 配置数据库

```sql
CREATE DATABASE blog_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

启动后端时会自动创建所有表（`Base.metadata.create_all`），无需手动操作。表结构由以下 9 个模型定义：

| 表 | 模型 | 说明 |
|------|------|------|
| `user` | User | 用户（含 user_type 角色） |
| `knowledge_article` | KnowledgeArticle | 文章 |
| `knowledge_category` | KnowledgeCategory | 分类 |
| `user_favorite` | UserFavorite | 收藏 |
| `consultation_session` | ConsultationSession | Agent 会话 |
| `consultation_message` | ConsultationMessage | Agent 消息 |
| `announcement` | Announcement | 公告 |
| `music` | Music | 音乐 |
| `project` | Project | 项目 |
| `visitor_log` | VisitorLog | 访客记录 |

### 2. 后端

```bash
cd python-backend
pip install -r requirements.txt
cp .env.example .env  # 编辑 .env 填入真实配置
```

必填配置：`DATABASE_URL`、`JWT_SECRET`、`AI_API_KEY`

```bash
# 也可以用项目自带的启动脚本
start-backend.bat  # Windows 双击即可
```

### 3. 前端

```bash
cd astro-blog
npm install
npm run dev  # 端口 4321
# 或双击 start-frontend.bat
```

### 4. 可选：MCP 外部服务

在 `.env` 的 `MCP_SERVERS` 中每行一个 JSON 配置：

```bash
# Stdio 传输（本地进程）
MCP_SERVERS={"name":"bazi","command":"npx","args":"-y bazi-mcp"}

# HTTP/SSE 传输（远程 API）
MCP_SERVERS={"name":"amap","url":"https://mcp.amap.com/mcp?key=YOUR_KEY"}

# 某些 MCP Server 需要额外环境变量（如飞书）
# APP_ID=xxx
# APP_SECRET=xxx
# MCP_SERVERS={"name":"feishu","command":"feishu-mcp.cmd","args":"start-server"}
```

不配置 `MCP_SERVERS` 则仅使用内置 12 个工具。

## API 端点

| 模块 | 前缀 | 说明 |
|------|------|------|
| 用户 | /api/user | 登录/注册/个人信息 |
| 文章 | /api/knowledge/article | CRUD + 分页/发布/下架 |
| 分类 | /api/knowledge/category | 分类树 |
| 收藏 | /api/knowledge/favorite | 收藏/取消 |
| AI 聊天 | /api/psychological-chat | 会话/流式对话/导出/删除 |
| 邮箱 | /api/email | 验证码发送/校验 |
| 验证码 | /api/captcha | 图形验证码 |
| 文件 | /api/file | 头像/Agent文件上传 |
| 站点 | /api/site | 背景图管理 |
| 访客 | /api/visitor | 统计/ping |

## 安全

- 所有敏感信息在 `.env` 中（已加入 `.gitignore`）
- JWT 24h 过期
- Admin/普通用户工具权限隔离
- 邮箱验证码注册 + 频率限制 + 图形验证码防刷
