#!/usr/bin/env python3
"""合成「中性、帶點震撼感，但整體輕鬆」的原創背景音樂（無版權問題）。

像紀錄片揭曉一件事的配樂：每分鐘 92 拍，和弦 Am → F → C → G 循環。
  - 柔和偏暗的鋼琴八分音符反覆（像心跳往前推）、溫暖的合成器長音、低音脈動
  - 鉤子段不放鼓營造懸念，第二段起加入輕柔的大鼓與腳踏鈸
  - 開頭一聲低沉的衝擊音；段落交接前有漸強的上升音效
  - 片尾和弦解決到明亮的 C 大和弦，音樂浮上來後淡出
段落時間用 --sections 指定（影片各段的開始秒數），變化點會對齊影片。
輸出前把響度調到 -18 LUFS，方便和人聲混音。

用法：
  python3 tools/bgm_reveal.py --dur 93.5 --sections 0,15.67,31.43,50.3,65.97 --outro 86.5 -o output/bgm_reveal.wav
"""
import argparse
import subprocess
import tempfile
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BPM = 92
BEAT = 60 / BPM
BAR = BEAT * 4
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
OSTINATO = [0, 2, 1, 2, 0, 2, 1, 2]  # 八分音符：根音、五度、三度、五度…
FINAL = [48, 55, 60, 64, 67]  # 片尾 C 大和弦


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, sig, gain=1.0):
    s = int(start * SR)
    if s < 0 or s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += gain * sig[: e - s]


def lp(x, cutoff, order=2):
    return sosfilt(butter(order, cutoff, btype="lowpass", fs=SR, output="sos"), x)


def piano(f, dur=1.8):
    """柔和偏暗的鋼琴（毛氈鋼琴感）。"""
    t = np.arange(int(dur * SR)) / SR
    att = 1 - np.exp(-t / 0.004)
    sig = sum(a * np.sin(2 * np.pi * k * f * t) * np.exp(-t / tau)
              for k, a, tau in [(1, 1.0, 0.9), (2, 0.35, 0.5), (3, 0.15, 0.3), (4, 0.06, 0.2)])
    return att * sig


def pad(freqs, dur, rng):
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros_like(t)
    for f in freqs:
        for cents in (-6, 0, 7):
            ff = f * 2 ** (cents / 1200)
            ph = rng.uniform(0, 2 * np.pi)
            sig += sum(np.sin(2 * np.pi * n * ff * t + ph) / n for n in range(1, 7))
    sig = lp(sig, 1100)
    a, r = min(1.5, dur / 3), min(1.5, dur / 3)
    env = np.ones_like(t)
    env[: int(a * SR)] = np.linspace(0, 1, int(a * SR)) ** 2
    env[-int(r * SR):] *= np.linspace(1, 0, int(r * SR)) ** 2
    return env * sig / (len(freqs) * 3 * 2.4)


def sub(f, dur=0.9):
    t = np.arange(int(dur * SR)) / SR
    return (1 - np.exp(-t / 0.01)) * np.exp(-t / 0.45) * np.sin(2 * np.pi * f * t)


def kick():
    t = np.arange(int(0.35 * SR)) / SR
    f = 42 + 55 * np.exp(-t / 0.035)
    return lp(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16), 900)


def hat(rng):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return sosfilt(butter(2, 8000, btype="highpass", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t / 0.015)


def impact(rng):
    """低沉的衝擊音：下沉的低頻＋短促的低通雜訊。"""
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    f = 32 + 60 * np.exp(-t / 0.08)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    thud = lp(rng.standard_normal(n), 400) * np.exp(-t / 0.12)
    return boom + 0.5 * thud


def riser(rng, dur=2.2):
    """漸強上升音：中心頻率往上掃的濾波雜訊。"""
    n = int(dur * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 2048
    for i in range(0, n, seg):
        frac = i / n
        fc = 400 + 5000 * frac ** 2
        sos = butter(2, [fc * 0.7, fc * 1.3], btype="bandpass", fs=SR, output="sos")
        out[i:i + seg] = sosfilt(sos, x[i:i + seg])
    return out * np.linspace(0, 1, n) ** 2.5


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
    ap.add_argument("--sections", required=True, help="影片各段開始秒數，逗號分隔")
    ap.add_argument("--outro", type=float, required=True, help="片尾開始的秒數")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    sections = [float(s) for s in args.sections.split(",")]
    drums_from = sections[1] if len(sections) > 1 else BAR * 2

    total = int((args.dur + 3) * SR)
    L = {k: np.zeros(total) for k in ("pno", "pad", "sub", "kick", "hat", "fx")}
    outro_bar = int(args.outro // BAR)
    n_bars = int(np.ceil(args.dur / BAR))

    for b in range(n_bars):
        t0 = b * BAR
        in_outro = t0 >= args.outro - 0.01
        chord = FINAL[:3] if in_outro else CHORDS[b % 4]
        # 鋼琴八分音符反覆（中音域），力度有起伏
        for i, k in enumerate(OSTINATO):
            vel = 0.85 if i % 4 == 0 else (0.55 if i % 2 == 0 else 0.45)
            add(L["pno"], t0 + i * BEAT / 2, piano(hz(chord[k] + 12)), vel)
        # 第四段起在上方加一個高八度的回應音，增加推進感
        if t0 >= sections[min(3, len(sections) - 1)] and not in_outro:
            add(L["pno"], t0 + 3 * BEAT, piano(hz(chord[2] + 24), 1.4), 0.35)
        # 長音鋪底
        add(L["pad"], t0, pad([hz(m) for m in chord], BAR + 1.0, rng), 1.0)
        # 低音脈動：每拍一下，第 1 拍最重
        for i in range(4):
            add(L["sub"], t0 + i * BEAT, sub(hz(chord[0] - 24)), 1.0 if i == 0 else 0.45)
        # 鼓：鉤子段不放；之後輕柔的大鼓（1、3 拍）與腳踏鈸（八分音符）
        if t0 >= drums_from - 0.01 and not in_outro:
            add(L["kick"], t0, kick())
            add(L["kick"], t0 + 2 * BEAT, kick(), 0.7)
            for i in range(8):
                add(L["hat"], t0 + i * BEAT / 2, hat(rng), 1.0 if i % 2 == 1 else 0.5)

    # 開頭衝擊音；段落交接前的上升音＋輕衝擊
    add(L["fx"], 0.0, impact(rng), 1.0)
    for s in sections[1:] + [args.outro]:
        add(L["fx"], s - 2.2, riser(rng), 0.35)
        add(L["fx"], s, impact(rng), 0.35)
    # 片尾最後的長和弦
    end_t = args.dur - 4.5
    add(L["pad"], end_t, pad([hz(m) for m in FINAL], 4.5, rng), 1.2)
    add(L["pno"], end_t, piano(hz(72), 4.0), 0.8)

    mix = {"pno": 0.30, "pad": 0.55, "sub": 0.42, "kick": 0.40, "hat": 0.035, "fx": 0.30}
    pan = {"pno": -0.15, "pad": 0.0, "sub": 0.0, "kick": 0.0, "hat": 0.3, "fx": 0.0}
    left = sum(mix[k] * L[k] * np.sqrt(1 - pan[k]) for k in L)
    right = sum(mix[k] * L[k] * np.sqrt(1 + pan[k]) for k in L)

    # 較大的空間殘響（電影感）
    ir_t = np.arange(int(2.2 * SR)) / SR
    out = []
    for ch in (left, right):
        ir = lp(rng.standard_normal(len(ir_t)), 5000) * np.exp(-ir_t / 0.6)
        ir /= np.sqrt((ir ** 2).sum())
        out.append(ch + 0.45 * fftconvolve(ch, ir)[:total])
    y = np.stack(out, axis=1)

    # 片尾音量浮上來；最後 1.8 秒淡出
    g = np.ones(total)
    o = int(args.outro * SR)
    g[o:] = np.minimum(1.35, 1 + np.arange(total - o) / SR * 0.3)
    y *= g[:, None]
    end = int(args.dur * SR)
    y = y[:end]
    fo = int(1.8 * SR)
    y[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
    y /= np.abs(y).max() / 0.8

    with tempfile.NamedTemporaryFile(suffix=".wav") as tf:
        write(tf.name, y)
        gain = 10 ** ((-18.0 - lufs(tf.name)) / 20)
    y *= gain
    if np.abs(y).max() > 0.95:
        y *= 0.95 / np.abs(y).max()
    write(args.out, y)
    print(f"{args.out}  {args.dur}s  {BPM} BPM")


if __name__ == "__main__":
    main()
