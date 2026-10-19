# -*- coding: utf-8 -*-
"""用 ffmpeg silencedetect + 字数权重分配，计算新版配音的 8 段字幕时间轴。"""
import os, re, subprocess
import imageio_ffmpeg

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
MP3 = os.path.join(ROOT, "assets/audio/capcut_voice_v2.mp3")

SEGS = [
 "你有没有过——后来你再怎么努力，都复制不了，第一次见他的那一眼。",
 "我是笔澜，专门把民谣里没说出口的心事，翻译给你听。今天，聊第一眼。",
 "你一定记得那种光吧，午后的，刚好落在他睫毛上。风把一缕他的头发吹到肩上，你假装看别处，心跳漏了一拍。",
 "我也一样。见他那天刚下过雨，他笑着递来一杯温的，指尖碰到，我慌得把手缩回。那一秒，整条街都静了。",
 "可第一眼太短了，短到来不及说一句你好。后来我们走散在人海，我再没找回那束光——你有没有过，把一个人，永远停在最好看的那一帧？",
 "赵雷在《程艾影》里唱：永远都想初次见你那样，让我心荡漾。不是爱了多久，是“初次”两个字，就够让人心荡漾一辈子。我们念念不忘的，从来不是结局，是开头那一下。",
 "马頔在《南山南》里写：他说你任何为人称道的美丽，不及他第一次遇见你。原来全世界的人，都曾输给过某个人第一次的模样。",
 "这两句歌词，你觉得哪句更好？评论区二选一。顺便，把下一期想听的歌词，也打在评论区——翻给你听。",
]

# 1. 时长
exe = imageio_ffmpeg.get_ffmpeg_exe()
r = subprocess.run([exe, "-i", MP3, "-f", "null", "-"], capture_output=True, text=True)
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
total = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
print("TOTAL=%.2f" % total)

# 2. 静音检测
r2 = subprocess.run([exe, "-i", MP3, "-af", "silencedetect=noise=-32dB:d=0.22", "-f", "null", "-"],
                    capture_output=True, text=True)
sil_starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r2.stderr)]
sil_ends   = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r2.stderr)]
silences = list(zip(sil_starts, sil_ends))
print("SILENCES(%d):" % len(silences))
for a, b in silences:
    print("  %.2f - %.2f (%.2fs)" % (a, b, b-a))

# 3. 权重（字符 + 标点停顿）
PUNCT_W = {"，":0.55, "、":0.3, "。":1.1, "？":1.1, "！":1.1, "：":0.6, "；":0.7, "—":1.3}
def weight(s):
    w = 0.0
    for ch in s:
        if ch in "《》“”，。？！：；、":
            w += PUNCT_W.get(ch, 0.0)
        elif ch.strip():
            w += 1.0
    return w

weights = [weight(s) for s in SEGS]
unit = total / sum(weights)
print("\nUNIT=%.4f s/字(含标点权重)" % unit)

# 4. 比例边界 → 吸附到最近静音
bounds = []
acc = 0.0
for i in range(len(SEGS)-1):
    acc += weights[i]
    raw = acc * unit
    # 吸附：±1.4s 内有静音中点则对齐
    cand = None
    for a, b in silences:
        mid = (a+b)/2
        if abs(mid - raw) <= 1.4:
            if cand is None or abs(mid-raw) < abs(cand-raw):
                cand = mid
    bounds.append(cand if cand is not None else raw)

# 5. 输出时间轴
t = 0.0
print("\n=== TIMELINE ===")
for i, s in enumerate(SEGS):
    start = 0.0 if i == 0 else bounds[i-1]
    end = bounds[i] if i < len(SEGS)-1 else total
    print("seg%d: %.2f - %.2f (%.2fs) | %s..." % (i+1, start, end, end-start, s[:18]))
    print("   SUB%d = (%.2f, %.2f)" % (i+1, start, end))
print("\nBG_SEGS = [")
bg_keys = ["bg_open","bg_open","bg_mem","bg_heart","bg_reg","bg_reg","bg_reg","bg_int"]
starts = [0.0]+bounds
ends = bounds+[total]
for i,k in enumerate(bg_keys):
    print("  (%s, %.2f, %.2f)," % (k, starts[i], ends[i]))
print("]")
