# -*- coding: utf-8 -*-
"""按「左右错开 20%、上下重叠 20%」生成几种候选，用于挑一个定稿。"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
GREEN_C = (109, 216, 176)
BLUE_C = (146, 205, 245)
GREEN_TXT = (11, 107, 79, 255)
BLUE_TXT = (11, 79, 107, 255)


def vgrad(size):
    base = Image.new("RGB", (1, size))
    d = ImageDraw.Draw(base)
    for y in range(size):
        t = y / float(size - 1)
        d.point((0, y), fill=(
            int(GREEN_C[0] + (BLUE_C[0] - GREEN_C[0]) * t),
            int(GREEN_C[1] + (BLUE_C[1] - GREEN_C[1]) * t),
            int(GREEN_C[2] + (BLUE_C[2] - GREEN_C[2]) * t)))
    return base.resize((size, size), Image.BILINEAR).convert("RGBA")


def make(size, fs=0.400, stag=0.100, overlap=0.200, ss=4):
    """stag: 每个数字相对中心的水平偏移（占边长比例）
       overlap: 两个数字上下重叠的比例（占字高）"""
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mask = Image.new("L", (S, S), 0)
    pad = int(S * 0.005)
    ImageDraw.Draw(mask).ellipse([pad, pad, S - 1 - pad, S - 1 - pad], fill=255)
    img.paste(vgrad(S), (0, 0), mask)

    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_B, int(S * fs))
    bb0 = d.textbbox((0, 0), "0", font=font)
    bb9 = d.textbbox((0, 0), "9", font=font)
    h = max(bb0[3] - bb0[1], bb9[3] - bb9[1])
    dyc = 0.5 * (1.0 - overlap) * h
    for txt, bb, cx, cy, color in (
            ("0", bb0, 0.5 - stag, 0.5 - dyc / S, GREEN_TXT),
            ("9", bb9, 0.5 + stag, 0.5 + dyc / S, BLUE_TXT)):
        w, hh = bb[2] - bb[0], bb[3] - bb[1]
        d.text((S * cx - w / 2 - bb[0], S * cy - hh / 2 - bb[1]), txt, font=font, fill=color)
    return img.resize((size, size), Image.LANCZOS)


def main():
    variants = [
        ("A 错开±10% 重叠20%", dict(stag=0.100, overlap=0.200)),
        ("B 错开±15% 重叠20%", dict(stag=0.150, overlap=0.200)),
        ("C 错开±10% 不重叠", dict(stag=0.100, overlap=0.0)),
        ("D 错开±20% 重叠20%", dict(stag=0.200, overlap=0.200)),
    ]
    W, H = 300 * len(variants), 340
    canvas = Image.new("RGB", (W, H), (8, 12, 16))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT_B, 20)
    for i, (label, kw) in enumerate(variants):
        x = 25 + i * 300
        big = make(240, **kw)
        canvas.paste(big, (x, 46), big)
        small = make(56, **kw)
        canvas.paste(small, (x + 170, 250), small)
        d.text((x, 14), label, font=f, fill=(150, 200, 200))
        p = os.path.join(HERE, "logo-v%d.png" % i)
        make(512, **kw).save(p)
    canvas.save(os.path.join(HERE, "logo-variants.png"))
    print("wrote", os.path.join(HERE, "logo-variants.png"))


if __name__ == "__main__":
    main()
