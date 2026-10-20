# -*- coding: utf-8 -*-
"""栏目片尾卡模板（每期通用）：光晕底图 + 品牌三件套 + 关注/点歌 CTA（1080x1920）
换期无需重做：只改 OUT 文件名即可复用同一底图。
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "assets", "cover_raw",
                  "竖构图极简电影感画面_深蓝色夜空中一团温暖橘色的光晕居中偏上_2026-10-20T07-13-06.png")
OUT = os.path.join(ROOT, "assets", "片尾卡_模板.png")

W, H = 1080, 1920
F_TITLE = r"C:\Windows\Fonts\simhei.ttf"
F_KAI   = r"C:\Windows\Fonts\STKAITI.TTF"

bg = Image.open(BG).convert("RGB")
s = max(W / bg.width, H / bg.height)
bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
x0 = (bg.width - W) // 2
canvas = bg.crop((x0, 0, x0 + W, H)).convert("RGBA")

# 下半部轻压暗，保证文字可读（保留上方光晕）
grad = Image.new("L", (1, H), 0)
for y in range(H):
    if y > 850:
        grad.putpixel((0, y), int(120 * min(1, (y - 850) / 500)))
shade = Image.new("RGBA", (W, H), (8, 10, 22, 255))
shade.putalpha(grad.resize((W, H)))
canvas = Image.alpha_composite(canvas, shade)
draw = ImageDraw.Draw(canvas)

def center_text(y, text, font, fill, tracking=0, glow=None, shadow=None):
    widths = [draw.textlength(c, font=font) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (W - total) / 2
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + 4), text, font=font, fill=shadow)
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    if glow:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(gl).text((x, y), text, font=font, fill=glow)
        canvas.alpha_composite(gl.filter(ImageFilter.GaussianBlur(18)))
    draw.text((x, y), text, font=font, fill=fill)
    return y + draw.textbbox((0, 0), text, font=font)[3]

# ① 栏目名（小）
center_text(870, "歌 词 里 的 心 事", ImageFont.truetype(F_KAI, 56), (255, 226, 192, 235), tracking=8)

# ② 账号名（大 + 暖光晕）
name = "民谣翻译官"
nf = ImageFont.truetype(F_TITLE, 150)
tw = sum(draw.textlength(c, font=nf) for c in name)
nx, ny = (W - tw) / 2, 975
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).text((nx, ny), name, font=nf, fill=(255, 150, 60, 210))
canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22)))
draw.text((nx, ny), name, font=nf, fill=(255, 250, 242, 255))

# ③ 价值主张（楷体两行）
kf = ImageFont.truetype(F_KAI, 56)
center_text(1230, "把每一句民谣", kf, (255, 240, 222, 245), shadow=(0, 0, 0, 150))
center_text(1315, "翻译成你没说出口的心事", kf, (255, 240, 222, 245), shadow=(0, 0, 0, 150))

# ④ 分隔线
draw.line([(W/2 - 110, 1465), (W/2 + 110, 1465)], fill=(255, 190, 120, 190), width=3)

# ⑤ 关注 + 点歌 CTA
center_text(1510, "关 注 我", ImageFont.truetype(F_TITLE, 72), (255, 214, 160, 255), tracking=14)
center_text(1630, "下一期，翻你点名的那句歌词", ImageFont.truetype(F_KAI, 50), (255, 236, 214, 235), shadow=(0, 0, 0, 150))

# ⑥ 底部更新节奏（小字）
center_text(1810, "每 周 深 夜 更 新", ImageFont.truetype(F_TITLE, 34), (214, 196, 176, 200), tracking=6)

canvas.convert("RGB").save(OUT, quality=95)
print("saved:", OUT)
