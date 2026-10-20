# -*- coding: utf-8 -*-
"""第1期封面 v2：雨夜路灯底图 + 电影感文字排版（1080x1920）"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "assets", "cover_raw",
                  "电影感竖构图剧照_深夜的老街巷口_一个穿深色大衣的年轻人背影_2026-10-20T06-54-04.png")
OUT = os.path.join(ROOT, "assets", "第1期_封面_第一眼_v2.png")

W, H = 1080, 1920
F_TITLE = r"C:\Windows\Fonts\simhei.ttf"      # 黑体：大标题
F_KAI   = r"C:\Windows\Fonts\STKAITI.TTF"    # 楷体：歌词句
F_SANS  = r"C:\Windows\Fonts\simhei.ttf"     # 黑体：辅助信息

# ---------- 底图：等比放大至盖满 1080x1920，居中裁切 ----------
bg = Image.open(BG).convert("RGB")
s = max(W / bg.width, H / bg.height)
bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
x0 = (bg.width - W) // 2
canvas = bg.crop((x0, 0, x0 + W, H)).convert("RGBA")

# ---------- 上下渐变压暗，保证文字可读 ----------
grad = Image.new("L", (1, H), 0)
for y in range(H):
    if y < 380:
        v = int(110 * (1 - y / 380))
    elif y > H - 480:
        v = int(150 * ((y - (H - 480)) / 480))
    else:
        v = 0
    grad.putpixel((0, y), v)
shade = Image.new("RGBA", (W, H), (8, 10, 22, 255))
shade.putalpha(grad.resize((W, H)))
canvas = Image.alpha_composite(canvas, shade)

draw = ImageDraw.Draw(canvas)

def center_text(y, text, font, fill, tracking=0, shadow=None):
    """水平居中绘制（可选字距与柔和阴影），返回文字底部 y"""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (W - total) / 2
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + 4), text, font=font, fill=shadow)
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        canvas.alpha_composite(sh)
    draw.text((x, y), text, font=font, fill=fill)
    return y + max(draw.textbbox((0, 0), ch, font=font)[3] for ch in text)

# ---------- 顶部栏目 ----------
brand_font = ImageFont.truetype(F_SANS, 40)
center_text(130, "歌 词 里 的 心 事", brand_font, (255, 232, 205, 235), tracking=10)
draw.line([(W/2 - 150, 215), (W/2 - 40, 215)], fill=(255, 190, 120, 160), width=2)
draw.line([(W/2 + 40, 215), (W/2 + 150, 215)], fill=(255, 190, 120, 160), width=2)
draw.ellipse([W/2 - 4, 211, W/2 + 4, 219], fill=(255, 200, 140, 220))

# ---------- 大标题「第一眼」：暖光晕 + 白字 ----------
title = "第一眼"
tf = ImageFont.truetype(F_TITLE, 250)
tracking = 26
tw = sum(draw.textlength(c, font=tf) for c in title) + tracking * (len(title) - 1)
tx, ty = (W - tw) / 2, 950

# 光晕层：暖橘多层模糊
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gx = tx
for c in title:
    gd.text((gx, ty), c, font=tf, fill=(255, 150, 60, 200))
    gx += draw.textlength(c, font=tf) + tracking
for r, alpha in [(30, 1.0), (16, 1.0)]:
    g = glow.filter(ImageFilter.GaussianBlur(r))
    canvas.alpha_composite(g)
canvas.alpha_composite(glow)  # 一层不模糊的暖色打底

# 白字 + 细描边
gx = tx
for c in title:
    draw.text((gx, ty), c, font=tf, fill=(12, 14, 24, 255),
              stroke_width=4, stroke_fill=(12, 14, 24, 255))
    draw.text((gx, ty), c, font=tf, fill=(255, 252, 246, 255))
    gx += draw.textlength(c, font=tf) + tracking

# ---------- 标题下装饰短线 ----------
draw.line([(W/2 - 90, 1330), (W/2 + 90, 1330)], fill=(255, 190, 120, 200), width=3)

# ---------- 勾人副句（楷体） ----------
kf = ImageFont.truetype(F_KAI, 62)
center_text(1380, "后来我们走散在人海", kf, (255, 240, 222, 250), shadow=(0, 0, 0, 180))
center_text(1470, "再也复制不了的那一眼", kf, (255, 240, 222, 250), shadow=(0, 0, 0, 180))

# ---------- 底部出处 ----------
sf = ImageFont.truetype(F_SANS, 38)
center_text(1795, "程艾影 × 南山南", sf, (232, 195, 150, 220), tracking=6)

canvas.convert("RGB").save(OUT, quality=95)
print("saved:", OUT)
