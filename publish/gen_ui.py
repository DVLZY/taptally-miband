# -*- coding: utf-8 -*-
"""把「点记」的每一个界面按源码一比一画出来，并套上手环 9 的真机边框。

为什么单独写一个脚本：`gen_cover.py` 是给社区源做头图的（构图优先），这个脚本
追求的是**像素级还原**——所有尺寸、圆角、字号、颜色都从 src/pages 里的常量抄过来：

    index.ux   : pad=0(胶囊屏) gap=dh*0.04 cardH=(usable-gap)/2 字号=min(卡宽/(0.6*位数)*0.96, 卡高*0.74, 430)
                 card radius 300（Vela 会夹到短边一半=240）cardW=480
                 mid 高=gap 字号=max(18, dh*0.0196)
    history.ux : pad=18 head 12% list 78% foot 10% itemH=max(64,min(150,dh*0.104))
                 noW=itemH*0.46 accentW=itemH*0.075 accentMl=itemH*0.06 accentMr=itemH*0.20
                 barH=itemH*0.52 valFs=itemH*0.66 noFs=itemH*0.52
                 titleFs=dh*0.036 dbgFs=dh*0.046 footFs=dh*0.036

输出：
    publish/ui/sheet.png          8 个界面 + 边框的总览图
    publish/ui/<name>.png         单张（3 倍图，576×1470 屏幕）
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "ui")

FB = r"C:\Windows\Fonts\msyhbd.ttc"
FR = r"C:\Windows\Fonts\msyh.ttc"

# ---------- 与源码一致的配色 ----------
BG = (7, 14, 18)
CARD_T, CARD_T_B = (127, 217, 183), (159, 240, 213)
CARD_B, CARD_B_B = (146, 205, 245), (191, 230, 255)
INK_T, INK_B = (6, 64, 44), (6, 58, 85)
MID_INK = (95, 201, 166)
ITEM_BG, ITEM_BRD = (16, 28, 35), (27, 41, 50)
ACC_A, ACC_B, ACC_D = (86, 217, 174), (108, 197, 243), (91, 113, 128)
NO_INK, VAL_INK = (109, 141, 156), (222, 238, 245)
TITLE_INK, DBG_INK, FOOT_INK = (214, 232, 235), (127, 217, 183), (79, 107, 120)

# ---------- 设计基准 ----------
DW = 480                 # designWidth（manifest.json）
SW, SH = 192, 490        # 手环 9 物理屏
DH = DW * SH / SW        # 1225 设计高
SS = 3                   # 超采样倍数


def font(path, size):
    return ImageFont.truetype(path, max(6, int(round(size))))


def center_text(d, box, text, f, fill):
    x0, y0, x1, y1 = box
    bb = d.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text((x0 + (x1 - x0 - w) / 2 - bb[0], y0 + (y1 - y0 - h) / 2 - bb[1]), text, font=f, fill=fill)


def rounded(d, box, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


# ---------- 一个屏幕 ----------
class Screen:
    """480×1225 设计坐标系里画，最后缩到 192×490。"""

    def __init__(self, bg=BG):
        self.k = SS
        self.img = Image.new("RGB", (int(DW * SS), int(DH * SS)), bg)
        self.d = ImageDraw.Draw(self.img)

    def px(self, v):
        return v * self.k

    def finish(self):
        return self.img.resize((SW * 4, SH * 4), Image.LANCZOS)


# ---------- 记分页 ----------
def score_metrics(pad_override=None):
    # 真机实测（1.7.2 照片）：卡片左右各留约 12%~15% 屏宽的空白，
    # 说明 device.getInfo().screenShape 在这台手环上返回的是 circle，
    # 于是 metricsOf 走了圆屏分支：pad = round(dw * 0.1465)。
    pad = round(DW * 0.1465) if pad_override is None else pad_override
    gap = round(DH * 0.04)       # 49
    usable = DH - pad * 2
    card_h = int((usable - gap) // 2)
    card_h2 = int(usable - gap - card_h)
    return pad, gap, card_h, card_h2, DW - pad * 2


def size_for(n, card_h, card_w):
    """与 index.ux 的 sizeFor 完全一致：按卡宽、卡高、430 三者取小。"""
    digits = len(str(n))
    by_w = card_w / (0.60 * digits) * 0.96
    by_h = card_h * 0.74
    return max(24, round(min(by_w, by_h, 430)))


def score_screen(top=0, bottom=0, mid="", radius=None, pad=None):
    pad, gap, card_h, card_h2, card_w = score_metrics(pad)
    s = Screen()
    k = s.k
    d = s.d
    mid_fs = max(18, round(DH * 0.0196))
    # 与 index.ux 保持一致：卡片圆角 170px（= 圆屏分支下的卡片半宽，与屏幕两端弧度一致）
    want = 170 if radius is None else radius
    r = min(want, (min(card_w, card_h) / 2))
    y = pad * k
    for (val, bg, brd, ink, h) in ((top, CARD_T, CARD_T_B, INK_T, card_h),
                                   (bottom, CARD_B, CARD_B_B, INK_B, card_h2)):
        rounded(d, [pad * k, y, (pad + card_w) * k, y + h * k], r * k, fill=bg, outline=brd, width=2 * k)
        fs = size_for(val, h, card_w)
        center_text(d, (pad * k, y, (pad + card_w) * k, y + h * k), str(val), font(FB, fs * k), ink)
        y += h * k + gap * k
    if mid:
        y0 = pad * k + card_h * k
        center_text(d, (0, y0, DW * k, y0 + gap * k), mid, font(FR, mid_fs * k), MID_INK)
    return s.finish()


# ---------- 记分列表页 ----------
def history_metrics():
    pad = round(DW * 0.1465)     # 70，与记分页同一个分支（circle）
    item_h = max(76, min(186, round(DH * 0.125)))
    return {
        "pad": pad,
        "itemH": item_h,
        "itemGap": round(item_h * 0.16),
        "barH": round(item_h * 0.52),
        "itemFs": round(item_h * 0.66),
        "noFs": max(24, round(item_h * 0.52)),
        "titleFs": max(24, round(DH * 0.036)),
        "dbgFs": max(40, round(DH * 0.046)),
        "footFs": max(30, round(DH * 0.036)),
        "accentW": max(6, round(item_h * 0.075)),
        "accentMl": round(item_h * 0.06),
        "accentMr": round(item_h * 0.20),
        "noW": round(item_h * 0.46),
        "valW": DW - pad * 2 - round(item_h * 0.40) - max(6, round(item_h * 0.075))
                - round(item_h * 0.06) - round(item_h * 0.20) - round(item_h * 0.08),
    }


def history_screen(records, dbg="", empty_text="还没有记录"):
    m = history_metrics()
    s = Screen()
    k = s.k
    d = s.d
    head_h, list_h, foot_h = DH * 0.12, DH * 0.78, DH * 0.10
    # 标题
    rounded(d, [0, 0, DW * k, head_h * k], 0, fill=BG)
    # .head 是 flex column 居中：标题一行，诊断串一行，两行合计正好落在 12% 内
    if dbg:
        block = m["titleFs"] * 1.45 + m["dbgFs"] * 1.45
        ty = (head_h - block) / 2
        center_text(d, (0, ty * k, DW * k, (ty + m["titleFs"] * 1.45) * k), "记录",
                    font(FB, m["titleFs"] * k), TITLE_INK)
        dy = ty + m["titleFs"] * 1.45
        center_text(d, (0, dy * k, DW * k, (dy + m["dbgFs"] * 1.45) * k), dbg,
                    font(FB, m["dbgFs"] * k), DBG_INK)
    else:
        center_text(d, (0, 0, DW * k, head_h * k), "记录", font(FB, m["titleFs"] * k), TITLE_INK)
    # 列表
    y = head_h
    if not records:
        center_text(d, (0, (head_h + 40) * k, DW * k, (head_h + 180) * k), empty_text,
                    font(FR, m["noFs"] * k), (79, 107, 120))
    for i, (t, b) in enumerate(records):
        x0, x1 = m["pad"] * k, (DW - m["pad"]) * k
        rounded(d, [x0, y * k, x1, (y + m["itemH"]) * k], 40 * k, fill=ITEM_BG, outline=ITEM_BRD, width=2 * k)
        side = ACC_A if t > b else (ACC_B if b > t else ACC_D)
        # flex 顺序：序号(noW) → 色条(margin-left, width, margin-right) → 比分
        ax = x0 + (m["noW"] + m["accentMl"]) * k
        ay = (y + (m["itemH"] - m["barH"]) / 2) * k
        rounded(d, [ax, ay, ax + m["accentW"] * k, ay + m["barH"] * k], 8 * k, fill=side)
        center_text(d, (x0, y * k, x0 + m["noW"] * k, (y + m["itemH"]) * k), str(i + 1),
                    font(FR, m["noFs"] * k), NO_INK)
        vx = ax + (m["accentW"] + m["accentMr"]) * k
        txt = "%d:%d" % (t, b)
        # 与 App 一致：比分越长字号越小，字宽≈0.62×字号
        val_fs = min(m["itemFs"], int(m["valW"] / (0.62 * len(txt))))
        center_text(d, (vx, y * k, vx + m["valW"] * k, (y + m["itemH"]) * k), txt,
                    font(FB, max(20, val_fs) * k), VAL_INK)
        y += m["itemH"] + m["itemGap"]
    # 页脚
    fy = DH - foot_h
    center_text(d, (0, fy * k, DW * k, DH * k), "单击恢复 · 长按删除", font(FR, m["footFs"] * k), FOOT_INK)
    return s.finish()


# ---------- 真机边框 ----------
def frame(screen_img, body=0.92):
    """给屏幕套上手环 9 的机身：深色机身、细边框、右侧按键、内外阴影。"""
    sw, sh = screen_img.size
    bez_x = int(sw * 0.032)
    bez_y = int(sh * 0.024)
    bw, bh = sw + bez_x * 2, sh + bez_y * 2
    pad = int(sw * 0.16)                     # 画布留白，放投影
    canvas = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    r_body = int(bw * 0.235)
    r_screen = int(sw * 0.19)

    # 投影
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [pad, pad + int(bh * 0.02), pad + bw, pad + bh + int(bh * 0.02)], radius=r_body, fill=(0, 0, 0, 210))
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(sw * 0.05)))
    canvas.alpha_composite(shadow)

    # 机身
    body_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(body_img)
    bd.rounded_rectangle([pad, pad, pad + bw, pad + bh], radius=r_body, fill=(14, 16, 18, 255),
                         outline=(46, 52, 58, 255), width=max(2, int(sw * 0.006)))
    # 机身高光
    bd.rounded_rectangle([pad + 2, pad + 2, pad + bw - 2, pad + bh - 2], radius=r_body - 2,
                         outline=(28, 33, 37, 255), width=max(1, int(sw * 0.003)))
    canvas.alpha_composite(body_img)

    # 屏幕（自己再裁一次圆角，机身内缘留一圈暗边）
    inner = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    mask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, sh - 1], radius=r_screen, fill=255)
    inner.paste(screen_img.convert("RGB"), (0, 0), mask)
    sx, sy = pad + bez_x, pad + bez_y
    canvas.alpha_composite(inner, (sx, sy))
    # 屏幕边缘的内阴影，让界面看起来是“陷进去”的
    rim = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.rounded_rectangle([0, 0, sw - 1, sh - 1], radius=r_screen, outline=(0, 0, 0, 90),
                         width=max(2, int(sw * 0.02)))
    rim = rim.filter(ImageFilter.GaussianBlur(int(sw * 0.02)))
    canvas.alpha_composite(rim, (sx, sy))

    # 右侧实体按键
    d = ImageDraw.Draw(canvas)
    bxo = pad + bw
    d.rounded_rectangle([bxo - 4, pad + int(bh * 0.30), bxo + int(sw * 0.028), pad + int(bh * 0.46)],
                        radius=int(sw * 0.014), fill=(38, 43, 48, 255))
    return canvas


# ---------- 排版 ----------
def label_strip(w, text):
    h = 64
    strip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    center_text(ImageDraw.Draw(strip), (0, 0, w, h), text, font(FR, 30), (150, 178, 190))
    return strip


def build():
    os.makedirs(OUT, exist_ok=True)
    shots = [
        ("score-default", "记分页 · 开局 0:0", score_screen(0, 0)),
        ("score-play", "记分页 · 对局中 12:9", score_screen(12, 9)),
        ("score-armed", "记分页 · 上滑一次（再滑确认）", score_screen(12, 9, "再滑确认")),
        ("score-3digit", "记分页 · 三位数 123:45", score_screen(123, 45)),
        ("score-saved", "记分页 · 归零后提示已存", score_screen(0, 0, "12:9 已存 3条")),
        ("list-full", "列表页 · 5 局（色条=胜方）", history_screen([(12, 9), (7, 11), (11, 5), (3, 3), (21, 18)])),
        ("list-empty", "列表页 · 空状态", history_screen([])),
        ("list-dbg", "列表页 · 长按标题看诊断", history_screen([(12, 9), (7, 11), (11, 5), (3, 3), (21, 18)], "S89 F89 N5")),
    ]
    framed = []
    for name, title, scr in shots:
        f = frame(scr)
        f.save(os.path.join(OUT, name + ".png"))
        framed.append((name, title, f))

    cols, gap, margin, top = 4, 56, 56, 128
    cw = max(f.width for _, _, f in framed)
    ch = max(f.height for _, _, f in framed) + 64
    rows = (len(framed) + cols - 1) // cols
    W = margin * 2 + cols * cw + (cols - 1) * gap
    H = top + rows * ch + margin
    sheet = Image.new("RGB", (W, H), (9, 14, 18))
    d = ImageDraw.Draw(sheet)
    d.text((margin, 40), "点记 TapTally · 全部界面（小米手环 9 / 192×490）", font=font(FB, 40), fill=(226, 240, 243))
    d.text((margin, 92), "按 src/pages 的尺寸、圆角、字号、配色一比一渲染，外套手环 9 机身边框", font=font(FR, 24), fill=(112, 140, 152))
    for i, (name, title, f) in enumerate(framed):
        r, c = divmod(i, cols)
        x = margin + c * (cw + gap) + (cw - f.width) // 2
        y = top + r * ch + (ch - 64 - f.height) // 2
        sheet.paste(f, (x, y), f)
        label_strip_img = label_strip(cw, title)
        sheet.paste(label_strip_img, (margin + c * (cw + gap), top + r * ch + ch - 64), label_strip_img)
    sheet.save(os.path.join(OUT, "sheet.png"))
    print("wrote", OUT)
    for name, _, f in framed:
        print("  %-14s %dx%d" % (name, f.width, f.height))
    print("  sheet", sheet.size)


def variants_pad():
    """留白对比：真机现在走圆屏分支（pad 70），这里给出 0 / 24 / 70 三档。"""
    os.makedirs(OUT, exist_ok=True)
    shots = [(0, "pad 0（铺满）"), (24, "pad 24（≈10 物理像素）"), (70, "pad 70（真机现状）")]
    imgs = [(t, frame(score_screen(2, 0, pad=p))) for p, t in shots]
    cw = max(i.width for _, i in imgs)
    ch = max(i.height for _, i in imgs) + 64
    gapx, margin, top = 48, 48, 96
    W = margin * 2 + len(imgs) * cw + (len(imgs) - 1) * gapx
    H = top + ch + margin
    sheet = Image.new("RGB", (W, H), (9, 14, 18))
    d = ImageDraw.Draw(sheet)
    d.text((margin, 34), "记分页留白对比 · 2:0（手环 9，192×490）", font=font(FB, 34), fill=(226, 240, 243))
    for i, (title, f) in enumerate(imgs):
        x = margin + i * (cw + gapx) + (cw - f.width) // 2
        sheet.paste(f, (x, top + (ch - 64 - f.height) // 2), f)
        center_text(d, (margin + i * (cw + gapx), top + ch - 56, margin + (i + 1) * (cw + gapx), top + ch), title,
                    font(FR, 26), (150, 178, 190))
    sheet.save(os.path.join(OUT, "pad-variants.png"))
    print("wrote pad-variants.png", sheet.size)


def variants():
    """圆角对比：卡片圆角越大，数字越容易被弧线切到。"""
    os.makedirs(OUT, exist_ok=True)
    shots = [(110, "110px（1.8.1）"), (160, "160px"), (170, "170px（1.8.2）"), (300, "300px（等效胶囊）")]
    imgs = [(t, frame(score_screen(12, 9, radius=r))) for r, t in shots]
    cw = max(i.width for _, i in imgs)
    ch = max(i.height for _, i in imgs) + 64
    gap, margin, top = 48, 48, 96
    W = margin * 2 + len(imgs) * cw + (len(imgs) - 1) * gap
    H = top + ch + margin
    sheet = Image.new("RGB", (W, H), (9, 14, 18))
    d = ImageDraw.Draw(sheet)
    d.text((margin, 34), "记分页圆角对比 · 12:9（手环 9，192×490）", font=font(FB, 34), fill=(226, 240, 243))
    for i, (title, f) in enumerate(imgs):
        x = margin + i * (cw + gap) + (cw - f.width) // 2
        sheet.paste(f, (x, top + (ch - 64 - f.height) // 2), f)
        center_text(d, (margin + i * (cw + gap), top + ch - 56, margin + (i + 1) * (cw + gap), top + ch), title,
                    font(FR, 26), (150, 178, 190))
    sheet.save(os.path.join(OUT, "radius-variants.png"))
    print("wrote radius-variants.png", sheet.size)


if __name__ == "__main__":
    build()
    variants()
    variants_pad()
