# -*- coding: utf-8 -*-
"""生成 AstroBox 社区源封面（1200×800，严格 3:2）。

思路（对应官方《资源封面指南》的「图文左右分栏」）：
  · 左侧：品牌标 + 一句主张 + 三条卖点 + 设备/价格标签
  · 右侧：两台手环的**真实界面渲染**（记分页 / 记分记录页），带机身边框与投影

界面不是画的示意图，而是按 src/pages 里的尺寸、圆角、配色、字号一比一渲染，
所以「所见即所得」——装到手上就是这张图里的样子。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MEDIA = os.path.join(ROOT, "media")

FB = r"C:\Windows\Fonts\msyhbd.ttc"   # 雅黑 Bold
FR = r"C:\Windows\Fonts\msyh.ttc"     # 雅黑 Regular

# 与 App 一致的配色
BG_APP = (7, 14, 18)
CARD_T = (127, 217, 183)
CARD_T_B = (159, 240, 213)
CARD_B = (146, 205, 245)
CARD_B_B = (191, 230, 255)
INK_T = (11, 107, 79)
INK_B = (11, 79, 107)
ITEM_BG = (15, 29, 37)
ACC_A = (86, 217, 174)
ACC_B = (108, 197, 243)

# 设计基准（与 index.ux 相同：设计宽 480，手环 9 屏 192×490 -> 设计高 1225）
DW, DH = 480, 1225


def font(path, size):
    return ImageFont.truetype(path, max(6, int(size)))


def center_text(d, box, text, f, fill):
    x0, y0, x1, y1 = box
    bb = d.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text((x0 + (x1 - x0 - w) / 2 - bb[0], y0 + (y1 - y0 - h) / 2 - bb[1]), text, font=f, fill=fill)


def render_score_page(ss=3):
    """记分页：两张 110px 圆角卡片，上绿下蓝，比分 12 : 9。"""
    W, H = DW * ss, DH * ss
    img = Image.new("RGB", (W, H), BG_APP)
    d = ImageDraw.Draw(img)
    pad, gap = 14 * ss, 49 * ss
    card_h = (H - 2 * pad - gap) // 2
    card_w = W - 2 * pad
    r = 110 * ss
    for top, bg, brd, txt, ink, val in (
            (True, CARD_T, CARD_T_B, "12", INK_T, "12"),
            (False, CARD_B, CARD_B_B, "9", INK_B, "9")):
        y0 = pad if top else pad + card_h + gap
        d.rounded_rectangle([pad, y0, pad + card_w, y0 + card_h], radius=r,
                            fill=bg, outline=brd, width=2 * ss)
        # 与 index.ux 的 sizeFor() 同一套公式：min(卡宽/(0.6×位数)×0.96, 卡高×0.74, 430)
        fs = min(card_w / (0.6 * len(val)) * 0.96, card_h * 0.74, 430 * ss) / ss
        center_text(d, (pad, y0, pad + card_w, y0 + card_h), val, font(FB, fs * ss), ink)
    return img.resize((192, 490), Image.LANCZOS)


def render_history_page(ss=3):
    """记分记录页：标题 + 5 条记录（序号左侧、比分居中）。"""
    W, H = DW * ss, DH * ss
    img = Image.new("RGB", (W, H), BG_APP)
    d = ImageDraw.Draw(img)
    pad = 14 * ss
    head_h = int(H * 0.12)
    list_h = int(H * 0.78)
    center_text(d, (0, 0, W, head_h), "记录", font(FB, DH * 0.036 * ss), (232, 245, 242))

    item_h = int(H * 0.104)
    rows = [("12", "9"), ("7", "11"), ("11", "5"), ("3", "3"), ("8", "6")]
    y = head_h + 6 * ss
    for i, (t, b) in enumerate(rows):
        if y + item_h > head_h + list_h:
            break
        d.rounded_rectangle([pad, y, W - pad, y + item_h - 8 * ss], radius=int(item_h * 0.26),
                            fill=ITEM_BG, outline=(34, 56, 68), width=1 * ss)
        # 左侧色条
        bw = int(item_h * 0.055)
        d.rounded_rectangle([pad + item_h * 0.12, y + item_h * 0.22,
                             pad + item_h * 0.12 + bw, y + item_h * 0.78 - 8 * ss],
                            radius=bw // 2, fill=ACC_A if i % 2 == 0 else ACC_B)
        # 序号
        d.text((pad + item_h * 0.30, y + item_h * 0.22), str(i + 1),
               font=font(FR, item_h * 0.30), fill=(120, 143, 155))
        # 比分
        val = "%s:%s" % (t, b)
        center_text(d, (pad + item_h * 0.9, y, W - pad, y + item_h - 8 * ss), val,
                    font(FB, item_h * 0.62), (238, 246, 244))
        y += item_h
    center_text(d, (0, int(H * 0.88), W, H), "单击恢复 · 长按删除",
                font(FR, DH * 0.024 * ss), (96, 122, 134))
    return img.resize((192, 490), Image.LANCZOS)


def device(screen, bezel=10, radius=34):
    """把 192×490 的界面装进手环机身（深色边框 + 圆角 + 高光）。"""
    s = 3  # 超采样
    bw, bh = (192 + bezel * 2) * s, (490 + bezel * 2) * s
    dev = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(dev)
    # 机身
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=(radius + bezel) * s,
                        fill=(12, 18, 22, 255), outline=(46, 62, 72, 255), width=2 * s)
    # 屏幕
    sc = screen.resize((192 * s, 490 * s), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", sc.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sc.size[0] - 1, sc.size[1] - 1],
                                           radius=radius * s, fill=255)
    dev.paste(sc, (bezel * s, bezel * s), mask)
    # 左上高光
    hl = Image.new("RGBA", dev.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle([2 * s, 2 * s, bw - 2 * s, bh - 2 * s],
                                         radius=(radius + bezel) * s,
                                         outline=(255, 255, 255, 26), width=2 * s)
    dev = Image.alpha_composite(dev, hl)
    return dev.resize((192 + bezel * 2, 490 + bezel * 2), Image.LANCZOS)


def shadow(img, blur=26, alpha=120, dy=18):
    a = img.split()[3].point(lambda v: min(255, int(v * alpha / 255)))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(a)
    pad = blur * 2
    big = Image.new("RGBA", (img.size[0] + pad * 2, img.size[1] + pad * 2), (0, 0, 0, 0))
    big.paste(sh, (pad, pad + dy), sh)
    return big.filter(ImageFilter.GaussianBlur(blur)), pad


def vgrad(w, h, top, bottom):
    g = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(g)
    for y in range(h):
        k = y / max(1, h - 1)
        d.point((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return g.resize((w, h), Image.BILINEAR)


def logo(size):
    """圆形渐变图标：上绿下蓝，0 左上、9 右下（与 src/common/logo.png 同款）。"""
    ss = 4
    S = size * ss
    inner = vgrad(S, S, (109, 216, 176), (146, 205, 245)).convert("RGBA")
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S - 1, S - 1], fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(inner, (0, 0), mask)
    d = ImageDraw.Draw(img)
    f = font(FB, S * 0.44)
    for txt, cx, cy, col in (("0", 0.40, 0.33, (18, 92, 70)), ("9", 0.60, 0.67, (17, 68, 90))):
        bb = d.textbbox((0, 0), txt, font=f)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        d.text((S * cx - w / 2 - bb[0], S * cy - h / 2 - bb[1]), txt, font=f, fill=col)
    return img.resize((size, size), Image.LANCZOS)


def build():
    W, H = 1200, 800
    bg = vgrad(W, H, (10, 22, 29), (16, 38, 50)).convert("RGBA")
    # 右上大光斑
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 620, -260, W + 180, 460], fill=(38, 122, 108, 78))
    gd.ellipse([-220, H - 320, 420, H + 220], fill=(28, 78, 116, 64))
    bg = Image.alpha_composite(bg, glow.filter(ImageFilter.GaussianBlur(90)))

    # 细网格
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdd = ImageDraw.Draw(grid)
    for x in range(0, W, 40):
        gdd.line([(x, 0), (x, H)], fill=(255, 255, 255, 5))
    for y in range(0, H, 40):
        gdd.line([(0, y), (W, y)], fill=(255, 255, 255, 5))
    bg = Image.alpha_composite(bg, grid)

    d = ImageDraw.Draw(bg)

    # ── 左侧品牌 ─────────────────────────────
    ic = logo(112)
    sh, pad = shadow(ic, blur=20, alpha=110, dy=14)
    bg.alpha_composite(sh, (72 - pad, 74 - pad))
    bg.alpha_composite(ic, (72, 74))
    d = ImageDraw.Draw(bg)
    d.text((206, 74), "点记", font=font(FB, 92), fill=(233, 245, 242))
    d.text((210, 186), "TapTally · 对局计分", font=font(FR, 34), fill=(126, 217, 192))

    # ── 主标题 ───────────────────────────────
    d.text((72, 276), "手腕上的", font=font(FB, 66), fill=(233, 245, 242))
    d.text((72, 358), "对局计分板", font=font(FB, 66), fill=(126, 217, 192))

    # ── 卖点 ─────────────────────────────────
    bullets = [
        ("单击 +1 · 长按 −1", "短震确认，戴着手套也能盲操"),
        ("上滑两次归零", "自动存进最近 5 局，随时翻回来"),
        ("单击恢复 · 长按删除", "接着上次的比分继续打"),
    ]
    y = 470
    for title, sub in bullets:
        d.ellipse([76, y + 13, 88, y + 25], fill=(126, 217, 192))
        d.text((104, y), title, font=font(FB, 32), fill=(232, 244, 241))
        d.text((104, y + 40), sub, font=font(FR, 25), fill=(122, 148, 160))
        y += 82

    # ── 底部标签 ─────────────────────────────
    tag = "小米手环 9 / 9 NFC · 免费"
    tw = d.textlength(tag, font=font(FR, 27))
    d.rounded_rectangle([72, 716, 72 + 22 + tw + 22, 768], radius=26,
                        fill=(22, 46, 56), outline=(46, 84, 96), width=2)
    d.text((94, 728), tag, font=font(FR, 27), fill=(141, 196, 183))

    # ── 右侧设备 ─────────────────────────────
    score = device(render_score_page())
    hist = device(render_history_page())

    # 轻微旋转制造层次
    def rot(im, deg, scale=1.0):
        im2 = im.resize((int(im.size[0] * scale), int(im.size[1] * scale)), Image.LANCZOS)
        return im2.rotate(deg, resample=Image.BICUBIC, expand=True)

    hist_r = rot(hist, -7, 0.90)
    score_r = rot(score, 5, 0.93)

    for im, pos in ((hist_r, (694, 132)), (score_r, (946, 176))):
        sh, pad = shadow(im, blur=30, alpha=150, dy=24)
        bg.alpha_composite(sh, (pos[0] - pad, pos[1] - pad))
        bg.alpha_composite(im, pos)

    out = bg.convert("RGB")
    p = os.path.join(MEDIA, "cover.png")
    out.save(p, optimize=True)
    print("wrote", p, out.size, os.path.getsize(p), "bytes")
    # 预览图：封面本身 + 两张真实界面
    out.save(os.path.join(MEDIA, "preview-1.png"), optimize=True)
    top = Image.new("RGB", (384, 980), BG_APP)
    top.paste(render_score_page(ss=2).resize((384, 980), Image.LANCZOS), (0, 0))
    top.save(os.path.join(MEDIA, "preview-2.png"), optimize=True)
    hist_big = render_history_page(ss=2).resize((384, 980), Image.LANCZOS)
    hist_big.save(os.path.join(MEDIA, "preview-3.png"), optimize=True)
    print("wrote previews")


if __name__ == "__main__":
    build()
