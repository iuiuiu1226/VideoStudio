#!/usr/bin/env python3
"""合成原創氛圍背景音樂（無版權問題）。

柔和長音鋪底＋零星鐘聲點綴＋空間殘響，沒有鼓點、沒有旋律主線，不和人聲搶。
結構：
  - 開頭：低音長音＋一聲鐘聲帶出懸念，長音約 2 秒後才進來
  - 中段：小調和弦慢慢進行（每個和弦 CHORD_LEN 秒）
  - 片尾（--outro 秒起）：解決到明亮的大和弦，音量浮上來，最後淡出

用法：
  python3 tools/bgm.py --dur 93.5 --outro 86.5 -o output/bgm.wav
"""
import argparse
import wave

import numpy as np
from scipy.signal import fftconvolve

SR = 48000
CHORD_LEN = 8.0
# 和弦（MIDI 音高）：Dm(add9) → B♭maj7 → Gm9 → A sus4，循環；片尾用 Fmaj9
PROG = [[50, 57, 62, 64, 65], [46, 53, 57, 62, 65], [43, 50, 57, 58, 62], [45, 52, 57, 62, 64]]
OUTRO = [41, 48, 57, 60, 64, 67]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad_note(freq, n, rng):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for cents in (-5, 0, 6):  # 三個略微走音的聲部，聲音比較寬、比較暖
        f = freq * 2 ** (cents / 1200)
        ph = rng.uniform(0, 2 * np.pi)
        out += np.sin(2 * np.pi * f * t + ph) + 0.18 * np.sin(2 * np.pi * 2 * f * t + ph)
    # 很慢的音量起伏，避免長音太死板
    out *= 0.85 + 0.15 * np.sin(2 * np.pi * rng.uniform(0.05, 0.12) * t + rng.uniform(0, 6))
    return out / 3


def envelope(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    # 一階低通，讓長音柔和
    for i in range(0, len(x), 4096):
        blk = x[i:i + 4096]
        out = np.empty_like(blk)
        for j, v in enumerate(blk):
            acc = (1 - a) * v + a * acc
            out[j] = acc
        y[i:i + 4096] = out
    return y


def bell(freq, n):
    t = np.arange(n) / SR
    env = np.exp(-t / 1.6) * (1 - np.exp(-t / 0.004))
    return env * (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--outro", type=float, required=True, help="片尾開始的秒數")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    total = int((args.dur + 4) * SR)
    pad = np.zeros(total)
    bells = np.zeros(total)

    # 開頭低音長音
    n = int(10 * SR)
    pad[:n] += 0.9 * pad_note(hz(38), n, rng) * envelope(n, 1.5, 4)

    # 中段和弦（從 2 秒開始，片尾前 1 秒交棒）
    t = 2.0
    k = 0
    while t < args.outro - 1:
        chord = PROG[k % len(PROG)]
        n = int((CHORD_LEN + 3) * SR)
        s = int(t * SR)
        seg = sum(pad_note(hz(m), n, rng) for m in chord) / len(chord)
        pad[s:s + n] += seg[: total - s] * envelope(n, 2.5, 3.5)[: total - s]
        t += CHORD_LEN
        k += 1

    # 片尾大和弦
    s = int((args.outro - 1) * SR)
    n = total - s
    seg = sum(pad_note(hz(m), n, rng) for m in OUTRO) / len(OUTRO)
    pad[s:] += 1.25 * seg * envelope(n, 2.0, 0.1)

    # 鐘聲：開頭一聲，之後每 6–9 秒一聲，片尾再一聲
    times = [0.25]
    t = 9.0
    while t < args.outro - 3:
        times.append(t)
        t += rng.uniform(6, 9)
    times.append(args.outro + 0.2)
    for bt in times:
        chord = OUTRO if bt >= args.outro else PROG[int(max(bt - 2, 0) // CHORD_LEN) % len(PROG)]
        m = rng.choice(chord) + 24
        s, n = int(bt * SR), int(5 * SR)
        e = min(total, s + n)
        bells[s:e] += 0.22 * bell(hz(m), n)[: e - s]

    mono = lowpass(pad, 1800) + bells
    # 殘響：雙聲道各自的衰減雜訊脈衝響應，產生空間感與立體寬度
    ir_t = np.arange(int(3.2 * SR)) / SR
    stereo = []
    for ch in range(2):
        ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 1.1)
        ir = lowpass(ir, 4000)
        ir /= np.sqrt((ir ** 2).sum())
        wet = fftconvolve(mono, ir)[:total]
        stereo.append(0.55 * mono + 0.9 * wet)
    y = np.stack(stereo, axis=1)

    # 整體音量曲線：片尾浮上來，最後 1.8 秒淡出
    g = np.ones(total)
    o = int(args.outro * SR)
    g[o:] = np.linspace(1, 1.6, total - o).clip(max=1.6)
    end = int(args.dur * SR)
    fade = int(1.8 * SR)
    g[end - fade:end] *= np.linspace(1, 0, fade) ** 1.5
    g[end:] = 0
    y = (y * g[:, None])[:end]
    y /= np.abs(y).max() / 0.7

    with wave.open(args.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    print(f"{args.out}  {args.dur}s")


if __name__ == "__main__":
    main()
