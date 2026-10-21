# -*- coding: utf-8 -*-
"""第2期《安和桥》成片合成：720x1280 / 37.7s / 6 段 Ken Burns + 精确字幕 + 轻 BGM
时间轴严格来自 timeline_ep2.json（逐句合成，构造精确），不做任何估时。
"""
import os, json, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips
from moviepy.video.fx import CrossFadeIn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, "assets", "audio")
OUT = os.path.join(ROOT, "assets", "第2期_安和桥_成片.mp4")
SUB_DIR = os.path.join(ROOT, "assets", "ep2_subs")
os.makedirs(SUB_DIR, exist_ok=True)

W, H, FPS = 720, 1280, 30
F = r"C:\Windows\Fonts\simhei.ttf"

HOOK_PNG = os.path.join(ROOT, "assets", "第2期_首帧_方案.png")
GIRL = os.path.join(ROOT, "assets", "cover_raw",
                    "竖构图电影感人像摄影_夏日黄昏的金色阳光里_一个年轻女孩半侧_2026-10-21T04-37-26.png")
BRIDGE = os.path.join(ROOT, "assets", "ep2_bg",
                      "竖构图电影感空镜摄影_黄昏时分的旧石桥与河面_金橙色夕阳在水_2026-10-21T04-43-13.png")
FACE = os.path.join(ROOT, "assets", "ep2_bg",
                    "竖构图电影感特写摄影_逆光下被风吹起的发丝边缘泛着金色轮廓光_2026-10-21T04-43-11.png")
ENDCARD = os.path.join(ROOT, "assets", "片尾卡_模板.png")

TL = json.load(open(os.path.join(AUD, "timeline_ep2.json"), encoding="utf-8"))
TOTAL = TL["total"]
SUBS = TL["sentences"]

# 修正：edge-tts 句边界存在 ±0.05s 重叠，强制单调不重叠，避免两条字幕同时画上去
_fixed, _prev = [], 0.0
for s in SUBS:
    a = max(s["start"], _prev)
    b = max(s["end"], a + 0.35)
    _fixed.append({"start": round(a, 3), "end": round(b, 3), "text": s["text"]})
    _prev = b
SUBS = _fixed

def to_720(path, out_name):
    """统一转成 720x1280 盖满裁切，避免 moviepy 端尺寸不一致"""
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x0 = (im.width - W) // 2; y0 = (im.height - H) // 2
    im = im.crop((x0, y0, x0 + W, y0 + H))
    p = os.path.join(SUB_DIR, out_name)
    im.save(p, quality=95)
    return p

# ---------- 分段 ----------
SEGS = [
    (0.00, 3.10, to_720(HOOK_PNG, "base_hook.png")),
    (3.10, 8.18, to_720(GIRL, "base_girl.png")),
    (8.18, 19.68, to_720(BRIDGE, "base_bridge.png")),
    (19.68, 28.43, to_720(FACE, "base_face.png")),
    (28.43, 32.60, to_720(BRIDGE, "base_bridge2.png")),
    (32.60, TOTAL, to_720(ENDCARD, "base_end.png")),
]

def make_seg(path, d, zoom=0.07):
    clip = ImageClip(path).with_duration(d)
    try:
        z = clip.resized(lambda t: 1.0 + zoom * (t / d))
        z = z.with_position(("center", "center"))
        return CompositeVideoClip([z], size=(W, H)).with_duration(d)
    except Exception as e:
        print("kenburns fallback:", e)
        return clip.with_duration(d)

segs = []
for i, (a, b, p) in enumerate(SEGS):
    d = b - a
    c = make_seg(p, d)
    if i > 0:
        c = c.with_effects([CrossFadeIn(0.22)])
    segs.append(c)

bg_video = concatenate_videoclips(segs, method="compose", padding=0)
print("video dur:", bg_video.duration, " total:", TOTAL)

# ---------- 字幕 ----------
def make_sub(text, idx):
    fs = 42
    font = ImageFont.truetype(F, fs)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = tmp.textlength(text, font=font)
    if tw > 610:
        fs = int(fs * 610 / tw)
        font = ImageFont.truetype(F, fs)
        tw = tmp.textlength(text, font=font)
    bw, bh, pad = int(tw + 60), 80, 24
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=22, fill=(0, 0, 0, 118))
    bb = d.textbbox((0, 0), text, font=font)
    tx = (bw - (bb[2] - bb[0])) / 2 - bb[0]
    ty = (bh - (bb[3] - bb[1])) / 2 - bb[1]
    d.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    return np.array(img)

sub_clips = []
for i, s in enumerate(SUBS):
    if i in (0, 14, 15):   # 0=首帧已是大字钩子；14/15 在片尾卡上不再叠字幕
        continue
    a, b = s["start"], s["end"]
    a = max(a, 3.12) if i == 1 else a
    dur = b - a
    if dur <= 0.2:
        continue
    arr = make_sub(s["text"], i)
    sub_clips.append(ImageClip(arr, transparent=True).with_start(a)
                     .with_duration(dur).with_position(("center", 988)))

video = CompositeVideoClip([bg_video] + sub_clips, size=(W, H)).with_duration(TOTAL)

# ---------- BGM：极轻 A 大调氛围垫 ----------
SR = 44100
n = int(SR * TOTAL)
t = np.arange(n) / SR
sig = np.zeros(n)
for f in [220.0, 277.18, 329.63, 440.0]:
    sig += 0.22 * np.sin(2 * np.pi * f * t)
    sig += 0.10 * np.sin(2 * np.pi * f * 1.004 * t)
env = 0.45 + 0.55 * (0.5 - 0.5 * np.cos(2 * np.pi * t / 14.0))
sig = sig * env
fade = int(SR * 2.2)
sig[:fade] *= np.linspace(0, 1, fade)
sig[-fade:] *= np.linspace(1, 0, fade)
sig = sig / (np.max(np.abs(sig)) + 1e-9) * 0.5
bgm_path = os.path.join(AUD, "ep2_bgm.wav")
with wave.open(bgm_path, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((sig * 32767).astype(np.int16).tobytes())

voice = AudioFileClip(os.path.join(AUD, "ep2_voice.wav"))
bgm = AudioFileClip(bgm_path)
try:
    bgm = bgm.with_volume_scaled(0.05)
except Exception:
    bgm = bgm.with_effects([])  # 兜底，不改音量
audio = CompositeAudioClip([bgm.with_duration(TOTAL), voice])
video = video.with_audio(audio)

video.write_videofile(OUT, fps=FPS, codec="libx264", audio_codec="aac",
                      bitrate="3000k", preset="medium", threads=4,
                      ffmpeg_params=["-pix_fmt", "yuv420p"])
print("DONE", OUT, os.path.getsize(OUT) / 1e6, "MB")
