# -*- coding: utf-8 -*-
"""记分页「上下半区圆角」候选样式（只出图，不改代码）。

思路：手环 9 的屏幕是胶囊形，两端本身就是半圆（屏宽 192 → 圆角半径 = 96 物理像素）。
把卡片圆角也做成屏幕的那种弧度，并且让卡片边缘贴着屏幕边缘，
卡片弧线和屏幕弧线就是同心的，看起来才"是一体的"。

设计坐标按 480×1225（App 里的 designWidth），物理 192×490，换算 ×0.4。
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"

DW, DH = 480, 1225          # 设计尺寸
SCALE = 3                    # 输出放大倍数（设计 px → 出图 px）
BG = (7, 14, 18)
BODY = (16, 20, 24)
CARD_T = (127, 217, 183)
CARD_B = (146, 205, 245)
INK_T = (11, 107, 79)
INK_B = (11, 79, 107)


def font(path, size):
    return ImageFont.truetype(path, size)


def size_for(val, card_h, card_w, r):
    """与 src/pages/index/index.ux 的 sizeFor 同构：把圆角造成的宽度内缩算进去。"""
    import math
    d = len(str(val))
    by_h = card_h * 0.74
    f = min(card_w / (0.60 * d) * 0.96, by_h, 430)
    for _ in range(3):
        half_h = f * 0.36
        straight = card_h / 2 - r
        inset = 0.0
        if half_h > straight:
            kk = half_h - max(0, straight)
            q = r * r - kk * kk
            inset = r - (math.sqrt(q) if q > 0 else 0)
        avail = card_w - inset * 2
        f = min(f, avail / (0.60 * d) * 0.96, by_h, 430)
    return max(24, round(f))


def center_text(d, box, text, f, fill):
    x0, y0, x1, y1 = box
    bb = d.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((x0 + x1 - w) / 2 - bb[0], (y0 + y1 - h) / 2 - bb[1]), text, font=f, fill=fill)


def score_screen(top, bottom, pad, radius, k=SCALE):
    """pad：卡片到屏幕左右边缘的距离（设计 px）；radius：卡片圆角（设计 px）。"""
    img = Image.new("RGB", (int(DW * k), int(DH * k)), BG)
    d = ImageDraw.Draw(img)
    gap = int(round(DH * 0.04 * k))
    usable = int(DH * k) - pad * 2 * k - gap
    c1 = usable // 2
    c2 = usable - c1
    cw = int(DW * k) - pad * 2 * k
    x0 = pad * k
    r = radius * k
    y = pad * k
    for val, h, color, ink in ((top, c1, CARD_T, INK_T), (bottom, c2, CARD_B, INK_B)):
        d.rounded_rectangle([x0, y, x0 + cw, y + h], radius=r, fill=color)
        fs = size_for(val, h / k, cw / k, radius) * k
        center_text(d, (x0, y, x0 + cw, y + h), str(val), font(FONT_B, fs), ink)
        y += h + gap
    return img


def score_screen_raw(top, bottom, pad, radius, k=SCALE):
    img = Image.new("RGB", (int(DW * k), int(DH * k)), BG)
    d = ImageDraw.Draw(img)
    gap = int(round(DH * 0.04 * k))
    usable = int(DH * k) - pad * 2 * k - gap
    c1 = usable // 2
    c2 = usable - c1
    cw = int(DW * k) - pad * 2 * k
    x0 = pad * k
    r = radius * k
    y = pad * k
    for val, h, color, ink in ((top, c1, CARD_T, INK_T), (bottom, c2, CARD_B, INK_B)):
        d.rounded_rectangle([x0, y, x0 + cw, y + h], radius=r, fill=color)
        fs = size_for(val, h / k, cw / k, radius) * k
        center_text(d, (x0, y, x0 + cw, y + h), str(val), font(FONT_B, fs), ink)
        y += h + gap
    return img


def frame(screen, k=SCALE):
    """套胶囊机身：屏幕圆角 = 屏宽一半（真机那块屏就是胶囊）。"""
    sw, sh = screen.size
    bez_x = int(sw * 0.035)
    bez_y = int(sh * 0.022)
    W, H = sw + bez_x * 2, sh + bez_y * 2
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    # 机身：手环 9 本体也是胶囊形（两端半圆），不是圆角矩形
    br = W // 2
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=br, fill=BODY + (255,))
    d.rounded_rectangle([2, 2, W - 3, H - 3], radius=br, outline=(96, 106, 116, 255), width=4)
    # 屏幕（胶囊：圆角 = 半宽）
    mask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, sh - 1], radius=sw // 2, fill=255)
    body.paste(screen, (bez_x, bez_y), mask)
    # 屏幕内高光
    hl = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle([0, 0, sw - 1, int(sh * 0.35)], radius=sw // 2, fill=(255, 255, 255, 12))
    body.alpha_composite(hl, (bez_x, bez_y))
    # 右侧按键
    d2 = ImageDraw.Draw(body)
    d2.rounded_rectangle([W - 4, int(H * 0.36), W + 6, int(H * 0.52)], radius=6, fill=(44, 50, 58, 255))
    return body


VARIANTS = [
    ("2:0", [("2", "0"), (0, 240)]),
    ("12:9", [("12", "9"), (0, 240)]),
    ("123:45", [("123", "45"), (0, 240)]),
]


def main():
    shots = [(name, frame(score_screen(int(t[0]) if t[0].isdigit() else 0, 0, 0, 240)),
              ) for name, (t, _) in []] or []
    shots = []
    for name, (pair, (pad, r)) in VARIANTS:
        a, b = pair
        shots.append((name, frame(score_screen_raw(a, b, pad, r))))
    cw = max(s.width for _, s in shots)
    ch = max(s.height for _, s in shots)
    gapx, margin, top = 44, 48, 92
    W = margin * 2 + len(shots) * cw + (len(shots) - 1) * gapx
    H = top + ch + margin + 20
    sheet = Image.new("RGB", (W, H), (38, 44, 50))
    d = ImageDraw.Draw(sheet)
    d.text((margin, 26), "记分页 · 上下半区圆角候选（小米手环9 / 192×490 / 得分 2:0）",
           font=font(FONT_B, 34), fill=(232, 240, 244))
    for i, (name, s) in enumerate(shots):
        x = margin + i * (cw + gapx) + (cw - s.width) // 2
        sheet.paste(s, (x, top), s)
        center_text(d, (margin + i * (cw + gapx), top + ch + 16, margin + (i + 1) * (cw + gapx), top + ch + 60),
                    name, font(FONT_R, 26), (150, 178, 190))
    out = os.path.join(OUT, "..", "publish", "ui", "radius-style.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
