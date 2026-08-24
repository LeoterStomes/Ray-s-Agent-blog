"""视频周报生成服务
依赖：Edge TTS (免费) + FFmpeg + Pillow
"""
import os, json, uuid, subprocess, asyncio, tempfile, shutil
from io import BytesIO

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "export")
os.makedirs(EXPORT_DIR, exist_ok=True)

# 尝试多种方式定位 ffmpeg
_FFMPEG_PATH = None
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ffmpeg.exe"))
for _candidate in [_project_root, "ffmpeg", "ffmpeg.exe",
                   os.path.expandvars(r"%ProgramFiles%\ffmpeg\bin\ffmpeg.exe"),
                   os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe")]:
    if os.path.exists(_candidate):
        _FFMPEG_PATH = _candidate
        break
    elif shutil.which(_candidate):
        _FFMPEG_PATH = shutil.which(_candidate)
        break


def _ffmpeg(*args) -> bool:
    """运行 ffmpeg，返回是否成功"""
    if not _FFMPEG_PATH:
        return False
    try:
        subprocess.run([_FFMPEG_PATH] + list(args), capture_output=True, check=True, timeout=300)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# VoiceBox TTS
# ═══════════════════════════════════════════════════════════

# Edge TTS 音色预设
VOICE_PRESETS = {
    "default":  ("zh-CN-XiaoxiaoNeural", None),       # 晓晓-默认活泼女声
    "news":     ("zh-CN-YunxiNeural", "newscast"),     # 云希-新闻男声
    "calm":     ("zh-CN-XiaoxiaoNeural", "calm"),      # 晓晓-平静
    "friendly": ("zh-CN-XiaoxiaoNeural", "friendly"),  # 晓晓-亲切
    "serious":  ("zh-CN-YunjianNeural", None),         # 云健-严肃男声
    "warm":     ("zh-CN-XiaoyiNeural", None),          # 晓伊-温暖女声
    "pro":      ("zh-CN-YunyangNeural", "professional"),# 云扬-专业男声
}


async def _edge_tts(text: str, voice_style: str = "default") -> bytes:
    """Edge TTS — 免费，支持 7 种音色预设"""
    import edge_tts, tempfile, os
    voice, style = VOICE_PRESETS.get(voice_style, VOICE_PRESETS["default"])
    out_path = os.path.join(tempfile.gettempdir(), f"edge_tts_{uuid.uuid4().hex[:8]}.mp3")
    try:
        if style:
            communicate = edge_tts.Communicate(text, voice, style=style)
        else:
            communicate = edge_tts.Communicate(text, voice)
        await communicate.save(out_path)
        with open(out_path, "rb") as f:
            data = f.read()
        os.remove(out_path)
        return data
    except Exception:
        return b""


# ═══════════════════════════════════════════════════════════
# 配图（本地生成设计感画面，零 API 依赖）
# ═══════════════════════════════════════════════════════════

def create_frame_with_text(image_bytes: bytes, text: str, segment_index: int = 0) -> bytes:
    """在图片上叠加字幕，返回 JPEG"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.resize((1920, 1080))

    draw = ImageDraw.Draw(img)

    # 底部半透明黑底
    draw.rectangle([(0, 850), (1920, 1080)], fill=(0, 0, 0, 180))

    # 尝试用中文字体，回退到默认
    font = None
    font_size = 36
    for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
               "C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/msyhbd.ttc"]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                pass

    # 文字换行
    max_chars_per_line = 40
    lines = []
    for line in text.split("\n"):
        while len(line) > max_chars_per_line:
            lines.append(line[:max_chars_per_line])
            line = line[max_chars_per_line:]
        if line:
            lines.append(line)

    y = 880
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (1920 - tw) // 2
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=font)  # 阴影
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += font_size + 8

    # 右上角页码
    if font:
        draw.text((1820, 20), str(segment_index + 1), fill=(255, 255, 255, 128), font=font)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════
# 视频合成
# ═══════════════════════════════════════════════════════════

def _make_segment(frame_bytes: bytes, audio_bytes: bytes, output_path: str, duration: float = 10.0):
    """将单帧图片 + 音频合成为视频片段"""
    with tempfile.TemporaryDirectory() as tmp:
        frame_path = os.path.join(tmp, "frame.jpg")
        audio_path = os.path.join(tmp, "audio.mp3")
        with open(frame_path, "wb") as f:
            f.write(frame_bytes)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        # 图片循环到音频时长 + 淡入淡出
        ok = _ffmpeg(
            "-loop", "1", "-i", frame_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-vf", "fade=in:0:30,fade=out:st={0}:d=30".format(max(0, duration - 1)),
            "-shortest", "-y",
            output_path,
        )
        if not ok:
            # 无 FFmpeg 时丢一个占位文件
            shutil.copy(frame_path, output_path.replace(".mp4", ".jpg"))


def _render_slide_frame(slide: dict, theme_name: str, index: int) -> bytes:
    """用 Pillow 渲染单张 PPT 风格的画面"""
    from PIL import Image, ImageDraw, ImageFont
    from services.slide_service import THEMES
    t = THEMES.get(theme_name, THEMES["dark"])

    img = Image.new("RGB", (1920, 1080), t["bg"])
    draw = ImageDraw.Draw(img)

    # 字体
    font_title = None
    font_body = None
    for fp in ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyh.ttc"]:
        if os.path.exists(fp):
            try:
                font_title = ImageFont.truetype(fp, 44)
                font_body = ImageFont.truetype(fp, 28)
                break
            except: pass

    stype = slide.get("type", "content")
    title = slide.get("title", "")
    bullets = slide.get("bullets", [])

    # 顶部色条
    draw.rectangle([(0, 0), (1920, 8)], fill=t["accent"])

    if stype == "title":
        draw.rectangle([(0, 500), (1920, 520)], fill=t["accent"])
        if title:
            bbox = draw.textbbox((0, 0), title, font=font_title)
            draw.text(((1920 - bbox[2]) // 2, 380), title, fill=t["text"], font=font_title)
        subtitle = slide.get("subtitle", "")
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=font_body)
            draw.text(((1920 - bbox[2]) // 2, 560), subtitle, fill=t["accent2"], font=font_body)
        draw.text((50, 1040), f"Ray的垃圾站 · AI 生成", fill=t["bg_light"], font=font_body)

    elif stype == "section":
        draw.rectangle([(0, 0), (1920, 1080)], fill=t["accent"])
        if title:
            bbox = draw.textbbox((0, 0), title, font=font_title)
            draw.text(((1920 - bbox[2]) // 2, 460), title, fill=(255, 255, 255), font=font_title)

    elif stype == "ending":
        draw.rectangle([(0, 500), (1920, 520)], fill=t["accent"])
        if title:
            bbox = draw.textbbox((0, 0), title, font=font_title)
            draw.text(((1920 - bbox[2]) // 2, 380), title, fill=t["text"], font=font_title)
        draw.text((50, 1040), "Ray的垃圾站 · 感谢收看", fill=t["accent2"], font=font_body)

    else:  # content
        if title:
            draw.text((80, 60), title, fill=t["text"], font=font_title)
            draw.rectangle([(80, 130), (600, 134)], fill=t["accent"])

        y = 200
        for b in bullets[:8]:
            draw.text((100, y), f"· {b}", fill=t["text"], font=font_body)
            y += 65

        # 页码
        draw.text((1850, 1040), str(index + 1), fill=t["bg_light"], font=font_body)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


async def ppt_to_video(script: dict) -> dict:
    """PPT → Pillow 渲染画面 → TTS 配音 → FFmpeg 合成 MP4"""
    if not _FFMPEG_PATH:
        return {"error": "FFmpeg 未安装"}

    # 1. 生成 PPT 文件（用于下载）
    from .slide_service import generate_presentation
    ppt_result = await generate_presentation(script)
    if "error" in ppt_result:
        return ppt_result

    # 2. 用 Pillow 渲染每页画面
    slides_data = script.get("slides", script.get("segments", []))
    if not slides_data:
        return {"error": "脚本中没有幻灯片"}

    theme = script.get("theme", "dark")
    clip_paths = []
    total_duration = 0

    for i, slide in enumerate(slides_data):
        # 渲染画面
        frame = _render_slide_frame(slide, theme, i)

        # TTS 配音
        notes = slide.get("notes", slide.get("title", ""))
        if not notes:
            notes = slide.get("title", "")
        audio = b""
        if notes:
            try:
                # Edge TTS 配音
                audio = await _edge_tts(notes, script.get("voice", "default"))
                if not audio:
                    audio = await _edge_tts(notes, script.get("voice", "default"))
            except Exception:
                pass

        dur = max(5, min(30, int(len(notes) / 2.5))) if notes else 5  # 中文 ~2.5字/秒
        clip_path = os.path.join(tempfile.gettempdir(), f"v3clip_{i}.mp4")

        # 写临时文件
        with tempfile.TemporaryDirectory() as tmp:
            fp = os.path.join(tmp, "frame.jpg")
            with open(fp, "wb") as f: f.write(frame)
            ap = os.path.join(tmp, "audio.mp3")
            if audio:
                with open(ap, "wb") as f: f.write(audio)

            # 有音频时用 fade 滤镜 + shortest，无音频时用 -t 控制时长
            if audio and len(audio) > 100:
                vf = f"fade=in:0:20"
                args = [
                    "-loop", "1", "-i", fp, "-i", ap,
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-vf", vf,
                    "-shortest", "-y", clip_path,
                ]
            else:
                args = [
                    "-loop", "1", "-i", fp,
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-pix_fmt", "yuv420p",
                    "-t", str(dur),
                    "-vf", f"fade=in:0:20,fade=out:st={max(0, dur - 0.5)}:d=20",
                    "-y", clip_path,
                ]
            ok = _ffmpeg(*args)
            if os.path.exists(clip_path):
                clip_paths.append(clip_path)
                total_duration += dur

    if not clip_paths:
        return {"error": "没有生成任何有效视频片段"}

    # 3. 拼接所有片段
    concat_file = os.path.join(tempfile.gettempdir(), "v3_concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{cp}'\n")

    video_name = f"weekly_{uuid.uuid4().hex[:8]}.mp4"
    video_path = os.path.join(EXPORT_DIR, video_name)
    ok = _ffmpeg(
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-y", video_path,
    )

    for cp in clip_paths:
        try: os.remove(cp)
        except: pass

    if not ok:
        return {"error": "FFmpeg 合成失败"}

    url = f"/uploads/export/{video_name}"
    return {
        "status": "success",
        "message": f"视频已生成：{video_name}，时长{round(total_duration)}秒，{len(slides_data)}页",
        "url": url,
        "filename": video_name,
        "duration": round(total_duration),
        "slides": len(slides_data),
        "ppt_url": ppt_result.get("url", ""),
    }
