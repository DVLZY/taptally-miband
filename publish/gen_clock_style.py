# -*- coding: utf-8 -*-
"""记分页：加宽中缝 + 在缝隙里显示时间（只出效果图，不改代码）。

需求理解（待确认）：
  · 中缝宽度 4% → 8%（设计 49 → 98px，≈ 物理 20 → 39px）
  · 缝隙中央显示当前时间 HH:MM，整体水平居中
  · 小时的第一位、分钟的最后一位字号大；剩下两位（小时的个位、分钟的十位）字号小

设计坐标 480×1225，物理 192×490（×0.4）。
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"

DW, DH = 480, 1225
K = 3
BG = (7, 14, 18)
CARD_T = (127, 217, 183)
CARD_B = (146, 205, 245)
INK_T = (11, 107, 79)
INK_B = (11, 79, 107)
CLOCK = (176, 224, 214)


def font(path, size):
    return ImageFont.truetype(path, size)


def center_text(d, box, text, f, fill):
    x0, y0, x1, y1 = box
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=f, fill=fill, anchor="mm")


def size_for(n, card_h, card_w, r):
    dgt = len(str(n))
    by_h = card_h * 0.74
    f = min(card_w / (0.60 * dgt) * 0.96, by_h, 430)
    for _ in range(3):
        half_h = f * 0.36
        straight = card_h / 2 - r
        inset = 0.0
        if half_h > straight:
            kk = half_h - max(0.0, straight)
            q = r * r - kk * kk
            inset = r - (math.sqrt(q) if q > 0 else 0.0)
        f = min(f, (card_w - inset * 2) / (0.60 * dgt) * 0.96, by_h)
    return max(24.0, f)


def clock_split(img, W, cy, hh, mm, big, small, margin, ink=(255, 255, 255), H=None):
    """中缝时钟：小时靠左、分钟靠右，无冒号。

    两个要点（都是用户提的）：
      1. 小时十位 / 分钟个位用大字号，另外两位用小字号；
      2. **每个数字各自按墨迹上下居中**，不是共用一条基线——
         共用基线时小字会贴在下面，看着像"踩在同一条下划线上"。
         做法：textbbox 取每个字形的墨迹上下界，逐字算 y，再落笔。
    """
    d = ImageDraw.Draw(img)
    fb, fs = font(FONT_B, int(big * K)), font(FONT_B, int(small * K))
    groups = [
        ([(hh[0], fb), (hh[1], fs)], margin, "l"),
        ([(mm[0], fs), (mm[1], fb)], W - margin, "r"),
    ]
    for parts, anchor_x, align in groups:
        widths = [d.textlength(t, font=f) for t, f in parts]
        x = anchor_x if align == "l" else anchor_x - sum(widths)
        for (t, f), w in zip(parts, widths):
            bb = d.textbbox((0, 0), t, font=f)
            y = cy - (bb[1] + bb[3]) / 2.0          # 墨迹中心对齐到 cy
            d.text((x, y), t, font=f, fill=ink, anchor="la")
            x += w


def clock_row(d, cx, cy, hh, mm, big, small, ink=CLOCK):
    """把 HH:MM 居中画在 (cx, cy) 上：第 1、4 位用 big，第 2、3 位和冒号用 small。"""
    fb, fs = font(FONT_B, int(big * K)), font(FONT_B, int(small * K))
    parts = [(hh[0], fb), (hh[1], fs), (":", fs), (mm[0], fs), (mm[1], fb)]
    widths = [d.textlength(t, font=f) for t, f in parts]
    x = cx - sum(widths) / 2
    # 数字统一落在一条基线上（anchor="ls"），冒号稍微下移做视觉居中
    ascent = fb.getmetrics()[0]
    base_y = cy + (fb.getmetrics()[0] + fb.getmetrics()[1]) / 2 - fb.getmetrics()[1] * 0.5
    for (txt, f), w in zip(parts, widths):
        if txt == ":":
            d.text((x + w / 2, base_y - ascent * 0.30), txt, font=f, fill=ink, anchor="ms")
        else:
            d.text((x + w / 2, base_y), txt, font=f, fill=ink, anchor="ms")
        x += w


def score_screen(gap_ratio, clock=None, big=60, small=42, margin=24, hint="", top="12", bottom="9"):
    W, H = int(DW * K), int(DH * K)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    gap = int(round(DH * gap_ratio)) * K
    card_h = (H - gap) // 2
    card_w = W
    r = W // 2
    for val, y, color, ink in ((top, 0, CARD_T, INK_T), (bottom, card_h + gap, CARD_B, INK_B)):
        d.rounded_rectangle([0, y, card_w, y + card_h], radius=r, fill=color)
        n = len(str(val))
        fs = min(0.86 * (card_w / K) / (0.617 * n), 0.62 * (card_h / K), 430) * K
        center_text(d, (0, y, card_w, y + card_h), val, font(FONT_B, int(fs)), ink)
    if clock:
        hh, mm = clock
        clock_split(img, W, card_h + gap / 2, hh, mm, big, small, int(margin * K), H=H)
    if hint:
        hint_fs = max(int(30 * K), int(gap * 0.30))
        center_text(d, (0, card_h + gap / 2 - 15 * K, W, card_h + gap / 2 + 15 * K),
                    hint, font(FONT_B, hint_fs), (126, 224, 192))
    # 胶囊屏幕裁切
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=W // 2, fill=255)
    out = Image.new("RGB", (W, H), (0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def frame(screen):
    sw, sh = screen.size
    bx, by = int(sw * 0.035), int(sh * 0.022)
    W, H = sw + bx * 2, sh + by * 2
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    br = W // 2
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=br, fill=(18, 22, 26, 255))
    d.rounded_rectangle([2, 2, W - 3, H - 3], radius=br, outline=(96, 106, 116, 255), width=4)
    mask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, sh - 1], radius=sw // 2, fill=255)
    body.paste(screen, (bx, by), mask)
    d2 = ImageDraw.Draw(body)
    d2.rounded_rectangle([W - 4, int(H * 0.36), W + 8, int(H * 0.52)], radius=6, fill=(44, 50, 58, 255))
    return body


VARIANTS = [
    ("C · 中缝13% 190/122（逐字居中）", dict(gap_ratio=0.13, clock=("21", "47"), big=190, small=122, margin=16)),
    ("C2 · 中缝12% 175/112", dict(gap_ratio=0.12, clock=("21", "47"), big=175, small=112, margin=20)),
    ("C3 · 中缝13% 小字更小 190/100", dict(gap_ratio=0.13, clock=("21", "47"), big=190, small=100, margin=16)),
    ("提示态 · 中缝13%，时间隐藏", dict(gap_ratio=0.13, clock=None, hint="再滑确认")),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    shots = [(t, frame(score_screen(**kw))) for t, kw in VARIANTS]
    cw = max(s.width for _, s in shots)
    ch = max(s.height for _, s in shots)
    gapx, margin, top = 40, 48, 92
    W = margin * 2 + len(shots) * cw + (len(shots) - 1) * gapx
    H = top + ch + margin + 44
    sheet = Image.new("RGB", (W, H), (38, 44, 50))
    d = ImageDraw.Draw(sheet)
    d.text((margin, 28), "记分页 · 中缝加宽 + 时间显示（手环9 / 192×490）",
           font=font(FONT_B, 34), fill=(232, 240, 244))
    for i, (name, s) in enumerate(shots):
        x = margin + i * (cw + gapx) + (cw - s.width) // 2
        sheet.paste(s, (x, top), s)
        center_text(d, (margin + i * (cw + gapx), top + ch + 14, margin + (i + 1) * (cw + gapx), top + ch + 52),
                    name, font(FONT_R, 26), (158, 184, 196))
    out = os.path.join(OUT, "clock-style.png")
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
