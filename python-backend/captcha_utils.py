"""验证码图片生成 — 4位字母数字 + 干扰线 + 噪点"""
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 排除易混淆字符
_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_IMG_WIDTH = 120
_IMG_HEIGHT = 44


def random_code(length: int = 4) -> str:
    return "".join(random.choices(_CHARS, k=length))


def make_image(code: str) -> BytesIO:
    """根据验证码文本生成 PNG 图片，返回 BytesIO"""
    img = Image.new("RGB", (_IMG_WIDTH, _IMG_HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 尝试加载字体，失败则用默认
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except (OSError, IOError):
        font = ImageFont.load_default(size=28) if hasattr(ImageFont, "load_default") else ImageFont.load_default()

    # 逐字符绘制（带偏移和旋转感）
    for i, ch in enumerate(code):
        x = 10 + i * 26 + random.randint(-3, 3)
        y = random.randint(3, 10)
        color = (
            random.randint(20, 120),
            random.randint(20, 120),
            random.randint(160, 255),
        )
        # 画字符
        char_img = Image.new("RGBA", (32, 36), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((2, 2), ch, fill=color, font=font)
        # 轻微旋转
        char_img = char_img.rotate(random.randint(-25, 25), expand=False, fillcolor=(0, 0, 0, 0))
        img.paste(char_img, (x, y), char_img)

    # 干扰线
    for _ in range(3):
        x1 = random.randint(0, _IMG_WIDTH // 3)
        y1 = random.randint(0, _IMG_HEIGHT)
        x2 = random.randint(_IMG_WIDTH * 2 // 3, _IMG_WIDTH)
        y2 = random.randint(0, _IMG_HEIGHT)
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)),
            width=random.randint(1, 2),
        )

    # 噪点
    for _ in range(60):
        x = random.randint(0, _IMG_WIDTH - 1)
        y = random.randint(0, _IMG_HEIGHT - 1)
        draw.point((x, y), fill=(random.randint(180, 230), random.randint(180, 230), random.randint(180, 230)))

    # 轻微模糊
    img = img.filter(ImageFilter.SMOOTH)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf