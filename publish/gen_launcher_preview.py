# -*- coding: utf-8 -*-
"""模拟手环应用列表：比较不同留白比例下的图标观感（含应用名）。"""
import os
from PIL import Image, ImageDraw, ImageFont
import gen_assets as ga

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_R = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
BG = (10, 16, 20)
PADS = [0.00, 0.06, 0.10, 0.14]


def tile(pad, canvas=128):
    """按手环列表的样子画一格：图标 + 下方应用名。"""
    S = 200
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    # 系统圆形遮罩：整块画布内切圆
    mask = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, canvas - 1, canvas - 1], fill=255)
    logo = ga.make_logo(canvas, pad_ratio=pad).convert("RGB")
    circle = Image.new("RGB", (canvas, canvas), BG)
    circle.paste(logo, (0, 0), mask)
    big = circle.resize((128, 128), Image.LANCZOS)
    img.paste(big, ((S - 128) // 2, 12))
    f = ImageFont.truetype(FONT_R, 26)
    txt = "点记"
    bb = d.textbbox((0, 0), txt, font=f)
    d.text(((S - (bb[2] - bb[0])) / 2, 150), txt, font=f, fill=(220, 232, 236))
    return img


def main():
    W, H = 200 * len(PADS), 200
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT_B, 18)
    for i, pad in enumerate(PADS):
        canvas.paste(tile(pad), (i * 200, 0))
        d.text((i * 200 + 12, 4), "留白 %d%%" % round(pad * 100), font=f, fill=(120, 190, 190))
    out = os.path.join(HERE, "icon-padding-compare.png")
    canvas.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
