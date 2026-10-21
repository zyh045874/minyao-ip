# -*- coding: utf-8 -*-
"""第2期《安和桥》首帧样图：硬钩子大字放中上部（避开底部UI），720x1280 与成片同分辨率"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "assets", "cover_raw",
                  "竖构图电影感人像摄影_夏日黄昏的金色阳光里_一个年轻女孩半侧_2026-10-21T04-37-26.png")
OUT = os.path.join(ROOT, "assets", "第2期_首帧_方案.png")

W, H = 720, 1280
F = r"C:\Windows\Fonts\simhei.ttf"
FK = r"C:\Windows\Fonts\STKAITI.TTF"

bg = Image.open(BG).convert("RGB")
s = max(W / bg.width, H / bg.height)
bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
x0 = (bg.width - W) // 2
canvas = bg.crop((x0, 0, x0 + W, H)).convert("RGBA")

# 顶部由深到透的渐变压暗（保证中上部大字可读）
grad = Image.new("L", (1, H), 0)
for y in range(H):
    if y < 540:
        grad.putpixel((0, y), int(170 * (1 - y / 540) ** 0.85))
shade = Image.new("RGBA", (W, H), (6, 8, 18, 255))
shade.putalpha(grad.resize((W, H)))
canvas = Image.alpha_composite(canvas, shade)
draw = ImageDraw.Draw(canvas)

def ctext(y, text, font, fill, stroke=0, sfill=(0, 0, 0, 220), tracking=0):
    widths = [draw.textlength(c, font=font) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (W - total) / 2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return y

# 栏目小标
ctext(78, "歌 词 里 的 心 事 · 第 2 期", ImageFont.truetype(FK, 30), (255, 226, 192, 235), tracking=2)

# 三行硬钩子
ctext(150, "越长大", ImageFont.truetype(F, 86), (255, 252, 248, 255), stroke=5)
ctext(258, "越不敢听", ImageFont.truetype(F, 86), (255, 252, 248, 255), stroke=5)
ctext(366, "《安和桥》", ImageFont.truetype(F, 88), (255, 214, 160, 255), stroke=5)

canvas.convert("RGB").save(OUT, quality=95)
print("saved:", OUT)
