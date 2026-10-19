# -*- coding: utf-8 -*-
"""v2：按 18 个句子边界逐一吸附静音，得到精确的段/句时间轴；并检查 moviepy fx API。"""
import os, re, subprocess
import imageio_ffmpeg

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
MP3 = os.path.join(ROOT, "assets/audio/capcut_voice_v2.mp3")

# 18 个句子（按顺序）
SENTS = [
 "你有没有过——后来你再怎么努力，都复制不了，第一次见他的那一眼。",
 "我是笔澜，专门把民谣里没说出口的心事，翻译给你听。",
 "今天，聊第一眼。",
 "你一定记得那种光吧，午后的，刚好落在他睫毛上。",
 "风把一缕他的头发吹到肩上，你假装看别处，心跳漏了一拍。",
 "我也一样。",
 "见他那天刚下过雨，他笑着递来一杯温的，指尖碰到，我慌得把手缩回。",
 "那一秒，整条街都静了。",
 "可第一眼太短了，短到来不及说一句你好。",
 "后来我们走散在人海，我再没找回那束光——你有没有过，把一个人，永远停在最好看的那一帧？",
 "赵雷在《程艾影》里唱：永远都想初次见你那样，让我心荡漾。",
 "不是爱了多久，是“初次”两个字，就够让人心荡漾一辈子。",
 "我们念念不忘的，从来不是结局，是开头那一下。",
 "马頔在《南山南》里写：他说你任何为人称道的美丽，不及他第一次遇见你。",
 "原来全世界的人，都曾输给过某个人第一次的模样。",
 "这两句歌词，你觉得哪句更好？",
 "评论区二选一。",
 "顺便，把下一期想听的歌词，也打在评论区——翻给你听。",
]
SEG_OF_SENT = [1,2,2,3,3,4,4,4,5,5,6,6,6,7,7,8,8,8]

exe = imageio_ffmpeg.get_ffmpeg_exe()
r = subprocess.run([exe, "-i", MP3, "-f", "null", "-"], capture_output=True, text=True)
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
total = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

r2 = subprocess.run([exe, "-i", MP3, "-af", "silencedetect=noise=-32dB:d=0.22", "-f", "null", "-"],
                    capture_output=True, text=True)
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r2.stderr)]
ends   = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r2.stderr)]
mids = [(a+b)/2 for a, b in zip(starts, ends)]

PUNCT_W = {"，":0.55, "、":0.3, "。":1.1, "？":1.1, "！":1.1, "：":0.6, "；":0.7, "—":1.3}
def weight(s):
    w = 0.0
    for ch in s:
        if ch in "《》“”，。？！：；、":
            w += PUNCT_W.get(ch, 0.0)
        elif ch.strip():
            w += 1.0
    return w

weights = [weight(s) for s in SENTS]
unit = total / sum(weights)

# 逐句边界：期望时间 → 单调吸附到最近静音（窗口 ±1.5s）
bounds = []
acc = 0.0
last = 0.0
for i in range(len(SENTS)-1):
    acc += weights[i]
    raw = acc * unit
    cand = None
    for mid in mids:
        if mid <= last + 0.3:
            continue
        if abs(mid - raw) <= 1.5:
            if cand is None or abs(mid-raw) < abs(cand-raw):
                cand = mid
    b = cand if cand is not None else raw
    bounds.append(b)
    last = b

print("TOTAL=%.2f  UNIT=%.4f" % (total, unit))
print("\n=== SENTENCE BOUNDS ===")
prev = 0.0
for i, s in enumerate(SENTS):
    end = bounds[i] if i < len(bounds) else total
    print("s%02d [%6.2f - %6.2f] (%.2fs) seg%d | %s" % (i+1, prev, end, end-prev, SEG_OF_SENT[i], s[:16]))
    prev = end

# 段边界 = 该段最后一句的结束
print("\n=== SEGMENT BOUNDS ===")
seg_bounds = {}
prev = 0.0
for i, s in enumerate(SENTS):
    end = bounds[i] if i < len(bounds) else total
    seg = SEG_OF_SENT[i]
    seg_bounds[seg] = end
    prev = end
for seg in sorted(seg_bounds):
    print("seg%d ends at %.2f" % (seg, seg_bounds[seg]))

# 检查 moviepy fx API
print("\n=== MOVIEPY FX CHECK ===")
import moviepy
print("moviepy version:", moviepy.__version__)
try:
    from moviepy.video.fx import CrossFadeIn, FadeIn
    print("CrossFadeIn import OK")
    import inspect
    print("CrossFadeIn sig:", inspect.signature(CrossFadeIn.__init__))
except Exception as e:
    print("CrossFadeIn import FAIL:", e)
