#!/usr/bin/env python3
"""素材降噪：去掉背景嘶聲與環境音，影像原封不動。

兩層處理：
  1. 頻譜降噪：每支素材找出整支最安靜的 12%（沒人講話的片段）當作噪音樣本，
     用頻譜閘控（noisereduce）從整支音訊扣掉這種噪音。
  2. 柔性噪音門：沒有人聲的空檔（句間、字間）再把殘留噪音平順壓低最多 GATE_RANGE_DB，
     門檻依每支素材的人聲大小自動設定（人聲 p90 再低 GATE_BELOW_DB），不會硬切成靜音。
輸出到另一個資料夾，檔名相同，影像串流直接複製（含旋轉資訊）。
之後輸出成片時把 --src 指到這個資料夾即可。

每支素材可在設定檔（--config，例如 cuts/denoise.json）各自指定：
  strength        頻譜降噪強度 0–1
  nstd            頻譜閘控門檻（標準差倍數，預設 1.5；越大越保守，子音越不會被當成噪音）
  nonstat         改用非穩態降噪，值是噪音估計的時間常數（秒，例如 2.0）；背景聲一直在變、
                  穩態降噪壓不乾淨又容易傷字時用（IMG_0632 實測：空檔改善 4 dB、字完整）
  noise_pct       取整支最安靜的百分之幾當噪音樣本（預設 12）
  highpass        降噪前先濾掉這個頻率以下（Hz），適合低頻轟聲重的素材
  eq              降噪後的等化（ffmpeg 濾鏡字串），例如補回子音清晰度
  rnnoise         再加一層人聲降噪（RNNoise，ffmpeg arnndn），值是模型名稱（assets/models/rnnoise/<名稱>.rnnn，
                  setup.sh 會下載 sh）；rnn_mix 是混入比例 0–1（全量會吃字，IMG_0632 實測 0.7 字完整）。
                  有設 rnnoise 時，噪音門改看 RNNoise 的輸出判斷有沒有人聲（側鏈噪音門）：
                  RNNoise 輸出的空檔幾乎全靜，輕聲的字不會被誤判成空檔壓掉
  gate_below_db / gate_threshold   噪音門門檻：比人聲 p90 低幾 dB，或直接給絕對值（0–1）
  gate_range_db / gate_ratio       噪音門最多壓低幾 dB、壓縮比
講話較輕、起伏大的人，或素材本身已被壓縮過的，要用溫和設定，否則子音、輕聲的字會被一起削掉
（輸出後請轉錄比對，並檢查 4–8 kHz 有沒有被削掉）。

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
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def load(path, highpass=None):
    af = ["-af", f"highpass=f={highpass}:poles=2"] if highpass else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", *af, "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def write_wav(path, y):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


def ffx(y, af):
    """把音訊陣列送過一串 ffmpeg 濾鏡"""
    with tempfile.TemporaryDirectory() as td:
        write_wav(td + "/a.wav", y)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", td + "/a.wav", "-af", af, "-ac", "1", "-ar", str(SR),
                              "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def rnn_model(name):
    path = name if name.endswith(".rnnn") else os.path.join(ROOT, "assets", "models", "rnnoise", name + ".rnnn")
    if not os.path.exists(path):
        raise SystemExit(f"找不到 RNNoise 模型 {path}，請先跑 sh tools/setup.sh")
    return path


def p90_db(y):
    n = SR // 50  # 20ms
    fr = y[: len(y) // n * n].reshape(-1, n)
    return np.percentile(20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9), 90)


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
        c = {"strength": args.strength, "gate_below_db": GATE_BELOW_DB, "gate_range_db": GATE_RANGE_DB,
             "nstd": 1.5, "noise_pct": 12, "gate_ratio": 6}
        c.update(conf.get("default", {}))
        c.update(conf.get(name, {}))
        a = load(src, c.get("highpass"))
        n = SR // 50  # 20ms
        frames = a[: len(a) // n * n].reshape(-1, n)
        db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
        quiet = frames[db <= np.percentile(db, c["noise_pct"])].reshape(-1)
        if c.get("nonstat"):
            # 非穩態降噪：噪音樣本跟著時間更新（time_constant_s 秒），適合背景聲一直在變的素材
            y = nr.reduce_noise(y=a, sr=SR, stationary=False, prop_decrease=c["strength"],
                                time_constant_s=c["nonstat"], n_fft=2048)
        else:
            y = nr.reduce_noise(y=a, sr=SR, y_noise=quiet, stationary=True, prop_decrease=c["strength"],
                                n_std_thresh_stationary=c["nstd"], n_fft=2048)
        key = None
        if c.get("rnnoise"):
            model = rnn_model(c["rnnoise"])
            key = ffx(a, f"arnndn=m={model}")  # 全量 RNNoise 只拿來判斷哪裡有人聲
            y = ffx(y, f"arnndn=m={model}:mix={c.get('rnn_mix', 1.0)}")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            wav = tf.name
        write_wav(wav, y)
        post = [c["eq"]] if c.get("eq") else []
        gate = ""
        if not args.no_gate:
            # 人聲大小：20ms 響度的 p90（側鏈時看 RNNoise 輸出）；門檻比它低 gate_below_db（或直接用 gate_threshold）
            thr = c.get("gate_threshold") or 10 ** ((p90_db(key if key is not None else y) - c["gate_below_db"]) / 20)
            gate = (f"threshold={thr:.5f}:ratio={c['gate_ratio']}"
                    f":range={10 ** (-c['gate_range_db'] / 20):.4f}:attack=6:release=250:knee=3")
        if post or gate:
            processed = wav[:-4] + "_p.wav"
            chain = ",".join(post)
            if key is not None and gate:
                keywav = wav[:-4] + "_k.wav"
                write_wav(keywav, key)
                graph = f"[0:a]{chain + ',' if chain else ''}anull[m];[m][1:a]sidechaingate={gate}"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-i", keywav, "-filter_complex", graph,
                                processed], check=True)
                os.remove(keywav)
            else:
                af = ",".join(post + ([f"agate={gate}"] if gate else []))
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", af, processed], check=True)
            os.replace(processed, wav)
        off = start_offset(src)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-itsoffset", f"{off:.6f}", "-i", wav,
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-ac", "2", dst], check=True)
        os.remove(wav)
        print(f"{name}: 強度 {c['strength']}、nstd {c['nstd']}、高通 {c.get('highpass') or '-'}、"
              f"EQ {'有' if c.get('eq') else '-'}、RNNoise {c.get('rnnoise') or '-'}、最多壓 {c['gate_range_db']}dB，"
              f"噪音樣本 {len(quiet) / SR:.1f}s，音軌延遲 {off:.3f}s → {dst}")


if __name__ == "__main__":
    main()
