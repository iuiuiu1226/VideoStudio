#!/usr/bin/env python3
"""編號 5「看不見的能量」水的變化動畫：字幕下方的透明疊加層，跟著講師講到哪裡長出來（使用者 2026/11/07 要加）。

水蒸氣（虛線＝看不見）→ 講「降溫」時長出箭頭 → 講「會不會出現」時水滴跳出來（小字「看不見 → 看得見」）
→ 講「零下 20 度」時再長一個箭頭 → 台下喊「冰塊」時冰塊跳出來；最後一句講完整排淡出。
- 水換狀態不畫成「能量 → 物質」（水蒸氣凝結是物質換狀態，見 README 課堂精華 VOL.02 的說明）
- 不放「液體 → 固體」大字（字幕已經有；舊版使用者也要拿掉）
- 圖示、深藍底板、箭頭沿用 class02_anim（同一系列同樣畫法）；冰塊／水／水蒸氣固定在同一排左中右，在字幕下方、不擋臉
- 這段中間拿掉一個「對吧」，分成 C1、C2 兩個片段：同一條時間軸切成兩個疊加層 ov_C1.mov、ov_C2.mov，
  片段的入出點、補停頓從 cuts/ep05/seg_lecture.json 讀（先跑 tools/gen_ep05.py）

用法：python3 tools/ep05_anim.py --font <NotoSansTC.ttf> [--out work/ep05_anim] [--preview 秒,秒]（預覽秒數是整段動畫的時間）
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import class02_anim as C  # noqa: E402
import life03_anim as L  # noqa: E402
from life03_anim import FPS, ease, pop  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# 重點字的時間（素材秒數，逐字轉錄＋聲音曲線確認）
# 逐字轉錄每句開頭的時間常常偏早，句子開頭用聲音曲線的開口時間、句中的字照比例換算
KEYS = {"panel": 104.95,   # 「舉例」講完：底板淡入
        "看不到": 105.80,  # 虛線水蒸氣出現
        "降溫": 113.39,    # 水蒸氣 → 水 的箭頭
        "出現": 117.35,    # 「會不會出現？」水滴跳出來
        "看得見": 119.40,  # 小字「看不見 → 看得見」（「它從能量變成物質」開口後）
        "零下": 123.84,    # 水 → 冰塊 的箭頭
        "冰塊": 127.00}    # 台下喊「冰塊」
PARTS = ("#C1", "#C2")


def rounded(x):
    return round(x * FPS) / FPS


def parts():
    """C1、C2 在整段動畫裡的起點與長度（跟 build_segment 一樣以格為單位取整）"""
    seg = json.load(open(os.path.join(ROOT, "cuts", "ep05", "seg_lecture.json"), encoding="utf-8"))
    clips = {c["id"]: c for c in seg["clips"]}
    out, t = [], 0.0
    for pid in PARTS:
        c = clips[pid]
        dur = rounded(c["out"] - c["in"]) + rounded(c.get("pad", 0.0)) + rounded(c.get("hold", 0.0))
        out.append((pid, c["in"], c["out"], t, dur))
        t += dur
    return out, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "ep05_anim"))
    ap.add_argument("--preview", default="")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    F = L.Fonts(args.font)
    ps, total = parts()

    def T(src):
        """素材秒數 → 整段動畫的秒數"""
        for _, a, b, off, dur in ps:
            if src <= b + 1e-6:
                return off + max(0.0, src - a)
        return ps[-1][3] + src - ps[-1][1]
    k = {n: T(s) for n, s in KEYS.items()}
    Y, LY, P = C.ROW_Y, C.ROW_Y + 90, C.POS

    def frame(t):
        base = C._layer()
        fo = 1.0 - ease((t - (total - 0.35)) / 0.35)          # 最後一句講完，整排一起淡出
        C.panel(base, ease((t - k["panel"]) / 0.35) * fo)
        top = C._layer()
        shown = ease((t - k["出現"]) / 0.4)                    # 水出現後，水蒸氣變淡（退到背景）
        e = ease((t - k["看不到"]) / 0.45)
        C.icon(top, "水蒸氣", P["水蒸氣"], Y, 1.0, e * (0.95 - 0.45 * shown), ghost=True)
        C.label(top, "水蒸氣", P["水蒸氣"], LY, F, e * (1 - 0.5 * shown))
        dim1 = 1 - 0.5 * ease((t - k["零下"]) / 0.4)
        C.arrow(top, P["水蒸氣"] - 95, P["水"] + 95, Y, ease((t - k["降溫"]) / 0.6), F, "降溫", a=dim1)
        C.icon(top, "水", P["水"], Y, pop((t - k["出現"]) / 0.45), ease((t - k["出現"]) / 0.3))
        C.label(top, "水", P["水"], LY, F, ease((t - k["出現"]) / 0.3))
        cap = ease((t - k["看得見"]) / 0.4) * (1 - ease((t - k["零下"]) / 0.35))
        if cap > 0.01:
            C.caption(top, "看不見 → 看得見", F, cap)
        C.arrow(top, P["水"] - 95, P["冰塊"] + 95, Y, ease((t - k["零下"]) / 0.6), F, "零下 20 度")
        C.icon(top, "冰塊", P["冰塊"], Y, pop((t - k["冰塊"]) / 0.45), ease((t - k["冰塊"]) / 0.3))
        C.label(top, "冰塊", P["冰塊"], LY, F, ease((t - k["冰塊"]) / 0.3))
        if fo < 1.0:
            arr = np.array(top)
            arr[..., 3] = (arr[..., 3] * fo).astype(np.uint8)
            top = Image.fromarray(arr, "RGBA")
        base.alpha_composite(top)
        return base

    if args.preview:
        for s in [float(x) for x in args.preview.split(",")]:
            frame(s).save(os.path.join(args.out, f"preview_{s:05.2f}.png"))
        print("預覽：", args.out)
        return
    for pid, a, b, off, dur in ps:
        path = os.path.join(args.out, f"ov_{pid.lstrip('#')}.mov")
        L.render(path, lambda t, off=off: frame(off + t), dur)
        print(path, f"{dur:.2f}s")
    print("重點字（動畫秒數）：", {n: round(v, 2) for n, v in k.items()}, "全長", round(total, 2))


if __name__ == "__main__":
    main()
