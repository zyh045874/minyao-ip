# -*- coding: utf-8 -*-
"""v3b：灵敏静音检测 + 碎片合并（gap<0.45s 视为一次停顿）+ DP 单调匹配 + 全程明细打印。"""
import os, re, json, subprocess
import imageio_ffmpeg

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
MP3 = os.path.join(ROOT, "assets/audio/capcut_voice_v2.mp3")

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
DISPLAY = {
 1:  "你有没有过——后来你再怎么努力，\n都复制不了，第一次见他的那一眼。",
 2:  "我是笔澜，专门把民谣里\n没说出口的心事，翻译给你听。",
 3:  "今天，聊第一眼。",
 4:  "你一定记得那种光吧，午后的，\n刚好落在他睫毛上。",
 5:  "风把一缕他的头发吹到肩上，\n你假装看别处，心跳漏了一拍。",
 6:  "我也一样。",
 7:  "见他那天刚下过雨，\n他笑着递来一杯温的，指尖碰到，\n我慌得把手缩回。",
 8:  "那一秒，整条街都静了。",
 9:  "可第一眼太短了，\n短到来不及说一句你好。",
 10: "后来我们走散在人海，\n我再没找回那束光——\n你有没有过，把一个人，\n永远停在最好看的那一帧？",
 12: "不是爱了多久，是“初次”两个字，\n就够让人心荡漾一辈子。",
 13: "我们念念不忘的，\n从来不是结局，是开头那一下。",
 15: "原来全世界的人，\n都曾输给过某个人第一次的模样。",
 16: "这两句歌词，你觉得哪句更好？",
 17: "评论区二选一。",
 18: "顺便，把下一期想听的歌词，\n也打在评论区——翻给你听。",
}
OLD_ENDS = {1:8.41, 2:14.52, 3:16.42, 4:23.15, 5:30.28, 6:32.21, 7:39.44, 8:41.74}

exe = imageio_ffmpeg.get_ffmpeg_exe()
r = subprocess.run([exe, "-i", MP3, "-f", "null", "-"], capture_output=True, text=True)
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
total = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

r2 = subprocess.run([exe, "-i", MP3, "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"],
                    capture_output=True, text=True)
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r2.stderr)]
ends   = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r2.stderr)]
raw = [(a, b) for a, b in zip(starts, ends) if a > 0.5]

# 碎片合并：相邻静音间隔 < 0.45s → 并成一次停顿
merged = []
for a, b in raw:
    if merged and a - merged[-1][1] < 0.45:
        merged[-1] = (merged[-1][0], b)
    else:
        merged.append((a, b))
silences = merged
print("TOTAL=%.2f raw=%d merged=%d" % (total, len(raw), len(silences)))
print("\n=== MERGED SILENCES ===")
for k, (a, b) in enumerate(silences):
    print("  sil%02d [%6.2f - %6.2f] (%.2fs)" % (k, a, b, b - a))

full = "".join(SENTS)
PUNCT_W = {"，":0.55, "、":0.3, "。":1.1, "？":1.1, "！":1.1, "：":0.6, "；":0.7, "—":1.3}
def weight(s):
    w = 0.0
    for ch in s:
        if ch in "《》“”，。？！：；、—":
            w += PUNCT_W.get(ch, 0.0)
        elif ch.strip():
            w += 1.0
    return w

total_w = weight(full)
unit = total / total_w
puncts = []
pos = 0
for si, s in enumerate(SENTS, start=1):
    for ch in s:
        if ch in "，。？：；、—":
            puncts.append({"pos": pos, "ch": ch, "sent": si,
                           "final": ch in "。？", "exp": weight(full[:pos+1]) * unit})
        pos += 1
print("\npunctuations=%d unit=%.4f" % (len(puncts), unit))

n, m = len(puncts), len(silences)
SKIP_P, SKIP_S = 1.2, 1.8
INF = float("inf")
dp = [[INF]*(m+1) for _ in range(n+1)]
bt = [[None]*(m+1) for _ in range(n+1)]
dp[0][0] = 0.0
for i in range(n+1):
    for j in range(m+1):
        if dp[i][j] == INF:
            continue
        if i < n and j < m:
            c = dp[i][j] + abs(puncts[i]["exp"] - (silences[j][0]+silences[j][1])/2)
            if c < dp[i+1][j+1]:
                dp[i+1][j+1] = c; bt[i+1][j+1] = ("M", i, j)
        if i < n:
            c = dp[i][j] + SKIP_P
            if c < dp[i+1][j]:
                dp[i+1][j] = c; bt[i+1][j] = ("P", i, j)
        if j < m:
            c = dp[i][j] + SKIP_S
            if c < dp[i][j+1]:
                dp[i][j+1] = c; bt[i][j+1] = ("S", i, j)

matches = {}
i, j = n, m
while (i, j) != (0, 0):
    op, pi, sj = bt[i][j]
    if op == "M":
        matches[pi] = sj
    i, j = pi, sj

print("\n=== MATCH DETAIL (punct -> silence) ===")
for k, p in enumerate(puncts):
    if k in matches:
        a, b = silences[matches[k]]
        print("  s%02d '%s' exp=%6.2f -> sil[%6.2f-%6.2f] dev=%+.2f" %
              (p["sent"], p["ch"], p["exp"], a, b, (a+b)/2 - p["exp"]))
    else:
        print("  s%02d '%s' exp=%6.2f -> (no pause matched)" % (p["sent"], p["ch"], p["exp"]))

def boundary_time(pi):
    if pi in matches:
        a, b = silences[matches[pi]]
        return a + min(0.15, (b - a) / 2)
    return puncts[pi]["exp"]

sentences = []
prev_end = 0.0
for si in range(1, len(SENTS)+1):
    fins = [k for k, p in enumerate(puncts) if p["sent"] == si and p["final"]]
    if fins:
        end = boundary_time(fins[-1])
    else:
        end = puncts[[k for k, p in enumerate(puncts) if p["sent"] == si][-1]]["exp"]
    sentences.append({"idx": si, "start": round(prev_end, 2), "end": round(end, 2),
                      "text": SENTS[si-1], "display": DISPLAY.get(si, "")})
    prev_end = end

print("\n=== v3b TIMELINE (vs v2) ===")
for s in sentences:
    old = OLD_ENDS.get(s["idx"])
    diff = "  [v2差 %+.2fs]" % (s["end"] - old) if old else ""
    flag = "  <<< 检查" if (s["end"] - s["start"]) < 0.8 or (s["end"] - s["start"]) > 14 else ""
    print("s%02d [%6.2f - %6.2f] (%.2fs)%s%s | %s" %
          (s["idx"], s["start"], s["end"], s["end"]-s["start"], diff, flag, s["text"][:14]))

def s_end(idx): return sentences[idx-1]["end"]
def s_start(idx): return sentences[idx-1]["start"]
bg_periods = [
 {"key": "bg_open",  "start": 0.0,       "end": s_end(3)},
 {"key": "bg_mem",   "start": s_end(3),  "end": s_end(5)},
 {"key": "bg_heart", "start": s_end(5),  "end": s_end(8)},
 {"key": "bg_reg",   "start": s_end(8),  "end": s_end(15)},
 {"key": "bg_int",   "start": s_end(15), "end": round(total, 2)},
]
lyric1 = {"start": s_start(11), "end": s_end(11)}
lyric2 = {"start": s_start(14), "end": s_end(14)}
outro  = {"start": round(max(s_start(18) + 1.0, total - 2.7), 2), "end": round(total, 2)}

with open(os.path.join(ROOT, "assets/audio/timeline_v3.json"), "w", encoding="utf-8") as f:
    json.dump({"total": round(total, 2), "sentences": sentences,
               "bg_periods": bg_periods, "lyric1": lyric1, "lyric2": lyric2, "outro": outro},
              f, ensure_ascii=False, indent=1)
print("\nBG:", [(b["key"], b["start"], b["end"]) for b in bg_periods])
print("lyric1:", lyric1, "lyric2:", lyric2, "outro:", outro)
print("TIMELINE_V3B_DONE")
