#!/usr/bin/env python3
"""把背景音樂的段落音量拉平，整首維持差不多一樣大。

曲子本身常有「收斂段」（例如間奏變小聲），放在影片底下會覺得音樂忽大忽小。
這個工具以約 4 秒為單位量音量，算出一條很平滑的補償曲線（最多 ±6 dB），
只修正段落之間的大小差，不影響鼓點本身的律動。
--keep-tail 秒數之後不補償，保留曲子自然的收尾。

用法：
  python3 tools/level_music.py music.wav -o music_leveled.wav [--keep-tail 2.5]
"""
import argparse
import subprocess
import wave

import numpy as np
from scipy.ndimage import gaussian_filter1d

SR = 48000
WIN = 4.0      # 量音量的視窗（秒）
MAX_DB = 6.0   # 最多補償多少


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("music")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--keep-tail", type=float, default=2.5, help="最後幾秒不補償（保留自然收尾）")
    args = ap.parse_args()

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", args.music, "-ac", "2", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    mono = y.mean(axis=1)
    hop = SR // 10
    n = len(mono) // hop
    rms = np.sqrt((mono[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9
    # 每 0.1 秒的能量，再用約 WIN 秒的高斯平滑 → 段落層級的音量
    level = 10 * np.log10(gaussian_filter1d(rms ** 2, sigma=WIN * 10 / 2))
    tail = int(max(0, len(mono) / SR - args.keep_tail) * 10)
    target = np.median(level[:tail])
    gain_db = np.clip(target - level, -MAX_DB, MAX_DB)
    gain_db[tail:] = gain_db[tail - 1] if tail > 0 else 0.0
    gain_db = gaussian_filter1d(gain_db, sigma=10)  # 再平滑一次，避免任何突變
    g = np.interp(np.arange(len(mono)) / hop, np.arange(n) + 0.5, 10 ** (gain_db / 20))
    out = y * g[:, None]
    peak = np.abs(out).max()
    if peak > 0.99:
        out *= 0.99 / peak
    with wave.open(args.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"{args.out}  補償範圍 {gain_db[:tail].min():+.1f} ~ {gain_db[:tail].max():+.1f} dB")


if __name__ == "__main__":
    main()
