# -*- coding: utf-8 -*-
"""第2期：edge-tts 4 大块合成（句级边界精确定位）+ numpy 拼接
产出：assets/audio/ep2_voice.wav + assets/audio/timeline_ep2.json（16 行精确时间轴）
"""
import os, json, asyncio, subprocess, wave, re, time
import numpy as np
import imageio_ffmpeg
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD  = os.path.join(ROOT, "assets", "audio")
WAV  = os.path.join(AUD, "ep2_voice.wav")
TL   = os.path.join(AUD, "timeline_ep2.json")
PROXY = "http://127.0.0.1:7897"
VOICE = "zh-CN-XiaoxiaoNeural"
RATE  = "-3%"
SR = 44100
FF = imageio_ffmpeg.get_ffmpeg_exe()

# 每句 → 对应字幕行（1~2 行/句），行文本不带句末标点用于显示
SENT_LINES = [
    ("越长大，越不敢听《安和桥》。", ["越长大，越不敢听《安和桥》"]),
    ("宋冬野唱，那些夏天，就像青春一样回不来。", ["宋冬野唱，那些夏天", "就像青春一样回不来"]),
    ("可你心里清楚，回不来的哪是夏天。", ["可你心里清楚", "回不来的，哪是夏天"]),
    ("是那年夏天，陪你走过安和桥的人。", ["是那年夏天", "陪你走过安和桥的人"]),
    ("后来你们没吵没闹，就那么走散了。", ["后来你们没吵没闹", "就那么走散了"]),
    ("连一句再见，都没来得及说。", ["连一句再见，都没来得及说"]),
    ("我们怀念的从来不是青春，是那个还相信永远的自己。", ["我们怀念的从来不是青春", "是那个还相信永远的自己"]),
    ("你回不去的，是那个夏天，还是那个人？", ["你回不去的", "是那个夏天，还是那个人"]),
    ("评论区告诉我。", ["评论区告诉我"]),
    ("下一期，翻你点名的歌词。", ["下一期，翻你点名的歌词"]),
]
# 打包成 4 大块（减少连接数、语调更连贯）
BLOCKS = [[0, 1], [2, 3, 4], [5, 6], [7, 8, 9]]

PUNC = "，。？！、；：“”《》（）…—·,.?!;:\"'()<>[] "

def norm(s):
    return re.sub("[" + re.escape(PUNC) + "]", "", s)

def decode(mp3_bytes):
    p = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
                        "-f", "s16le", "-ar", str(SR), "-ac", "1", "pipe:1"],
                       input=mp3_bytes, capture_output=True)
    if not p.stdout:
        raise RuntimeError("decode fail: " + p.stderr.decode("utf-8", "ignore")[:200])
    return np.frombuffer(p.stdout, dtype=np.int16)

async def synth_with_retry(text, tries=4):
    last = None
    for k in range(tries):
        try:
            c = edge_tts.Communicate(text, VOICE, rate=RATE, proxy=PROXY)
            buf = bytearray(); bnd = []
            async for ch in c.stream():
                if ch["type"] == "audio":
                    buf.extend(ch["data"])
                elif ch["type"] == "SentenceBoundary":
                    bnd.append((ch["offset"] / 1e7, ch["duration"] / 1e7))
            if buf:
                return bytes(buf), bnd
            last = RuntimeError("empty audio")
        except Exception as e:
            last = e
        await asyncio.sleep(2.0 * (k + 1))
    raise last

def split_lines(s_start, s_end, texts):
    w = [len(norm(t)) or 1 for t in texts]
    tw = sum(w); dur = s_end - s_start
    res, acc = [], 0
    for t, wi in zip(texts, w):
        a = s_start + dur * acc / tw
        acc += wi
        b = s_start + dur * acc / tw
        res.append((round(a, 3), round(b, 3), t))
    return res

async def main():
    os.makedirs(AUD, exist_ok=True)
    pcm_parts, timeline, cursor = [], [], 0.0
    for bi, block in enumerate(BLOCKS):
        text = "".join(SENT_LINES[i][0] for i in block)
        mp3, bnd = await synth_with_retry(text)
        pcm = decode(mp3)
        dur = len(pcm) / SR
        # 兜底：若句边界数量不符，按句长比例均分
        if len(bnd) != len(block):
            wsum = sum(len(norm(SENT_LINES[i][0])) for i in block); acc = 0.0
            bnd = []
            for i in block:
                w0 = len(norm(SENT_LINES[i][0]))
                bnd.append((dur * acc / wsum, dur * w0 / wsum)); acc += w0
        for (i, (so, sd)) in zip(block, bnd):
            texts = SENT_LINES[i][1]
            for (a, b, t) in split_lines(cursor + so, cursor + so + sd, texts):
                timeline.append({"start": a, "end": b, "text": t})
                print(f"  [{a:6.2f}-{b:6.2f}] {t}")
        pcm_parts.append(pcm)
        gap = int(SR * 0.5)
        pcm_parts.append(np.zeros(gap, dtype=np.int16))
        cursor += dur + 0.5
        await asyncio.sleep(0.8)

    audio = np.concatenate(pcm_parts).astype(np.int16)
    with wave.open(WAV, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(audio.tobytes())
    total = round(len(audio) / SR, 2)
    json.dump({"total": total, "voice": VOICE, "sentences": timeline},
              open(TL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nSAVED", WAV, " TOTAL %.2fs  lines=%d" % (total, len(timeline)))

asyncio.run(main())
