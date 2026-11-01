# -*- coding: utf-8 -*-
"""生成「点记 / TapTally」发布物料（AstroBox 资源社区 v2 布局）。

输出到 media/：
  icon.png        192x192  应用图标
  cover.png      1200x800  头图（3:2）
  preview-1.png  1200x800  预览图 1（与头图同图）
  preview-2.png   384x980  预览图 2（手环真实界面 192x490 的 2 倍图）
另在 publish/ 输出 logo-512/256.png 备用的高清图标。
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MEDIA = os.path.join(ROOT, "media")
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"

GREEN = (168, 230, 207, 255)
GREEN_C = (109, 216, 176)   # 渐变上端（偏深的薄荷绿）
BLUE_C = (146, 205, 245)    # 渐变下端（浅蓝）
BLUE = (179, 229, 252, 255)
DARK = (14, 20, 24, 255)
GREEN_TXT = (11, 107, 79, 255)
BLUE_TXT = (11, 79, 107, 255)
BG = (11, 26, 32, 255)


def rounded(size, radius, fill):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=fill)
    return img


def vgrad_circle(size, c_top, c_bot):
    """生成 size×size 的竖向线性渐变色块（RGB）。"""
    base = Image.new("RGB", (1, size))
    d = ImageDraw.Draw(base)
    for y in range(size):
        t = y / float(size - 1)
        d.point((0, y), fill=(
            int(c_top[0] + (c_bot[0] - c_top[0]) * t),
            int(c_top[1] + (c_bot[1] - c_top[1]) * t),
            int(c_top[2] + (c_bot[2] - c_top[2]) * t),
        ))
    return base.resize((size, size), Image.BILINEAR)


def make_logo(size, ss=4, digit_fs=0.576, stag=0.120, overlap=0.200, pad_ratio=0.120):
    """圆形图标：上绿下蓝竖向渐变（无分隔线）。

    数字布局按用户给的规则：
      · 左右错开 20% —— 两个数字的中心水平相距 0.20×边长（各自 ±0.10）
      · 上下重叠 20% —— 两个数字的字框竖直方向互相重叠 20% 字高
    字高用 PIL 实测的字框高度，所以换字号也不会错位；内容全部落在圆形安全区内。
    """
    S = size * ss
    grad = vgrad_circle(S, GREEN_C, BLUE_C).convert("RGBA")
    # 圆形四周留透明边距：手环列表里原生图标的视觉直径都比画布小一圈，
    # 我们自己画满会导致「图标比别家大一圈、把下面的应用名挤掉」
    pad = int(S * pad_ratio)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([pad, pad, S - 1 - pad, S - 1 - pad], fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    # 数字整体按内圆等比缩放：留白加大后，数字跟着缩小，避免压到圆弧外
    k = 1.0 - 2.0 * pad_ratio
    font = ImageFont.truetype(FONT_B, max(8, int(S * digit_fs * k)))
    bb0 = d.textbbox((0, 0), "0", font=font)
    bb9 = d.textbbox((0, 0), "9", font=font)
    h = max(bb0[3] - bb0[1], bb9[3] - bb9[1])
    dyc = 0.5 * (1.0 - overlap) * h       # 中心到中心的竖直距离
    off = stag * k                         # 水平错开（按内圆等比缩放）
    for txt, bb, cx, cy, color in (
            ("0", bb0, 0.5 - off, 0.5 - dyc / S, GREEN_TXT),
            ("9", bb9, 0.5 + off, 0.5 + dyc / S, BLUE_TXT)):
        w, hh = bb[2] - bb[0], bb[3] - bb[1]
        d.text((S * cx - w / 2 - bb[0], S * cy - hh / 2 - bb[1]), txt, font=font, fill=color)
    return img.resize((size, size), Image.LANCZOS)


def band_mock(W, H):
    """手环屏幕示意：贴边两片卡片 + 圆角=半宽（与 App 的 240px 圆角一致）。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gap = max(2, int(H * 0.040))       # App: round(dh*0.04)
    card_h = (H - gap) // 2            # App: (dh - gap) / 2，pad=0
    r = W // 2                         # App: border-radius 240 ≈ 屏宽 480 的一半
    top = [0, 0, W, card_h]
    bot = [0, card_h + gap, W, H]
    d.rounded_rectangle(top, radius=r, fill=GREEN)
    d.rounded_rectangle(bot, radius=r, fill=BLUE)
    for txt, box, color, n in (("12", top, GREEN_TXT, 2), ("9", bot, BLUE_TXT, 1)):
        # 与 index.ux 的 sizeFor 同构：受卡宽/卡高/圆角内缩三者约束
        fs = _size_for(n, card_h, W, W / 2.0)
        font = ImageFont.truetype(FONT_B, int(fs * W / 480.0))
        bb = d.textbbox((0, 0), txt, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        cx = (box[0] + box[2]) / 2 - w / 2 - bb[0]
        cy = (box[1] + box[3]) / 2 - h / 2 - bb[1]
        d.text((cx, cy), txt, font=font, fill=color)
    # 屏幕是胶囊形：整体按胶囊裁一刀，卡片两端才会跟着收成屏幕的弧度
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=W // 2, fill=255)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def _size_for(n, card_h, card_w, r):
    """复刻 src/pages/index/index.ux 的 sizeFor（含圆角内缩迭代）。"""
    import math
    d = len(str(n))
    by_h = card_h * 0.74
    f = min(card_w / (0.60 * d) * 0.96, by_h, 430 * card_w / 480.0)
    for _ in range(3):
        half_h = f * 0.36
        straight = card_h / 2 - r
        inset = 0.0
        if half_h > straight:
            kk = half_h - max(0.0, straight)
            q = r * r - kk * kk
            inset = r - (math.sqrt(q) if q > 0 else 0.0)
        avail = card_w - inset * 2
        f = min(f, avail / (0.60 * d) * 0.96, by_h)
    return max(24.0, f)


def make_cover(W=1200, H=800):
    """封面：左侧文案 + 右侧两台带仿真机身的手环（记分页 / 记录页）。"""
    from gen_radius_style import score_screen_raw, frame as band_frame

    img = Image.new("RGBA", (W, H), BG)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-W * 0.25, -H * 0.55, W * 0.75, H * 0.75], fill=(168, 230, 207, 34))
    gd.ellipse([W * 0.45, H * 0.15, W * 1.25, H * 1.35], fill=(179, 229, 252, 30))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    logo = make_logo(180)
    img.alpha_composite(logo, (80, 92))

    f_title = ImageFont.truetype(FONT_B, 104)
    f_sub = ImageFont.truetype(FONT_B, 32)
    f_body = ImageFont.truetype(FONT_R, 30)
    f_cap = ImageFont.truetype(FONT_R, 27)

    d.text((290, 86), "点记", font=f_title, fill=(255, 255, 255, 255))
    d.text((298, 232), "TapTally · 对局计分", font=f_sub, fill=GREEN)

    lines = [
        "单击 +1 / 长按 −1，短震反馈",
        "上绿下蓝双色分区，比分一眼看清",
        "右→左划看记录，单击恢复 / 长按删除",
        "上滑两次归零存档，左→右划退出",
    ]
    y = 320
    for t in lines:
        d.ellipse([88, y + 11, 100, y + 23], fill=(126, 224, 192, 255))
        d.text((120, y), t, font=f_body, fill=(214, 236, 232, 255))
        y += 60

    d.text((88, H - 88), "Xiaomi Smart Band 9 / Vela 快应用", font=f_body, fill=(120, 160, 160, 255))

    # ---- 右侧两台手环（带仿真机身边框）----
    shots = [
        ("记分页", band_frame(score_screen_raw("12", "9", 0, 240)), 560, 660),
        ("记录页", band_frame(make_list_screen([(12, 9), (7, 11), (11, 5), (3, 3), (21, 18)], 3)),
         512, 928),
    ]
    for cap, dev, th, x in shots:
        dev = dev.resize((int(dev.width * th / dev.height), th), Image.LANCZOS)
        yy = 96 + (560 - th) // 2
        img.alpha_composite(dev, (x, yy))
        bb = d.textbbox((0, 0), cap, font=f_cap)
        d.text((x + (dev.width - (bb[2] - bb[0])) / 2 - bb[0], yy + th + 22), cap,
               font=f_cap, fill=(150, 200, 195, 255))
    return img


def make_screen(top="12", bottom="9", scale=2):
    """手环真实界面 192x490 的 scale 倍图（记分页）：贴边卡片 + 圆角 240。"""
    W, H = 192 * scale, 490 * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    gap = int(round(H * 0.040))
    card_h = (H - gap) // 2
    r = W // 2
    for val, box in ((top, [0, 0, W, card_h]), (bottom, [0, card_h + gap, W, H])):
        d.rounded_rectangle(box, radius=r, fill=GREEN if box[0] == 0 and box[1] == 0 else BLUE)
        fs = _size_for(len(str(val)), card_h, W, W / 2.0)
        font = ImageFont.truetype(FONT_B, int(fs * W / 480.0))
        bb = d.textbbox((0, 0), val, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        cx = (box[0] + box[2]) / 2 - w / 2 - bb[0]
        cy = (box[1] + box[3]) / 2 - h / 2 - bb[1]
        d.text((cx, cy), val, font=font, fill=GREEN_TXT if box[1] == 0 else BLUE_TXT)
    return img


def make_list_screen(rows, scale=2):
    """列表页（192x490）：标题 + 5 条记录 + 页脚，参数取自 history.ux。"""
    W, H = 192 * scale, 490 * scale
    dh = 1225.0
    k = H / dh                                  # 设计 → 出图
    img = Image.new("RGBA", (W, H), (7, 14, 18, 255))
    d = ImageDraw.Draw(img)
    pad = int(round(14 * k))
    head_h = int(H * 0.12)
    item_h = max(64, min(180, round(dh * 0.125))) * k
    no_fs = int(max(24, round(dh * 0.125 * 0.52)) * k)
    val_fs = int(round(dh * 0.125 * 0.66) * k)
    title_fs = int(max(24, round(dh * 0.036)) * k)
    foot_fs = int(max(30, round(dh * 0.036)) * k)
    # 标题
    f_t = ImageFont.truetype(FONT_B, title_fs)
    bb = d.textbbox((0, 0), "记录", font=f_t)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], head_h * 0.35), "记录", font=f_t, fill=(214, 232, 235, 255))
    # 条目
    y = head_h
    f_no = ImageFont.truetype(FONT_R, no_fs)
    f_val = ImageFont.truetype(FONT_B, val_fs)
    for i, (a, b) in enumerate(rows[:5]):
        row = [pad, int(y), W - pad, int(y + item_h)]
        d.rounded_rectangle(row, radius=int(30 * k), fill=(16, 28, 35, 255), outline=(27, 41, 50, 255), width=max(1, int(2 * k)))
        side = (86, 217, 174, 255) if a > b else ((108, 197, 243, 255) if b > a else (91, 113, 128, 255))
        bar_h = int(item_h * 0.52)
        d.rectangle([pad + int(item_h * 0.46) + int(item_h * 0.06),
                     int(y + (item_h - bar_h) / 2),
                     pad + int(item_h * 0.46) + int(item_h * 0.06) + max(3, int(item_h * 0.075)),
                     int(y + (item_h + bar_h) / 2)], fill=side)
        bb = d.textbbox((0, 0), str(i + 1), font=f_no)
        d.text((pad + (item_h * 0.46 - (bb[2] - bb[0])) / 2 - bb[0],
                y + (item_h - (bb[3] - bb[1])) / 2 - bb[1]), str(i + 1), font=f_no, fill=(109, 141, 156, 255))
        txt = "%d:%d" % (a, b)
        bb = d.textbbox((0, 0), txt, font=f_val)
        d.text(((W - (bb[2] - bb[0])) / 2 - bb[0] + int(item_h * 0.17),
                y + (item_h - (bb[3] - bb[1])) / 2 - bb[1]), txt, font=f_val, fill=(222, 238, 245, 255))
        y += item_h + int(item_h * 0.16)
    # 页脚
    f_f = ImageFont.truetype(FONT_R, foot_fs)
    bb = d.textbbox((0, 0), "单击恢复 · 长按删除", font=f_f)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], H - int(H * 0.115)), "单击恢复 · 长按删除", font=f_f, fill=(79, 107, 120, 255))
    return img


if __name__ == "__main__":
    os.makedirs(MEDIA, exist_ok=True)
    # 应用商店/社区源的图标：192，靠 12% 留白把视觉直径压到 ~146
    make_logo(192, pad_ratio=0.120).convert("RGBA").save(os.path.join(MEDIA, "icon.png"))
    print("wrote media/icon.png 192x192 (pad 12%)")

    # 手环应用列表用的图标：画布 100（原生 App 就是 100，例如水平仪 test_level.rpk），
    # 只留 3% 透明边。画布尺寸会参与启动器排版——128 的画布会把下方 App 名挤出去，
    # 视觉直径保持在 ~94（128x0.76≈97 与原生一致）。
    make_logo(100, pad_ratio=0.050).convert("RGBA").save(
        os.path.join(HERE, "..", "src", "common", "logo.png"))
    print("wrote src/common/logo.png 100x100 (pad 7.5%)")
    for s in (512, 256):
        p = os.path.join(HERE, "logo-%d.png" % s)
        make_logo(s).save(p)
        print("wrote", p)
    cover = make_cover()
    cover.convert("RGB").save(os.path.join(MEDIA, "cover.png"))
    cover.convert("RGB").save(os.path.join(MEDIA, "preview-1.png"))
    print("wrote media/cover.png + preview-1.png", cover.size)
    screen = make_screen("12", "9", 2)
    screen.convert("RGB").save(os.path.join(MEDIA, "preview-2.png"))
    print("wrote media/preview-2.png", screen.size)
    lst = make_list_screen([(12, 9), (7, 11), (11, 5), (3, 3), (21, 18)], 2)
    lst.convert("RGB").save(os.path.join(MEDIA, "preview-3.png"))
    print("wrote media/preview-3.png", lst.size)
