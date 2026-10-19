# -*- coding: utf-8 -*-
"""精简钩子版合成：capcut_voice_v2.mp3 主音轨 + 逐句吸附字幕 + 背景交叉溶解 + 歌词卡(精确到句) + 栏目卡 + 轻 BGM。
时间轴来自 scripts/align_timeline_v2.py（ffmpeg 静音检测 + 字数权重分配，18 句全部锚定真实停顿）。"""
import os, glob, numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, AudioArrayClip
from moviepy.video.fx import CrossFadeIn
try:
    from moviepy.video.fx import CrossFadeOut
    HAS_OUT = True
except Exception:
    HAS_OUT = False

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
    """自适应字号字幕：行宽不超 680px，深色横带 + 白字描边。"""
    lines = text.split("\n")
    tmp = Image.new("RGBA", (10, 10)); td = ImageDraw.Draw(tmp)
    size = 30
    for cand in (38, 36, 34, 32, 30):
        f = get_font(cand)
        if all(td.textbbox((0, 0), ln, font=f)[2] <= 680 for ln in lines):
            size = cand; break
    f = get_font(size)
    lh = size + 14
    H = lh * len(lines) + 56
    img = Image.new("RGB" if False else "RGBA", (OUT_W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 20, OUT_W, H - 16], fill=(0, 0, 0, 130))
    y = (H - lh * len(lines)) // 2 + 4
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=f); tw = bb[2] - bb[0]
        d.text(((OUT_W - tw) // 2, y), ln, font=f, fill=(255, 255, 255, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(path)

# ============ 逐句字幕（时间轴 = 静音吸附结果） ============
SUBS = [
 ("v2s01", 0.00,  8.41,  "你有没有过——后来你再怎么努力，\n都复制不了，第一次见他的那一眼。"),
 ("v2s02", 8.41,  14.52, "我是笔澜，专门把民谣里\n没说出口的心事，翻译给你听。"),
 ("v2s03", 14.52, 16.42, "今天，聊第一眼。"),
 ("v2s04", 16.42, 23.15, "你一定记得那种光吧，午后的，\n刚好落在他睫毛上。"),
 ("v2s05", 23.15, 30.28, "风把一缕他的头发吹到肩上，\n你假装看别处，心跳漏了一拍。"),
 ("v2s06", 30.28, 32.21, "我也一样。"),
 ("v2s07", 32.21, 39.44, "见他那天刚下过雨，\n他笑着递来一杯温的，指尖碰到，\n我慌得把手缩回。"),
 ("v2s08", 39.44, 41.74, "那一秒，整条街都静了。"),
 ("v2s09", 41.74, 45.99, "可第一眼太短了，\n短到来不及说一句你好。"),
 ("v2s10", 45.99, 58.36, "后来我们走散在人海，\n我再没找回那束光——\n你有没有过，把一个人，\n永远停在最好看的那一帧？"),
 ("v2s12", 63.92, 71.32, "不是爱了多久，是“初次”两个字，\n就够让人心荡漾一辈子。"),
 ("v2s13", 71.32, 76.16, "我们念念不忘的，\n从来不是结局，是开头那一下。"),
 ("v2s15", 83.51, 89.52, "原来全世界的人，\n都曾输给过某个人第一次的模样。"),
 ("v2s16", 89.52, 92.67, "这两句歌词，你觉得哪句更好？"),
 ("v2s17", 92.67, 95.32, "评论区二选一。"),
 ("v2s18", 95.32, 99.80, "顺便，把下一期想听的歌词，\n也打在评论区——翻给你听。"),
]
sub_clips = []
for name, s, e, txt in SUBS:
    p = os.path.join(CARD, name + ".png")
    render_sub(txt, p)
    sub_clips.append(ImageClip(p).with_start(s).with_duration(e - s)
                     .with_position(("center", int(OUT_H * 0.80))))

# ============ 背景（5 段，交叉溶解 0.6s） ============
def find_bg(key):
    for f in glob.glob(os.path.join(BG, "*.png")):
        if key in os.path.basename(f): return f
    return None
bg_open = find_bg("Cinematic_vertical")
bg_mem  = find_bg("Warm_afternoon")
bg_heart= find_bg("After_rain")
bg_reg  = find_bg("Night_city")
bg_int  = find_bg("Warm_glowing")

FADE = 0.6
BG_PERIODS = [
 (bg_open,  0.00,  16.42),
 (bg_mem,   16.42, 30.28),
 (bg_heart, 30.28, 41.74),
 (bg_reg,   41.74, 89.52),
 (bg_int,   89.52, 102.48),
]

def ken_burns(path, duration, zoom=1.12):
    zw, zh = int(OUT_W * zoom), int(OUT_H * zoom)
    img = ImageClip(path).resized((zw, zh)).with_duration(duration)
    cx, cy = -(zw - OUT_W) / 2, -(zh - OUT_H) / 2
    def pos(t):
        p = t / duration
        return (cx + (zw - OUT_W) * 0.05 * (p - 0.5), cy + (zh - OUT_H) * 0.03 * (p - 0.5))
    return CompositeVideoClip([img.with_position(pos)], size=(OUT_W, OUT_H)).with_duration(duration)

bg_clips = []
for i, (path, s, e) in enumerate(BG_PERIODS):
    last = (i == len(BG_PERIODS) - 1)
    dur = (e - s) + (0.0 if last else FADE)
    c = ken_burns(path, dur)
    if i == 0:
        c = c.with_start(0.0)
    else:
        c = c.with_start(s - FADE).with_effects([CrossFadeIn(FADE)])
    bg_clips.append(c)
base = CompositeVideoClip(bg_clips, size=(OUT_W, OUT_H))

# ============ 歌词卡（只在念到该句歌词时出现）+ 栏目卡 ============
def card_clip(name, s, e, fade_in=0.35):
    p = os.path.join(CARD, name + ".png")
    c = ImageClip(p).resized((OUT_W, OUT_H)).with_start(s).with_duration(e - s).with_position("center")
    fx = [CrossFadeIn(fade_in)]
    if HAS_OUT:
        fx.append(CrossFadeOut(fade_in))
    return c.with_effects(fx)

cards = [
 card_clip("lyric1", 58.36, 63.92),   # 程艾影：赵雷唱→歌词念完
 card_clip("lyric2", 76.16, 83.51),   # 南山南：马頔写→歌词念完
 card_clip("outro",  99.80, 102.48, fade_in=0.4),  # 栏目卡收尾
]

# ============ 音频：剪映 AI 配音 + 轻钢琴 pad ============
audio = AudioFileClip(os.path.join(AUD, "capcut_voice_v2.mp3"))
total = audio.duration
final_video = CompositeVideoClip([base] + cards + sub_clips, size=(OUT_W, OUT_H)).with_duration(total)

sr = 44100
t = np.linspace(0, total, int(sr * total), endpoint=False)
freqs = [110.0, 164.81, 220.0, 277.18]
pad = np.zeros_like(t)
for f in freqs: pad += np.sin(2 * np.pi * f * t)
pad = pad / len(freqs) * 0.035
pad[:sr * 3] *= np.linspace(0, 1, sr * 3); pad[-sr * 3:] *= np.linspace(1, 0, sr * 3)
pad_clip = AudioArrayClip(pad.reshape(-1, 1), fps=sr).with_duration(total)

final = final_video.with_audio(CompositeAudioClip([audio, pad_clip]).with_duration(total))

out_path = os.path.join(ROOT, "assets", "第1期_第一眼_精简钩子版.mp4")
final.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=24, threads=4)
print("VIDEO_DONE", out_path, "duration=%.1f" % total)
