# -*- coding: utf-8 -*-
"""真人声版合成：用户 m4a 主音轨 + 按真实时间轴对齐字幕 + 5段背景图 Ken Burns + 歌词卡/栏目卡叠加 + 轻 BGM。"""
import os, glob, numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, AudioArrayClip, concatenate_videoclips

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
BG = os.path.join(ROOT, "assets/backgrounds")
AUD = os.path.join(ROOT, "assets/audio")
CARD = os.path.join(ROOT, "assets/cards")
FONT = r"C:/Windows/Fonts/msyh.ttc"
OUT_W, OUT_H = 720, 1280

def get_font(size):
    try: return ImageFont.truetype(FONT, size)
    except Exception: return ImageFont.load_default()

def render_sub(text, path):
    W, H = 720, 300
    img = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 40, W, H-20], fill=(0,0,0,120))
    f = get_font(42)
    lines = text.split("\n")
    lh = 60
    y = (H - lh*len(lines))//2
    for ln in lines:
        bb = d.textbbox((0,0), ln, font=f); tw = bb[2]-bb[0]
        d.text(((W-tw)//2, y), ln, font=f, fill=(255,255,255,255), stroke_width=3, stroke_fill=(0,0,0,255))
        y += lh
    img.save(path)

# 字幕段（start, end, 修正后文本）—— 时间轴严格对齐用户真实录音
SUBS = [
 ("sub1", 0.0, 13.89, "我是笔澜，专门把民谣里那些没说出口的心事，\n一句一句翻译给你听。今天这一期，咱们聊一聊第一眼。"),
 ("sub2", 13.89, 29.70, "你一定记得那种光吧，午后的，刚好落在他睫毛上。\n风把一缕他的头发吹到肩上，你假装看别处，心跳却漏了一拍。"),
 ("sub3", 29.70, 42.40, "后来你见过他好多种样子，最忘不掉的，偏偏是那一眼。\n我也一样，第一次见他那天，空气里有刚下过雨的青草味。"),
 ("sub4", 42.40, 50.34, "他笑着递来一杯温的。\n指尖碰到的时候，我慌得把手缩回。"),
 ("sub5", 50.34, 57.92, "那一秒，整条街的嘈杂都静了，只剩他自己。\n可第一眼太短了，短到我来不及说一句你好。"),
 ("sub6", 57.92, 72.44, "后来我们走散在各自的人海。\n我再没找到那个味道，那束光。\n你有没有过，把一个人永远停在最好看的那一帧？"),
 ("sub7", 72.44, 76.0, "永远停在最好看的那一帧。"),
 ("sub8", 90.0, 99.94, "你听，不是爱了很久，是初次两个字，\n够让人心荡漾一辈子。\n我们念念不忘的，从来不是结局，是开头那一下。"),
 ("sub9", 99.94, 102.36, "可这哪只是我的私心呢？"),
 ("sub10", 116.26, 125.76, "这两句歌词你觉得哪句更好？\n评论区二选一，告诉我你更偏爱哪一句，又为什么？"),
 ("sub11", 126.64, 130.85, "我呀，先去把那第一眼再想一遍。"),
]
sub_clips = []
for name, s, e, txt in SUBS:
    p = os.path.join(CARD, name+".png")
    render_sub(txt, p)
    sc = ImageClip(p).with_start(s).with_duration(e-s).with_position(("center", int(OUT_H*0.80)))
    sub_clips.append(sc)

def find_bg(key):
    for f in glob.glob(os.path.join(BG, "*.png")):
        if key in os.path.basename(f): return f
    return None
bg_open = find_bg("Cinematic_vertical")
bg_mem  = find_bg("Warm_afternoon")
bg_heart= find_bg("After_rain")
bg_reg  = find_bg("Night_city")
bg_int  = find_bg("Warm_glowing")

BG_SEGS = [
 (bg_open, 0.0, 13.89),
 (bg_mem, 13.89, 42.40),
 (bg_heart, 42.40, 57.92),
 (bg_reg, 57.92, 116.26),
 (bg_int, 116.26, 139.23),
]

def ken_burns(path, duration, zoom=1.12):
    zw, zh = int(OUT_W*zoom), int(OUT_H*zoom)
    img = ImageClip(path).resized((zw, zh)).with_duration(duration)
    cx, cy = -(zw-OUT_W)/2, -(zh-OUT_H)/2
    def pos(t):
        p = t/duration
        return (cx + (zw-OUT_W)*0.05*(p-0.5), cy + (zh-OUT_H)*0.03*(p-0.5))
    return CompositeVideoClip([img.with_position(pos)], size=(OUT_W, OUT_H)).with_duration(duration)

base = concatenate_videoclips([ken_burns(p, e-s) for p, s, e in BG_SEGS], method="compose")

cards = [
 (os.path.join(CARD,"lyric1.png"), 76.0, 90.0),
 (os.path.join(CARD,"lyric2.png"), 102.36, 116.26),
 (os.path.join(CARD,"outro.png"), 130.85, 139.23),
]
card_clips = [ImageClip(p).resized((OUT_W,OUT_H)).with_start(s).with_duration(e-s).with_position("center") for p, s, e in cards]

audio = AudioFileClip(os.path.join(AUD, "user_voice.m4a"))
total = audio.duration
final_video = CompositeVideoClip([base] + sub_clips + card_clips, size=(OUT_W, OUT_H)).with_duration(total)

# 轻氛围 BGM（A 大调柔和 pad，极低音量）
sr = 44100
t = np.linspace(0, total, int(sr*total), endpoint=False)
freqs = [110.0, 164.81, 220.0, 277.18]
pad = np.zeros_like(t)
for f in freqs: pad += np.sin(2*np.pi*f*t)
pad = pad/len(freqs)*0.035
pad[:sr*3]*=np.linspace(0,1,sr*3); pad[-sr*3:]*=np.linspace(1,0,sr*3)
pad_clip = AudioArrayClip(pad.reshape(-1,1), fps=sr).with_duration(total)

voice_track = CompositeAudioClip([audio, pad_clip]).with_duration(total)
final = final_video.with_audio(voice_track)

out_path = os.path.join(ROOT, "assets", "第1期_第一眼_真人声成片.mp4")
final.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=24, threads=4)
print("VIDEO_DONE", out_path, "duration=%.1f" % total)
