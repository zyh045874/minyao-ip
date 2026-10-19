# -*- coding: utf-8 -*-
"""第1期《第一眼》精修版 v3 —— 在精简钩子版基础上做四项升级：

① 时长修正：配音整体提速 1.25x（ffmpeg atempo，保音高），102.5s -> 约 82s，
   回到定稿时设计的 80 秒量级；时间轴按同比例缩放，字幕仍逐句同步。
② 字幕升级：全局统一加大字号（约 40px，原 30-38）、描边 2->3、底部锚定不再溢出。
③ 开场标题卡：前 4 秒叠加「歌词里的心事 / 第一眼」栏目标题，刷到即知这是谁。
④ 输出质量：码率提到 2500k，结尾 0.8s 渐隐。

输出：assets/第1期_第一眼_精修版.mp4（不覆盖旧版）
"""
import os, re, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, AudioArrayClip
from moviepy.video.fx import CrossFadeIn
try:
    from moviepy.video.fx import CrossFadeOut
    HAS_OUT = True
except Exception:
    HAS_OUT = False

import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
BG = os.path.join(ROOT, "assets/backgrounds")
AUD = os.path.join(ROOT, "assets/audio")
CARD = os.path.join(ROOT, "assets/cards")
FONT = r"C:/Windows/Fonts/msyh.ttc"
OUT_W, OUT_H = 720, 1280

SRC_AUDIO = os.path.join(AUD, "capcut_voice_v2.mp3")
SPD_AUDIO = os.path.join(AUD, "capcut_voice_v3_125.mp3")
TEMPO = 1.25
BASE_DUR = 102.48  # 原配音时长（下方 SUBS/BG/CARDS 时间轴的基准）

def probe_dur(p):
    r = subprocess.run([FF, "-i", p], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise RuntimeError("probe failed: " + p)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

# ---------- ① 提速配音 ----------
if not os.path.exists(SPD_AUDIO):
    print("生成提速配音 atempo=%s ..." % TEMPO)
    subprocess.run([FF, "-y", "-i", SRC_AUDIO, "-filter:a", "atempo=%s" % TEMPO,
                    "-b:a", "192k", SPD_AUDIO], capture_output=True)
audio = AudioFileClip(SPD_AUDIO)
total = audio.duration
K = total / BASE_DUR
print("配音 %.2fs -> %.2fs，时间轴缩放系数 K=%.4f" % (BASE_DUR, total, K))

def get_font(size):
    try: return ImageFont.truetype(FONT, size)
    except Exception: return ImageFont.load_default()

# ---------- ② 字幕（时间 = 原始时间，渲染时统一乘 K） ----------
SUBS = [
 (0.00,  8.41,  "你有没有过——后来你再怎么努力，\n都复制不了，第一次见他的那一眼。"),
 (8.41,  14.52, "我是笔澜，专门把民谣里\n没说出口的心事，翻译给你听。"),
 (14.52, 16.42, "今天，聊第一眼。"),
 (16.42, 23.15, "你一定记得那种光吧，午后的，\n刚好落在他睫毛上。"),
 (23.15, 30.28, "风把一缕他的头发吹到肩上，\n你假装看别处，心跳漏了一拍。"),
 (30.28, 32.21, "我也一样。"),
 (32.21, 39.44, "见他那天刚下过雨，\n他笑着递来一杯温的，指尖碰到，\n我慌得把手缩回。"),
 (39.44, 41.74, "那一秒，整条街都静了。"),
 (41.74, 45.99, "可第一眼太短了，\n短到来不及说一句你好。"),
 (45.99, 58.36, "后来我们走散在人海，\n我再没找回那束光——\n你有没有过，把一个人，\n永远停在最好看的那一帧？"),
 (63.92, 71.32, "不是爱了多久，是“初次”两个字，\n就够让人心荡漾一辈子。"),
 (71.32, 76.16, "我们念念不忘的，\n从来不是结局，是开头那一下。"),
 (83.51, 89.52, "原来全世界的人，\n都曾输给过某个人第一次的模样。"),
 (89.52, 92.67, "这两句歌词，你觉得哪句更好？"),
 (92.67, 95.32, "评论区二选一。"),
 (95.32, 99.80, "顺便，把下一期想听的歌词，\n也打在评论区——翻给你听。"),
]

# 全局统一字号：取所有字幕都装得下的最大号（视觉一致）
def pick_global_size(subs):
    tmp = Image.new("RGBA", (10, 10)); td = ImageDraw.Draw(tmp)
    for cand in (44, 42, 40, 38, 36, 34):
        f = get_font(cand)
        ok = True
        for _, _, txt in subs:
            for ln in txt.split("\n"):
                if td.textbbox((0, 0), ln, font=f)[2] > 664:
                    ok = False; break
            if not ok: break
        if ok:
            return cand
    return 34

SUB_SIZE = pick_global_size(SUBS)
print("全局字幕字号 =", SUB_SIZE)

def render_sub(text, path):
    lines = text.split("\n")
    f = get_font(SUB_SIZE)
    lh = SUB_SIZE + 16
    H = lh * len(lines) + 64
    img = Image.new("RGBA", (OUT_W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 22, OUT_W, H - 18], fill=(0, 0, 0, 150))
    y = (H - lh * len(lines)) // 2 + 6
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=f); tw = bb[2] - bb[0]
        d.text(((OUT_W - tw) // 2, y), ln, font=f, fill=(255, 255, 255, 255),
               stroke_width=3, stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(path)
    return H

sub_clips = []
for i, (s, e, txt) in enumerate(SUBS):
    p = os.path.join(CARD, "v3s%02d.png" % (i + 1))
    H = render_sub(txt, p)
    sub_clips.append(ImageClip(p)
                     .with_start(s * K).with_duration((e - s) * K)
                     .with_position(("center", OUT_H - 64 - H)))  # 底部锚定，杜绝溢出

# ---------- ③ 开场标题卡 ----------
def render_title_card(path):
    img = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_tag = get_font(30); f_big = get_font(104); f_small = get_font(26)
    y0 = 300
    t1 = "歌词里的心事"
    bb = d.textbbox((0, 0), t1, font=f_tag); w = bb[2] - bb[0]
    d.text(((OUT_W - w) // 2, y0), t1, font=f_tag, fill=(255, 240, 220, 235),
           stroke_width=2, stroke_fill=(0, 0, 0, 200))
    t2 = "第 一 眼"
    bb = d.textbbox((0, 0), t2, font=f_big); w = bb[2] - bb[0]
    d.text(((OUT_W - w) // 2, y0 + 54), t2, font=f_big, fill=(255, 255, 255, 255),
           stroke_width=4, stroke_fill=(0, 0, 0, 230))
    d.line([OUT_W // 2 - 90, y0 + 216, OUT_W // 2 + 90, y0 + 216],
           fill=(255, 214, 165, 230), width=3)
    t3 = "把民谣里没说出口的心事，翻译给你听"
    bb = d.textbbox((0, 0), t3, font=f_small); w = bb[2] - bb[0]
    d.text(((OUT_W - w) // 2, y0 + 240), t3, font=f_small, fill=(255, 240, 220, 215),
           stroke_width=2, stroke_fill=(0, 0, 0, 190))
    img.save(path)

TITLE_PNG = os.path.join(CARD, "v3_title.png")
render_title_card(TITLE_PNG)
title_clip = (ImageClip(TITLE_PNG)
              .with_start(0.3 * K).with_duration(4.7 * K)
              .with_position("center").with_effects([CrossFadeIn(0.4), CrossFadeOut(0.4)]))

# ---------- 背景（时间轴同乘 K，交叉溶解不变） ----------
def find_bg(key):
    for f in glob.glob(os.path.join(BG, "*.png")):
        if key in os.path.basename(f): return f
    return None

FADE = 0.6
BG_PERIODS = [
 (find_bg("Cinematic_vertical"), 0.00,  16.42),
 (find_bg("Warm_afternoon"),     16.42, 30.28),
 (find_bg("After_rain"),         30.28, 41.74),
 (find_bg("Night_city"),         41.74, 89.52),
 (find_bg("Warm_glowing"),       89.52, 102.48),
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
    dur = ((e - s) * K) + (0.0 if last else FADE)
    c = ken_burns(path, dur)
    if i == 0:
        c = c.with_start(0.0)
    else:
        c = c.with_start(s * K - FADE).with_effects([CrossFadeIn(FADE)])
    bg_clips.append(c)
base = CompositeVideoClip(bg_clips, size=(OUT_W, OUT_H))

def card_clip(name, s, e, fade_in=0.35):
    p = os.path.join(CARD, name + ".png")
    c = ImageClip(p).resized((OUT_W, OUT_H)).with_start(s * K).with_duration((e - s) * K).with_position("center")
    fx = [CrossFadeIn(fade_in)]
    if HAS_OUT:
        fx.append(CrossFadeOut(fade_in))
    return c.with_effects(fx)

cards = [
 card_clip("lyric1", 58.36, 63.92),
 card_clip("lyric2", 76.16, 83.51),
 card_clip("outro",  99.80, 102.48, fade_in=0.4),
]

# ---------- 合成 ----------
final_video = CompositeVideoClip([base] + cards + [title_clip] + sub_clips,
                                 size=(OUT_W, OUT_H)).with_duration(total)
try:
    from moviepy.video.fx import FadeOut
    final_video = final_video.with_effects([FadeOut(0.8)])
    print("已加结尾渐隐 0.8s")
except Exception as e:
    print("渐隐不可用，跳过：", e)

sr = 44100
t = np.linspace(0, total, int(sr * total), endpoint=False)
freqs = [110.0, 164.81, 220.0, 277.18]
pad = np.zeros_like(t)
for f in freqs: pad += np.sin(2 * np.pi * f * t)
pad = pad / len(freqs) * 0.035
pad[:sr * 3] *= np.linspace(0, 1, sr * 3); pad[-sr * 3:] *= np.linspace(1, 0, sr * 3)
pad_clip = AudioArrayClip(pad.reshape(-1, 1), fps=sr).with_duration(total)

final = final_video.with_audio(CompositeAudioClip([audio, pad_clip]).with_duration(total))

out_path = os.path.join(ROOT, "assets", "第1期_第一眼_精修版.mp4")
final.write_videofile(out_path, codec="libx264", audio_codec="aac",
                      fps=24, threads=4, bitrate="2500k")
print("VIDEO_DONE", out_path, "duration=%.2f" % total)
