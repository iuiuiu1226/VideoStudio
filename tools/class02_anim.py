#!/usr/bin/env python3
"""課堂精華 VOL.02（能量看不見，但真實存在）的動畫：開頭問題卡、講師段落上的小圖示、結尾收尾卡。

開頭：「看不見、摸不到的東西，就不存在嗎？」（女聲旁白，深藍底、空氣中淡淡漂浮的微粒）
講師段落：字幕下方的透明疊加層（ov_<片段>.mov）：水蒸氣看不到但存在、能量⇄物質、水降溫變水／變冰、加溫變回去；
  冰塊／水／水蒸氣固定在同一排位置（左中右），畫面上的圖會延續到下一段，像同一張圖慢慢長出來。
  水換狀態只標「看不見 → 看得見」「液體 → 固體」（水換狀態不是能量變物質，不畫成那樣）；
  講師講「能量跟物質互相轉化」時另外畫「能量 ⇄ 物質」，不配水的圖
結尾：「看不見，不代表不存在。」
開頭與結尾的文字就是旁白內容，所以這兩段不另外上字幕（字幕不重複畫面上的大字）。
（v1 的「冰塊、水、水蒸氣，哪一個能量最高？」問答與揭曉，使用者決定先跳過，避免爭議）

用法：
  python3 tools/class02_anim.py --vo work/class02_vo --font <NotoSansTC.ttf> --out work/class02_anim [--only intro|outro|overlay] [--preview 1,2.5]
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import life03_anim as L  # noqa: E402  共用深藍底、文字、膠囊標籤、輸出等工具
from life03_anim import W, H, NAVY, GOLD, WHITE, BLUE, ease, pop, layer_text, pill, vignette_bg  # noqa: E402

TEMPO = 1.12                      # 旁白加快（同課堂精華 VOL.01）
SPLIT = 4.4                       # 配音檔裡「就不存在嗎？」與「看不見，不代表不存在」之間的停頓
HEAD = 0.3
ICE_C = (196, 232, 248)
STEAM_C = (226, 234, 242)

# 三種狀態固定的位置（講師段落與開頭、結尾共用同一排的左中右）
ROW_Y = 1505
POS = {"冰塊": 240, "水": 540, "水蒸氣": 840}
CARD_X = {"冰塊": 270, "水": 540, "水蒸氣": 810}   # 開頭、結尾的選項卡（右邊那張避開 IG 右側按鈕）
CARD_Y = 1050


# ---------- 圖示 ----------

def _layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def icon(base, kind, cx, cy, s=1.0, a=1.0, ghost=False):
    """冰塊（立方體）、水（水滴）、水蒸氣（三道上升的煙）；ghost=True 是半透明虛線版（看不到的感覺）"""
    if a <= 0.01 or s <= 0.01:
        return
    lay = _layer()
    d = ImageDraw.Draw(lay)
    A = lambda k: int(255 * a * k)
    if kind == "冰塊":
        r = 54 * s
        front = [cx - r, cy - r * 0.6, cx + r * 0.6, cy + r]
        top = [(cx - r, cy - r * 0.6), (cx - r * 0.4, cy - r * 1.1), (cx + r, cy - r * 1.1), (cx + r * 0.6, cy - r * 0.6)]
        side = [(cx + r * 0.6, cy - r * 0.6), (cx + r, cy - r * 1.1), (cx + r, cy + r * 0.5), (cx + r * 0.6, cy + r)]
        d.polygon(top, fill=(232, 247, 255, A(0.95)), outline=(255, 255, 255, A(1)))
        d.polygon(side, fill=(150, 205, 232, A(0.95)), outline=(255, 255, 255, A(1)))
        d.rectangle(front, fill=ICE_C + (A(0.95),), outline=(255, 255, 255, A(1)), width=max(2, int(3 * s)))
        d.line([cx - r * 0.7, cy - r * 0.3, cx - r * 0.35, cy - r * 0.3], fill=(255, 255, 255, A(0.9)), width=max(2, int(5 * s)))
    elif kind == "水":
        r = 46 * s
        top = (cx, cy - r * 1.9)
        d.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 1.4], fill=BLUE + (A(1),))
        d.polygon([top, (cx - r * 0.93, cy + r * 0.05), (cx + r * 0.93, cy + r * 0.05)], fill=BLUE + (A(1),))
        d.ellipse([cx - r * 0.55, cy + r * 0.1, cx - r * 0.2, cy + r * 0.6], fill=(255, 255, 255, A(0.75)))
    else:  # 水蒸氣
        for i, dx in enumerate((-30, 0, 30)):
            pts = []
            for k in range(25):
                yy = cy + 52 * s - k * 4.4 * s
                xx = cx + dx * s + 9 * s * math.sin(k / 3.2 + i * 1.7)
                pts.append((xx, yy))
            col = STEAM_C + (A(0.55 if ghost else 0.95),)
            if ghost:   # 虛線
                for k in range(0, len(pts) - 1, 2):
                    d.line([pts[k], pts[k + 1]], fill=col, width=max(2, int(7 * s)))
            else:
                d.line(pts, fill=col, width=max(2, int(8 * s)), joint="curve")
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.6)))


def label(base, kind, cx, y, F, a=1.0, color=WHITE):
    layer_text(base, (cx, y), kind, F(40, 800), color, alpha=a, stroke=3)


def arrow(base, x0, x1, y, prog, F, text="", a=1.0, color=GOLD):
    """x0→x1 的箭頭（可往左），prog 0→1 長出來；text 寫在箭頭上方"""
    if prog <= 0.01 or a <= 0.01:
        return
    lay = _layer()
    d = ImageDraw.Draw(lay)
    xe = x0 + (x1 - x0) * prog
    d.line([x0, y, xe, y], fill=color + (int(255 * a),), width=7)
    sgn = 1 if x1 > x0 else -1
    d.polygon([(xe + sgn * 6, y), (xe - sgn * 16, y - 13), (xe - sgn * 16, y + 13)], fill=color + (int(255 * a),))
    base.alpha_composite(lay)
    if text:
        layer_text(base, ((x0 + x1) / 2, y - 40), text, F(34, 800), color, alpha=a * min(1.0, prog * 1.5), stroke=3)


def panel(base, a):
    """圖示那一排後面的半透明深藍底（講師的淺灰褲子上，白色小圖會看不清楚）"""
    if a <= 0.01:
        return
    lay = _layer()
    ImageDraw.Draw(lay).rounded_rectangle([110, 1336, 970, 1650], radius=36, fill=(13, 22, 40, int(165 * a)))
    base.alpha_composite(lay)


def caption(base, text, F, a, y=1388):
    layer_text(base, (W / 2, y), text, F(46, 800), GOLD, alpha=a, stroke=4)


def card(base, kind, cx, cy, F, a=1.0, s=1.0, hi=0.0, dim=0.0):
    """選項卡：圓角方塊＋圖示＋名稱；hi 0→1 變金色外框＋打勾，dim 0→1 變淡"""
    if a <= 0.01 or s <= 0.01:
        return
    k = a * (1 - 0.65 * dim)
    w, h = 220 * s, 250 * s
    lay = _layer()
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=28 * s,
                        fill=(34, 52, 82, int(235 * k)),
                        outline=tuple(int(c1 + (c2 - c1) * hi) for c1, c2 in zip((120, 140, 170), GOLD)) + (int(255 * k),),
                        width=max(2, int((4 + 4 * hi) * s)))
    base.alpha_composite(lay)
    if hi > 0:
        L.glow_ring(base, cx, cy, 150 * s, GOLD, hi * a * 0.8)
    icon(base, kind, cx, cy - 22 * s, s * 0.95, k)
    layer_text(base, (cx, cy + 82 * s), kind, F(int(44 * s), 800), GOLD if hi > 0.5 else WHITE, alpha=k, stroke=3)
    if hi > 0.01:
        r = 30 * pop(hi)
        x, y = cx + w / 2 - 12, cy - h / 2 + 12
        lay = _layer()
        d = ImageDraw.Draw(lay)
        d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD + (int(255 * a),))
        d.line([(x - r * 0.45, y), (x - r * 0.1, y + r * 0.38), (x + r * 0.5, y - r * 0.35)], fill=NAVY + (int(255 * a),), width=max(2, int(r * 0.22)))
        base.alpha_composite(lay)


# ---------- 旁白 ----------

def load_vo(vo):
    """配音檔切成問題、答案兩段，各自加快 TEMPO 倍；回傳兩段聲音（48k）與每個字的時間（加快後、段落內）"""
    meta = json.load(open(os.path.join(vo, "lines.json"), encoding="utf-8"))["lines"][0]
    path = os.path.join(vo, meta["file"])
    out = []
    for a, b, fade in ((0.0, SPLIT, False), (SPLIT, meta["duration"], True)):
        af = f"rubberband=tempo={TEMPO}:pitch=1:pitchq=quality"
        if fade:   # 最後「你答對了嗎？」尾音自然淡出
            af += f",afade=t=out:st={max(0.0, (b - a) / TEMPO - 0.35):.3f}:d=0.35"
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", path, "-af", af,
                              "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
        y = np.frombuffer(raw, np.float32).copy()
        words = [((ws - a) / TEMPO, txt) for ws, we, txt in meta["words"] if a <= ws < b]
        out.append((y, words))
    return out


def word_time(words, txt, default):
    for t, w in words:
        if txt in w:
            return t
    return default


# ---------- 段落 ----------

def particles(base, t, a=1.0, n=46):
    """空氣中淡淡漂浮的微粒（看不見的東西其實一直都在）"""
    rng = np.random.default_rng(7)
    xs, ys, rs, sp = rng.uniform(80, W - 80, n), rng.uniform(300, 1700, n), rng.uniform(3, 8, n), rng.uniform(12, 30, n)
    lay = _layer()
    d = ImageDraw.Draw(lay)
    for x, y0, r, v, ph in zip(xs, ys, rs, sp, rng.uniform(0, 6.28, n)):
        y = 300 + (y0 - 300 - v * t) % 1400
        xx = x + 14 * math.sin(t * 0.7 + ph)
        al = int(255 * a * (0.18 + 0.12 * math.sin(t * 1.3 + ph)))
        d.ellipse([xx - r, y - r, xx + r, y + r], fill=(200, 225, 255, max(0, al)))
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.5)))


def intro(args, F, out):
    (y, words), _ = load_vo(args.vo)
    total = HEAD + len(y) / 48000 + 0.9          # 問完停一下，再交叉淡化進講師
    audio = np.zeros(int(total * 48000), np.float32)
    audio[int(HEAD * 48000):int(HEAD * 48000) + len(y)] = y
    t_q = HEAD + word_time(words, "就", 2.2)

    def frame(t):
        base = vignette_bg(t).convert("RGBA")
        particles(base, t, ease(t / 0.6))
        e = ease((t - 0.05) / 0.45)
        layer_text(base, (W / 2, 780), "看不見、摸不到的東西", F(80, 900), WHITE, alpha=e, stroke=4)
        if t >= t_q - 0.1:
            s = pop((t - t_q + 0.1) / 0.45)
            layer_text(base, (W / 2, 930), "就不存在嗎？", F(max(8, int(118 * s)), 900), GOLD, stroke=5)
        return base

    L.render(os.path.join(out, "intro.mp4"), frame, total, audio)
    return total


def outro(args, F, out):
    _, (y, words) = load_vo(args.vo)
    head = 0.35
    total = head + len(y) / 48000 + 1.6           # 講完多停一下，再交叉淡化進片尾
    audio = np.zeros(int(total * 48000), np.float32)
    audio[int(head * 48000):int(head * 48000) + len(y)] = y
    t1 = head + word_time(words, "看", 0.2)
    t2 = head + word_time(words, "代", 1.2) - 0.25

    def frame(t):
        base = vignette_bg(t + 7).convert("RGBA")
        particles(base, t + 20, ease(t / 0.5))
        if t >= t1 - 0.1:
            layer_text(base, (W / 2, 800), "看不見，", F(96, 900), WHITE, alpha=ease((t - t1 + 0.1) / 0.35), stroke=4)
        if t >= t2 - 0.05:
            s = pop((t - t2 + 0.05) / 0.45)
            layer_text(base, (W / 2, 950), "不代表不存在", F(max(8, int(124 * s)), 900), GOLD, stroke=5)
        return base

    L.render(os.path.join(out, "outro.mp4"), frame, total, audio)
    return total


# 講師片段（素材秒數）與疊加的時間點；同一排的圖會延續到下一段
CLIPS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cuts", "class02", "clips.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cuts", "class02", "clips.json")) else {}


def overlays(args, F, out):
    """每個講師片段一個透明疊加層；cuts/class02/clips.json 記每段的素材時間與重點字的時間"""
    for cid, c in CLIPS.items():
        kind = c.get("ov")
        if not kind:
            continue
        a0, a1, k = c["in"], c["out"], c.get("keys", {})
        dur = a1 - a0
        at = lambda name, d=0.0: k.get(name, a0 + d) - a0      # 重點字（素材秒數）→ 片段內秒數
        Y, LY = ROW_Y, ROW_Y + 90

        def frame(t, kind=kind, at=at, dur=dur, c=c):
            base = _layer()
            out_k = 1.0
            # 連續幾段都有圖示時，底板一直留著；第一段淡入、最後一段淡出
            pa = 1.0
            if c.get("panel_in"):
                pa *= ease((t - (at("panel", 0.25) - 0.25)) / 0.35)
            if c.get("panel_out"):
                pa *= 1.0 - ease((t - (dur - 0.3)) / 0.3)
            panel(base, pa)
            under, base = base, _layer()
            if kind == "steam_hidden":          # 有水蒸氣，你看不到，但它真實存在
                ts = at("水蒸氣", 0.5)
                e = ease((t - ts) / 0.4)
                real = ease((t - at("真實", 3.5)) / 0.5)
                icon(base, "水蒸氣", W / 2, Y, 1.2, e * (0.55 + 0.45 * real), ghost=real < 0.5)
                label(base, "水蒸氣", W / 2, LY + 10, F, e)
                if real > 0.01:
                    caption(base, "看不到，但真實存在", F, real)
            elif kind == "energy_matter":      # 能量會變成物質，物質會變成能量
                e = ease(t / 0.3)
                pill(base, 300, Y, "能量", F(54, 800), NAVY, GOLD, scale=pop(t / 0.4), alpha=e)
                pill(base, 780, Y, "物質", F(54, 800), WHITE, (70, 96, 136), scale=pop((t - 0.15) / 0.4), alpha=e)
                arrow(base, 410, 670, Y - 24, ease((t - at("能量會變成物質", 2.0)) / 0.45), F)
                arrow(base, 670, 410, Y + 24, ease((t - at("物質會變成能量", 4.0)) / 0.45), F)
            elif kind == "cool_to_water":      # 降到零度，空氣中的水出現：看不見的水蒸氣變成看得見的水
                icon(base, "水蒸氣", POS["水蒸氣"], Y, 1.0, ease(t / 0.3))
                label(base, "水蒸氣", POS["水蒸氣"], LY, F, ease(t / 0.3))
                arrow(base, POS["水蒸氣"] - 95, POS["水"] + 95, Y, ease((t - at("降溫", 1.4)) / 0.6), F, "降溫")
                tw = at("水會不會出現", 4.2)
                icon(base, "水", POS["水"], Y, pop((t - tw) / 0.45), ease((t - tw) / 0.3))
                label(base, "水", POS["水"], LY, F, ease((t - tw) / 0.3))
                ce = ease((t - at("看得見", 5.0)) / 0.4)
                if ce > 0.01:
                    caption(base, "看不見 → 看得見", F, ce)
            elif kind == "cool_to_ice":        # 零下 20 度，水變冰塊：液體變固體
                for kd in ("水蒸氣", "水"):
                    icon(base, kd, POS[kd], Y, 1.0, 0.45 if kd == "水蒸氣" else 1.0)
                    label(base, kd, POS[kd], LY, F, 0.45 if kd == "水蒸氣" else 1.0)
                arrow(base, POS["水蒸氣"] - 95, POS["水"] + 95, Y, 1.0, F, "降溫", a=0.45)
                arrow(base, POS["水"] - 95, POS["冰塊"] + 95, Y, ease((t - at("零下", 1.2)) / 0.6), F, "降溫")
                ti = at("冰塊", 4.0)
                icon(base, "冰塊", POS["冰塊"], Y, pop((t - ti) / 0.45), ease((t - ti) / 0.3))
                label(base, "冰塊", POS["冰塊"], LY, F, ease((t - ti) / 0.3))
                # 「液體 → 固體」字卡依使用者要求拿掉
            elif kind == "heat_back":          # 冰塊加溫變成水，再加溫變成水蒸氣
                for kd in ("冰塊", "水", "水蒸氣"):
                    icon(base, kd, POS[kd], Y, 1.0, 1.0)
                    label(base, kd, POS[kd], LY, F)
                arrow(base, POS["冰塊"] + 95, POS["水"] - 95, Y, ease((t - at("加溫", 0.6)) / 0.5), F, "加溫", color=(240, 140, 90))
                arrow(base, POS["水"] + 95, POS["水蒸氣"] - 95, Y, ease((t - at("再加溫", 2.6)) / 0.5), F, "加溫", color=(240, 140, 90))
            elif kind == "energy_cycle":       # 能量跟物質互相存在、互相轉化（另外畫，不配水的圖）
                e = ease(t / 0.3)
                pill(base, 300, Y, "能量", F(54, 800), NAVY, GOLD, scale=pop(t / 0.4), alpha=e)
                pill(base, 780, Y, "物質", F(54, 800), WHITE, (70, 96, 136), scale=pop((t - 0.15) / 0.4), alpha=e)
                p = ease((t - at("互相", 3.0)) / 0.5)
                arrow(base, 410, 670, Y - 24, p, F)
                arrow(base, 670, 410, Y + 24, p, F)
                ce = ease((t - at("轉化", 5.0)) / 0.4)
                if ce > 0.01:
                    caption(base, "互相轉化", F, ce)
            if c.get("fade_out", True):     # 片段最後 0.25 秒圖示淡出（下一段若是同一排圖會再接上）
                out_k = 1.0 - ease((t - (dur - 0.25)) / 0.25)
                if out_k < 1.0:
                    arr = np.array(base)
                    arr[..., 3] = (arr[..., 3] * out_k).astype(np.uint8)
                    base = Image.fromarray(arr, "RGBA")
            under.alpha_composite(base)
            return under

        L.render(os.path.join(out, f"ov_{cid}.mov"), frame, dur)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vo", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", choices=["intro", "outro", "overlay"])
    ap.add_argument("--preview", default="")
    args = ap.parse_args()
    L.PREVIEW[:] = [float(x) for x in args.preview.split(",") if x]
    os.makedirs(args.out, exist_ok=True)
    F = L.Fonts(args.font)
    info_path = os.path.join(args.out, "durations.json")
    info = json.load(open(info_path)) if os.path.exists(info_path) else {}
    if args.only in (None, "intro"):
        info["intro"] = round(intro(args, F, args.out), 3)
    info.pop("reveal", None)
    if args.only in (None, "outro"):
        info["outro"] = round(outro(args, F, args.out), 3)
    if args.only in (None, "overlay"):
        overlays(args, F, args.out)
    json.dump(info, open(info_path, "w"), indent=2)
    print(info)


if __name__ == "__main__":
    main()
