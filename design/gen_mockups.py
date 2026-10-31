# -*- coding: utf-8 -*-
"""生成「点记」界面风格方案图（主页面 192x490 的两倍图 384x980）。"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = r"E:\AIAgent\DeepSeekHarness\Default\ScoreBoard-Band9-vela\design"
os.makedirs(OUT, exist_ok=True)

FB = r"C:\Windows\Fonts\msyhbd.ttc"   # 粗体
FR = r"C:\Windows\Fonts\msyh.ttc"     # 常规

DESIGN_W, DESIGN_H = 480, 1225
OUT_W, OUT_H = 384, 980
S = 3  # 超采样倍数


def vgrad(w, h, c1, c2):
    """垂直渐变"""
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return img.resize((w, h), Image.BILINEAR)


def font(path, size):
    return ImageFont.truetype(path, size)


def center_text(d, box, text, fnt, fill):
    x0, y0, x1, y1 = box
    b = d.textbbox((0, 0), text, font=fnt)
    tw, th = b[2] - b[0], b[3] - b[1]
    d.text(((x0 + x1 - tw) / 2 - b[0], (y0 + y1 - th) / 2 - b[1]), text, font=fnt, fill=fill)


def base_canvas(bg):
    return Image.new("RGB", (DESIGN_W * S, DESIGN_H * S), bg)


def sc(x):
    return int(x * S)


# ---------------- 现状 ----------------
def draw_now():
    W, H = DESIGN_W * S, DESIGN_H * S
    img = base_canvas((0, 0, 0))
    d = ImageDraw.Draw(img)
    half = 0.48
    hh = int(H * half)
    bar = H - 2 * hh
    d.rectangle([0, 0, W, hh], fill=(168, 230, 207))
    d.rectangle([0, hh + bar, W, H], fill=(179, 229, 252))
    d.rectangle([0, hh, W, hh + bar], fill=(16, 26, 30))
    f = font(FB, sc(300))
    center_text(d, (0, 0, W, hh), "12", f, (11, 107, 79))
    center_text(d, (0, hh + bar, W, H), "9", f, (11, 79, 107))
    fb = font(FR, sc(26))
    center_text(d, (0, hh, W, hh + bar), "重置", fb, (126, 224, 192))
    return img


# ---------------- 方案 A：浅色极简 ----------------
def draw_a():
    W, H = DESIGN_W * S, DESIGN_H * S
    img = Image.new("RGB", (W, H), (255, 255, 255))
    top = vgrad(W, H // 2, (233, 249, 242), (168, 230, 207))
    bot = vgrad(W, H - H // 2, (179, 229, 252), (226, 244, 254))
    img.paste(top, (0, 0))
    img.paste(bot, (0, H // 2))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, H // 2 - sc(2), W, H // 2 + sc(2)], fill=(12, 32, 40, 90))
    f = font(FR, sc(300))
    center_text(d, (0, 0, W, H // 2 - sc(60)), "12", f, (14, 92, 68))
    center_text(d, (0, H // 2 + sc(60), W, H), "9", f, (16, 74, 100))
    fh = font(FR, sc(24))
    center_text(d, (0, H - sc(96), W, H - sc(48)), "上滑两次归零 · 右滑退出", fh, (90, 130, 140, 210))
    return img


# ---------------- 方案 B：深色卡片 ----------------
def draw_b():
    W, H = DESIGN_W * S, DESIGN_H * S
    img = base_canvas((9, 17, 22))
    d = ImageDraw.Draw(img, "RGBA")
    # 背景光斑
    glow = Image.new("RGB", (W, H), (9, 17, 22))
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.ellipse([-sc(160), -sc(220), sc(360), sc(300)], fill=(24, 74, 62, 255))
    gd.ellipse([sc(140), H - sc(320), W + sc(180), H + sc(200)], fill=(18, 56, 82, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(sc(120)))
    img = glow
    d = ImageDraw.Draw(img, "RGBA")
    gap = sc(40)
    half = (H - gap) // 2
    r = sc(46)
    ins = sc(28)
    # 卡片
    d.rounded_rectangle([sc(18), sc(18), W - sc(18), half - ins], radius=r,
                        fill=(18, 33, 39, 255), outline=(120, 210, 180, 70), width=sc(3))
    d.rounded_rectangle([sc(18), half + ins, W - sc(18), H - sc(18)], radius=r,
                        fill=(15, 29, 37, 255), outline=(120, 190, 240, 70), width=sc(3))
    f = font(FB, sc(250))
    d.text((0, 0), "", font=f)  # noop
    center_text(d, (0, sc(18), W, half - ins), "12", f, (150, 240, 205))
    center_text(d, (0, half + ins, W, H - sc(18)), "9", f, (150, 210, 250))
    fs = font(FR, sc(24))
    d.text((sc(46), sc(46)), "P1", font=fs, fill=(120, 200, 172, 200))
    d.text((sc(46), half + ins + sc(28)), "P2", font=fs, fill=(130, 186, 226, 200))
    center_text(d, (0, half - ins, W, half + ins), "上滑两次归零", fs, (110, 150, 165, 220))
    return img


# ---------------- 方案 C：饱和渐变发光 ----------------
def draw_c():
    W, H = DESIGN_W * S, DESIGN_H * S
    bar = sc(10)
    hh = (H - bar) // 2
    img = Image.new("RGB", (W, H), (0, 0, 0))
    t = vgrad(W, hh, (86, 217, 174), (196, 245, 231))
    b = vgrad(W, hh, (199, 240, 255), (111, 200, 245))
    img.paste(t, (0, 0))
    img.paste(b, (0, hh + bar))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, hh, W, hh + bar], fill=(8, 20, 26))
    # 光晕
    for txt, fill, box, color in (
        ("12", None, (0, 0, W, hh), (5, 58, 38)),
        ("9", None, (0, hh + bar, W, H), (6, 54, 79)),
    ):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        f = font(FB, sc(310))
        center_text(ld, box, txt, f, (255, 255, 255, 120))
        layer = layer.filter(ImageFilter.GaussianBlur(sc(14)))
        img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
        center_text(d, box, txt, f, color)
    fh = font(FR, sc(24))
    center_text(d, (0, hh - sc(52), W, hh + sc(4)), "上滑两次归零", fh, (255, 255, 255, 190))
    return img


def save(img, name):
    small = img.resize((OUT_W, OUT_H), Image.LANCZOS)
    p = os.path.join(OUT, name)
    small.save(p)
    print("wrote", p)
    return small


def draw_list(kind):
    W, H = DESIGN_W * S, DESIGN_H * S
    light = kind == "light"
    bg = (244, 249, 252) if light else (10, 18, 22)
    img = base_canvas(bg)
    d = ImageDraw.Draw(img, "RGBA")
    fh = font(FB, sc(40))
    d.text((sc(36), sc(48)), "比分记录", font=fh, fill=(18, 40, 50) if light else (225, 235, 240))
    fs = font(FR, sc(22))
    d.text((W - sc(36) - sc(150), sc(64)), "最近 10 条", font=fs,
           fill=(120, 145, 155) if light else (110, 140, 155))

    rows = [("12 : 9", "刚刚"), ("7 : 11", "21:40"), ("11 : 5", "21:12"),
            ("3 : 3", "20:58"), ("15 : 13", "20:31"), ("9 : 9", "19:47"),
            ("21 : 18", "19:05")]
    y = sc(150)
    ih = sc(96)
    gap = sc(14)
    fi = font(FR, sc(26))
    fsc = font(FB, sc(46))
    ft = font(FR, sc(22))
    for i, (score, t) in enumerate(rows):
        top, bot = y, y + ih
        if light:
            d.rounded_rectangle([sc(28), top, W - sc(28), bot], radius=sc(24),
                                fill=(255, 255, 255), outline=(224, 236, 243), width=sc(2))
            acc = (168, 230, 207) if i % 2 == 0 else (179, 229, 252)
            d.rounded_rectangle([sc(28), top, sc(28) + sc(8), bot], radius=sc(4), fill=acc)
            tcol, sc_col, icol = (35, 60, 70), (16, 70, 96), (150, 170, 180)
        else:
            d.rounded_rectangle([sc(28), top, W - sc(28), bot], radius=sc(24), fill=(20, 33, 42))
            acc = (120, 220, 185) if i % 2 == 0 else (120, 190, 240)
            d.rounded_rectangle([sc(28), top, sc(28) + sc(8), bot], radius=sc(4), fill=acc)
            tcol, sc_col, icol = (200, 215, 222), (215, 240, 250), (100, 130, 145)
        d.text((sc(60), top + sc(34)), str(i + 1), font=fi, fill=icol)
        center_text(d, (sc(60), top, W - sc(150), bot), score, fsc, sc_col)
        d.text((W - sc(130), top + sc(36)), t, font=ft, fill=icol)
        y = bot + gap
    # 顶部提示
    center_text(d, (0, H - sc(70), W, H - sc(24)), "单击恢复 · 双击删除", fs,
                (130, 155, 165) if light else (110, 140, 155))
    return img


FM = r"C:\Windows\Fonts\consolab.ttf"  # 等宽（Consolas Bold），仅用于示意


def draw_d():
    """方案 D = C 的渐变配色 + 圆角卡片 + 等宽数字 + 无中间文字提示"""
    W, H = DESIGN_W * S, DESIGN_H * S
    img = base_canvas((7, 14, 18))
    d = ImageDraw.Draw(img, "RGBA")
    gap = sc(22)
    half = (H - gap) // 2
    m = sc(16)
    r = sc(48)
    box_top = [m, m, W - m, half - sc(8)]
    box_bot = [m, half + sc(8), W - m, H - m]

    for box, c1, c2 in ((box_top, (58, 199, 156), (206, 245, 232)),
                        (box_bot, (206, 243, 255), (108, 197, 243))):
        gw, gh = box[2] - box[0], box[3] - box[1]
        g = vgrad(gw, gh, c1, c2)
        mask = Image.new("L", (gw, gh), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, gw - 1, gh - 1], radius=r, fill=255)
        img.paste(g, (box[0], box[1]), mask)
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle(box, radius=r, outline=(255, 255, 255, 26), width=sc(3))

    f = font(FM, sc(272))
    center_text(d, box_top, "12", f, (10, 66, 46))
    center_text(d, box_bot, "9", f, (8, 62, 92))
    return img


def draw_list_d():
    """列表页跟随主页：深色底 + 圆角卡片 + 渐变左侧色条"""
    W, H = DESIGN_W * S, DESIGN_H * S
    img = base_canvas((7, 14, 18))
    d = ImageDraw.Draw(img, "RGBA")
    fh = font(FR, sc(38))
    d.text((sc(34), sc(44)), "记录", font=fh, fill=(214, 232, 235))
    fs = font(FR, sc(22))
    d.text((W - sc(34) - sc(110), sc(58)), "最近 10 条", font=fs, fill=(110, 140, 155))

    rows = [("12:9", "刚刚"), ("7:11", "21:40"), ("11:5", "21:12"),
            ("3:3", "20:58"), ("15:13", "20:31"), ("9:9", "19:47"),
            ("21:18", "19:05")]
    y = sc(130)
    ih = sc(92)
    ft = font(FR, sc(22))
    fsc = font(FM, sc(44))
    for i, (score, t) in enumerate(rows):
        top, bot = y, y + ih
        d.rounded_rectangle([sc(24), top, W - sc(24), bot], radius=sc(26),
                            fill=(16, 28, 35, 255), outline=(255, 255, 255, 22), width=sc(2))
        # 左侧色条（上绿下蓝交替）
        acc = (86, 217, 174) if i % 2 == 0 else (108, 197, 243)
        d.rounded_rectangle([sc(24), top + sc(16), sc(24) + sc(9), bot - sc(16)],
                            radius=sc(6), fill=acc)
        d.text((sc(54), top + sc(32)), str(i + 1), font=ft, fill=(96, 126, 140))
        center_text(d, (sc(80), top, W - sc(150), bot), score, fsc, (222, 240, 248))
        d.text((W - sc(126), top + sc(34)), t, font=ft, fill=(96, 126, 140))
        y = bot + sc(12)
    center_text(d, (0, H - sc(64), W, H - sc(20)), "单击恢复 · 长按删除", fs, (104, 132, 146))
    return img


def save_sheet2(panels, name):
    pad, lab = 28, 44
    w = pad + sum(p.width + pad for p, _ in panels)
    h = pad + OUT_H + lab
    sheet = Image.new("RGB", (w, h), (24, 26, 30))
    sd = ImageDraw.Draw(sheet)
    fl = font(FR, 26)
    x = pad
    for p, label in panels:
        sheet.paste(p, (x, pad))
        sd.text((x + 4, pad + OUT_H + 8), label, font=fl, fill=(210, 214, 220))
        x += p.width + pad
    path = os.path.join(OUT, name)
    sheet.save(path)
    print("wrote", path, sheet.size)


if __name__ == "__main__":
    panels = []
    for fn, name, label in (
        (draw_now, "mock-now.png", "现状"),
        (draw_a, "mock-A.png", "方案A 浅色极简"),
        (draw_b, "mock-B.png", "方案B 深色卡片"),
        (draw_c, "mock-C.png", "方案C 渐变发光"),
    ):
        panels.append((save(fn(), name), label))

    save_sheet2(panels, "compare.png")

    lp = [(save(draw_list("light"), "mock-list-light.png"), "记分列表 · 浅色"),
          (save(draw_list("dark"), "mock-list-dark.png"), "记分列表 · 深色")]
    save_sheet2(lp, "compare-list.png")

    dp = [(save(draw_c(), "mock-C.png"), "方案C 渐变发光（参考）"),
          (save(draw_d(), "mock-D.png"), "方案D 定稿：C配色+圆角卡片+等宽"),
          (save(draw_list_d(), "mock-list-D.png"), "列表页（跟随主页）")]
    save_sheet2(dp, "compare-final.png")

def draw_final():
    """最终实现稿：纯色圆角卡片 + 系统字体大数字 + 无渐变、无发光、无中间文字"""
    W, H = DESIGN_W * S, DESIGN_H * S
    img = base_canvas((7, 14, 18))
    d = ImageDraw.Draw(img, "RGBA")
    pad = sc(14)
    mid = sc(int(DESIGN_H * 0.04))
    r = sc(52)
    half = (H - pad * 2 - mid) // 2
    box_top = [pad, pad, W - pad, pad + half]
    box_bot = [pad, pad + half + mid, W - pad, H - pad]
    d.rounded_rectangle(box_top, radius=r, fill=(127, 217, 183), outline=(159, 240, 213), width=sc(2))
    d.rounded_rectangle(box_bot, radius=r, fill=(146, 205, 245), outline=(191, 230, 255), width=sc(2))
    # 字号按 sizeFor：<10 -> 400, <100 -> 350, else 210
    f2 = font(FB, sc(350))
    f1 = font(FB, sc(400))
    center_text(d, box_top, "12", f2, (6, 64, 44))
    center_text(d, box_bot, "9", f1, (6, 58, 85))
    return img
