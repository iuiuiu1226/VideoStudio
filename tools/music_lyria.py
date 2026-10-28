#!/usr/bin/env python3
"""配樂：Google Lyria（與配音同一把 GEMINI_API_KEY），生成後自動檢查有沒有混進人聲。

英文描述要寫風格、BPM、樂器、情緒走向，結尾加 "Instrumental only, no vocals"。
就算寫了 no vocals，還是常混進人聲或英文浮水印，所以每首都用 faster-whisper（含語音偵測）檢查：
聽得出字的片段就淘汰（檔名加 _rejected）。通過的曲子可以重複用在很多支影片。
一首約 0.08 美元。描述與檢查結果存在同名 .json。

用法：
  python3 tools/music_lyria.py "Warm curious background music, 100 BPM, …, Instrumental only, no vocals" \
      --name curious_warm -o assets/music
  python3 tools/music_lyria.py --check assets/music/xxx.mp3      # 只檢查現有的曲子
"""
import argparse
import json
import os
import re
import subprocess

import numpy as np

MODEL = "lyria-3.5"
# whisper 在純音樂上常幻聽出這類字幕文字，不算人聲
HALLUCINATION = re.compile(r"字幕|Amara|訂閱|订阅|感謝觀看|感谢观看|謝謝觀看|MING PAO|"
                           r"thank(s)? (you )?for watching|subscribe", re.I)
WIN, HOP = 8.0, 4.0  # 每 8 秒聽一段、每 4 秒往前滑


def decode16k(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def check_vocals(path, max_voice=0.0, model=None):
    """回傳 (通過與否, 可疑片段)。

    語音偵測（VAD）在有音樂時幾乎聽不到人聲，一次聽 30 秒又容易被音樂帶去幻聽，
    所以改成每 8 秒一段逐段聽：「沒有人聲」機率低於 0.5、又不是常見幻聽字串，就算有人聲。
    （實測：純音樂這個機率都在 0.54 以上；混進與音樂一樣大或小 6 dB 的講話時降到 0.10–0.49）
    中文、英文各聽一次（浮水印常是英文）。可疑片段總長超過 max_voice 秒就淘汰。
    """
    from faster_whisper import WhisperModel
    model = model or WhisperModel("large-v3", device="cpu", compute_type="int8")
    audio = decode16k(path)
    hits = []
    for lang in ("zh", "en"):
        for st in np.arange(0, max(len(audio) / 16000 - WIN / 2, 0.1), HOP):
            x = audio[int(st * 16000):int((st + WIN) * 16000)]
            segs = list(model.transcribe(x, language=lang, vad_filter=False, beam_size=5,
                                         condition_on_previous_text=False, without_timestamps=True)[0])
            text = "".join(s.text for s in segs).strip()
            ns = min((s.no_speech_prob for s in segs), default=1.0)
            if len(re.sub(r"\W", "", text)) >= 2 and ns < 0.5 and not HALLUCINATION.search(text):
                hits.append({"lang": lang, "start": round(float(st), 1),
                             "end": round(float(min(st + WIN, len(audio) / 16000)), 1),
                             "text": text, "no_speech": round(ns, 2)})
    spans = sorted((h["start"], h["end"]) for h in hits)
    voiced, cur = 0.0, None
    for a, b in spans:  # 重疊的片段合併後算總長
        if cur and a <= cur[1]:
            cur[1] = max(cur[1], b)
        else:
            voiced += (cur[1] - cur[0]) if cur else 0.0
            cur = [a, b]
    voiced += (cur[1] - cur[0]) if cur else 0.0
    return voiced <= max_voice, hits


def save_audio(path_noext, data):
    ext = ".wav" if data[:4] == b"RIFF" else ".mp3"
    path = path_noext + ext
    open(path, "wb").write(data)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", help="英文描述")
    ap.add_argument("--name", help="檔名（不含副檔名）")
    ap.add_argument("-o", "--out", default="assets/music")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--max-voice", type=float, default=0.0, help="可疑人聲超過幾秒就淘汰（預設有就淘汰）")
    ap.add_argument("--check", help="只檢查這個現有音檔有沒有人聲")
    args = ap.parse_args()

    if args.check:
        ok, hits = check_vocals(args.check, args.max_voice)
        print(f"{args.check}：{'通過（沒有人聲）' if ok else '有人聲，淘汰'}")
        for h in hits:
            print(f"  {h['start']:6.1f}–{h['end']:6.1f}s [{h['lang']}] {h['text']}")
        return

    if not (args.prompt and args.name):
        ap.error("生成新曲子需要英文描述與 --name")
    from gemini_api import ApiError, find_audio, post
    os.makedirs(args.out, exist_ok=True)
    try:
        data, mime = find_audio(post({"model": args.model, "input": args.prompt}))
    except ApiError as e:
        raise SystemExit(f"配樂生成失敗：{e}")
    path = save_audio(os.path.join(args.out, args.name), data)
    ok, hits = check_vocals(path, args.max_voice)
    info = {"model": args.model, "prompt": args.prompt, "mime": mime, "vocals_ok": ok, "suspect": hits}
    if not ok:
        root, ext = os.path.splitext(path)
        os.replace(path, root + "_rejected" + ext)
        path = root + "_rejected" + ext
    with open(os.path.splitext(path)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    dur = len(decode16k(path)) / 16000
    print(f"{path}  {dur:.1f} 秒  {'通過（沒有人聲）' if ok else '有人聲，已淘汰'}")
    for h in hits:
        print(f"  {h['start']:6.1f}–{h['end']:6.1f}s [{h['lang']}] {h['text']}")


if __name__ == "__main__":
    main()
