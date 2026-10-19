# -*- coding: utf-8 -*-
"""用本机离线语音(pyttsx3 / Windows SAPI, Microsoft Huihui 中文女声)逐段合成配音 wav。"""
import os, pyttsx3

OUT_DIR = r"C:/Users/LYY/WorkBuddy/2026-10-17-10-20-29/assets/audio"
RATE = 150  # 偏舒缓

SEGMENTS = [
    ("seg1_open", "我是你的民谣翻译官。专门把民谣里，那些没说出口的心事，一句句翻译给你听。今天这一期，咱们聊聊，第一眼。"),
    ("seg2_memory", "你一定记得那种光吧，午后的，刚好落在他睫毛上。风把你一缕头发吹到他肩，你假装看别处，心跳却漏了一拍。后来你见过他好多种样子，最忘不掉的，偏偏就是那一眼。"),
    ("seg3_heart", "我也一样。第一次见他那天，空气里有刚下过雨的青草味，他笑着递来一杯温的，指尖碰到时我慌得把手缩回。那一秒，整条街的嘈杂都静了，只剩他自己。"),
    ("seg4_regret", "可第一眼太短了，短到我还来不及说一句你好。后来我们走散在各自的人海，我再没找回那个味道，那束光。你有没有过，把一个人，永远停在最好看的那一帧。"),
    ("seg5_lyric1", "赵雷唱过，永远都想初次见你那样让我心荡漾。你听，不是爱了多久，是初次两个字，就够让人心荡漾一辈子。我们念念不忘的，从来不是结局，是开头那一下。"),
    ("seg6_lyric2", "可这哪只是我的私心。马頔也写，他说你任何为人称道的美丽，不及他第一次遇见你。原来我们都在偷偷收藏同一束光，全世界的人，都曾输给过某个人第一次的模样。"),
    ("seg7_interact", "这两句歌词，你觉得哪句更好？评论区二选一，告诉我你更偏爱哪一句，又为什么。我呀，先去把那第一眼，再想一遍。"),
    ("seg8_outro", "下一期，你最想听我把哪句歌词翻译出来？打在评论区，下期，翻给你听。"),
]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    engine = pyttsx3.init()
    vs = engine.getProperty("voices")
    zh = None
    for v in vs:
        if "Chinese" in v.name or "zh" in (v.id or "").lower():
            zh = v.id
            break
    if zh:
        engine.setProperty("voice", zh)
    engine.setProperty("rate", RATE)
    engine.setProperty("volume", 1.0)
    for name, text in SEGMENTS:
        path = os.path.join(OUT_DIR, name + ".wav")
        engine.save_to_file(text, path)
        engine.runAndWait()
        print("saved:", name)
    print("TTS_DONE")

if __name__ == "__main__":
    main()
