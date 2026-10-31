"""画「卡片圆角」对比图：52 / 90 / 110 / 140 设计像素，输出 design/radius-compare.png。

画布按手环9 的真实比例：480 设计宽 × 1225 设计高（= 192×490 物理屏等比放大），
最后缩小到 384×980 输出，方便在电脑上看。
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'design', 'radius-compare.png')
FB = r'C:\Windows\Fonts\msyhbd.ttc'

DW, DH = 480, 1225
SW, SH = 384, 980
S = 3


def sc(v):
    return int(round(v * S))


def center_text(d, box, txt, font, fill):
    x0, y0, x1, y1 = box
    bb = d.textbbox((0, 0), txt, font=font)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((x0 + x1) / 2 - w / 2 - bb[0], (y0 + y1) / 2 - h / 2 - bb[1]), txt, font=font, fill=fill)


def frame(radius):
    W, H = sc(DW), sc(DH)
    img = Image.new('RGB', (W, H), (7, 14, 18))
    d = ImageDraw.Draw(img)
    pad = sc(18)
    gap = sc(round(DH * 0.04))
    cardH = (DH - 2 * 18 - round(DH * 0.04)) // 2
    f = ImageFont.truetype(FB, sc(370))
    top = [pad, sc(18), W - pad, sc(18) + sc(cardH)]
    bot = [pad, sc(18) + sc(cardH) + gap, W - pad, sc(18) + sc(cardH) * 2 + gap]
    for box, color, txt, tcol in ((top, (127, 217, 183), '12', (11, 80, 60)),
                                  (bot, (146, 205, 245), '9', (10, 62, 90))):
        d.rounded_rectangle(box, radius=sc(radius), fill=color)
        center_text(d, box, txt, f, tcol)
    return img.resize((SW, SH), Image.LANCZOS)


def main():
    radii = [52, 90, 110, 140]
    frames = [frame(r) for r in radii]
    pad = 16
    W = (SW + pad) * len(frames) + pad
    H = SH + 64
    sheet = Image.new('RGB', (W, H), (24, 26, 30))
    d = ImageDraw.Draw(sheet)
    fl = ImageFont.truetype(FB, 30)
    for i, (r, im) in enumerate(zip(radii, frames)):
        x = pad + i * (SW + pad)
        sheet.paste(im, (x, 48))
        d.text((x + 4, 8), f'圆角 {r}px' + ('（当前 1.5.3）' if r == 52 else ''), font=fl, fill=(220, 230, 235))
    sheet.save(OUT)
    print('wrote', OUT, sheet.size)


if __name__ == '__main__':
    main()
