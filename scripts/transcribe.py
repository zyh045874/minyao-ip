# -*- coding: utf-8 -*-
"""用 faster-whisper 把 capcut_voice_v2.mp3 实际说的内容转写出来，作为字幕对齐的 ground truth。
绕过 PyAV 版本不兼容：用 ffmpeg 直接解出 16k 单声道 float 数组喂给 whisper。"""
import os, json, subprocess
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import numpy as np
import imageio_ffmpeg
from faster_whisper import WhisperModel

ROOT = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29"
MP3 = os.path.join(ROOT, "assets/audio/capcut_voice_v2.mp3")
FF = imageio_ffmpeg.get_ffmpeg_exe()

print("decoding audio via ffmpeg ...")
raw = subprocess.run([FF, "-i", MP3, "-ar", "16000", "-ac", "1", "-f", "f32le", "-"],
                    capture_output=True).stdout
audio = np.frombuffer(raw, dtype=np.float32)
print("samples:", len(audio), "=> %.1f s" % (len(audio) / 16000.0))

print("loading model base ...")
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio, language="zh", beam_size=5, vad_filter=False,
                                   word_timestamps=True)
print("detected language:", info.language, " duration:", round(info.duration, 2))

out = []
all_words = []
for s in segments:
    t = s.text.strip()
    wseg = []
    for w in getattr(s, "words", []) or []:
        ws = round(w.start, 2); we = round(w.end, 2); wt = w.word.strip()
        wseg.append({"start": ws, "end": we, "word": wt})
        all_words.append({"start": ws, "end": we, "word": wt})
    out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": t, "words": wseg})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {t}")

with open(os.path.join(ROOT, "assets/audio/transcript_v2.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
with open(os.path.join(ROOT, "assets/audio/transcript_words.json"), "w", encoding="utf-8") as f:
    json.dump(all_words, f, ensure_ascii=False, indent=1)
print("\nTRANSCRIPT_DONE segments=%d words=%d" % (len(out), len(all_words)))
