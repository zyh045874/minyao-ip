# -*- coding: utf-8 -*-
"""复刻 gen_video_v4.py 的字幕边界计算，仅打印与真实停顿的对齐校验，不重新渲染。"""
import os, re, json, subprocess
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
AUD = os.path.join(ROOT, "assets/audio")
mp3 = os.path.join(AUD, "capcut_voice_v2.mp3")

def real_silences(mp3):
    r = subprocess.run([FF, "-i", mp3, "-af", "silencedetect=noise=-32dB:d=0.22",
                        "-f", "null", "-"], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore").stderr
    s = sorted(set(round(float(x), 3) for x in re.findall(r"silence_start: ([\d.]+)", r)))
    cs = []
    for x in s:
        if cs and abs(x - cs[-1]) < 0.5: cs[-1] = (cs[-1] + x) / 2
        else: cs.append(x)
    return cs
C = real_silences(mp3)
print("真实停顿数量 =", len(C))

TL = json.load(open(os.path.join(AUD, "timeline_v3.json"), encoding="utf-8"))
S = TL["sentences"]; outro = TL["outro"]
def seg(i): return S[i - 1]

TEXTS = {
 1:"你有没有过——后来你再怎么努力，\n都复制不了，第一次见他的那一眼。",
 2:"我是笔澜，专门把民谣里\n没说出口的心事，翻译给你听。",
 3:"今天，聊第一眼。",
 4:"你一定记得那种光吧，午后的，\n刚好落在他睫毛上。",
 5:"风把一缕他的头发吹到肩上，\n你假装看别处，心跳漏了一拍。",
 6:"我也一样。",
 7:"见他那天刚下过雨，\n他笑着递来一杯温的，指尖碰到，\n我慌得把手缩回。",
 8:"那一秒，整条街都静了。",
 9:"可第一眼太短了，\n短到来不及说一句你好。",
 10:"后来我们走散在人海，\n我再没找回那束光——\n你有没有过，把一个人，\n永远停在最好看的那一帧？",
 12:"不是爱了多久，是“初次”两个字，\n就够让人心荡漾一辈子。",
 13:"我们念念不忘的，\n从来不是结局，是开头那一下。",
 15:"原来全世界的人，\n都曾输给过某个人第一次的模样。",
 16:"这两句歌词，你觉得哪句更好？",
 17:"评论区二选一。",
 18:"顺便，把下一期想听的歌词，\n也打在评论区——翻给你听。",
}
SUB_IDX = [1,2,3,4,5,6,7,8,9,10,12,13,15,16,17,18]
def nearest(t): return min(C, key=lambda c: abs(c - t))
def snap(t, maxdist=1.0):
    n = nearest(t)
    return round(n, 2) if abs(t - n) <= maxdist else round(t, 2)

SUBS = []
for i in SUB_IDX:
    st = seg(i)["start"]; en = seg(i)["end"]
    if i == 18: en = outro["start"]
    SUBS.append((snap(st), snap(en), TEXTS[i]))

print("\n[校验] 每条字幕 开始/结束 -> 最近真实停顿 偏差：")
maxd = 0
for i, (st, en, txt) in zip(SUB_IDX, SUBS):
    ds = abs(st - nearest(st)); de = abs(en - nearest(en))
    maxd = max(maxd, ds, de)
    mark = "OK" if (ds <= 0.4 and de <= 0.4) else "⚠️"
    print(f"  #{i:2d}  {st:6.2f}~{en:6.2f}  Δstart={ds:+.2f} Δend={de:+.2f}  {mark}")
print(f"\n最大边界偏差 = {maxd:.2f}s  （≤0.4s 视为与配音同步）")
print("✅ 同步良好" if maxd <= 0.4 else "⚠️ 仍有偏差较大处")
