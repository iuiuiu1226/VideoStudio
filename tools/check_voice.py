#!/usr/bin/env python3
"""逐句檢查配音：本機 faster-whisper 辨識每一句，跟稿子逐字比對，抓唸錯、多字、漏字。

同時把每個字的時間寫回 lines.json（字幕對齊用），以及每句實際開口、收尾的時間（剪掉頭尾空白用）。
比對前會去掉標點、空白，簡體轉繁體、英文轉大寫；數字唸法（80／八十）不同會被列出來，請人工確認。
有問題的句子用 tools/voice_gemini.py --only N 重配。

用法：
  python3 tools/check_voice.py work/test_vo
"""
import argparse
import difflib
import json
import os
import re
import wave

import numpy as np

PUNCT = re.compile(r"[\s，。、！？；：「」『』（）《》〈〉…⋯—\-,.!?;:\"'()\[\]|]")


def norm(s, cc):
    return PUNCT.sub("", cc.convert(s)).upper()


def load_wav(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != 16000:  # whisper 要 16 kHz
        a = np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)
    return a


def describe(expected, heard):
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, expected, heard).get_opcodes():
        if op == "replace":
            out.append(f"「{expected[i1:i2]}」唸成「{heard[j1:j2]}」")
        elif op == "delete":
            out.append(f"漏了「{expected[i1:i2]}」")
        elif op == "insert":
            out.append(f"多了「{heard[j1:j2]}」")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="voice_gemini.py 的輸出資料夾（含 lines.json）")
    ap.add_argument("--model", default="large-v3")
    args = ap.parse_args()

    import opencc
    from faster_whisper import WhisperModel
    cc = opencc.OpenCC("s2tw")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    meta_path = os.path.join(args.folder, "lines.json")
    meta = json.load(open(meta_path, encoding="utf-8"))
    bad = []
    for ln in meta["lines"]:
        audio = load_wav(os.path.join(args.folder, ln["file"]))
        segs, _ = model.transcribe(audio, language="zh", initial_prompt="以下是繁體中文。",
                                   beam_size=5, word_timestamps=True, vad_filter=False)
        words = [w for s in segs for w in s.words]
        heard = "".join(w.word for w in words)
        exp, got = norm(ln["text"], cc), norm(heard, cc)
        ratio = difflib.SequenceMatcher(None, exp, got).ratio()
        ln.update({
            "heard": cc.convert(heard).strip(), "match": round(ratio, 3),
            "duration": round(len(audio) / 16000, 3),
            "speech_start": round(words[0].start, 3) if words else 0.0,
            "speech_end": round(words[-1].end, 3) if words else round(len(audio) / 16000, 3),
            "words": [[round(w.start, 3), round(w.end, 3), cc.convert(w.word).strip()] for w in words],
        })
        diffs = describe(exp, got)
        ok = not diffs
        print(f"第 {ln['n']:2d} 句 {'OK  ' if ok else '要確認'} 相符 {ratio:.0%}  稿：{ln['text']}")
        if not ok:
            print(f"        聽到：{ln['heard']}\n        差異：{'；'.join(diffs)}")
            bad.append(ln["n"])
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    if bad:
        print(f"\n要確認的句子：{','.join(map(str, bad))}（確定唸錯就用 voice_gemini.py --only {','.join(map(str, bad))} 重配）")
    else:
        print("\n全部相符")


if __name__ == "__main__":
    main()
