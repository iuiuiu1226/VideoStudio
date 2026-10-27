#!/usr/bin/env python3
"""素材降噪：去掉背景嘶聲與環境音，影像原封不動。

每支素材先找出整支最安靜的 12%（沒人講話的片段）當作噪音樣本，
再用頻譜閘控（noisereduce）從整支音訊扣掉這種噪音。
輸出到另一個資料夾，檔名相同，影像串流直接複製（含旋轉資訊）。
之後輸出成片時把 --src 指到這個資料夾即可。

用法：
  python3 tools/denoise.py --src <素材資料夾> --out <降噪後資料夾> [--strength 0.85]
"""
import argparse
import os
import subprocess
import tempfile
import wave

import noisereduce as nr
import numpy as np

SR = 48000
EXTS = (".mov", ".mp4", ".m4v")


def start_offset(path):
    """音軌相對畫面的起始延遲（秒）。重新封裝時要保留，否則嘴型會對不上。"""
    def st(sel):
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel,
                              "-show_entries", "stream=start_time", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.split()
        try:
            return float(out[0])
        except (IndexError, ValueError):
            return 0.0
    return st("a:0") - st("v:0")


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--strength", type=float, default=0.85, help="0–1，越大降越多")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    for name in sorted(os.listdir(args.src)):
        if not name.lower().endswith(EXTS):
            continue
        src, dst = os.path.join(args.src, name), os.path.join(args.out, name)
        a = load(src)
        n = SR // 50  # 20ms
        frames = a[: len(a) // n * n].reshape(-1, n)
        db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
        quiet = frames[db <= np.percentile(db, 12)].reshape(-1)
        y = nr.reduce_noise(y=a, sr=SR, y_noise=quiet, stationary=True,
                            prop_decrease=args.strength, n_fft=2048)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            wav = tf.name
        with wave.open(wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
        off = start_offset(src)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-itsoffset", f"{off:.6f}", "-i", wav,
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-ac", "2", dst], check=True)
        os.remove(wav)
        print(f"{name}: 噪音樣本 {len(quiet) / SR:.1f}s，音軌延遲 {off:.3f}s → {dst}")


if __name__ == "__main__":
    main()
