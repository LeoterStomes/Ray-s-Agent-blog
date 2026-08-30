# 更新日志 / Changelog

本文件记录项目的所有重要修改、功能新增和问题修复。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 🧠 Agent 思考链路重构（2026-08-30）
- **深度思考实时可见**：解析模型 `reasoning_content` 并以 thinking 事件流式推送，前端思考卡片流式时自动展开、结束后自动折叠，用户可实时观看 Agent 推理过程
- **每轮状态心跳**：每轮 LLM 调用前推送"正在思考/正在整理"状态，不再长时间无反馈
- **Skills 按需注入**：11 个 skill 不再全量注入每条 system prompt（约 15KB），改为注册表化 + 按触发词特异度取 top-2；闲聊 prompt 体积从 ~29KB 降至 1.5KB
- **触发匹配升级**：匹配文本覆盖当前消息 + 最近 2 条用户消息；跟进消息（"继续"等）自动继承上一轮命中的 prompt/skill（按会话缓存）
- **思考/正文分离**：有工具调用的轮次文本不再混入最终回复，持久化只存正文
- **协议合规修复**：去重跳过/超限拦截的工具调用回填 skipped 响应，杜绝悬空 tool_calls
- **跨工具失败记忆**：同一链接读取失败后，换工具重试会被拦截并引导模型如实告知用户
- **LLM 响应状态检查**：模型服务 4xx/5xx 时显式重试，不再静默吞掉（修复对话无回复消失的问题）
- **工具执行独立 DB Session**：不再共享请求级 Session，消除并发隐患
- **历史回放过滤**：会话历史接口不再把工具执行记录当作 AI 消息回放
- **提示词冲突统一**：researcher.skill 停止条件与 search-guide 对齐（兜底一次、不无限重试）；content-writer 补充"整理笔记/美化/排版/发布到博客"触发词

### 🛡️ 运维加固
- **uvicorn reload 排除运行时目录**：uploads/chroma_db/logs/__pycache__ 写入不再触发 worker 重启（修复上传文件后工具调用全部 502 的问题）
- **后端看门狗**：`start-backend.bat` 崩溃后 3 秒自动重启

### 🧠 跨会话记忆系统（Mem0）
- **Mem0 替换手写压缩**：从 "LLM压缩→BGE嵌入→ChromaDB" 升级为 Mem0，自动提取事实、去重、合并
- **结构化记忆**：偏好/习惯/话题自动提取为结构化事实，支持更新（"不喜欢Python了"旧记忆自动失效）
- **检索增强**：对话开始前注入用户历史事实，Agent 自然引用（"上次我们聊过 FastAPI..."）
- **持久化**：工具执行记录保存到数据库（sender_type=3），"继续"时不会从头开始

### 🔧 Agent 稳定性修复
- **死循环防护体系**：8 道防线——工具去重/硬上限(15次)/分类限制(搜索5次,读网页5次)/连续失败断路器(6次)/18轮兜底/超时取消/兜底回复/内容分离
- **双重回复修复**：强制总结只在调用过工具时触发，避免无工具对话输出两次
- **"继续"记忆**：工具执行记录持久化，说"继续"时 Agent 知道之前搜了什么
- **搜索超时取消**：`task.cancel()` + `await task` 确保超时工具彻底关闭，不悬挂
- **BGE 启动预加载**：后台线程加载模型，首次对话不再卡 30 秒
- **兜底回复**：全程无输出时返回"抱歉，处理请求时遇到问题"，不再静默丢失

### 🔍 搜索引擎升级
- **三引擎故障转移**：DuckDuckGo→Bing→SearXNG，SearXNG 直接解析 JSON 结构化结果
- **Bing 修复**：从 `cn.bing.com`(JS渲染无效) 改为 `www.bing.com` + Chrome UA 模拟
- **数据源扩展**：DuckDuckGo Lite 版（无需 JS）+ SearXNG 公共实例
- **图片提取工具**：新增 `extract_images` 工具，从网页提取 og:image + `<img>` 标签，自动过滤头像/图标

### 📝 System Prompt 精炼
- **从 206 行压缩到 ~80 行**：去冗余、合并规则、核心命令 ⚠️ 标记
- **搜索策略强化**：关键词提取+停止条件+搜索引擎兜底 合并为一块
- **工具名禁止**：回复中不出现 `export_file`/`search_articles` 等工具名
- **博客功能速览**：40 行详细清单改为 8 行表格

### 🎬 视频/PPT 功能
- **PPT 生成**：`generate_presentation` 替换视频方案，python-pptx 秒出
- **3 套主题**：dark（深色）/ tech（极客蓝）/ warm（暖色亮底）
- **幻灯片配图**：`image_url` 字段 + `extract_images` 提取网页真实图片
- **演讲者备注**：每张幻灯片可带 TTS 配音备注
- **视频生成保留**：Edge TTS 兜底 + FFmpeg 合成 + Pillow 渐变画面

### 🛡️ 工具调用限制（可配）
- 搜索上限 5 次、读网页上限 5 次、总工具硬上限 15 次
- 连续失败 6 次断路器 + MAX_TOOL_ROUNDS=18 兜底
- 同工具+参数去重，防止无限重试

### 📐 提示词架构重构
- **prompts/ 目录**：system_prompt.md 拆为 8 个独立 .md 文件，带 YAML metadata（description/triggers/tools/links/version）
- **动态加载**：chat.py 根据用户消息匹配 trigger，按需组装 prompt，2 个常驻 + 按需匹配
- **Skill 内嵌**：11 个 skill 全部加 `## tools` 和 `## links`，Agent 快速定位
- **白皮书 skill**：封面/目录/正文/提示框(3色)/代码块/封底 HTML 模板
- **脑图 skill**：Markdown→脑图工作流，两工具区分

### ⚡ Agent 引擎优化
- **并行执行**：同轮工具 asyncio.gather 并行，批次超时 30s，轮次间取消残留
- **百度 AI 搜索**：百度千帆 web_search API（`qianfan.baidubce.com/v2/ai_search`），中文最优+时间过滤
- **搜索去限制**：联网搜索/读网页/总工具调用全部解除限制（999）
- **XML 过滤**：流式+保存两道防线过滤 DeepSeek 误输出的 `<tool_calls>` 标签

### 🎨 前端体验优化
- 批量工具卡片合并为一行"已调用 6 个工具"
- 工具结果卡简化为 `✓ 工具完成` 灰字
- 工具面板同名去重 + thinking 单条显示
- Agent 能力边界规则：无工具直接拒绝

### 🧠 跨会话记忆系统（旧版，已替换）

### 🧠 RAG 知识库系统
- **语义搜索**：`search_articles` 从 SQL LIKE 升级为 RAG 语义搜索，理解问题含义而非关键词匹配
- **向量库**：ChromaDB 本地存储，BGE 中文嵌入模型（`BAAI/bge-small-zh-v1.5`），自动切片（500字/块+50字重叠）
- **自动同步**：文章发布→索引，下架→删除，更新→重建；全量重建接口 `/api/rag/reindex`
- **外部文档导入**：管理后台「知识库」支持上传 PDF/DOCX/TXT/MD，自动解析入库
- **全库搜索**：新增 `search_knowledge` 工具，同时搜索博客文章 + 外部参考文档
- **三级降级**：RAG 语义搜索 → LIKE 关键词搜索 → search_web 联网搜索
- **管理界面**：`/admin/rag` KnowledgeManager.vue，上传/查看/删除外部文档 + 一键重建索引
- **嵌入配置**：`config.py` 新增 EMBEDDING_PROVIDER/KEY/URL/MODEL，支持本地/云切换

### 🤖 Agent 提示词优化
- **信息安全边界**：普通读者不透露技术架构/站长信息/敏感配置，含 3 句自然拒绝话术
- **表情规则**：禁止 😅💦🤣🙄 等嘲讽表情，仅允许正面表情，每段最多 2 个
- **功能清单**：博客功能介绍重写为 4 类详细清单（读者/写作/管理/AI），含最近更新
- **导航指引**：禁止输出裸路径（/agent、/editor），改用视觉化位置描述
- **分角色语气**：管理员=私人助理（"您"），读者=导览员（"你"），各有话术范例
- **功能问询规则**：问功能直接答，不调工具搜文章

### 🔧 Agent 交互优化
- **文章页返回 Agent**：左下角浮钮 `onclick` 读取 `agentSessionId` 跳回对应对话；AgentView 支持 `?session=` URL 参数
- **watch 自动保存会话**：AIChatWidget + AgentView 用 `watch(sessionId)` 确保会话 ID 实时写入 localStorage
- **ThinkingTyping 打字动画**：纯 CSS `clip-path` 逐字显现 + 三句循环（thinking.../!!!/right away...），零 JS 零性能影响
- **工具执行流式通知**：每次调用工具前发送"正在联网搜索..."等文本，消除空白等待感
- **ToolCallCard 超时自愈**：5s 后自动标记完成 + 8s 自动隐藏，不再卡在 thinking
- **搜索超时保护**：`asyncio.wait_for(15s)` + 单引擎 5s 超时，防 Agent 卡死
- **System Prompt 优化**：博客功能介绍 + 管理员/普通用户区别语气 + 自动联网兜底 + 用户信息注入

### 🔌 MCP 外部服务集成
- **Stdio 客户端**：`services/mcp_client.py` MCPServer 类，JSON-RPC 2.0 over 子进程 stdio
- **HTTP/SSE 客户端**：MCPHttpServer 类，支持 Streamable HTTP 传输（高德、飞书等）
- **自动合并工具**：启动时加载所有 MCP Server → 以 `mcp_<name>__<tool>` 命名合并
- **跳过横幅**：自动跳过非 JSON 行（如 `bazi-mcp` 欢迎语）
- **已接入**：filesystem(14) + bazi算命(3) + Amap高德(15) + deepwiki(1) + feishu飞书(2) = 5 个外部 Server
- **文章格式优化**：content-writer.skill 要求 HTML 标签（h2/h3/pre/code/blockquote/ul/ol/table），至少 2 种元素

### 🐛 MCP 阻塞问题修复
- **NameError 崩溃**：`status_msg` 残留引用导致每次 MCP 工具调用抛出 NameError，Agent 卡死。已清理
- **MCP 异步化**：`call_mcp_tool` 改为 `loop.run_in_executor` 线程池执行，避免同步 I/O 阻塞事件循环
- **循环跳号修复**：`load_mcp_servers` 中 `break` 改 `continue`，空号不再跳过后续 MCP
- **飞书 MCP 注释**：feishu 启动失败阻塞后端，默认禁用

### 🧠 Agent 幻觉治理
- **防幻觉专节**：System Prompt 新增 4 条硬规——只回复最新消息/不编造用户没说的话/不回复历史摘要/不替用户提问
- **历史滑动窗口**：最近 5 条原文 + 之前压缩为摘要，Agent 既有上下文又不被淹没
- **时间问候修正**：`_now()` 从 UTC 改为本地时间，按时段选择问候语（早上好/中午好/下午好/晚上好）

### 🧠 Agent 能力增强
- **HTML 深度格式化**：content-writer.skill 要求表格/卡片/代码块/引用/列表全带内联样式，深色主题配色
- **思维导图**：新增 `make_mindmap` 工具，自动生成交互式 HTML 脑图 → 复制到 `/uploads/export/` → 返回 iframe 代码
- **HTML 导出**：`export_file` 支持 format="html"，保存任意 HTML 到公开目录
- **脑图降权**：仅用户明确要求时才生成脑图，平时优先表格/列表/卡片
- **MAX_TOOL_ROUNDS → 20**：模型自行决定停止时机，硬限制仅做兜底

### 🔒 安全审计
- **修复密码泄漏**：`scripts/migrate-articles.ts` 硬编码 DB 密码 → 环境变量
- **已确认安全**：`.env`/`python-backend/.env` 均在 `.gitignore`，API Key 未泄漏到源码

### 🛡️ Agent 权限控制
- **Admin vs 普通用户**：`_filter_tools_for_user()` 根据 `user_type` 过滤工具
- Admin 12 工具全开，普通用户仅 10 个（无 create_draft / export_file）
- 实时用户信息注入 System Prompt（用户名/昵称/角色+语气指导）

### 📦 Agent 文件导出 + Skills 扩展
- **文件导出**：`export_file` 工具支持 PDF/DOCX/TXT（fpdf2 + python-docx），生成文件到 `/uploads/export/`
- **下载卡片**：绿色内联下载按钮，PDF/DOCX/TXT 各有图标，刷新/切页后文本正则兜底恢复
- **AI 摘要**：`summarize_url` / `summarize_text` 工具，调用 DeepSeek 生成中文摘要
- **多搜索引擎**：`search_web` 升级为 Bing→DuckDuckGo→Sogou 三引擎自动故障转移
- **Skills 扩展**：6 个 Skill（content-writer/researcher/reader-helper/multi-search/proactive/summarize/export）
- **Agent 终止按钮**：流式对话中红色终止方块，AbortController 即时断开 SSE
- **历史删除**：DELETE /session/{id} 端点 + 前后端垃圾桶按钮

### 🎨 文章页重设计
- **深色主题**：文章详情页独立深色背景 `#0b0f19`，白字排版，进入/离开自动切换壁纸
- **三栏卡片布局**：目录(200px) + 正文(max-780px) + 推荐(240px)，均带圆角边框 + 毛玻璃效果
- **目录导航**：左侧 sticky 目录，滚动时高亮当前位置，ViewTransitions 安全
- **排版优化**：16px/1.9 行高，代码块深色主题，引用靛蓝边框，列表标记着色
- **管理入口**：admin 用户导航栏 + 用户菜单双入口，ViewTransitions 持久化
- **页面通用修复**：ViewTransitions 切换后壁纸/管理入口/Footer 均保持正确状态

### 🎨 站点美化
- **背景图替换**：默认背景从 `mc.png` 改为白色，支持 admin 上传自定义壁纸
- **自定义背景上传**：管理后台「站点背景」卡片，localStorage 缓存 + `!important` 优先级
- **Footer 透明化**：去掉白色底色，与全局背景融合

### 🐛 Agent 紧急修复
- **修复 stream 端点崩溃**：`replace_all` 误将 `int(session_id)` → `sid_int` 同时替换了赋值语句本身，导致 `sid_int = sid_int` NameError，Agent 完全不响应

### 🚀 Agent 可视化 + Function Calling
- **Function Calling 循环**：chat.py stream 端点改为 5 轮工具调用循环，模型主动决定调用时机
- **5 个 Agent 工具**：search_articles / get_article / search_web / get_categories / recommend_articles
- **SSE 类型化事件**：thinking / tool_call / tool_result / message / done
- **可视化卡片组件**：ThinkingCard（可折叠思考过程）、ToolCallCard（工具调用状态+旋转动画）、ToolResultCard（文章列表/分类/搜索结果渲染）
- **AIChatWidget 升级**：块级消息渲染 + 全屏展开按钮 → 跳转 `/agent`
- **/agent 全屏页面**：AgentView.vue 两栏布局（左对话 + 右工具面板），工具调用历史可追溯
- **会话共享**：store.ts `$agentSessionId` 浮窗↔全屏联动

### 🐛 邮箱验证码
- **新增邮箱验证码注册**：替代图形验证码，注册时发送 6 位数字验证码到用户邮箱（支持 QQ/163/126/Gmail/Outlook），60 秒发送倒计时，5 分钟内有效
- **新增频率限制**：同一 IP 5 分钟内发送超过 3 次触发图形验证码二次验证
- **修复 SMTP 发送失败**：`From` 头中文名未按 RFC 2047 编码导致 QQ 邮箱拒收，改用 `email.utils.formataddr()` 自动 Base64 编码

### 🐛 Bug 修复 — AI 聊天
- **修复 AI 聊天静默失败（浏览器无回应）**：`session/start` 调用未包裹在 try/catch 中，后端异常时 `streaming` 状态永久卡死，导致后续点击被静默吞掉。现已将 session/start 纳入 try 块，失败时显示明确错误并恢复 UI。
- **修复首条消息重复保存**：session/start 不再发送 `initialMessage`，由 stream 端点统一保存，消除数据库重复记录。
- **新增连接状态指示**：建立会话时显示「正在连接 AI 服务...」旋转动画，输入框/发送按钮在此期间禁用。
- **新增全局错误横幅**：连接失败、会话创建失败等错误以红色横幅显示在聊天区顶部，用户可点击关闭。
- **新增 `onclose` 处理**：SSE 连接意外关闭时提示用户，而非静默丢失消息。

### 工程优化
- **统一启动脚本**：根目录 `start.bat` 改为使用 venv Python，启动前检查 `.env` 和虚拟环境是否存在。删除冗余的 `python-backend/start.bat`。

### 🟡 已记录待修复
- 数据库迁移工具（Alembic）未引入
- API 无限流保护
- 无单元/集成测试
- agent-browser (Playwright) 安装受阻，暂未集成

### 安全修复
- **config.py 移除硬编码凭据**：`DATABASE_URL`、`JWT_SECRET`、`AI_API_KEY` 改为强制从环境变量读取，无默认值
- **config.py 增加 `load_dotenv()` 支持**：自动从同目录 `.env` 文件加载配置
- **CORS 安全加固**：`allow_origins` 从 `["*"]` 改为白名单模式（`CORS_ORIGINS` 环境变量，默认 localhost:4321/3000）
- **requirements.txt 新增 `python-dotenv`**

### 修复
- **api.ts 超时功能实现**：`request()` 使用 `AbortController` + `API.TIMEOUT`(15s)，超时抛出 `ApiError('TIMEOUT', ...)`
- **articles router 重构**：路由层转为薄层，删除内联 SQL 查询，全部委托给 `article_service`
- **article_service 完善**：
  - 新增 `_article_to_dict()` 公共序列化函数，消除 router/service 重复代码
  - `paginate()` 新增 `sort_field`/`sort_direction` 参数
  - `size` 参数增加 `max(1, size)` 防护，杜绝除零
  - `datetime.utcnow()` → `datetime.now(timezone.utc)` 修复弃用警告
  - 移除未使用的 `tag` 参数

### 新增
- **CHANGELOG.md**：项目更新日志
- **配置文件模块注释**：所有配置项均有中英文注释和生成方式说明

---

## [0.3.0] - 2026-05-23

### 新增
- **博客编辑器** (`/editor`)：富文本 + Markdown 快捷输入（`#`标题/`**粗体**`/粘贴转换）
- **图片上传/粘贴**功能集成到编辑器
- **Slash 命令菜单**（`/`触发）：标题 H1-H6、标注框、编号/无序列表、引用、分隔线、代码块
- **Notion 风格块样式**：悬停高亮、Tab 缩进、Shift+Tab 反向缩进
- **标注框（callout）**：蓝底提示框，支持嵌套内容
- **代码块**：黑底等宽字，Tab 插入空格，Shift+Enter 退出
- **首页全动态 API 渲染**（HomeContent.vue）：HeroCarousel + 文章列表实时获取
- **博客列表分类筛选**支持（BlogListClient.vue）
- **深夜模式**：BlurControl 面板开关，全局 CSS 变量覆盖
- **ViewTransitions 启用**：astro.config.mjs 添加 prefetch，页面切换客户端过渡
- **全局文章排版优化**：prose 样式 + @tailwindcss/typography 插件
- **音乐播放器跨页面持久化**：`window.__m` 原生 JS + sessionStorage 恢复
- **文章详情页右侧推荐栏**：同分类文章推荐（前 3 篇）

### 修复
- `require('@tailwindcss/typography')` ESM 兼容问题 → 改用 `import typography from`
- 博客列表改为客户端 API 渲染（BlogListClient.vue），与管理端同 MySQL 数据源
- 文章详情页改为 SSR API 渲染（[slug].astro），修复详情页 404 问题
- 文章编辑时内容丢失：`openEditor` 改为先调详情 API 获取 content 再填充表单
- 全栈连通性测试通过

### 变更
- 管理端文章管理精简：移除新建/导入按钮，只保留搜索/筛选/编辑/发布/下架/删除
- 导航栏用户菜单增加「上传博文」入口

### 移除
- ArticleCard.astro、audioManager.ts、AuthModal.vue、AudioEngine.vue、HeroTitle.vue、Announcement.astro
- Content Collections（6 个 .md + config.ts）

---

## [0.2.0] - 2026-05-23

### 新增
- **后端四层架构重构**：models/ → schemas/ → services/ → routers/ 分离
- 补全 `articles.py` 缺失的 CRUD 端点（POST/PUT/DELETE/publish/offline）

### 架构
- 9 个模型文件：user, article, category, favorite, chat, announcement, music, project, visitor
- 6 个 schema 文件：user, article, category, favorite, chat, common
- 9 个 service 模块
- 10 个 router 模块

---

## [0.1.0] - 初始版本

### 新增
- 项目初始化：Astro 5 + Vue 3 + Tailwind CSS 前端
- FastAPI + SQLAlchemy + MySQL 后端
- 用户管理和身份认证（JWT）
- AI 心理咨询对话（DeepSeek API）
- 文章/博客管理
- 音乐播放器集成
- 网站统计和分析
- 项目和分类管理
- 收藏功能
- 樱花特效动画