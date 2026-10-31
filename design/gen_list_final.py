# -*- coding: utf-8 -*-
"""1.3.0 列表页预览：只展示序号 + 比分，时间降序（最新在最上）。"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"

W, H = 480, 1225      # 手环 9 设计画布
S = 2                 # 超采样
DW, DH = W * S, H * S
OUT = os.path.join(HERE, "mock-list-final.png")


def sc(x):
    return int(round(x * S))


def main():
    img = Image.new("RGB", (DW, DH), (7, 14, 18))
    d = ImageDraw.Draw(img)
    pad = sc(10)
    dh = H
    itemH = sc(max(60, min(132, round(dh * 0.092))))
    itemR = sc(round(itemH / S * 0.26))
    barH = sc(round(itemH / S * 0.55))
    accentW = sc(max(6, round(itemH / S * 0.085)))
    accentMl = sc(round(itemH / S * 0.20))
    noW = sc(round(itemH / S * 0.36))
    noMl = sc(round(itemH / S * 0.12))
    valFs = sc(round(itemH / S * 0.54))
    noFs = sc(max(16, round(itemH / S * 0.26)))
    titleFs = sc(max(20, round(dh * 0.032)))

    f_title = ImageFont.truetype(FONT_R, titleFs)
    f_no = ImageFont.truetype(FONT_R, noFs)
    f_val = ImageFont.truetype(FONT_B, valFs)

    head_h = int(DH * 0.09)
    d.text((sc(22), int(head_h / 2 - titleFs * 0.62)), "记录", font=f_title, fill=(214, 232, 235))
    cnt = "7 / 10"
    bb = d.textbbox((0, 0), cnt, font=f_no)
    d.text((DW - sc(22) - (bb[2] - bb[0]), int(head_h / 2 - noFs * 0.62)), cnt, font=f_no, fill=(110, 140, 155))

    rows = ["12:9", "7:11", "11:5", "3:3", "15:13", "9:9", "21:18"]
    y = head_h
    for i, s in enumerate(rows):
        x0, x1 = pad, DW - pad
        d.rounded_rectangle([x0, y, x1, y + itemH], radius=itemR, fill=(16, 28, 35), outline=(27, 41, 50), width=sc(2))
        cx = x0 + accentMl
        col = (86, 217, 174) if i % 2 == 0 else (108, 197, 243)
        d.rounded_rectangle([cx, y + (itemH - barH) // 2, cx + accentW, y + (itemH + barH) // 2],
                            radius=sc(4), fill=col)
        nx = cx + accentW + noMl
        bb = d.textbbox((0, 0), str(i + 1), font=f_no)
        d.text((nx + (noW - (bb[2] - bb[0])) / 2 - bb[0], y + (itemH - (bb[3] - bb[1])) / 2 - bb[1]),
               str(i + 1), font=f_no, fill=(96, 128, 143))
        vx = nx + noW
        vw = x1 - sc(round(itemH / S * 0.10)) - vx
        bb = d.textbbox((0, 0), s, font=f_val)
        d.text((vx + (vw - (bb[2] - bb[0])) / 2 - bb[0], y + (itemH - (bb[3] - bb[1])) / 2 - bb[1]),
               s, font=f_val, fill=(222, 238, 245))
        y += itemH + sc(12)

    f_foot = ImageFont.truetype(FONT_R, noFs)
    ft = "单击恢复 · 长按删除"
    bb = d.textbbox((0, 0), ft, font=f_foot)
    d.text(((DW - (bb[2] - bb[0])) / 2, DH - int(DH * 0.07) + (int(DH * 0.07) - (bb[3] - bb[1])) / 2 - bb[1]),
           ft, font=f_foot, fill=(79, 107, 120))

    img.resize((W * 4 // 5, H * 4 // 5), Image.LANCZOS).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
