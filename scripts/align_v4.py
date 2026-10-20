# -*- coding: utf-8 -*-
"""align_v4.py —— 用 faster-whisper 真实词级时间戳，重建字幕时间轴。

彻底替代 align_v3b.py 的"按字数估时"（那是漂移根因）。
做法：把 18 句字幕正文拼成一条 clean 串，把转写出的词拼成 whisper 串，
用 difflib 对齐两者，再按"句子覆盖到哪些真实词"取真实起止时间。
输出 assets/audio/timeline_v4.json（与 timeline_v3.json 同 schema，时间是真实的）。
"""
import os, json, difflib

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
AUD = os.path.join(ROOT, "assets/audio")

TL3 = json.load(open(os.path.join(AUD, "timeline_v3.json"), encoding="utf-8"))
WORDS = json.load(open(os.path.join(AUD, "transcript_words.json"), encoding="utf-8"))

# ---- 繁->简 归一化（覆盖转写里出现的常见繁体，提升对齐质量） ----
T2S = {
 "後":"后","複":"复","專":"专","裡":"里","語":"语","謠":"谣","說":"说","該":"该","稱":"称",
 "麗":"丽","這":"这","兩":"两","個":"个","來":"来","還":"还","會":"会","幀":"帧","樣":"样",
 "們":"们","從":"从","頭":"头","髮":"发","剛":"刚","過":"过","遞":"递","溫":"温","慌":"慌",
 "縮":"缩","回":"回","靜":"静","對":"对","輸":"输","給":"给","評":"评","論":"论","區":"区",
 "順":"顺","備":"备","聽":"听","親":"亲","見":"见","顏":"颜","歲":"岁","師":"师","點":"点",
 "當":"当","場":"场","覺":"觉","誰":"谁","認":"认","錯":"错","讓":"让","話":"话","讀":"读",
 "書":"书","間":"间","關":"关","開":"开","題":"题","學":"学","體":"体","禮":"礼","視":"视",
 "詞":"词","親":"亲","歲":"岁","氣":"气","愛":"爱","夢":"梦","機":"机","電":"电","時":"时",
 "題":"题","長":"长","東":"东","車":"车","鳥":"鸟","魚":"鱼","馬":"马","為":"为","與":"与",
 "爾":"尔","續":"续","終":"终","處":"处","歡":"欢","歲":"岁","興":"兴","樂":"乐","殺":"杀",
}
def norm(s):
    return "".join(T2S.get(ch, ch) for ch in s)

PUNCT = set("，。、：；！？—“”‘’（）《》…·,.!?;:\"'()[]{} \n\t")

# ---- 1) 拼 clean 串（18 句正文，去标点），记录每句 char 区间 ----
sent_texts = [s["text"] for s in TL3["sentences"]]   # idx 1..18 顺序
clean_parts, spans = [], []
cpos = 0
for t in sent_texts:
    pt = "".join(ch for ch in t if ch not in PUNCT)
    pt = norm(pt)
    spans.append((cpos, cpos + len(pt)))
    clean_parts.append(pt)
    cpos += len(pt)
clean = "".join(clean_parts)
Nc = len(clean)

# ---- 2) 拼 whisper 串（词），记录每词 char 区间 + 时间 ----
wparts, wspans = [], []
wpos = 0
for w in WORDS:
    wt = norm("".join(ch for ch in w["word"] if ch not in PUNCT))
    wspans.append((wpos, wpos + len(wt), w["start"], w["end"]))
    wparts.append(wt)
    wpos += len(wt)
whisper = "".join(wparts)
Nw = len(whisper)

# ---- 3) difflib 对齐，建 char<->char 双向映射 ----
sm = difflib.SequenceMatcher(None, clean, whisper, autojunk=False)
blocks = sm.get_matching_blocks()
c2w = [None] * Nc
w2c = [None] * Nw
for i, j, size in blocks:
    for k in range(size):
        if i + k < Nc: c2w[i + k] = j + k
        if j + k < Nw: w2c[j + k] = i + k
# 填空（前向+后向最近）
def fill_none(arr):
    last = None
    for k in range(len(arr)):
        if arr[k] is None:
            arr[k] = last
        else:
            last = arr[k]
    last = None
    for k in range(len(arr) - 1, -1, -1):
        if arr[k] is None:
            arr[k] = last
        else:
            last = arr[k]
    return arr
c2w = fill_none(c2w)
w2c = fill_none(w2c)

# ---- 4) 逐句：找出覆盖该句 char 区间的真实词，取时间 ----
def sent_time(c0, c1):
    ts, te = [], []
    for (j0, j1, ws, we) in wspans:
        ci0 = w2c[j0]; ci1 = w2c[j1 - 1]
        if ci0 is None or ci1 is None:
            continue
        # 词覆盖的 clean 区间与句子区间有无重叠
        lo, hi = min(ci0, ci1), max(ci0, ci1)
        if hi >= c0 and lo < c1:
            ts.append(ws); te.append(we)
    if not ts:
        return None
    return (round(min(ts), 2), round(max(te), 2))

new_sentences = []
for idx, s in enumerate(TL3["sentences"]):
    c0, c1 = spans[idx]
    t = sent_time(c0, c1)
    if t is None:
        t = (s["start"], s["end"])  # 兜底用旧值
    new_sentences.append({
        "idx": s["idx"], "start": t[0], "end": t[1],
        "text": s["text"], "display": s.get("display", "")
    })

# ---- 5) bg_periods / lyric / outro 也重锚到真实段落 ----
def seg_anchor(approx):
    # 找离 approx 最近的真实词时间
    return min(WORDS, key=lambda w: abs(w["start"] - approx))["start"]

# 真实段落边界（来自段落语义 + 词时间戳）
bg_periods = [
    {"key": "bg_open",  "start": 0.0,       "end": 16.38},
    {"key": "bg_mem",   "start": 16.38,     "end": 25.68},
    {"key": "bg_heart", "start": 25.68,     "end": 47.74},
    {"key": "bg_reg",   "start": 47.74,     "end": 87.90},
    {"key": "bg_int",   "start": 87.90,     "end": 102.48},
]
# 歌词卡：赵雷《程艾影》"永远都想初次见你那样让我心荡漾" ~ 真实 50.26-58.46
#        马頔《南山南》"他说你任何为人称道的美丽不及他第一次遇见你" ~ 真实 74.38-87.90
lyric1 = {"start": 50.26, "end": 58.46}
lyric2 = {"start": 74.38, "end": 87.90}
outro  = {"start": 99.78, "end": 102.48}

out = {
    "total": TL3["total"],
    "sentences": new_sentences,
    "bg_periods": bg_periods,
    "lyric1": lyric1,
    "lyric2": lyric2,
    "outro": outro,
}
with open(os.path.join(AUD, "timeline_v4.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

# ---- 报告：旧(估算) vs 新(真实) 起止，看漂移修了多少 ----
print("idx  旧start 新start 旧end  新end   漂移(start)")
for i, s in enumerate(new_sentences):
    old = TL3["sentences"][i]
    drift = round(s["start"] - old["start"], 2)
    print(f"{s['idx']:>3}  {old['start']:>6}  {s['start']:>6}  {old['end']:>6}  {s['end']:>6}   {drift:+.2f}s")
print("\nDONE -> timeline_v4.json")
