# -*- coding: utf-8 -*-
"""生成「图标在画布里的大小」三档对比，用来在真机上选一个合适的占比。

留白 pad_ratio p 时，圆形直径占画布 (1-2p)：
    p=0.15 -> 70%   p=0.10 -> 80%   p=0.05 -> 90%
手环 9 实测：70% 标题正常但偏小；94%（p=0.03）标题被遮挡。
"""
import os
from PIL import Image, ImageDraw, ImageFont
import gen_assets as ga

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [(0.15, "70%  1.6.6"), (0.10, "80%  本版"), (0.05, "90%  偏大")]
TILE = 180
LABEL_H = 76
W = 60 + len(STEPS) * (TILE + 40)
H = 60 + TILE + LABEL_H
img = Image.new("RGB", (W, H), (10, 18, 24))
d = ImageDraw.Draw(img)
fb = ImageFont.truetype(ga.FONT_B, 26)
for i, (p, name) in enumerate(STEPS):
    ic = ga.make_logo(TILE, pad_ratio=p).convert("RGBA")
    x = 30 + i * (TILE + 40)
    img.paste(ic, (x, 40), ic)
    d.text((x, 40 + TILE + 16), name, font=fb, fill=(200, 225, 232))
out = os.path.join(HERE, "logo-size-steps.png")
img.save(out)
print("wrote", out, img.size)
