#!/usr/bin/env python3
"""從素材裡做「背景聲」循環檔，給 build_segment 的 room 用：補停頓（pad、hold）時放這支素材本來的空氣聲，
不要突然變成完全無聲（教室、現場錄音都有背景聲，忽然全靜音再出現，聽起來很不自然）。

做法：
1. 找整支最安靜的 0.8 秒（平均音量最低、而且中間沒有突然的聲音），用 whisper 確認沒有人聲
2. 這 0.8 秒＋倒放接起來（接縫交疊淡入淡出），可以無縫循環
3. 音量調到跟「講話中間的空檔」一樣（整支每 10 毫秒音量的最小 10%），補的停頓跟原本的停頓聽起來一樣大

用法：
  python3 tools/roomtone.py <工作檔.MOV> <輸出 room_xxx.wav> [--check] [--win 開始秒 結束秒]
  --win：只在這段時間裡找、音量也跟這段的空檔對齊（同一支素材前後背景聲差很多時用，例如後半台下人多、比較吵）
"""
import argparse
import subprocess

import numpy as np


def env16k(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    return y, 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + 160] ** 2)) for i in range(0, len(y) - 160, 160)]) + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--check", action="store_true", help="用 whisper 確認挑到的那段沒有人聲")
    ap.add_argument("--win", nargs=2, type=float, metavar=("START", "END"), help="只在這段時間裡找（秒）")
    args = ap.parse_args()
    y, e = env16k(args.video)
    W = 80
    best = None
    k0, k1 = 50, len(e) - W - 50
    if args.win:
        k0, k1 = max(k0, int(args.win[0] * 100)), min(k1, int(args.win[1] * 100) - W)
    for k in range(k0, k1, 5):
        seg = e[k:k + W]
        score = seg.mean() + 0.7 * max(0, seg.max() - seg.mean() - 5)
        if best is None or score < best[0]:
            best = (score, k)
    t = best[1] / 100
    floor = np.percentile(e[k0:k1 + W], 10)
    seg = y[int(t * 16000):int((t + 0.8) * 16000)]
    lvl = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
    gain = floor - lvl
    print(f"最安靜的 0.8 秒：{t:.2f} 秒起（{lvl:.1f} dB）；講話中間空檔約 {floor:.1f} dB → 背景聲調 {gain:+.1f} dB")
    if args.check:
        from faster_whisper import WhisperModel
        wm = WhisperModel("large-v3", device="cpu", compute_type="int8")
        z = np.concatenate([np.zeros(8000, np.float32), seg * 4, np.zeros(8000, np.float32)])
        segs = list(wm.transcribe(z, language="zh", beam_size=5, condition_on_previous_text=False)[0])
        print("人聲機率（no_speech 越接近 1 越沒有人聲）：", round(segs[0].no_speech_prob, 2) if segs else 1.0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-t", "0.8", "-i", args.video, "-vn", "-ac", "2", "-ar", "48000",
                    "-filter_complex", f"[0:a]volume={gain:.1f}dB,asplit=2[x][y];[y]areverse[r];[x][r]acrossfade=d=0.1[xr];"
                    "[xr]asplit=2[p][q];[p][q]acrossfade=d=0.1", args.out], check=True)
    print("→", args.out)


if __name__ == "__main__":
    main()
