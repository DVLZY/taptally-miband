# -*- coding: utf-8 -*-
"""比较不同倾斜角度的斜线图标。"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
GREEN = (168, 230, 207, 255)
BLUE = (179, 229, 252, 255)
GREEN_TXT = (11, 107, 79, 255)
BLUE_TXT = (11, 79, 107, 255)
OUT = os.path.join(HERE, "logo-compare.png")


def make(size, tilt=20, gapf=0.050, dist=0.200, along=0.100, fs=0.31, ss=4):
    S = size * ss
    inner = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    di = ImageDraw.Draw(inner)
    gap = max(2, int(S * gapf))
    di.rectangle([0, 0, S, S // 2 - gap // 2], fill=GREEN)
    di.rectangle([0, S // 2 + gap // 2, S, S], fill=BLUE)
    di.rectangle([0, S // 2 - gap // 2 - 1, S, S // 2 + gap // 2], fill=(14, 20, 24, 255))
    inner = inner.rotate(tilt, resample=Image.BICUBIC, expand=False)
    mask = Image.new("L", (S, S), 0)
    pad = int(S * 0.01)
    ImageDraw.Draw(mask).ellipse([pad, pad, S - 1 - pad, S - 1 - pad], fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(inner, (0, 0), mask)

    t = math.radians(tilt)
    u = (math.cos(t), -math.sin(t))
    n = (math.sin(t), math.cos(t))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_B, int(S * fs))
    for sign, txt, color in ((-1, "0", GREEN_TXT), (1, "9", BLUE_TXT)):
        cx = 0.5 + sign * (dist * n[0] + along * u[0])
        cy = 0.5 + sign * (dist * n[1] + along * u[1])
        bb = d.textbbox((0, 0), txt, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        d.text((S * cx - w / 2 - bb[0], S * cy - h / 2 - bb[1]), txt, font=font, fill=color)
    return img.resize((size, size), Image.LANCZOS)


def main():
    cols = [(12, 0.205, 0.10, 0.31), (20, 0.205, 0.10, 0.31), (28, 0.205, 0.10, 0.30), (36, 0.200, 0.10, 0.29)]
    W, H = 240 * len(cols), 320
    canvas = Image.new("RGB", (W, H), (8, 12, 16))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT_B, 18)
    for i, (tilt, dist, along, fs) in enumerate(cols):
        x = 30 + i * 240
        big = make(180, tilt, dist=dist, along=along, fs=fs)
        canvas.paste(big, (x, 40), big)
        small = make(72, tilt, dist=dist, along=along, fs=fs)
        canvas.paste(small, (x + 108, 240), small)
        d.text((x, 12), "tilt %d deg" % tilt, font=f, fill=(140, 190, 190))
        d.text((x, 300), "180px / 72px", font=f, fill=(90, 130, 140))
    canvas.save(OUT)
    print("wrote", OUT, canvas.size)


if __name__ == "__main__":
    main()
