# -*- coding: utf-8 -*-
"""生成「点记 / TapTally」发布物料（AstroBox 资源社区 v2 布局）。

输出到 media/：
  icon.png        192x192  应用图标
  cover.png      1200x800  头图（3:2）
  preview-1.png  1200x800  预览图 1（与头图同图）
  preview-2.png   384x980  预览图 2（手环真实界面 192x490 的 2 倍图）
另在 publish/ 输出 logo-512/256.png 备用的高清图标。
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MEDIA = os.path.join(ROOT, "media")
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"

GREEN = (168, 230, 207, 255)
BLUE = (179, 229, 252, 255)
DARK = (14, 20, 24, 255)
GREEN_TXT = (11, 107, 79, 255)
BLUE_TXT = (11, 79, 107, 255)
BG = (11, 26, 32, 255)


def rounded(size, radius, fill):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=fill)
    return img


def make_logo(size):
    """深色圆角底 + 上半浅绿 0 / 下半浅蓝 9。"""
    S = size
    img = rounded(S, int(S * 0.24), DARK)
    d = ImageDraw.Draw(img)
    pad = int(S * 0.13)
    gap = max(1, int(S * 0.035))
    r = int(S * 0.11)
    top = [pad, pad, S - pad, S // 2 - gap // 2 - 1]
    bot = [pad, S // 2 + gap // 2 + 1, S - pad, S - pad]
    d.rounded_rectangle(top, radius=r, fill=GREEN)
    d.rounded_rectangle(bot, radius=r, fill=BLUE)

    font = ImageFont.truetype(FONT_B, int(S * 0.34))
    for txt, box, color in (("0", top, GREEN_TXT), ("9", bot, BLUE_TXT)):
        bb = d.textbbox((0, 0), txt, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        cx = (box[0] + box[2]) / 2 - w / 2 - bb[0]
        cy = (box[1] + box[3]) / 2 - h / 2 - bb[1]
        d.text((cx, cy), txt, font=font, fill=color)
    return img


def band_mock(W, H):
    """手环屏幕示意：上下双色 + 比分。"""
    img = rounded(W, int(W * 0.13), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    pad = int(W * 0.06)
    gap = max(2, int(H * 0.03))
    r = int(W * 0.07)
    top = [pad, pad, W - pad, H // 2 - gap // 2]
    bot = [pad, H // 2 + gap // 2, W - pad, H - pad]
    d.rounded_rectangle(top, radius=r, fill=GREEN)
    d.rounded_rectangle(bot, radius=r, fill=BLUE)
    font = ImageFont.truetype(FONT_B, int(W * 0.30))
    for txt, box, color in (("12", top, GREEN_TXT), ("9", bot, BLUE_TXT)):
        bb = d.textbbox((0, 0), txt, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        cx = (box[0] + box[2]) / 2 - w / 2 - bb[0]
        cy = (box[1] + box[3]) / 2 - h / 2 - bb[1]
        d.text((cx, cy), txt, font=font, fill=color)
    return img


def make_cover(W=1200, H=800):
    img = Image.new("RGBA", (W, H), BG)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-W * 0.25, -H * 0.55, W * 0.75, H * 0.75], fill=(168, 230, 207, 34))
    gd.ellipse([W * 0.45, H * 0.15, W * 1.25, H * 1.35], fill=(179, 229, 252, 30))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    logo = make_logo(180)
    img.alpha_composite(logo, (80, 92))

    f_title = ImageFont.truetype(FONT_B, 104)
    f_sub = ImageFont.truetype(FONT_B, 32)
    f_body = ImageFont.truetype(FONT_R, 31)

    d.text((290, 86), "点记", font=f_title, fill=(255, 255, 255, 255))
    d.text((298, 232), "TapTally · 对局计分", font=f_sub, fill=GREEN)

    lines = [
        "单击 +1 / 双击 −1，短震反馈",
        "上绿下蓝双色分区，比分一眼看清",
        "比分自动记住，退出重进不丢",
        "上滑二次确认归零，右滑退出",
    ]
    y = 320
    for t in lines:
        d.ellipse([88, y + 11, 100, y + 23], fill=(126, 224, 192, 255))
        d.text((120, y), t, font=f_body, fill=(214, 236, 232, 255))
        y += 60

    d.text((88, H - 88), "Xiaomi Smart Band 9 / Vela 快应用", font=f_body, fill=(120, 160, 160, 255))

    mock = band_mock(370, 370)
    img.alpha_composite(mock, (W - 370 - 100, 210))
    d.text((W - 370 - 100, 600), "单击加分 · 双击减分", font=f_body, fill=(150, 200, 195, 255))
    return img


def make_screen(scale=2):
    """手环真实界面 192x490 的 scale 倍图：上下两半 48% + 中间 4% 分隔条。"""
    W, H = 192 * scale, 490 * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    half = int(H * 0.48)
    bar = H - half * 2
    d.rectangle([0, 0, W, half], fill=GREEN)
    d.rectangle([0, half, W, half + bar], fill=(16, 26, 30, 255))
    d.rectangle([0, half + bar, W, H], fill=BLUE)

    fs = int(120 * scale * 0.92)  # 设计 300px → 物理 120px
    font = ImageFont.truetype(FONT_B, fs)
    for txt, box, color in (("12", (0, 0, W, half), GREEN_TXT), ("9", (0, half + bar, W, H), BLUE_TXT)):
        bb = d.textbbox((0, 0), txt, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        cx = (box[0] + box[2]) / 2 - w / 2 - bb[0]
        cy = (box[1] + box[3]) / 2 - h / 2 - bb[1]
        d.text((cx, cy), txt, font=font, fill=color)
    return img


if __name__ == "__main__":
    os.makedirs(MEDIA, exist_ok=True)
    make_logo(192).convert("RGBA").save(os.path.join(MEDIA, "icon.png"))
    print("wrote media/icon.png 192x192")
    for s in (512, 256):
        p = os.path.join(HERE, "logo-%d.png" % s)
        make_logo(s).save(p)
        print("wrote", p)
    cover = make_cover()
    cover.convert("RGB").save(os.path.join(MEDIA, "cover.png"))
    cover.convert("RGB").save(os.path.join(MEDIA, "preview-1.png"))
    print("wrote media/cover.png + preview-1.png", cover.size)
    screen = make_screen(2)
    screen.convert("RGB").save(os.path.join(MEDIA, "preview-2.png"))
    print("wrote media/preview-2.png", screen.size)
