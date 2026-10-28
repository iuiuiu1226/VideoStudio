#!/usr/bin/env python3
"""旁白＋配樂合成一支直式短影音（1080x1920）。

輸入是 voice_gemini.py 配好、check_voice.py 檢查過的資料夾（lines.json＋每句 wav）：
  - 每句先剪掉頭尾空白，句與句之間留 --gap 秒的停頓
  - 字幕一句拆成幾段（遇到標點或「|」就斷、每段最多 12 字），時間用 check_voice 記下的逐字時間對齊
  - 配樂：不夠長就從頭接續，頭尾淡入淡出，音量壓在旁白下方 --music-db（預設 -18 dB），不搶旁白
  - 整支響度做到 --lufs（預設 -14 LUFS，兩段式 loudnorm 線性調整），峰值再用 alimiter 限幅
  - 背景可以是顏色（預設深藍）、圖片或影片（影片不夠長會循環）

用法：
  python3 tools/narrate.py work/test_vo --music assets/music/curious_warm.mp3 \
      --font <字型資料夾> -o output/narrate_test.mp4 [--bg 圖片或影片] [--title "BK 測試｜生活應用"]
"""
import argparse
import json
import os
import re
import subprocess
import tempfile
import wave

import numpy as np

from build_segment import build_ass

W, H, FPS, SR = 1080, 1920, 30, 48000
MAX_CHARS = 12


def decode(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def write_wav(path, y):
    y = np.clip(y, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(y.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


def trim_bounds(y, pad=0.08, thresh_db=-45):
    """回傳 (開口, 收尾) 秒數：以 10 ms 能量找第一個、最後一個高於門檻的位置，各留 pad 秒。"""
    hop = SR // 100
    n = len(y) // hop
    db = 20 * np.log10(np.sqrt((y[:n * hop, 0].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    on = np.nonzero(db > thresh_db)[0]
    if not len(on):
        return 0.0, len(y) / SR
    return max(0.0, on[0] * hop / SR - pad), min(len(y) / SR, (on[-1] + 1) * hop / SR + pad)


def chunks(text):
    """一句拆成字幕段：遇到標點或「|」就斷，太長再對半切；回傳 [(段落文字, 在原句中的起訖字元位置)]。

    「|」是稿子裡的字幕斷行記號（配音時會拿掉），長句請自己標在詞與詞之間，避免從詞中間切開。"""
    out, pos = [], 0
    for part in re.split(r"([，。！？、；：,.!?;:|])", text):
        start = pos
        pos += len(part)
        if not part.strip() or re.fullmatch(r"[，。！？、；：,.!?;:|]", part):
            continue
        while len(part) > MAX_CHARS:
            cut = len(part) // 2 if len(part) <= MAX_CHARS * 2 else MAX_CHARS
            out.append((part[:cut], start, start + cut))
            part, start = part[cut:], start + cut
        out.append((part, start, start + len(part)))
    return out


def chunk_times(ln, t0, t1):
    """字幕段的時間：有逐字時間就照字數對到辨識出來的字，沒有就照字數比例分配。"""
    text = ln["text"]
    parts = chunks(text)
    n_chars = max(1, sum(e - s for _, s, e in parts))
    words = ln.get("words") or []
    stamps = []  # 每個辨識出來的「字」的開始時間
    for ws, we, w in words:
        w = re.sub(r"\W", "", w)
        for k in range(len(w)):
            stamps.append(ws + (we - ws) * k / max(1, len(w)))
    res, acc = [], 0
    for txt, s, e in parts:
        if len(stamps) >= n_chars * 0.8:
            i = min(len(stamps) - 1, int(acc / n_chars * len(stamps)))
            st = stamps[i]
        else:
            st = t0 + (t1 - t0) * acc / n_chars
        res.append([st, txt])
        acc += e - s
    for i, r in enumerate(res):
        r.append(res[i + 1][0] if i + 1 < len(res) else t1)
    return [(max(t0, s), min(t1, e), txt) for s, txt, e in res]


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float([l.split()[1] for l in r.splitlines() if l.strip().startswith("I:")][-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voice", help="voice_gemini.py 的輸出資料夾")
    ap.add_argument("--music", help="配樂檔（mp3／wav）")
    ap.add_argument("--music-db", type=float, default=-18.0, help="配樂比旁白低幾 dB")
    ap.add_argument("--gap", type=float, default=0.35, help="句與句之間的停頓（秒）")
    ap.add_argument("--head", type=float, default=0.6)
    ap.add_argument("--tail", type=float, default=1.5)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--bg", default="0x0D1018", help="背景：顏色（0xRRGGBB）、圖片或影片")
    ap.add_argument("--title", default="", help="上方常駐標題")
    ap.add_argument("--font", required=True, help="含字型檔的資料夾")
    ap.add_argument("--margin-v", type=int, default=660, help="字幕離下緣距離（預設胸口高度）")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    meta = json.load(open(os.path.join(args.voice, "lines.json"), encoding="utf-8"))
    tmp = tempfile.mkdtemp()

    # 1. 旁白：每句剪掉頭尾空白後依序排好
    pieces, events, t = [np.zeros((int(args.head * SR), 1), np.float32)], [], args.head
    for i, ln in enumerate(meta["lines"]):
        y = decode(os.path.join(args.voice, ln["file"]), 1)
        a, b = trim_bounds(y)
        seg = y[int(a * SR):int(b * SR)]
        shifted = dict(ln, words=[[ws - a + t, we - a + t, w] for ws, we, w in ln.get("words", [])])
        events += [(s, e, txt, "Default") for s, e, txt in chunk_times(shifted, t, t + len(seg) / SR)]
        pieces.append(seg)
        t += len(seg) / SR
        if i + 1 < len(meta["lines"]):
            pieces.append(np.zeros((int(args.gap * SR), 1), np.float32))
            t += args.gap
    for k in range(len(events) - 1):  # 句間停頓不到 1 秒時字幕延續，不會一閃一閃
        if 0 < events[k + 1][0] - events[k][1] < 1.0:
            events[k] = (events[k][0], events[k + 1][0], *events[k][2:])
    pieces.append(np.zeros((int(args.tail * SR), 1), np.float32))
    voice = np.concatenate(pieces)
    total = len(voice) / SR
    write_wav(os.path.join(tmp, "voice.wav"), np.repeat(voice, 2, axis=1))

    # 2. 配樂：循環到夠長、淡入淡出，音量對齊到旁白下方 music_db
    mix = np.repeat(voice, 2, axis=1)
    if args.music:
        m = decode(args.music, 2)
        reps = int(np.ceil(len(mix) / len(m)))
        m = np.concatenate([m] * reps)[:len(mix)]
        fi, fo = int(1.0 * SR), int(2.5 * SR)
        m[:fi] *= np.linspace(0, 1, fi)[:, None]
        m[-fo:] *= np.linspace(1, 0, fo)[:, None]
        write_wav(os.path.join(tmp, "music.wav"), m)
        gain_db = lufs(os.path.join(tmp, "voice.wav")) + args.music_db - lufs(os.path.join(tmp, "music.wav"))
        mix = mix + m * 10 ** (gain_db / 20)
        print(f"配樂增益 {gain_db:+.1f} dB（比旁白低 {-args.music_db:.0f} dB）")
    write_wav(os.path.join(tmp, "mix.wav"), mix / max(1.0, np.abs(mix).max()))

    # 3. 響度：兩段式 loudnorm 線性調整到目標，再限幅
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", os.path.join(tmp, "mix.wav"), "-af",
                        f"loudnorm=I={args.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    mj = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    final = os.path.join(tmp, "final.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(tmp, "mix.wav"), "-af",
                    f"loudnorm=I={args.lufs}:TP=-1.5:LRA=11:linear=true:measured_I={mj['input_i']}:"
                    f"measured_TP={mj['input_tp']}:measured_LRA={mj['input_lra']}:"
                    f"measured_thresh={mj['input_thresh']}:offset={mj['target_offset']},"
                    "alimiter=limit=0.89:level=false,aresample=48000", "-ar", "48000", final], check=True)

    # 4. 畫面：背景＋字幕
    style = {"font": "Noto Sans TC", "size": 78, "outline": 4, "shadow": 1, "margin_v": args.margin_v}
    if args.title:
        events += [(0, total, args.title, "Title")]
    ass = os.path.join(tmp, "subs.ass")
    build_ass(events, ass, style)
    if re.fullmatch(r"0x[0-9A-Fa-f]{6}", args.bg):
        vin = ["-f", "lavfi", "-i", f"color=c={args.bg}:s={W}x{H}:r={FPS}:d={total:.3f}"]
    elif os.path.splitext(args.bg)[1].lower() in (".jpg", ".jpeg", ".png"):
        vin = ["-loop", "1", "-framerate", str(FPS), "-i", args.bg]
    else:
        vin = ["-stream_loop", "-1", "-i", args.bg]
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
          f"trim=duration={total:.3f},setpts=PTS-STARTPTS,format=yuv420p,"
          f"subtitles={ass}:fontsdir={args.font}[v]")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *vin, "-i", final, "-filter_complex", vf,
                    "-map", "[v]", "-map", "1:a", "-t", f"{total:.3f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", args.out], check=True)
    print(f"{args.out}  {total:.1f} 秒，響度目標 {args.lufs} LUFS")


if __name__ == "__main__":
    main()
