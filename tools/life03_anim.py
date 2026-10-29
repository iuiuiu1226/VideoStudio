#!/usr/bin/env python3
"""課堂精華 VOL.01（水結晶）的自製段落：AI 旁白（Gemini TTS）＋動畫，以及講師段落上的穿插動畫。

開頭（旁白稿 scripts/narration/life03_water_v2.txt 第 1–2 句）：只拋問題，答案留給講師
  書封《來自水的信息》浮上 →「水結晶實驗」金色六角形畫出 →「水結晶 × 能量」＋問號
講師段落穿插（透明疊加層，build_segment.py 的 overlay）：
  「好的力量…六角形」→「謝謝」的漂亮結晶＋金色六角形描邊；「不好的力量…打散」→「煩死了」的破碎結晶＋六角形碎裂；
  「正能量」→ 金色大字；「說好話、做好事、存善心」→ 三個金色標籤
結尾（第 3–6 句）：文字／聲音／念頭圖示＋能量波紋 → 人形注水六到七成 → 地球七成是水 → 善念 vs 惡念（最後多停一下）
結晶照片、書封取自講師投影片（素材 IMG_6552 的 19–22 秒鏡頭帶過投影片的畫面）。

輸出 --out 資料夾：intro.mp4、outro.mp4（含旁白）、overlay1.mov、overlay2.mov（透明疊加層）
與 subs.json（開頭、結尾各自的字幕，秒數從 0 起算），再用 build_segment.py 接成成片。

用法：
  python3 tools/life03_anim.py --src <素材資料夾> --vo work/life03_vo2 --font <NotoSansTC.ttf> --out work/life03_anim
"""
import argparse
import json
import math
import os
import re
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from build_segment import tonemap_chain

W, H, FPS = 1080, 1920, 30
TEMPO = 1.12                 # 旁白稍微加快（音高不變）
HEAD, GAP, TAIL = 0.35, 0.28, 0.55
NAVY = (13, 16, 24)
GOLD = (217, 180, 90)
WHITE = (255, 255, 255)
BLUE = (88, 168, 232)
GRAY = (150, 150, 160)
SRC_NAME = "IMG_6552.MOV"

# 每句旁白的字幕分段（顯示用文字；配音稿的「姜本勝」「姜本聖」是讀音寫法，字幕寫「江本勝」）
CHUNKS = {
    1: ["這本《來自水的信息》", "的作者江本勝", "做過一個很有名的", "「水結晶實驗」"],
    2: ["到底是什麼實驗？", "水結晶，又跟能量", "有什麼關係呢？"],
    3: ["江本勝認為", "文字、聲音、念頭", "都帶著訊息的能量"],
    4: ["人體約有六到七成是水"],
    5: ["地球表面約七成被水覆蓋"],
    6: ["我們每天給出的", "是善念 還是惡念呢？"],
}
PUNCT = re.compile(r"[\s，。、「」《》？！,.?!|]")


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def pop(x):
    """0→1 的彈出縮放（略為超過再回到 1）"""
    x = min(max(x, 0.0), 1.0)
    return 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2 if x < 1 else 1.0


class Fonts:
    def __init__(self, path):
        self.path = path
        self.cache = {}

    def __call__(self, size, weight=700):
        k = (size, weight)
        if k not in self.cache:
            f = ImageFont.truetype(self.path, size)
            f.set_variation_by_axes([weight])
            self.cache[k] = f
        return self.cache[k]


# ---------- 素材 ----------

def grab(src, t, crop):
    """從素材取一格（HDR 轉 SDR），crop=(x, y, w, h) 是原始 2160x3840 畫面上的位置"""
    x, y, w, h = crop
    vf = f"crop={w}:{h}:{x}:{y}," + tonemap_chain("arib-std-b67") + "format=rgb24"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombuffer("RGB", (w, h), raw).copy()


def load_vo(vo, n):
    """讀第 n 句旁白：去掉頭尾空白、加快 TEMPO 倍，回傳 (48k 單聲道 float 陣列, 字幕分段時間)"""
    meta = json.load(open(os.path.join(vo, "lines.json"), encoding="utf-8"))["lines"][n - 1]
    s, e = meta.get("speech_start", 0.0), meta.get("speech_end", meta["duration"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(s), "-t", str(e - s + 0.05),
                          "-i", os.path.join(vo, meta["file"]),
                          "-af", f"rubberband=tempo={TEMPO}:pitch=1:pitchq=quality", "-ac", "1", "-ar", "48000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32).copy()
    # 每個字的開始時間（加快後），用來對齊字幕與動畫
    chars = []
    words = meta["words"]
    for i, (ws, we, txt) in enumerate(words):
        cs = PUNCT.sub("", txt)
        nxt = words[i + 1][0] if i + 1 < len(words) else we
        for j in range(len(cs)):
            chars.append((ws + (nxt - ws) * j / max(len(cs), 1) - s) / TEMPO)
    dur = len(y) / 48000
    subs, k = [], 0
    for text in CHUNKS[n]:
        m = len(PUNCT.sub("", text))
        a = chars[k] if k < len(chars) else dur
        k += m
        b = chars[k] if k < len(chars) else dur
        subs.append([max(0.0, a), b, text])
    subs[-1][1] = dur
    return y, subs, chars, dur


# ---------- 繪圖小工具 ----------

def canvas(color=NAVY):
    return Image.new("RGB", (W, H), color)


def vignette_bg(t):
    """深藍底＋緩慢流動的光暈，跟片尾同色系（小圖模糊再放大，省時間）"""
    s = 4
    glow = Image.new("RGB", (W // s, H // s), NAVY)
    d = ImageDraw.Draw(glow)
    cx = (W / 2 + 120 * math.sin(t * 0.5)) / s
    cy = (820 + 80 * math.cos(t * 0.4)) / s
    for r, c in ((620, (20, 34, 58)), (420, (26, 50, 84)), (240, (34, 66, 106))):
        r /= s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    return glow.filter(ImageFilter.GaussianBlur(40)).resize((W, H), Image.BILINEAR)


def layer_text(base, xy, txt, font, fill, alpha=1.0, stroke=0, stroke_fill=NAVY):
    """置中文字（可半透明）"""
    if alpha <= 0:
        return
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, txt, font=font, fill=fill[:3] + (int(255 * alpha),), anchor="mm",
                               stroke_width=stroke, stroke_fill=stroke_fill[:3] + (int(255 * alpha),))
    base.alpha_composite(layer)


def paste_card(base, img, cx, cy, width, scale=1.0, alpha=1.0, radius=36, shadow=True):
    """圓角照片卡（含陰影），可縮放、淡入淡出"""
    if alpha <= 0.01:
        return
    w = max(2, int(width * scale))
    h = max(2, int(img.height * w / img.width))
    card = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=min(radius * scale, w / 2, h / 2),
                                           fill=int(255 * alpha))
    card.putalpha(mask)
    x, y = int(cx - w / 2), int(cy - h / 2)
    if shadow:
        pad = 90
        sh = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([pad + 8, pad + 22, pad + w + 8, pad + h + 22],
                                             radius=min(radius * scale, w / 2, h / 2), fill=(0, 0, 0, int(150 * alpha)))
        sh = sh.filter(ImageFilter.GaussianBlur(26))
        base.alpha_composite(sh, (max(0, x - pad), max(0, y - pad)),
                             (max(0, pad - x), max(0, pad - y)))
    base.alpha_composite(card, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))


def pill(base, cx, cy, txt, font, fg, bg, scale=1.0, alpha=1.0):
    if alpha <= 0 or scale <= 0.01:
        return
    tw = font.getlength(txt)
    pw, ph = int((tw + 70) * scale), int((font.size + 44) * scale)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], radius=ph / 2,
                        fill=bg + (int(235 * alpha),))
    f = ImageFont.truetype(font.path, max(8, int(font.size * scale)))
    f.set_variation_by_axes([800])
    d.text((cx, cy), txt, font=f, fill=fg + (int(255 * alpha),), anchor="mm")
    base.alpha_composite(layer)


def hexagon_pts(cx, cy, r, rot=0.0):
    return [(cx + r * math.cos(math.radians(60 * i + 30 + rot)), cy + r * math.sin(math.radians(60 * i + 30 + rot)))
            for i in range(6)]


def draw_hex_progress(base, cx, cy, r, prog, color=GOLD, width=10, rot=0.0, glow=True):
    """六角形描邊動畫：prog 0→1 依序畫出六條邊"""
    pts = hexagon_pts(cx, cy, r, rot)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    total = prog * 6
    for i in range(6):
        seg = min(max(total - i, 0.0), 1.0)
        if seg <= 0:
            break
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 6]
        d.line([(x0, y0), (x0 + (x1 - x0) * seg, y0 + (y1 - y0) * seg)], fill=color + (255,), width=width)
    if glow:
        base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(12)))
    base.alpha_composite(layer)


def draw_hex_shatter(base, cx, cy, r, k, color=(200, 200, 210), width=10):
    """六角形碎裂：六條邊往外飛散、旋轉、淡出（k 0→1）"""
    pts = hexagon_pts(cx, cy, r)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(7)
    for i in range(6):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 6]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = mx - cx, my - cy
        dist = 260 * ease(k) * (0.8 + 0.4 * rng.random())
        ang = math.radians((rng.random() - 0.5) * 140 * k)
        ox, oy = mx + dx / r * dist, my + dy / r * dist + 120 * k * k
        hx, hy = (x1 - x0) / 2 * 0.8, (y1 - y0) / 2 * 0.8
        rx, ry = hx * math.cos(ang) - hy * math.sin(ang), hx * math.sin(ang) + hy * math.cos(ang)
        a = int(255 * (1 - ease(max(0.0, (k - 0.35) / 0.65))))
        d.line([(ox - rx, oy - ry), (ox + rx, oy + ry)], fill=color + (a,), width=width)
    base.alpha_composite(layer)


def sparkle(base, cx, cy, t, n=10, rad=330, color=GOLD):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(n):
        ang = i * 2 * math.pi / n + t * 0.6
        rr = rad + 30 * math.sin(t * 3 + i)
        x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        s = 6 + 5 * (1 + math.sin(t * 5 + i * 1.7))
        a = int(160 + 90 * math.sin(t * 4 + i))
        d.polygon([(x, y - s * 2), (x + s * 0.5, y - s * 0.5), (x + s * 2, y), (x + s * 0.5, y + s * 0.5),
                   (x, y + s * 2), (x - s * 0.5, y + s * 0.5), (x - s * 2, y), (x - s * 0.5, y - s * 0.5)],
                  fill=color + (max(0, min(255, a)),))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1)))


# ---------- 段落 ----------

def build_timeline(vo, lines, tail=TAIL):
    audio, subs, marks, t = [], [], {}, HEAD
    for n in lines:
        y, s, chars, dur = load_vo(vo, n)
        marks[n] = (t, dur, chars)
        audio.append((t, y))
        subs += [[t + a, t + b, txt] for a, b, txt in s]
        t += dur + GAP
    total = t - GAP + tail
    mix = np.zeros(int(total * 48000) + 48000, np.float32)
    for t0, y in audio:
        i = int(t0 * 48000)
        mix[i:i + len(y)] += y
    return mix[:int(total * 48000)], subs, marks, total


def word_t(marks, n, k):
    """第 n 句第 k 個字（從 0 起算，不含標點）開始的時間（段落時間）"""
    t0, dur, chars = marks[n]
    return t0 + (chars[k] if k < len(chars) else dur)


PREVIEW = []  # --preview 秒數：只輸出這幾格的圖檔檢查版面，不輸出影片


def render(path, frames_fn, total, audio=None):
    """audio=None 時輸出透明疊加層（qtrle，含 alpha），否則輸出含旁白的 mp4"""
    if PREVIEW:
        for s in PREVIEW:
            if s <= total:
                frames_fn(s).convert("RGB").save(f"{os.path.splitext(path)[0]}_{s:05.2f}.jpg", quality=88)
        return
    if audio is None:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb", path], stdin=subprocess.PIPE)
        for i in range(int(round(total * FPS))):
            p.stdin.write(frames_fn(i / FPS).tobytes())
        p.stdin.close()
        p.wait()
        return
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.f32")
        audio.astype(np.float32).tofile(wav)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", wav,
                              "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                              "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                              "-c:a", "aac", "-b:a", "192k", "-shortest", path], stdin=subprocess.PIPE)
        for i in range(int(round(total * FPS))):
            p.stdin.write(frames_fn(i / FPS).convert("RGB").tobytes())
        p.stdin.close()
        p.wait()


def intro(args, F, out):
    """開頭：只拋問題（這本書的作者做過水結晶實驗——到底是什麼實驗？跟能量有什麼關係？），答案留給講師"""
    src = os.path.join(args.src, SRC_NAME)
    cover = grab(src, 19.7, (520, 470, 1400, 1940))       # 書封《來自水的信息》
    audio, subs, M, total = build_timeline(args.vo, [1, 2])
    t1, d1, _ = M[1]
    t2, d2, _ = M[2]
    w_exp = word_t(M, 1, 22)       # 「水結晶實驗」（第 22 個字起，不含標點）
    w_what = word_t(M, 2, 0)       # 「到底是什麼實驗？」
    w_energy = word_t(M, 2, 7)     # 「水結晶，又跟能量」
    CY = 800

    def frame(t):
        base = vignette_bg(t).convert("RGBA")
        # 書封：浮上、緩慢推近；講到「水結晶實驗」時縮進六角形中心消失（像變成結晶）
        k = ease((t - 0.05) / 0.7)
        out_k = ease((t - (w_exp - 0.3)) / 0.6)
        sc = (0.94 + 0.06 * min(t / max(w_exp, 0.1), 1.0)) * (1 - 0.7 * out_k)
        cy = CY + 60 + 80 * (1 - k)
        paste_card(base, cover, W / 2, cy, 560, scale=sc, alpha=k * (1 - out_k))
        if t >= w_exp - 0.2:
            # 「水結晶實驗」：金色六角形畫出來，標籤跳出
            hk = ease((t - (w_exp - 0.2)) / 0.9)
            rot = 12 * max(0.0, t - w_energy) if t >= w_energy else 0.0
            draw_hex_progress(base, W / 2, CY + 60, 280, hk, rot=rot)
            if t < w_what - 0.05:
                pill(base, W / 2, CY + 60, "水結晶實驗", F(60, 800), NAVY, GOLD, scale=pop((t - w_exp) / 0.45))
        if t >= w_what - 0.05:
            # 「到底是什麼實驗？」：六角形中間跳出大問號
            q = pop((t - w_what + 0.05) / 0.45)
            if q > 0.01:
                layer_text(base, (W / 2, CY + 60), "？", F(max(8, int(260 * q)), 900), GOLD, stroke=6)
        if t >= w_energy - 0.05:
            # 「水結晶，又跟能量有什麼關係呢？」
            e = pop((t - w_energy + 0.05) / 0.45)
            if e > 0.01:
                layer_text(base, (W / 2, CY - 330), "水結晶 × 能量", F(max(8, int(92 * e)), 900), WHITE, stroke=4)
            sparkle(base, W / 2, CY + 60, t, rad=330)
        # 結尾淡到黑，接講師畫面
        if t > total - 0.3:
            base = Image.blend(base.convert("RGB"), canvas((0, 0, 0)), ease((t - (total - 0.3)) / 0.3)).convert("RGBA")
        return base

    render(os.path.join(out, "intro.mp4"), frame, total, audio)
    return subs, total


def overlays(args, F, out):
    """講師段落上的穿插動畫（透明疊加層），時間用素材秒數；片段 1 是素材 0–19.05 秒，片段 2 是 22.14–33.25 秒"""
    src = os.path.join(args.src, SRC_NAME)
    good = grab(src, 20.7, (10, 1350, 680, 680))
    bad = grab(src, 22.2, (1016, 1447, 780, 780))
    Y = 990            # 放在臉的下方（臉約在 y 530–740），不會擋到臉，也在字幕（約 1180 起）上方
    R = 300            # 結晶圓圖直徑

    def crystal(base, img, s, a, b, x, hexa=None, shatter=None, label=None, lab_fg=NAVY, lab_bg=GOLD):
        if not (a - 0.05 <= s <= b + 0.35):
            return
        k = ease((s - a) / 0.35) * (1.0 - ease((s - b) / 0.35))
        paste_card(base, img, x, Y, R, scale=0.85 + 0.15 * k, alpha=k, radius=R / 2)
        if hexa is not None and s >= hexa:
            draw_hex_progress(base, x, Y, R * 0.62, ease((s - hexa) / 0.8) * (1 if s < b else k), width=7)
            if s >= hexa + 0.6:
                sparkle(base, x, Y, s, n=8, rad=R * 0.66)
        if shatter is not None:
            if s < shatter:
                draw_hex_progress(base, x, Y, R * 0.62, k, color=(210, 210, 220), width=7, glow=False)
            else:
                draw_hex_shatter(base, x, Y, R * 0.62, min((s - shatter) / 1.0, 1.0), width=7)
        if label:
            pill(base, x, Y - R / 2 - 30, label, F(44, 800), lab_fg, lab_bg, scale=pop((s - a) / 0.4), alpha=k)

    def frame1(t):
        s = t                                   # 片段 1 從素材 0 秒開始
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        crystal(base, good, s, 3.30, 6.70, 290, hexa=4.86, label="謝謝")
        crystal(base, bad, s, 6.95, 9.90, 290, shatter=8.86, label="煩死了", lab_fg=WHITE, lab_bg=(90, 92, 104))
        if s >= 18.15:
            e = pop((s - 18.15) / 0.4)
            if e > 0.01:
                layer_text(base, (300, Y), "正能量", F(max(8, int(120 * e)), 900), GOLD, stroke=6)
        return base

    def frame2(t):
        s = t + 22.14                           # 片段 2 從素材 22.14 秒開始
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        end = 29.9
        if 25.9 <= s <= end + 0.4:
            fade = 1.0 - ease((s - end) / 0.4)
            for i, (txt, ts) in enumerate((("說好話", 26.02), ("做好事", 27.60), ("存善心", 28.28))):
                if s >= ts - 0.05:
                    pill(base, 860, 830 + i * 120, txt, F(54, 800), NAVY, GOLD, scale=pop((s - ts + 0.05) / 0.4), alpha=fade)
        return base

    render(os.path.join(out, "overlay1.mov"), frame1, 19.05)
    render(os.path.join(out, "overlay2.mov"), frame2, 33.25 - 22.14)


def person_shape(d, cx, top, s, fill):
    """簡單人形：頭＋身體（圓角）"""
    d.ellipse([cx - 70 * s, top, cx + 70 * s, top + 140 * s], fill=fill)
    d.rounded_rectangle([cx - 135 * s, top + 165 * s, cx + 135 * s, top + 620 * s], radius=110 * s, fill=fill)


def outro(args, F, out):
    src = os.path.join(args.src, SRC_NAME)
    cover = grab(src, 19.7, (520, 470, 1400, 1940))
    good = grab(src, 20.7, (10, 1350, 680, 680))
    bad = grab(src, 22.2, (1016, 1447, 780, 780))
    audio, subs, M, total = build_timeline(args.vo, [3, 4, 5, 6], tail=1.4)   # 最後一句講完多停一下，收得溫柔
    t5, d5, _ = M[3]
    t6, d6, _ = M[4]
    t7, d7, _ = M[5]
    t8, d8, _ = M[6]
    w_word, w_sound, w_mind = word_t(M, 3, 5), word_t(M, 3, 7), word_t(M, 3, 9)
    w_energy = word_t(M, 3, 17)
    w_good, w_bad = word_t(M, 6, 8), word_t(M, 6, 12)
    CY = 760

    def icon(base, kind, cx, cy, s, a):
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        col = GOLD + (int(255 * a),)
        r = 120 * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=max(2, int(8 * s)))
        if kind == "文":
            d.text((cx, cy - 6 * s), "文", font=F(max(8, int(120 * s)), 800), fill=col, anchor="mm")
        elif kind == "聲":
            for i, hh in enumerate((40, 80, 120, 80, 40)):
                x = cx + (i - 2) * 34 * s
                d.rounded_rectangle([x - 10 * s, cy - hh / 2 * s, x + 10 * s, cy + hh / 2 * s], radius=10 * s, fill=col)
        else:
            d.ellipse([cx - 60 * s, cy - 55 * s, cx + 60 * s, cy + 30 * s], outline=col, width=max(2, int(8 * s)))
            for i, rr in enumerate((16, 11)):
                x, y = cx - 50 * s - i * 26 * s, cy + 52 * s + i * 24 * s
                d.ellipse([x - rr * s, y - rr * s, x + rr * s, y + rr * s], fill=col)
        base.alpha_composite(layer)

    def frame(t):
        base = vignette_bg(t).convert("RGBA")
        d = ImageDraw.Draw(base)
        if t < w_word + 0.3:
            k = ease((t - 0.05) / 0.5) * (1.0 - ease((t - (w_word - 0.25)) / 0.4))
            paste_card(base, cover, W / 2, CY - 20, 420, scale=0.95 + 0.05 * min(t / w_word, 1.0), alpha=k)
        if t < t6 - 0.1:
            fade = 1.0 - ease((t - (t6 - 0.5)) / 0.4)
            for kind, ts, label, x in (("文", w_word, "文字", 230), ("聲", w_sound, "聲音", 540), ("念", w_mind, "念頭", 850)):
                if t >= ts - 0.1:
                    s = pop((t - ts + 0.1) / 0.45)
                    icon(base, kind, x, CY - 60, 0.9 * s, fade)
                    layer_text(base, (x, CY + 110), label, F(52, 700), WHITE, alpha=fade * min(1.0, s))
            if t >= w_energy - 0.3:
                # 能量波紋：從中間往外擴散的同心圓
                layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
                ld = ImageDraw.Draw(layer)
                for i in range(4):
                    ph = ((t - (w_energy - 0.3)) * 0.9 + i * 0.25) % 1.0
                    r = 140 + 520 * ph
                    a = int(200 * (1 - ph) * fade)
                    ld.ellipse([W / 2 - r, CY - 60 - r, W / 2 + r, CY - 60 + r], outline=BLUE + (a,), width=6)
                base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(2)))
        if t6 - 0.3 <= t < t7 - 0.05:
            # 人體六到七成是水：人形從下往上注水，水面有波浪
            k = ease((t - (t6 - 0.3)) / 0.4)
            fade = 1.0 - ease((t - (t7 - 0.4)) / 0.35)
            s, top, cx = 0.95, CY - 340, W / 2
            m = Image.new("L", base.size, 0)
            person_shape(ImageDraw.Draw(m), cx, top, s, 255)
            body = Image.new("RGBA", base.size, (255, 255, 255, 0))
            ImageDraw.Draw(body).rectangle([0, 0, W, H], fill=(255, 255, 255, int(40 * k * fade)))
            base.alpha_composite(Image.composite(body, Image.new("RGBA", base.size, (0, 0, 0, 0)), m))
            level = 0.65 * ease((t - t6) / (d6 * 0.8))
            y_bot, y_top = top + 620 * s, top
            wy = y_bot - (y_bot - y_top) * level
            water = Image.new("RGBA", base.size, (0, 0, 0, 0))
            wd = ImageDraw.Draw(water)
            pts = [(x, wy + 12 * math.sin(x / 55 + t * 5)) for x in range(int(cx - 160), int(cx + 161), 8)]
            wd.polygon(pts + [(cx + 160, y_bot + 10), (cx - 160, y_bot + 10)], fill=BLUE + (int(230 * k * fade),))
            base.alpha_composite(Image.composite(water, Image.new("RGBA", base.size, (0, 0, 0, 0)), m))
            outline = Image.new("RGBA", base.size, (0, 0, 0, 0))
            om = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
            outline.paste((255, 255, 255, int(255 * k * fade)), (0, 0), om)
            base.alpha_composite(outline)
            pct = int(round(70 * ease((t - t6) / (d6 * 0.8))))
            layer_text(base, (cx + 300, CY - 40), f"60–{pct}%" if pct > 60 else f"{pct}%",
                       F(80, 900), GOLD, alpha=k * fade, stroke=3)
        if t7 - 0.3 <= t < t8 - 0.05:
            # 地球七成是水：圓形依序填滿 70% 藍色
            k = ease((t - (t7 - 0.3)) / 0.4)
            fade = 1.0 - ease((t - (t8 - 0.4)) / 0.35)
            r, cx, cy = 300 * (0.9 + 0.1 * k), W / 2, CY - 40
            layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 120, 80, int(255 * k * fade)))
            sweep = 252 * ease((t - t7) / (d7 * 0.75))
            ld.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + sweep, fill=BLUE + (int(255 * k * fade),))
            ld.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE + (int(220 * k * fade),), width=6)
            base.alpha_composite(layer)
            pct = int(round(70 * ease((t - t7) / (d7 * 0.75))))
            layer_text(base, (cx, cy), f"{pct}%", F(130, 900), WHITE, alpha=k * fade, stroke=5)
        if t >= t8 - 0.3:
            # 善念 vs 惡念：左右兩個結晶，問號
            k = ease((t - (t8 - 0.3)) / 0.5)
            paste_card(base, good, 275, CY - 40, 380, scale=0.9 + 0.1 * k, alpha=k, radius=190)
            paste_card(base, bad, 805, CY - 40, 380, scale=0.9 + 0.1 * k, alpha=k, radius=190)
            if t >= w_good - 0.05:
                pill(base, 275, CY + 230, "善念", F(60, 800), NAVY, GOLD, scale=pop((t - w_good) / 0.4))
            if t >= w_bad - 0.05:
                pill(base, 805, CY + 230, "惡念", F(60, 800), WHITE, (90, 92, 104), scale=pop((t - w_bad) / 0.4))
            if t >= w_bad + 0.3:
                q = pop((t - w_bad - 0.3) / 0.45)
                if q > 0.01:
                    layer_text(base, (W / 2, CY - 40), "？", F(max(8, int(170 * q)), 900), GOLD, stroke=6)
        return base

    render(os.path.join(out, "outro.mp4"), frame, total, audio)
    return subs, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="含 IMG_6552.MOV 的素材資料夾")
    ap.add_argument("--vo", required=True, help="voice_gemini.py 的輸出資料夾")
    ap.add_argument("--font", required=True, help="NotoSansTC 字型檔")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", choices=["intro", "outro", "overlay"])
    ap.add_argument("--preview", default="", help="只輸出這幾個時間點的畫面，例如 1,5.5,12")
    args = ap.parse_args()
    PREVIEW[:] = [float(x) for x in args.preview.split(",") if x]
    os.makedirs(args.out, exist_ok=True)
    F = Fonts(args.font)
    path = os.path.join(args.out, "subs.json")
    res = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    if args.only in (None, "intro"):
        s, d = intro(args, F, args.out)
        res["intro"] = {"dur": round(d, 3), "subs": [[round(a, 2), round(b, 2), x] for a, b, x in s]}
    if args.only in (None, "overlay"):
        overlays(args, F, args.out)
    if args.only in (None, "outro"):
        s, d = outro(args, F, args.out)
        res["outro"] = {"dur": round(d, 3), "subs": [[round(a, 2), round(b, 2), x] for a, b, x in s]}
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for k, v in res.items():
        print(f"{k}: {v['dur']:.2f} 秒，字幕 {len(v['subs'])} 段")


if __name__ == "__main__":
    main()
