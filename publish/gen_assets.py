# -*- coding: utf-8 -*-
"""生成「点记 / TapTally」发布物料（AstroBox 资源社区 v2 布局）。

输出到 media/：
  icon.png        192x192  应用图标
  cover.png      1200x800  头图（3:2）
  preview-1.png   384x980  预览图 1（记分页「再滑确认」状态）
  preview-2.png   384x980  预览图 2（记分页 · 中缝时钟）
  preview-3.png   384x980  预览图 3（记分列表页）
另在 publish/ 输出 logo-512/256.png 备用的高清图标（本地备用，不入库）。
"""
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


def make_cover(W=1200, H=800):
    """封面：左侧文案 + 右侧两台带仿真机身的手环（记分页 / 记录页）。"""
    from gen_ui import score_screen, history_screen, frame as band_frame

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
        "中缝显示时间，上下双色分区一眼分清",
        "右→左划看记录，单击恢复 / 长按删除",
        "上滑两次归零存档（全行程防误触）",
    ]
    y = 320
    for t in lines:
        d.ellipse([88, y + 11, 100, y + 23], fill=(126, 224, 192, 255))
        d.text((120, y), t, font=f_body, fill=(214, 236, 232, 255))
        y += 60

    d.text((88, H - 88), "Xiaomi Smart Band 9 / Vela 快应用", font=f_body, fill=(120, 160, 160, 255))

    # ---- 右侧两台手环（带仿真机身边框）----
    shots = [
        ("记分页", band_frame(score_screen(12, 9)), 640, 645),
        ("记录页", band_frame(history_screen([(12, 9), (7, 11), (11, 5), (3, 3), (21, 18)])),
         500, 925),
    ]
    for cap, dev, th, x in shots:
        dev = dev.resize((int(dev.width * th / dev.height), th), Image.LANCZOS)
        yy = 700 - th
        img.alpha_composite(dev, (x, yy))
        bb = d.textbbox((0, 0), cap, font=f_cap)
        d.text((x + (dev.width - (bb[2] - bb[0])) / 2 - bb[0], yy + th + 18), cap,
               font=f_cap, fill=(150, 200, 195, 255))
    return img


def make_screen(top="12", bottom="9", scale=2, mid=None):
    """手环真实界面 192×490 的 scale 倍图（记分页）：界面由 gen_ui 渲染。

    不传 mid 时中缝显示时钟；传 `mid`（如「再滑确认」）时中缝改为提示文字，
    用来出「上滑一次、等待二次确认」这一状态。
    """
    from gen_ui import score_screen
    return score_screen(int(top), int(bottom), mid or "").resize((192 * scale, 490 * scale), Image.LANCZOS)


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
    print("wrote media/cover.png", cover.size)
    # preview-1 不再与封面重复：出「上滑一次 → 再滑确认」的状态，三张预览各看一页
    armed = make_screen("12", "9", 2, mid="再滑确认")
    armed.convert("RGB").save(os.path.join(MEDIA, "preview-1.png"))
    print("wrote media/preview-1.png", armed.size)
    screen = make_screen("12", "9", 2)
    screen.convert("RGB").save(os.path.join(MEDIA, "preview-2.png"))
    print("wrote media/preview-2.png", screen.size)
    from gen_ui import history_screen
    lst = history_screen([(12, 9), (7, 11), (11, 5), (3, 3), (21, 18)]).resize((384, 980), Image.LANCZOS)
    lst.convert("RGB").save(os.path.join(MEDIA, "preview-3.png"))
    print("wrote media/preview-3.png", lst.size)
