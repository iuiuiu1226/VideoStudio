#!/usr/bin/env python3
"""合成輕鬆愉快的原創背景音樂（無版權問題）。

大調、每分鐘 100 拍，和弦 C → G → Am → F 循環：
  - 木琴般的跳動琶音（主角，但不唱主旋律，不和人聲搶）
  - 電鋼琴和弦、柔和貝斯、輕大鼓、彈指、沙鈴
結構：
  - 第 1 小節只有木琴（鉤子）；第 2–3 小節加入電鋼琴與沙鈴；之後完整律動
  - 每 8 小節的最後一小節拿掉大鼓、木琴加花，避免單調
  - 片尾（--outro 秒起）加一段木琴旋律，最後停在 C 大和弦並淡出
輸出前把響度調到 -18 LUFS，方便和人聲混音。

用法：
  python3 tools/bgm_bright.py --dur 93.5 --outro 86.5 -o output/bgm_bright.wav
"""
import argparse
import subprocess
import tempfile
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BPM = 100
BEAT = 60 / BPM
BAR = BEAT * 4
# 和弦（MIDI）：根音、三度、五度、八度
CHORDS = [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]]  # C G Am F
ARP = [0, 1, 2, 1, 3, 2, 1, 2]  # 八分音符琶音的順序
MELODY = [76, 74, 72, 74, 76, 79, 76, 74, 72, 74, 72, 67, 72]  # 片尾旋律（C 大調五聲音階）


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, sig, gain=1.0):
    s = int(start * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += gain * sig[: e - s]


def marimba(f, dur=1.2):
    t = np.arange(int(dur * SR)) / SR
    att = 1 - np.exp(-t / 0.002)
    return att * (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.35)
                  + 0.25 * np.sin(2 * np.pi * 4.0 * f * t) * np.exp(-t / 0.06)
                  + 0.06 * np.sin(2 * np.pi * 9.9 * f * t) * np.exp(-t / 0.02))


def epiano(freqs, dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    env = (1 - np.exp(-t / 0.01)) * np.exp(-t / 0.9)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 5.0 * t)
    sig = sum(np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.3) for f in freqs)
    return env * trem * sig / len(freqs)


def bass(f, dur=0.45):
    t = np.arange(int(dur * SR)) / SR
    env = (1 - np.exp(-t / 0.005)) * np.exp(-t / 0.25)
    return env * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t))


def kick():
    t = np.arange(int(0.3 * SR)) / SR
    f = 45 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.14)


def noise_burst(rng, dur, tau, band):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sos = butter(2, band, btype="bandpass" if isinstance(band, list) else "highpass", fs=SR, output="sos")
    return sosfilt(sos, rng.standard_normal(n)) * np.exp(-t / tau)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float([l.split()[1] for l in r.splitlines() if l.strip().startswith("I:")][-1])


def write(path, y):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--outro", type=float, required=True, help="片尾開始的秒數")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    total = int((args.dur + 2) * SR)
    L = {k: np.zeros(total) for k in ("mar", "ep", "bass", "kick", "snap", "shk", "mel")}
    n_bars = int(np.ceil(args.dur / BAR))
    outro_bar = int(args.outro // BAR)
    last_bar = int((args.dur - 1.5) // BAR)  # 最後的主和弦落在這一小節

    for b in range(n_bars):
        t0 = b * BAR
        chord = CHORDS[b % 4] if b < last_bar else CHORDS[0]
        fill = b % 8 == 7 and b < outro_bar
        # 木琴琶音
        for i, k in enumerate(ARP):
            note = chord[k] + 12
            if fill and i >= 4:
                note = chord[(k + i) % 4] + 24
            add(L["mar"], t0 + i * BEAT / 2, marimba(hz(note)), 0.55 if i % 2 == 0 else 0.4)
        if b == 0:
            continue
        # 電鋼琴：第 1 拍與第 2 拍後半，帶一點切分的彈跳感
        add(L["ep"], t0, epiano([hz(m) for m in chord[:3]]), 0.9)
        add(L["ep"], t0 + 1.5 * BEAT, epiano([hz(m) for m in chord[:3]], 0.8), 0.5)
        # 沙鈴：十六分音符，正拍稍重
        for i in range(16):
            add(L["shk"], t0 + i * BEAT / 4, noise_burst(rng, 0.06, 0.018, 7000), 1.0 if i % 4 == 2 else 0.5)
        if b < 3:
            continue
        root = chord[0] - 24
        for beat_pos in (0, 1.5, 2, 3.5):
            add(L["bass"], t0 + beat_pos * BEAT, bass(hz(root)), 1.0 if beat_pos in (0, 2) else 0.6)
        if not fill:
            add(L["kick"], t0, kick())
            add(L["kick"], t0 + 2 * BEAT, kick(), 0.8)
        for beat_pos in (1, 3):
            add(L["snap"], t0 + beat_pos * BEAT, noise_burst(rng, 0.12, 0.03, [1200, 4500]))

    # 片尾旋律
    for i, m in enumerate(MELODY):
        t = outro_bar * BAR + i * BEAT
        if t > args.dur - 1.2:
            break
        add(L["mel"], t, marimba(hz(m), 1.6), 0.8)
    # 收尾的 C 大和弦（長一點）
    end_t = last_bar * BAR
    add(L["ep"], end_t + BAR, epiano([hz(m) for m in [60, 64, 67, 72]], 3.0), 1.0)

    lp = butter(2, 2500, btype="lowpass", fs=SR, output="sos")
    L["bass"] = sosfilt(lp, L["bass"])
    mix = {"mar": 0.32, "ep": 0.22, "bass": 0.32, "kick": 0.38, "snap": 0.09, "shk": 0.035, "mel": 0.3}
    pan = {"mar": -0.25, "ep": 0.2, "bass": 0.0, "kick": 0.0, "snap": 0.15, "shk": 0.35, "mel": 0.1}
    left = sum(mix[k] * L[k] * np.sqrt(0.5 - pan[k] / 2) * np.sqrt(2) for k in L)
    right = sum(mix[k] * L[k] * np.sqrt(0.5 + pan[k] / 2) * np.sqrt(2) for k in L)

    # 輕殘響
    ir_t = np.arange(int(1.2 * SR)) / SR
    out = []
    for ch in (left, right):
        ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.35)
        ir /= np.sqrt((ir ** 2).sum())
        out.append(ch + 0.35 * fftconvolve(ch, ir)[:total])
    y = np.stack(out, axis=1)

    # 開頭 0.3 秒淡入、最後 1.5 秒淡出
    end = int(args.dur * SR)
    y = y[:end]
    fi, fo = int(0.3 * SR), int(1.5 * SR)
    y[:fi] *= np.linspace(0, 1, fi)[:, None]
    y[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
    y /= np.abs(y).max() / 0.8

    # 響度對齊到 -18 LUFS
    with tempfile.NamedTemporaryFile(suffix=".wav") as tf:
        write(tf.name, y)
        gain = 10 ** ((-18.0 - lufs(tf.name)) / 20)
    y = y * gain
    if np.abs(y).max() > 0.95:
        y *= 0.95 / np.abs(y).max()
    write(args.out, y)
    print(f"{args.out}  {args.dur}s  {BPM} BPM")


if __name__ == "__main__":
    main()
