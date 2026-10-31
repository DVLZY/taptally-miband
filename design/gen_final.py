# -*- coding: utf-8 -*-
"""生成最终实现稿预览图（纯色圆角卡片 + 系统字体大数字）"""
import gen_mockups as g

if __name__ == "__main__":
    p = g.save(g.draw_final(), "mock-final.png")
    print("wrote", p)
