---
description: PPT 幻灯片 + 视频周报生成工作流
triggers: ["PPT", "幻灯片", "周报", "演示文稿", "做份简报", "视频", "周报视频"]
tools: [generate_presentation, generate_weekly_video, extract_images, search_web, read_url]
links:
  - weekly-report.skill
version: 2
---

## PPT 生成规则

### 配图
- 优先用 `extract_images` 提取真实项目图片（og:image → `<img>` 标签）
- 可直接构造 URL：`https://opengraph.githubassets.com/1/{owner}/{repo}`
- 没有合适图就不塞，纯文字 slides 也好看

### 脚本 JSON 格式
```json
{
  "title": "标题",
  "theme": "dark|tech|warm",
  "slides": [
    {"type": "title", "title": "封面标题", "subtitle": "副标题"},
    {"type": "section", "title": "章节名"},
    {"type": "content", "title": "页标题", "bullets": ["要点1", "要点2"], "image_url": "https://...", "notes": "演讲备注"},
    {"type": "ending", "title": "感谢收看"}
  ]
}
```

→ 详细工作流见 weekly-report.skill

## 视频周报生成

`generate_weekly_video` 工具接受相同的脚本 JSON，自动完成：
1. 生成 PPT → 2. 每页截图 → 3. TTS 配音（念演讲备注） → 4. 合成 MP4
返回同时包含 `.pptx` 和 `.mp4` 下载链接。
- 用户说"视频"或"周报视频"时优先用这个工具
- 用户说"PPT"或"幻灯片"时用 `generate_presentation`
- PPT 生成很快（秒级），视频需要等待 2-5 分钟（LibreOffice 截图 + TTS + FFmpeg 合成）
- 视频生成超时时间 5 分钟，期间不要重复调用，耐心等待
- 如果用户要视频但等不及，建议先给 PPT
