# -*- coding: utf-8 -*-
"""图标预览：各尺寸落在手环深色背景上，并模拟圆形裁切，检查裁切后是否缺角。"""
import os
from PIL import Image, ImageDraw
import gen_assets as ga

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "logo-preview.png")


def circle_crop(img):
    S = img.size[0]
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S - 1, S - 1], fill=255)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def main():
    sizes = [192, 120, 96, 64, 44]
    W, H = 900, 420
    img = Image.new("RGB", (W, H), (8, 12, 16))
    d = ImageDraw.Draw(img)
    d.text((28, 18), "Band 9 circular icon check", fill=(150, 200, 200))
    x = 40
    for s in sizes:
        logo = ga.make_logo(s)
        img.paste(circle_crop(logo), (x, 70), circle_crop(logo))
        d.text((x, 70 + s + 10), "%dpx" % s, fill=(120, 170, 170))
        x += s + 44
    # 右半：浅色背景对照
    light = Image.new("RGB", (W, 200), (238, 244, 246))
    dl = ImageDraw.Draw(light)
    x = 40
    for s in (96, 64, 44):
        logo = ga.make_logo(s)
        light.paste(circle_crop(logo), (x, 60), circle_crop(logo))
        dl.text((x, 60 + s + 8), "%dpx" % s, fill=(90, 120, 130))
        x += s + 50
    dl.text((440, 18), "on light background", fill=(90, 120, 130))
    canvas = Image.new("RGB", (W, H + 200), (8, 12, 16))
    canvas.paste(img, (0, 0))
    canvas.paste(light, (0, H))
    canvas.save(OUT)
    print("wrote", OUT, canvas.size)


if __name__ == "__main__":
    main()
