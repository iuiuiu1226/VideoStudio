#!/usr/bin/env python3
"""旁白配音：Gemini TTS，一句一個檔，唸錯只重配那一句。

稿子是純文字檔，一行一句（空行和 # 開頭的行略過）；句中的「|」是字幕斷行記號，配音時會拿掉。
輸出到 --out 資料夾：
  line01.wav、line02.wav…（24 kHz 單聲道）與 lines.json（每句的稿子文字）
已經配好的句子預設不重配；--only 3,5 只重配第 3、5 句，--force 全部重配。
配完請跑 tools/check_voice.py 逐句比對有沒有唸錯、多字或漏字。

用法：
  python3 tools/voice_gemini.py scripts/narration/test.txt --out work/test_vo [--voice Charon] [--style "…"]
"""
import argparse
import json
import os
import wave

from gemini_api import ApiError, find_audio, post

MODEL = "gemini-3.8-flash-tts"
VOICE = "Charon"  # 男聲；可換其他聲音名
STYLE = ("台灣口音的國語，語速中等、自然不急，語氣親切真誠，像在跟朋友分享一件有趣的事，咬字清楚。"
         "只唸稿上的字，一字不加、一字不減，不要唸出標點符號。")
SR = 24000


def read_script(path):
    lines = [l.strip() for l in open(path, encoding="utf-8")]
    return [l for l in lines if l and not l.startswith("#")]


def synth(text, voice, style, model):
    body = {"model": model,
            "input": [{"type": "user_input", "content": [{
                "type": "text", "text": text.replace("|", ""),
                "annotations": [{"type": "speech_metadata", "style": style}]}]}],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice}]}}
    return find_audio(post(body))


def save_wav(path, data):
    if data[:4] == b"RIFF":  # 已經是 wav
        open(path, "wb").write(data)
        return
    with wave.open(path, "wb") as w:  # 原始 PCM（16-bit、24 kHz、單聲道）補上 wav 檔頭
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--style", default=STYLE)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--only", default="", help="只重配這幾句，例如 2,5（從 1 開始）")
    ap.add_argument("--force", action="store_true", help="全部重配")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    texts = read_script(args.script)
    only = {int(x) for x in args.only.split(",") if x.strip()}
    meta = {"voice": args.voice, "style": args.style, "model": args.model,
            "lines": [{"n": i + 1, "text": t, "file": f"line{i + 1:02d}.wav"} for i, t in enumerate(texts)]}
    for ln in meta["lines"]:
        path = os.path.join(args.out, ln["file"])
        redo = args.force or ln["n"] in only or (not only and not os.path.exists(path))
        if not redo:
            continue
        try:
            data, mime = synth(ln["text"], args.voice, args.style, args.model)
        except ApiError as e:
            raise SystemExit(f"第 {ln['n']} 句配音失敗：{e}")
        save_wav(path, data)
        print(f"第 {ln['n']:2d} 句 → {path}  {mime}  「{ln['text']}」")
    with open(os.path.join(args.out, "lines.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
