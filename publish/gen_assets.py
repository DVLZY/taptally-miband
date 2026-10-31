# -*- coding: utf-8 -*-
"""生成「点记」发布物料：logo(100/256/512)、cover(1280x789)"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"

GREEN = (168, 230, 207, 255)
BLUE = (179, 229, 252, 255)
DARK = (14, 20, 24, 255)
GREEN_TXT = (11, 107, 79, 255)
BLUE_TXT = (11, 79, 107, 255)


def rounded(size, radius, fill):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=fill)
    return img


def make_logo(size):
    S = size
    img = rounded(S, int(S * 0.24), DARK)  # 深色圆角底板
    d = ImageDraw.Draw(img)
    pad = int(S * 0.13)
    gap = max(1, int(S * 0.035))
    r = int(S * 0.11)
    top = [pad, pad, S - pad, S // 2 - gap // 2 - 1]
    bot = [pad, S // 2 + gap // 2 + 1, S - pad, S - pad]
    d.rounded_rectangle(top, radius=r, fill=GREEN)
    d.rounded_rectangle(bot, radius=r, fill=BLUE)

    fs = int(S * 0.34)
    font = ImageFont.truetype(FONT_B, fs)
    for txt, box, color in (("0", top, GREEN_TXT), ("9", bot, BLUE_TXT)):
        bb = d.textbbox((0, 0), txt, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        cx = (box[0] + box[2]) / 2 - w / 2 - bb[0]
        cy = (box[1] + box[3]) / 2 - h / 2 - bb[1]
        d.text((cx, cy), txt, font=font, fill=color)
    return img


def band_mock(W, H):
    """手环屏幕示意：上下双色 + 0 / 9"""
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


def make_cover(W=1280, H=789):
    img = Image.new("RGBA", (W, H), (11, 26, 32, 255))
    d = ImageDraw.Draw(img)
    # 背景径向渐变感：叠加两个大圆
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-W * 0.25, -H * 0.55, W * 0.75, H * 0.75], fill=(168, 230, 207, 34))
    gd.ellipse([W * 0.45, H * 0.15, W * 1.25, H * 1.35], fill=(179, 229, 252, 30))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    logo = make_logo(190)
    img.alpha_composite(logo, (86, 92))

    f_title = ImageFont.truetype(FONT_B, 110)
    f_sub = ImageFont.truetype(FONT_B, 34)
    f_body = ImageFont.truetype(FONT_R, 33)

    d.text((308, 86), "点记", font=f_title, fill=(255, 255, 255, 255))
    d.text((316, 240), "TapTally · 对局计分", font=f_sub, fill=(168, 230, 207, 255))

    lines = [
        "单击 +1 / 双击 −1，短震反馈",
        "上绿下蓝双色分区，比分一眼看清",
        "比分自动记住，退出重进不丢",
        "上滑二次确认归零，右滑退出",
    ]
    y = 330
    for t in lines:
        d.ellipse([94, y + 12, 106, y + 24], fill=(126, 224, 192, 255))
        d.text((126, y), t, font=f_body, fill=(214, 236, 232, 255))
        y += 62

    d.text((94, H - 92), "Xiaomi Smart Band 9 / Vela 快应用", font=f_body, fill=(120, 160, 160, 255))

    mock = band_mock(380, 380)
    img.alpha_composite(mock, (W - 380 - 110, 200))
    d.text((W - 380 - 110, 600), "单击加分 · 双击减分", font=f_body, fill=(150, 200, 195, 255))
    return img


if __name__ == "__main__":
    for s in (512, 256, 100):
        p = os.path.join(OUT, "logo-%d.png" % s)
        make_logo(s).save(p)
        print("wrote", p)
    cover = make_cover()
    cp = os.path.join(OUT, "cover.png")
    cover.convert("RGB").save(cp, quality=95)
    print("wrote", cp, cover.size)
