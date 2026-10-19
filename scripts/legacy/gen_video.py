# -*- coding: utf-8 -*-
"""合成第1期口播成片：背景图 Ken Burns + 歌词卡/栏目卡 + AI 配音 + PIL字幕 + 轻氛围 BGM。
字幕与文字卡全部用 PIL 渲染(绕过 ImageMagick 依赖)。"""
import os, glob, numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, AudioArrayClip

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
BG = os.path.join(ROOT, "assets/backgrounds")
AUD = os.path.join(ROOT, "assets/audio")
CARD = os.path.join(ROOT, "assets/cards")
os.makedirs(CARD, exist_ok=True)

FONT = r"C:/Windows/Fonts/msyh.ttc"
OUT_W, OUT_H = 720, 1280

def get_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()

def gradient_bg(w, h, top, bottom):
    base = Image.new("RGB", (w, h))
    px = base.load()
    for y in range(h):
        r = int(top[0] + (bottom[0]-top[0])*y/h)
        g = int(top[1] + (bottom[1]-top[1])*y/h)
        b = int(top[2] + (bottom[2]-top[2])*y/h)
        for x in range(w):
            px[x, y] = (r, g, b)
    return base

def draw_lyric_card(path, lyric, caption):
    w, h = 1080, 1920
    img = gradient_bg(w, h, (18, 22, 48), (40, 28, 30))
    d = ImageDraw.Draw(img)
    d.line([(w*0.18, h*0.16), (w*0.82, h*0.16)], fill=(240, 180, 120), width=4)
    f = get_font(66)
    lines, cur = [], ""
    for ch in lyric:
        cur += ch
        if len(cur) >= 13 and ch in "，。、":
            lines.append(cur); cur = ""
    if cur: lines.append(cur)
    lh = 98
    y = h*0.30 - lh*len(lines)/2
    for ln in lines:
        bb = d.textbbox((0,0), ln, font=f); tw = bb[2]-bb[0]
        d.text(((w-tw)/2, y), ln, font=f, fill=(255,255,255))
        y += lh
    f2 = get_font(46)
    bb = d.textbbox((0,0), caption, font=f2); tw = bb[2]-bb[0]
    d.text(((w-tw)/2, h*0.64), caption, font=f2, fill=(240, 180, 120))
    img.save(path)

def draw_outro_card(path):
    w, h = 1080, 1920
    img = gradient_bg(w, h, (30, 22, 20), (52, 34, 22))
    d = ImageDraw.Draw(img)
    d.line([(w*0.30, h*0.34), (w*0.70, h*0.34)], fill=(255,210,150), width=5)
    f1 = get_font(112); t1 = "歌词里的心事"
    bb = d.textbbox((0,0), t1, font=f1); tw = bb[2]-bb[0]
    d.text(((w-tw)/2, h*0.40), t1, font=f1, fill=(255,255,255))
    f2 = get_font(54); t2 = "民谣翻译官"
    bb = d.textbbox((0,0), t2, font=f2); tw = bb[2]-bb[0]
    d.text(((w-tw)/2, h*0.52), t2, font=f2, fill=(255,210,150))
    f3 = get_font(42); t3 = "下期，翻给你听"
    bb = d.textbbox((0,0), t3, font=f3); tw = bb[2]-bb[0]
    d.text(((w-tw)/2, h*0.60), t3, font=f3, fill=(220,220,220))
    img.save(path)

lyric1 = os.path.join(CARD, "lyric1.png")
lyric2 = os.path.join(CARD, "lyric2.png")
outro = os.path.join(CARD, "outro.png")
draw_lyric_card(lyric1, "永远都想初次见你那样让我心荡漾", "赵雷《程艾影》")
draw_lyric_card(lyric2, "他说你任何为人称道的美丽，不及他第一次遇见你", "马頔《南山南》")
draw_outro_card(outro)

# 字幕 PNG（透明底 + 半透明黑条 + 白字描边）
def render_sub(text, path):
    W, H = 720, 280
    img = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 50, W, H-20], fill=(0,0,0,120))
    f = get_font(44)
    lines = text.split("\n")
    lh = 62
    y = (H - lh*len(lines))//2
    for ln in lines:
        bb = d.textbbox((0,0), ln, font=f); tw = bb[2]-bb[0]
        d.text(((W-tw)//2, y), ln, font=f, fill=(255,255,255,255),
               stroke_width=3, stroke_fill=(0,0,0,255))
        y += lh
    img.save(path)

SUBTITLES = {
    "seg1_open": "我是你的民谣翻译官。\n专门把民谣里没说出口的心事，翻译给你听。\n今天聊聊——第一眼。",
    "seg2_memory": "你一定记得那种光吧，\n午后的，刚好落在他睫毛上。\n最忘不掉的，偏偏就是那一眼。",
    "seg3_heart": "第一次见他那天，\n空气里有刚下过雨的青草味。\n那一秒，整条街的嘈杂都静了。",
    "seg4_regret": "可第一眼太短了，\n短到我还来不及说一句你好。\n把一个人，永远停在最好看的那一帧。",
    "seg5_lyric1": "赵雷唱过：\n永远都想初次见你那样让我心荡漾。\n我们念念不忘的，是开头那一下。",
    "seg6_lyric2": "马頔也写：\n他说你任何为人称道的美丽，\n不及他第一次遇见你。",
    "seg7_interact": "这两句歌词，你觉得哪句更好？\n评论区二选一，告诉我你更偏爱哪一句。",
    "seg8_outro": "下一期，你最想听我把哪句歌词翻译出来？\n打在评论区——下期，翻给你听。",
}
SUB_PATHS = {}
for name, txt in SUBTITLES.items():
    p = os.path.join(CARD, "sub_" + name + ".png")
    render_sub(txt, p)
    SUB_PATHS[name] = p

def find_bg(key):
    for f in glob.glob(os.path.join(BG, "*.png")):
        if key in os.path.basename(f):
            return f
    return None
bg_open = find_bg("Cinematic_vertical")
bg_mem  = find_bg("Warm_afternoon")
bg_heart= find_bg("After_rain")
bg_reg  = find_bg("Night_city")
bg_int  = find_bg("Warm_glowing")

SEGS = [
    ("seg1_open", bg_open, "img"),
    ("seg2_memory", bg_mem, "img"),
    ("seg3_heart", bg_heart, "img"),
    ("seg4_regret", bg_reg, "img"),
    ("seg5_lyric1", lyric1, "card"),
    ("seg6_lyric2", lyric2, "card"),
    ("seg7_interact", bg_int, "img"),
    ("seg8_outro", outro, "card"),
]

def ken_burns(path, duration, zoom=1.12):
    zw, zh = int(OUT_W*zoom), int(OUT_H*zoom)
    img = ImageClip(path).resized((zw, zh)).with_duration(duration)
    cx, cy = -(zw-OUT_W)/2, -(zh-OUT_H)/2
    def pos(t):
        p = t/duration
        return (cx + (zw-OUT_W)*0.05*(p-0.5), cy + (zh-OUT_H)*0.03*(p-0.5))
    moved = img.with_position(pos)
    return CompositeVideoClip([moved], size=(OUT_W, OUT_H)).with_duration(duration)

clips = []
durations = []
for name, path, kind in SEGS:
    a = AudioFileClip(os.path.join(AUD, name+".wav"))
    dur = a.duration
    durations.append(dur)
    vis = ken_burns(path, dur) if kind == "img" else ImageClip(path).resized((OUT_W, OUT_H)).with_duration(dur)
    sub = ImageClip(SUB_PATHS[name]).with_duration(dur).with_position(("center", int(OUT_H*0.74)))
    seg = CompositeVideoClip([vis, sub], size=(OUT_W, OUT_H)).with_duration(dur).with_audio(a)
    clips.append(seg)

total = sum(durations)
final_video = CompositeVideoClip(clips, size=(OUT_W, OUT_H)).with_duration(total)

# 轻氛围 BGM（A 大调柔和 pad，极低音量）
sr = 44100
t = np.linspace(0, total, int(sr*total), endpoint=False)
freqs = [110.0, 164.81, 220.0, 277.18]
pad = np.zeros_like(t)
for f in freqs:
    pad += np.sin(2*np.pi*f*t)
pad = pad/len(freqs)*0.04
pad[:sr*3] *= np.linspace(0,1,sr*3)
pad[-sr*3:] *= np.linspace(1,0,sr*3)
pad_clip = AudioArrayClip(pad.reshape(-1,1), fps=sr).with_duration(total)

voice_track = CompositeAudioClip([final_video.audio, pad_clip]).with_duration(total)
final = final_video.with_audio(voice_track)

out_path = os.path.join(ROOT, "assets", "第1期_第一眼_成片.mp4")
final.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=24, threads=4)
print("VIDEO_DONE", out_path, "duration=%.1f" % total)
