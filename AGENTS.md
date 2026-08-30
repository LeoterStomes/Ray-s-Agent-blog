# Codex 项目记忆

## 项目概述
Ray的垃圾站 — 全栈个人博客系统
- 前端：Astro 5 + Vue 3 + Tailwind (端口 4321)
- 后端：FastAPI + SQLAlchemy + MySQL (端口 1235)
- 数据库：blog_db (MySQL 8.0, 端口 3307)
- 路径：`personal-blog/The-new-AI-Psychological-assistant/`

## 📋 待实现计划

### ✅ API 管理面板
- **位置**：管理后台 → API Key
- **功能**：读写 .env，按分组展示（AI/搜索/邮件/飞书），敏感 key 脱敏
- **状态**：已完成（2026-07-21）

### ✅ 视频周报 v2（Pillow 渲染 + TTS 方案）
- **流程**：Agent 生成 PPT → Pillow 渲染 PPT 风格画面 → Edge TTS 配音 → FFmpeg 合成 MP4
- **状态**：已完成（2026-07-21）

---

## 重要规则
1. **完成任务后必须主动提问**：阶段性完成时告诉用户已完成什么，询问是否继续下一步，不要擅自做决定。
2. **后端规范**：models/schemas/services/routers 四层分离。router 只做参数校验和路由，业务逻辑在 service，数据模型在 model，请求/响应在 schema。
3. **前端规范**：页面用 .astro，交互组件用 .vue (client:only="vue")。BaseLayout 是全局布局，AdminLayout 是管理端布局。
4. **代码清理**：新增功能替代旧功能后，必须删除废弃的组件和 import，保持代码干净。
5. **路径敏感**：项目目录可能被用户重命名，使用 `%~dp0` 或动态路径。
6. **⚠️ 重大修改后必须更新此文件**：每次完成重要的代码修改、bug修复、架构调整后，立即更新 AGENTS.md 对应章节，记录改动内容和原因。不要等用户提醒。
7. **主动检查遗漏**：完成一个模块的所有功能后，检查是否每个端点、每个功能都已实现，别留"半成品"（如只写了前端按钮但后端端点缺失）。
8. **⚠️ 修改后必须做连通性测试**：每次修改前端或后端后，自动用 curl 验证后端 API → 前端页面 → 完整数据流。至少测：health(200)、文章列表(total>0)、文章详情(200)、博客列表页(200)、博客详情页(200)、管理端(200)、登录页(200)。验证前端是否真的收到了后端数据。

## 后端结构 (已完成重构)
```
python-backend/
├── models/      # 10个模型文件 (user, article, category, favorite, chat, announcement, music, project, visitor, comment)
├── schemas/     # 6个schema文件 (user, article, category, favorite, chat, common)
├── services/    # 业务逻辑层 (11个模块: article/comment/rag/agent/visitor/...)
├── routers/     # 路由层 (14个模块: users/articles/categories/favorites/chat/comments/rag/files/announcements/music/projects/captcha/email/site_settings)
├── main.py      # 入口 + CORS + 访客统计
├── config.py    # 配置 (数据库/JWT/AI/SMTP/CORS/Embedding)
├── database.py  # 数据库引擎
├── auth.py      # JWT
├── captcha_utils.py  # 图形验证码生成 (Pillow)
├── captcha_store.py  # 验证码内存存储
├── email_utils.py    # SMTP 邮件发送 (formataddr编码)
├── email_store.py    # 邮箱验证码存储 + 频率限制
├── agent_service.py  # Agent 工具定义 + 执行器 (14个工具)
├── rag_service.py    # RAG 知识库：ChromaDB + BGE嵌入 + 切片 + 索引 + 搜索
├── mcp_client.py     # MCP 外部服务客户端
├── export_service.py # 文件导出 (PDF/DOCX/TXT/HTML)
├── summarize.py      # AI 摘要服务
├── site_settings.py  # 站点设置 (背景上传/获取/重置)
├── skills/           # Agent Skills (7个.skill文件)
├── chroma_db/        # ChromaDB 向量库持久化目录
├── .env              # 环境变量 (不提交)
└── start-backend.bat # 后端启动脚本
```

## 启动方式
- 后端：双击 `start-backend.bat`（端口 1235）
- 前端：双击 `start-frontend.bat`（端口 4321）
- 需要先启动 MySQL (端口 3307)，再启动后端

## 前端结构
```
astro-blog/src/
├── pages/       # 16个页面 (前台11 + 管理端5)，新增 /agent
├── components/  # vue/ (Agent相关: ThinkingTyping/ThinkingCard/ToolCallCard/ToolResultCard/AgentView/AIChatWidget + 其他30个) + astro/ (4个)
├── layouts/     # BaseLayout, AdminLayout, BlogPostLayout
├── lib/         # api.ts, auth.ts, store.ts, constants.ts
├── styles/      # global.css (Tailwind+自定义+深色模式+文章排版)
└── (scripts/ 已移除)
```

## 关键API端点
- 用户：/api/user/login, /register, /current, /profile, /password, /page, /{id}/status
- 文章：/api/knowledge/article/page, /{id}, /{id}/read, /{id}/publish, /{id}/offline
- 分类：/api/knowledge/category/tree, /all
- 收藏：/api/knowledge/favorite/page, /{articleId}, /{articleId}/status
- 聊天：/api/psychological-chat/session/start, /stream, /generate-doc, /export
- 公告：/api/announcement/list, /all
- 音乐：/api/music/list, /upload, /{id}
- 项目：/api/project/list, /all, /fetch-readme
- 文件：/api/file/simple/upload/image
- 访客：/api/visitor/stats, /api/visitor/ping

## 修复记录
- **2026-07-04** 修复 Agent stream 端点崩溃：`replace_all` 误替换 `int(session_id)` → `sid_int` 导致赋值语句变成 `sid_int = sid_int` (NameError)。已修复回 `int(session_id)`。
- **2026-07-04** 站点背景：默认改为纯色渐变，管理后台支持上传自定义壁纸（routers/site_settings.py + AdminDashboard UI）。
- **2026-07-04** 新增邮箱验证码注册系统：email_utils.py (SMTP/formataddr编码) + email_store.py (内存存储+频率限制) + routers/email.py (send-code/verify-code)。注册表单改为邮箱+验证码+60s倒计时，5分钟超限3次触发图形验证码。修复 SMTP From 头中文编码导致 QQ 邮箱拒收。
- **2026-07-04** 启动脚本拆分为 start-backend.bat + start-frontend.bat（含路径空格和端口冲突修复）。
- **2026-07-04** 修复 AI 聊天静默失败：session/start 未在 try/catch 中 → streaming 状态卡死 → 后续点击无响应。重写 send() 增加连接状态/错误横幅/onclose 处理，session/start 不再发送 initialMessage 避免重复保存。
- **2026-07-04** 安全加固：config.py 移除硬编码凭据（DATABASE_URL/JWT_SECRET/AI_API_KEY），改为强制环境变量 + load_dotenv() 自动加载 .env；CORS 改为白名单模式（CORS_ORIGINS 环境变量）。
- **2026-07-04** 前端 api.ts 实现超时：AbortController + API.TIMEOUT(15s)，超时抛 TIMEOUT 错误。
- **2026-07-04** articles router 重构为薄层：删除内联 SQL/序列化逻辑，全部委托 article_service。article_service 新增 _article_to_dict() 公共序列化函数，paginate() 新增排序参数，size 加除零防护，datetime.utcnow()→now(timezone.utc)。
- **2026-05-23** 补全 articles.py 缺失的 CRUD 端点（POST/PUT/DELETE/publish/offline）。原因：前端 ArticleManager 调用了这些端点但后端从未实现，导致"新建文章"按钮无效。修复后管理端可正常创建、编辑、删除、发布、下架文章。
- **2026-05-23** 完成后端四层架构重构：拆分 models/schemas/services，所有 router 改为薄层调用 service。
- **2026-05-23** 修复文章编辑时内容丢失：openEditor 改为先调详情 API 获取 content 再填充表单。原因是列表 API 不返回 content 字段。
- **2026-05-23** 博客列表改为客户端 API 渲染（BlogListClient.vue），与管理端同 MySQL 数据源，不再依赖 Content Collections。
- **2026-05-23** 文章详情页改为 SSR API 渲染（[slug].astro），从 API 获取文章内容。修复详情页 404 问题。
- **2026-05-23** 全栈连通性测试通过：backend health/文章列表/文章详情 + frontend 博客列表/详情/管理端/登录页 全部 200。
- **2026-05-23** 创建 `/editor` 博客编辑器：富文本 + Markdown 快捷输入（`#`标题/`**粗体**`/粘贴转换）+ 图片上传/粘贴 + 工具栏 + 存草稿/发布。
- **2026-05-23** 编辑器增加 Slash 命令菜单（`/`触发）：标题H1-H6、标注框、编号/无序列表、引用、分隔线、代码块。支持↑↓选择、Enter确认、Esc关闭。
- **2026-05-23** 编辑器增加 Notion 风格块样式：悬停高亮、Tab缩进、Shift+Tab反向缩进。
- **2026-05-23** 样式格式化行为：标题/引用/标注→回车立即转正文；列表→回车延续，空行退出；代码块→Shift+Enter退出。
- **2026-05-23** 标注框（callout）：当前块直接变为💡蓝底标注框，嵌套内容保留，回车不退出，空行还原。
- **2026-05-23** 代码块：`/`选代码块→自动首行缩进2字符，黑底等宽字，Tab插入空格，Shift+Enter退出到正文。
- **2026-05-23** 首页改为全动态API渲染（HomeContent.vue）：HeroCarousel+文章列表从后端实时获取，按发布时间倒序。
- **2026-05-23** 博客列表改为BlogListClient.vue客户端API渲染，分类筛选支持。
- **2026-05-23** 管理端文章管理精简：移除新建/导入按钮，只保留搜索/筛选/编辑/发布/下架/删除。
- **2026-05-23** 导航栏用户菜单增加「上传博文」，跳转`/editor`。
- **2026-05-23** 深夜模式：BlurControl面板新增开关，全局CSS变量覆盖，面板/文字/边框/公告/代码块全适配。
- **2026-05-23** 清理无效文件：ArticleCard.astro、audioManager.ts、AuthModal.vue、AudioEngine.vue、HeroTitle.vue、Announcement.astro、Content Collections（6个.md+config.ts）。
- **2026-05-23** ViewTransitions启用：astro.config.mjs添加prefetch，BaseLayout添加ViewTransitions组件，页面切换客户端过渡。
- **2026-05-23** 修复`require('@tailwindcss/typography')`ESM兼容问题→改用`import typography from`。
- **2026-05-23** 全局文章排版优化：prose样式（h1-h6/段落/引用/代码/图片/表格/链接）+ @tailwindcss/typography插件。
- **2026-05-23** 音乐播放器跨页面持久化：AudioEngine→`window.__m`原生JS脚本在BaseLayout<head>中，ViewTransitions+sessionStorage恢复播放。
- **2026-05-23** 文章详情页增加右侧推荐栏：同分类文章推荐（自动过滤当前文章），取前3篇，带封面/标题/阅读数，无推荐时隐藏。

## 最近修复记录
- **2026-07-18** 跨会话记忆（Mem0）：自动提取/去重/合并事实，替换手写 ChromaDB 压缩
- **2026-07-18** Agent 死循环防护：8 道防线（去重/硬上限/分类限制/断路器/超时取消/兜底/双层 break）
- **2026-07-18** 搜索引擎升级：DuckDuckGo→Bing→SearXNG 三引擎 + `extract_images` 提取网页图片
- **2026-07-18** System Prompt 精炼：206→80 行，核心规则 ⚠️ 标记，去冗余
- **2026-07-18** PPT 生成：`generate_presentation`（python-pptx, 3 套主题）+ `extract_images` 配图
- **2026-07-18** BGE 启动预加载：后台线程加载，首次对话不再卡顿
- **2026-07-18** "继续"记忆：工具记录持久化到 DB，确保后续对话有上下文
- **2026-07-12** 提示词抽离：`system_prompt.md` 独立文件，热加载；优先级：.md > .skill > chat.py 动态注入
- **2026-07-12** 评论系统：model + service + router + CommentSection.vue，嵌套回复，游客提示登录
- **2026-07-12** RAG 知识库：ChromaDB + BGE 嵌入，博客文章自动同步，外部文档导入，search_articles 升级为全库语义搜索
- **2026-07-12** 文章编辑入口：文章页底部编辑按钮（仅 admin 可见），编辑器支持 ?id= 预加载
- **2026-07-12** 安全加固：删除不安全的 GET /forget 密码重置；公告/分类/音乐/项目/站点/用户状态 API 全补鉴权；AdminLayout 加 AdminGuard；新增速率限制中间件；聊天导出改用一次性下载令牌；文件上传加大小限制；SSE 异常不泄露内部信息；改密码需验证旧密码；gitignore 补 chroma_db/logs/.bak
- **2026-07-12** 脑图修复：markmap 注入浅色主题；make_mindmap 与 MCP 版描述区分；禁止 Agent 撒谎"已生成"
- **2026-07-12** Agent 工具面板：中文名映射（45个）+ 最新优先 + 超过 6 个折叠
- **2026-07-21** API 管理面板：`/admin/api-keys`，读写 .env，按分组展示，敏感 key 脱敏
- **2026-07-21** 视频周报 v2：Pillow 渲染 PPT 画面 + Edge TTS + FFmpeg → MP4（放弃 LibreOffice 截图）
- **2026-07-21** Agent 稳定性修复：强制总结只在无自然产出时触发 + Vite 代理 10 分钟超时 + BATCH_TIMEOUT 300s
- **2026-07-21** 工具结果加 status/message 字段：Agent 不再误判成功为"空结果"
- **2026-07-21** read_document 支持 .pptx：python-pptx 提取幻灯片文本
- **2026-07-21** get_article 截断 3000→8000 字 + Agent "直接行动不预告"规则
- **2026-07-21** 搜索优先级：博客内容优先 search_articles（RAG），外部信息才用 search_web
- **2026-07-21** PDF 导出修 fpdf2 HTML 问题：_html_to_text 转纯文本
- **2026-07-18** 提示词架构重构：`prompts/` 8 文件 + metadata 头 + 按 trigger 动态加载；11 个 skill 全加 tools/links
- **2026-07-12** System Prompt 全面优化：信息安全边界、表情规则、问候语规则、引用标注规则、导航指引规则、角色语气细则、禁止 Agent 自称 Codex/GPT

## 文章页设计
- **深色主题**：`background:#0b0f19`，白字，16px/1.9 行高
- **三栏卡片**：左目录(200px) + 正文(max-780px) + 右推荐(240px)，圆角边框 + 毛玻璃
- **背景切换**：进入文章页 JS `setProperty('!important')` 强设暗色，离开时恢复 `_bgUrl` 缓存壁纸
- **目录**：sticky + IntersectionObserver scroll spy，ViewTransitions 兼容
- **BlogPostLayout**：封面/标题/分类/元信息/正文/Footer 全部组件化

## 壁纸系统
- 上传：`POST /api/site/background/upload` → `uploads/background/custom-bg.jpg`
- 加载：BaseLayout JS 优先读 `localStorage._bgUrl` 缓存，再异步 fetch API
- 优先级：`setProperty('background', ..., 'important')` 最高
- 深色模式：`.dark-mode body { background: #111118 !important }`

## Agent 系统
- **后端**：`services/agent_service.py` 定义 14 个工具 + `routers/chat.py` function calling 循环（max 20 轮兜底）
- **权限**：`_filter_tools_for_user()` 按 user_type 过滤，admin 14 工具 / 普通用户 12 工具
- **MCP**：`services/mcp_client.py` stdio + HTTP/SSE 双传输，已接 5 个外部 Server
- **RAG 知识库**：`services/rag_service.py` ChromaDB + BGE 嵌入，语义搜索 + LIKE 降级 + 联网兜底三级策略
- **外部文档**：`routers/rag.py` 导入 PDF/DOCX/TXT/MD → 自动切片入库，`/admin/rag` 管理界面
- **安全**：`.env` 不入 Git；敏感信息仅存 `.env`；迁移脚本密码已清除
- **会话持久化**：`watch(sessionId)` → localStorage → 文章页浮钮 onclick 带回 `/agent?session=xxx`
- **提示词**：System Prompt 含博客功能说明 + 角色语气 + 自动联网兜底 + 实时用户信息
- **工具**：search_articles / get_article / get_categories / recommend_articles / search_web(多引擎) / read_url / get_recent_articles / create_draft / read_document / summarize_url / summarize_text / export_file
- **Skills**：7 个 .skill 文件（content-writer / researcher / reader-helper / multi-search / proactive / summarize / export），启动时加载到 System Prompt
- **导出**：`services/export_service.py` (PDF/DOCX/TXT)，前端绿色内联下载卡片，刷新不丢失
- **AI 摘要**：`services/summarize.py` 调用 DeepSeek 生成中文摘要
- **前端浮窗**：AIChatWidget.vue 块级渲染 + 展开按钮 + 附件上传 + 终止按钮 + 历史管理
- **前端全屏**：`/agent` 页面（AgentView.vue），三栏布局 + 历史侧栏 + 拖拽上传 + 终止按钮
- **SSE 事件**：thinking / tool_call / tool_result / message / done / error

## 技术要点
- **配置**：config.py 强制从环境变量/.env 读取敏感配置，启动前需复制 .env.example 为 .env 填入真实值
- **CORS**：通过 `CORS_ORIGINS` 环境变量控制允许的前端域名，逗号分隔
- **SMTP**：邮箱验证码通过 QQ 邮箱 SMTP 发送（smtp.qq.com:587），`From` 头用 `formataddr()` 编码中文名
- 全局音频：`window.__m` (原生JS，在BaseLayout <head>中)，方法: play/pause/setVol/getAudio/isPlaying/getTime
- 头像上传：POST /api/file/simple/upload/image，multipart/form-data，token header
- 登录跳转：admin (user_type=2) → /admin，普通用户 → /
- 响应格式：{code:"200", msg:"...", data:...}
- Auth token 通过 header "token" 传递，非 "Authorization: Bearer"
- JWT 有效期24小时
- API 请求超时 15 秒（api.ts AbortController）