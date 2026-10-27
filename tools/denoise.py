#!/usr/bin/env python3
"""素材降噪：去掉背景嘶聲與環境音，影像原封不動。

兩層處理：
  1. 頻譜降噪：每支素材找出整支最安靜的 12%（沒人講話的片段）當作噪音樣本，
     用頻譜閘控（noisereduce）從整支音訊扣掉這種噪音。
  2. 柔性噪音門：沒有人聲的空檔（句間、字間）再把殘留噪音平順壓低最多 GATE_RANGE_DB，
     門檻依每支素材的人聲大小自動設定（人聲 p90 再低 GATE_BELOW_DB），不會硬切成靜音。
輸出到另一個資料夾，檔名相同，影像串流直接複製（含旋轉資訊）。
之後輸出成片時把 --src 指到這個資料夾即可。

每支素材可在設定檔（--config，例如 cuts/denoise.json）各自指定強度：
  {"default": {"strength": 1.0, "gate_below_db": 6, "gate_range_db": 22},
   "某檔名.MOV": {"strength": 0.85, "gate_below_db": 16, "gate_range_db": 12}}
講話較輕、起伏大的人要用溫和設定，否則輕聲的字會被一起削掉（輸出後請轉錄比對）。

用法：
  python3 tools/denoise.py --src <素材資料夾> --out <降噪後資料夾> [--config cuts/denoise.json]
"""
import argparse
import json
import os
import subprocess
import tempfile
import wave

import noisereduce as nr
import numpy as np

SR = 48000
GATE_BELOW_DB = 6.0   # 噪音門門檻：比人聲（p90）低多少
GATE_RANGE_DB = 22.0  # 噪音門最多壓低多少
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
    ap.add_argument("--strength", type=float, default=1.0, help="頻譜降噪強度 0–1，越大降越多")
    ap.add_argument("--no-gate", action="store_true", help="不加噪音門")
    ap.add_argument("--config", help="每支素材各自的降噪設定（JSON）")
    args = ap.parse_args()
    conf = json.load(open(args.config, encoding="utf-8")) if args.config else {}
    os.makedirs(args.out, exist_ok=True)

    for name in sorted(os.listdir(args.src)):
        if not name.lower().endswith(EXTS):
            continue
        src, dst = os.path.join(args.src, name), os.path.join(args.out, name)
        c = {"strength": args.strength, "gate_below_db": GATE_BELOW_DB, "gate_range_db": GATE_RANGE_DB}
        c.update(conf.get("default", {}))
        c.update(conf.get(name, {}))
        a = load(src)
        n = SR // 50  # 20ms
        frames = a[: len(a) // n * n].reshape(-1, n)
        db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
        quiet = frames[db <= np.percentile(db, 12)].reshape(-1)
        y = nr.reduce_noise(y=a, sr=SR, y_noise=quiet, stationary=True,
                            prop_decrease=c["strength"], n_fft=2048)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            wav = tf.name
        with wave.open(wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
        if not args.no_gate:
            # 人聲大小：降噪後 20ms 響度的 p90；門檻比它低 GATE_BELOW_DB
            fr2 = y[: len(y) // n * n].reshape(-1, n)
            p90 = np.percentile(20 * np.log10(np.sqrt((fr2 ** 2).mean(axis=1)) + 1e-9), 90)
            thr = 10 ** ((p90 - c["gate_below_db"]) / 20)
            gated = wav[:-4] + "_g.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af",
                            f"agate=threshold={thr:.5f}:ratio=6:range={10 ** (-c['gate_range_db'] / 20):.4f}"
                            ":attack=6:release=250:knee=3", gated], check=True)
            os.replace(gated, wav)
        off = start_offset(src)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-itsoffset", f"{off:.6f}", "-i", wav,
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-ac", "2", dst], check=True)
        os.remove(wav)
        print(f"{name}: 強度 {c['strength']}、門檻 -{c['gate_below_db']}dB、最多壓 {c['gate_range_db']}dB，"
              f"噪音樣本 {len(quiet) / SR:.1f}s，音軌延遲 {off:.3f}s → {dst}")


if __name__ == "__main__":
    main()
