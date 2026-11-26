#!/usr/bin/env python3
"""編號 10「BK 是什麼？」的自製動畫段落（跟課堂精華 VOL.01 水結晶同一套深藍底＋金色）。

timeline.mp4：「從哪裡來」的時間軸，配合旁白（目前還沒配音，旁白先用字幕代替，秒數照預估的配音長度）
  1960 年代｜應用肌動學（壓手臂，看肌肉的力氣）→ 線往下長 → 1970 年代｜預防醫學的醫生（加進情緒、心理的因素）
  書（《BK》1979）不放在動畫裡：講師下一段自己會講，畫面是講師投影片上的書封（真的照片）
第二版（「BK 為什麼會出現」，--v2 --px <工作檔資料夾>）另外輸出：
  timeline_v2.mp4：第二個節點的說明改成「在生病之前預防」（旁白講預防醫學的醫生想找出什麼對身體好）
  demo.mp4：安和老師「人產生兩種反應…撐住…掉下去…胸腺是管免疫力荷爾蒙分泌的」（IMG_8497 5.10–19.58 的原音），
    講到「撐住」「掉下去」時畫面換成糖果測試（IMG_8496）手臂真的撐住、真的掉下去的那幾秒（動作對在講到那個詞的時候）
  thymus_a.mov／thymus_b.mov：胸腺位置小卡（透明疊加層，字幕下方、不擋臉）：上半身剪影＋胸口金色亮點＋「胸腺」；
    a 疊在 demo.mp4（講到「胸腺有關」出現、到結尾不收），b 疊在下一段「會讓你的胸腺萎縮」（一開始就在，
    講到「萎縮」金色亮點縮小變灰，「分泌減少」講完收掉）；a、b 卡片位置一樣，接起來看起來是同一張
版面：時間軸在 y 480–1110（系列標題下面、字幕上面）；字幕在胸口高度、段落標籤 y 1350 由 build_segment 疊上去。
聲音：無聲（之後配旁白時，旁白另外混進來）。

用法：python3 tools/ep10_anim.py --font <NotoSansTC.ttf> [--out work/ep10_anim] [--dur 7.6] [--step 3.6] [--preview 1,5]
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import life03_anim as L  # noqa: E402
from life03_anim import ease  # noqa: E402

W, H, FPS = 1080, 1920, 30
NAVY, GOLD, WHITE, GRAY = (13, 16, 24), (217, 180, 90), (255, 255, 255), (170, 172, 182)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

NODES = [  # (年代, 主題, 說明, y)
    ("1960 年代", "應用肌動學", "壓手臂，看肌肉的力氣", 560),
    ("1970 年代", "預防醫學的醫生", "加進情緒、心理的因素", 880),
]
DOT_X, TEXT_X = 196, 262


def background():
    """深藍底＋中間微亮（跟水結晶那部的開頭同一種感覺）"""
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
    k = np.clip(1.0 - d * 1.6, 0, 1)[..., None]
    base = np.array(NAVY, float) + k * np.array([22, 26, 38], float)
    return Image.fromarray(base.astype(np.uint8), "RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "ep10_anim"))
    ap.add_argument("--dur", type=float, default=7.6, help="整段長度（秒）")
    ap.add_argument("--step", type=float, default=3.6, help="第二個節點（1970 年代）出現的時間＝第二句旁白開始")
    ap.add_argument("--preview", default="")
    ap.add_argument("--book-src", default="", help="書封段落：講師那支工作檔（IMG_8498），書封取自投影片、聲音取 --a-in～--a-out")
    ap.add_argument("--book-t", type=float, default=104.6, help="投影片上書封拍得最完整的那一格（素材秒數）")
    ap.add_argument("--a-in", type=float, default=134.00)
    ap.add_argument("--a-out", type=float, default=137.95)
    ap.add_argument("--v2", action="store_true", help="第二版的 timeline_v2、demo、thymus_a／b")
    ap.add_argument("--px", default="", help="--v2 用：工作檔資料夾（IMG_8497.MOV、IMG_8496.MOV）")
    ap.add_argument("--v3", action="store_true", help="第三版的 book_v3（《BK》→ 後來改名《Your Body Doesn't Lie》），要加 --book-src")
    ap.add_argument("--v3anim", action="store_true", help="第三版旁白段落的動畫：deltoid.mp4、observe.mp4、question.mp4")
    ap.add_argument("--vo", default=os.path.join(ROOT, "work", "ep10_vo"), help="--v3anim 用：旁白配音資料夾（voice_gemini.py 的輸出）")
    args = ap.parse_args()
    if args.v3anim:
        v3_anims(args)
        return
    if args.v2:
        NODES[1] = ("1970 年代", "預防醫學的醫生", "在生病之前預防", 880)
    if args.book_src:
        # 書封：IMG_8498 104.6 秒投影片左邊那本《BK》（真的照片，不用網路圖）
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{args.book_t}", "-i", args.book_src, "-frames:v", "1",
                              "-vf", "crop=362:684:2:292", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        cover = Image.frombuffer("RGB", (362, 684), raw).copy()
        # 同一張投影片右邊那本《Your Body Doesn't Lie》（《BK》後來改的書名）
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{args.book_t}", "-i", args.book_src, "-frames:v", "1",
                              "-vf", "crop=338:592:432:358", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        cover2 = Image.frombuffer("RGB", (338, 592), raw).copy()
    os.makedirs(args.out, exist_ok=True)
    F = L.Fonts(args.font)
    f_year, f_main, f_sub = F(60, 800), F(78, 900), F(44, 500)
    bg = background()
    starts = [0.25, args.step]

    def frame(t):
        im = bg.copy().convert("RGBA")
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        # 節點之間的線：第二句開始前 0.3 秒開始往下長
        y0, y1 = NODES[0][3] + 34, NODES[1][3] - 34
        g = ease((t - (args.step - 0.3)) / 0.6)
        d.line([(DOT_X, y0), (DOT_X, y0 + (y1 - y0) * g)], fill=GOLD + (200,), width=6)
        for (year, main_t, sub, y), st in zip(NODES, starts):
            a = ease((t - st) / 0.45)
            if a <= 0:
                continue
            dx = int((1 - a) * 40)
            r = 22 * (0.6 + 0.4 * a)
            d.ellipse([DOT_X - r, y - r, DOT_X + r, y + r], fill=GOLD + (int(255 * a),))
            d.text((TEXT_X + dx, y - 38), year, font=f_year, fill=GOLD + (int(255 * a),), anchor="lm")
            d.text((TEXT_X + dx, y + 52), main_t, font=f_main, fill=WHITE + (int(255 * a),), anchor="lm",
                   stroke_width=2, stroke_fill=NAVY + (int(255 * a),))
            d.text((TEXT_X + dx, y + 132), sub, font=f_sub, fill=GRAY + (int(255 * a),), anchor="lm")
        im.alpha_composite(lay)
        fo = ease((args.dur - t) / 0.3)          # 最後 0.3 秒淡出（接講師畫面另外有交叉淡化）
        if fo < 1:
            im = Image.blend(bg.convert("RGBA"), im, fo)
        return im.convert("RGB")

    f_pill = F(46, 800)

    def book_frame(t):
        """書封放在系列標題和字幕中間（y 約 400–1035，字幕兩行時頂端約 1070，不會擋到書），慢慢放大一點；書的右上方外面金色「1979」
        （使用者 2026/11/20：原本書太大、下半部被字幕擋住 → 寬 430 改 330、中心 y 780 改 715）"""
        dur = args.a_out - args.a_in
        im = bg.copy().convert("RGBA")
        s = 1.0 + 0.04 * min(t / dur, 1.0)
        a = ease(t / 0.35)
        w = int(330 * s * (0.94 + 0.06 * a))
        h = int(w * cover.height / cover.width)
        cx, cy = W // 2, 715
        card = cover.resize((w, h), Image.LANCZOS).convert("RGBA")
        shadow = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([30, 36, w + 30, h + 36], 18, fill=(0, 0, 0, int(150 * a)))
        from PIL import ImageFilter
        shadow = shadow.filter(ImageFilter.GaussianBlur(16))
        im.alpha_composite(shadow, (cx - w // 2 - 30, cy - h // 2 - 30))
        card.putalpha(int(255 * a))
        im.alpha_composite(card, (cx - w // 2, cy - h // 2))
        pa = ease((t - 0.5) / 0.4)
        if pa > 0:
            d = ImageDraw.Draw(im)
            px, py = cx + w // 2 + 104, cy - h // 2 + 40   # 書封右邊外面（文字不壓到書；x 到 900 以內，避開右側按鈕）
            d.rounded_rectangle([px - 90, py - 36, px + 90, py + 36], 36, fill=GOLD + (int(255 * pa),))
            d.text((px, py), "1979", font=f_pill, fill=NAVY + (int(255 * pa),), anchor="mm")
        return im.convert("RGB")

    def card(im, img, cx, cy, w, a):
        """書封＋陰影，中心 (cx, cy)、寬 w、透明度 a"""
        from PIL import ImageFilter
        w = int(w)
        h = int(w * img.height / img.width)
        sh = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([30, 36, w + 30, h + 36], 18, fill=(0, 0, 0, int(150 * a)))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (int(cx - w / 2 - 30), int(cy - h / 2 - 30)))
        c = img.resize((w, h), Image.LANCZOS).convert("RGBA")
        c.putalpha(int(255 * a))
        im.alpha_composite(c, (int(cx - w / 2), int(cy - h / 2)))
        return h

    BOOK_DUR = args.a_out - args.a_in
    MOVE_T, MOVE_D = BOOK_DUR + 0.07, 0.7

    def book_v3_frame(t):
        """第三版：講師講完「這本是他第一本出的書，就是叫 BK」之後，《BK》移到左邊，右邊滑進《Your Body Doesn't Lie》，
        中間金色箭頭（後來改的書名）；「1979」移到《BK》上方。兩本都在系列標題和字幕中間（y 約 450–980）"""
        if t < MOVE_T:
            return book_frame(t)
        k = ease((t - MOVE_T) / MOVE_D)
        im = bg.copy().convert("RGBA")
        w1 = 330 * 1.04 + (280 - 330 * 1.04) * k
        cx1, cy = 540 + (350 - 540) * k, 715
        h1 = card(im, cover, cx1, cy, w1, 1.0)
        card(im, cover2, 900 + (730 - 900) * k, cy, 280, k)
        d = ImageDraw.Draw(im)
        if k > 0:                                   # 箭頭：《BK》右邊（x 490）到《Your Body Doesn't Lie》左邊（x 590）中間
            col = GOLD + (int(255 * k),)
            d.line([(505, cy), (562, cy)], fill=col, width=9)
            d.polygon([(578, cy), (556, cy - 18), (556, cy + 18)], fill=col)
        px0, py0 = 540 + 330 * 1.04 / 2 + 104, cy - int(330 * 1.04 * cover.height / cover.width) / 2 + 40
        px, py = px0 + (cx1 - px0) * k, py0 + (cy - h1 / 2 - 46 - py0) * k
        d.rounded_rectangle([px - 90, py - 36, px + 90, py + 36], 36, fill=GOLD + (255,))
        d.text((px, py), "1979", font=f_pill, fill=NAVY + (255,), anchor="mm")
        return im.convert("RGB")

    if args.preview:
        for s in [float(x) for x in args.preview.split(",")]:
            frame(s).save(os.path.join(args.out, f"preview_{s:05.2f}.png"))
            if args.book_src:
                book_frame(s).save(os.path.join(args.out, f"preview_book_{s:05.2f}.png"))
                book_v3_frame(s).save(os.path.join(args.out, f"preview_book3_{s:05.2f}.png"))
        print("預覽：", args.out)
        return
    if args.v3:
        # 聲音：前 3.93 秒是講師原音（IMG_8498 134.00–137.95），後面剪輯時用背景聲補（pad）
        write(os.path.join(args.out, "book_v3.mp4"), book_v3_frame, BOOK_DUR + 2.8, audio=(args.book_src, args.a_in, args.a_out + 2.8))
        return
    if args.v2:
        write(os.path.join(args.out, "timeline_v2.mp4"), frame, args.dur)
        demo(args.px, os.path.join(args.out, "demo.mp4"))
        tf = thymus_frames(F)
        write_overlay(os.path.join(args.out, "thymus_a.mov"), lambda t: tf(t, appear=DEMO_THYMUS_IN), DEMO_DUR + 0.5)   # 多 0.5 秒蓋過後面的停頓
        write_overlay(os.path.join(args.out, "thymus_b.mov"),
                      lambda t: tf(t, appear=None, shrink=(27.20 - 24.90, 28.40 - 24.90), leave=31.80 - 24.90), 31.80 - 24.90)
        return
    write(os.path.join(args.out, "timeline.mp4"), frame, args.dur)
    if args.book_src:
        write(os.path.join(args.out, "book.mp4"), book_frame, args.a_out - args.a_in,
              audio=(args.book_src, args.a_in, args.a_out))


# ── 第三版旁白段落的動畫（使用者 2026/11/24：旁白做成動畫比較適合，取代學員練習畫面）──
# 同一套深藍底＋金色；圖都畫在系列標題和字幕中間（y 約 440–1030）；無聲（之後配旁白再混進來）
SIL = (232, 234, 240)          # 人形剪影（同胸腺小卡）
DELTOID_DUR, OBSERVE_DUR, QUESTION_DUR = 3.4, 11.72, 7.5
# 對照圖（compare.mp4）：聲音＝cuts/ep10/seg_cmp_audio.json 用 build_segment 接好的老師原音（work/ep10_anim/cmp_audio.mp4，14.27 秒）
# 各欄（出現, 免疫力那行, 正／負能量）＝原片秒數換算到接好的時間：「掉」40.00、「免疫力」44.32、「下降」44.96；「肩膀」50.83、「免疫力」59.02、「比較強」59.60
COMPARE_DUR = 14.27
CMP_R = (1.45, 3.45, 4.15)    # 右欄 掉下去
CMP_L = (7.45, 12.50, 13.15)  # 左欄 撐住
# 旁白配音（使用者 2026/11/25 儲值後要配；scripts/narration/ep10_v3.txt → work/ep10_vo，Sulafat，加快 1.12 倍）
# 時間＝配音原檔的秒數（聲音能量找到的開口時間）÷ 1.12
VO_TEMPO = 1.12
OBS_NS = 0.3                                   # 旁白開始（對照圖拆出去成 compare.mp4）
OBS_CANDY_END = 3.11                           # 「不只是吃的東西」講完（旁白秒數）
OBS_CHIPS = [3.59, 4.35, 5.09, 6.01, 6.87, 7.50, 8.17]   # 姿勢、聲音、情緒、穿著、燈光、圖像、表情 唸到的時間
OBS_VO_END = 10.92
Q_NS = 0.3                                     # 問句旁白開始
Q_L2, Q_CTA, Q_VO_END = 1.45, 3.64, 5.49        # 「能分辨…」「歡迎來報名…」開口、唸完（旁白秒數）
CHIPS = ["姿勢", "聲音", "情緒", "穿著", "燈光", "圖像", "表情"]
SLOTS = [(320, 480), (720, 480), (320, 620), (720, 620), (320, 760), (720, 760), (320, 900), (720, 900)]


def figure(d, cx, top, s, arm="up", a=1.0, other_arm=True, arm_len=1.0):
    """正面人形：頭、身體、畫面左邊的手下垂、畫面右邊的手平舉（up）或往下掉（down）；回傳 (肩膀, 手) 的位置
    other_arm=False 不畫下垂的那隻手（只留表示撐住／掉下去的手）；arm_len 是那隻手的長度比例"""
    import math
    c = SIL + (int(235 * a),)
    hr = 58 * s
    hy = top + hr
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=c)
    d.rounded_rectangle([cx - 22 * s, hy + hr - 10 * s, cx + 22 * s, hy + hr + 40 * s], 8 * s, fill=c)
    t0 = hy + hr + 30 * s
    d.rounded_rectangle([cx - 110 * s, t0, cx + 110 * s, t0 + 380 * s], 70 * s, fill=c)
    if other_arm:
        d.rounded_rectangle([cx - 160 * s, t0 + 20 * s, cx - 108 * s, t0 + 330 * s], 26 * s, fill=c)
    sh = (cx + 104 * s, t0 + 48 * s)
    d.ellipse([sh[0] - 36 * s, sh[1] - 36 * s, sh[0] + 36 * s, sh[1] + 36 * s], fill=c)
    ln = 300 * s * arm_len
    ang = 0 if arm == "up" else math.radians(58)
    hand = (sh[0] + ln * math.cos(ang), sh[1] + ln * math.sin(ang))
    d.line([sh, hand], fill=c, width=int(58 * s))
    d.ellipse([hand[0] - 31 * s, hand[1] - 31 * s, hand[0] + 31 * s, hand[1] + 31 * s], fill=c)
    return sh, hand


def smooth_figure(im, cx, top, s, arm="up", a=1.0, arm_len=0.75, ss=3):
    """對照圖用的人形（使用者 2026/11/25：手臂不要凸凸的）：頭、身體、一隻手（平舉 up／往下掉 down）
    手臂粗細一致、從身體裡面長出來（肩膀跟身體連在一起，不另外畫一顆圓）、末端用同樣粗細的圓頭收尾；
    放大 ss 倍畫再縮小，邊緣平滑"""
    import math
    hr = 58 * s
    t0 = top + 2 * hr + 30 * s
    L = 300 * s * arm_len                       # 手臂露出身體的長度
    x0, y0 = cx - 120 * s, top - 4               # 畫布範圍（夠放平舉的手）
    x1, y1 = cx + 120 * s + L + 40 * s, t0 + 390 * s
    Wc, Hc = int((x1 - x0) * ss), int((y1 - y0) * ss)
    cv = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    c = SIL + (int(235 * a),)
    X = lambda x: (x - x0) * ss
    Y = lambda y: (y - y0) * ss
    hy = top + hr
    d.ellipse([X(cx - hr), Y(hy - hr), X(cx + hr), Y(hy + hr)], fill=c)
    d.rounded_rectangle([X(cx - 22 * s), Y(hy + hr - 10 * s), X(cx + 22 * s), Y(t0 + 20 * s)], 8 * s * ss, fill=c)
    d.rounded_rectangle([X(cx - 110 * s), Y(t0), X(cx + 110 * s), Y(t0 + 380 * s)], 70 * s * ss, fill=c)
    w = 54 * s                                   # 手臂粗細
    p0 = (cx + 56 * s, t0 + 52 * s)              # 從身體裡面開始
    ang = 0 if arm == "up" else math.radians(60)
    inside = (110 * s - 56 * s) / max(math.cos(ang), 0.3)
    p1 = (p0[0] + (inside + L) * math.cos(ang), p0[1] + (inside + L) * math.sin(ang))
    d.line([(X(p0[0]), Y(p0[1])), (X(p1[0]), Y(p1[1]))], fill=c, width=int(w * ss))
    r = w / 2
    for px, py in (p0, p1):
        d.ellipse([X(px - r), Y(py - r), X(px + r), Y(py + r)], fill=c)
    cv = cv.resize((max(1, Wc // ss), max(1, Hc // ss)), Image.LANCZOS)
    im.alpha_composite(cv, (int(x0), int(y0)))


def arrow(d, x, y0, y1, col, w=10):
    """直的箭頭，從 y0 指向 y1"""
    d.line([(x, y0), (x, y1 - (12 if y1 > y0 else -12))], fill=col, width=w)
    h = 24 if y1 > y0 else -24
    d.polygon([(x, y1), (x - 20, y1 - h), (x + 20, y1 - h)], fill=col)


def glow(im, cx, cy, r, col, a):
    from PIL import ImageFilter
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (int(170 * a),))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(float(r) * 0.4)))


def v3_anims(args):
    os.makedirs(args.out, exist_ok=True)
    F = L.Fonts(args.font)
    bg = background()
    f_lab, f_chip, f_small, f_q = F(70, 900), F(60, 800), F(50, 800), F(82, 900)
    f_head, f_act, f_imm, f_eng = F(54, 800), F(58, 900), F(50, 800), F(72, 900)
    f_cta = F(54, 900)
    from life03_anim import pop

    def deltoid(t):
        """「測試時看的是手臂和肩膀之間的三角肌」：人形手臂平舉 → 肩膀（三角肌）金色亮起＋「三角肌」→ 手腕上方往下壓的箭頭，手臂撐住"""
        im = bg.copy().convert("RGBA")
        a = ease((t - 0.1) / 0.35)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        sh, hand = figure(d, 440, 450, 1.0, "up", a)
        im.alpha_composite(lay)
        k = ease((t - 0.6) / 0.4)
        if k > 0:
            pulse = 1 + 0.08 * np.sin((t - 0.6) * 2 * np.pi / 1.4)
            glow(im, sh[0] - 4, sh[1] - 4, 70 * pulse, GOLD, k)
            d = ImageDraw.Draw(im)
            d.ellipse([sh[0] - 50, sh[1] - 44, sh[0] + 46, sh[1] + 40], fill=GOLD + (int(255 * k),))
        k2 = ease((t - 0.9) / 0.4)
        if k2 > 0:
            d = ImageDraw.Draw(im)
            col = GOLD + (int(255 * k2),)
            # 標籤放在手臂下面（上面留給往下壓的箭頭）
            d.line([(sh[0] + 14, sh[1] + 42), (sh[0] + 70, sh[1] + 110)], fill=col, width=5)
            d.text((sh[0] + 82, sh[1] + 110), "三角肌", font=f_lab, fill=col, anchor="lm", stroke_width=2, stroke_fill=NAVY + (255,))
        k3 = ease((t - 1.6) / 0.3)
        if k3 > 0:
            dy = 14 * max(0.0, np.sin((t - 1.6) * 2 * np.pi / 0.9))       # 輕輕往下壓的動作
            ax = hand[0] - 40
            arrow(ImageDraw.Draw(im), ax, hand[1] - 150 + dy, hand[1] - 46 + dy, GOLD + (int(255 * k3),))
        return im.convert("RGB")

    def candy(d, cx, cy, s, col, a):
        c = col + (int(255 * a),)
        d.ellipse([cx - 80 * s, cy - 55 * s, cx + 80 * s, cy + 55 * s], fill=c)
        d.polygon([(cx - 70 * s, cy), (cx - 150 * s, cy - 55 * s), (cx - 150 * s, cy + 55 * s)], fill=c)
        d.polygon([(cx + 70 * s, cy), (cx + 150 * s, cy - 55 * s), (cx + 150 * s, cy + 55 * s)], fill=c)
        st = NAVY + (int(110 * a),)
        d.line([(cx - 28 * s, cy - 50 * s), (cx - 48 * s, cy + 46 * s)], fill=st, width=max(2, int(10 * s)))
        d.line([(cx + 30 * s, cy - 50 * s), (cx + 10 * s, cy + 46 * s)], fill=st, width=max(2, int(10 * s)))

    def chip(d, cx, cy, text, a, sc=1.0, muted=False):
        w, h = 340 * sc, 108 * sc
        edge = (GRAYED if muted else GOLD) + (int(255 * a),)
        d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 28 * sc, fill=(30, 36, 52, int(235 * a)),
                            outline=edge, width=4)
        if text:
            d.text((cx, cy), text, font=f_chip, fill=WHITE + (int(255 * a),), anchor="mm")

    CARD_T = 0.0      # 對照圖 2026/11/26 改成獨立一段 compare.mp4（配老師原音），observe 直接從糖果開始

    def compare(t):
        """對照圖（使用者 2026/11/24：要很明確分別撐住＝免疫力提升＝正能量、掉下去＝免疫力下降＝負能量）
        2026/11/26 改成配老師原音（cmp_audio.mp4：IMG_8497「所以剛剛那個手掉下去，因為那會讓你的免疫力下降。
        那如果那個東西會讓你肩膀肌肉撐住，表示那個時候胸腺是正常擴張的狀態，那時候你的身體的免疫力就比較強」）：
        老師先講掉下去 → 右欄先出現；講到撐住 → 左欄出現；「免疫力下降／比較強」講到時那一行和「負能量／正能量」才出現。
        版面（使用者 2026/11/26：「在 BK 測試裡」離框太近，整個重排；這段的字幕可以跟其他段不一樣）：
        小標 y 492、框 y 615–1215（小標和框之間留約 90 px）、框內人形 645–855、文字 915、免疫力 1010、正／負能量 1120；
        字幕移到框下面（剪輯清單裡用 \pos 把字幕底邊放在 y 1500，兩行時上緣約 1300，離框約 85 px）"""
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        ah = ease((t - 0.05) / 0.35)
        d.text((540, 492), "在 BK 測試裡", font=f_head, fill=GOLD + (int(255 * ah),), anchor="mm")
        for cx, arm, col, (t0, t_imm, t_eng), act, imm, up, eng in [
                (300, "up", GOLD, CMP_L, "手臂撐住", "免疫力提升", True, "正能量"),
                (720, "down", GRAYED, CMP_R, "手臂掉下去", "免疫力下降", False, "負能量")]:
            ab = ease((t - t0) / 0.3)
            if ab <= 0:
                continue
            d.rounded_rectangle([cx - 185, 615, cx + 185, 1215], 34, fill=(24, 30, 44, int(225 * ab)),
                                outline=col + (int(255 * ab),), width=5)
            smooth_figure(lay, cx - 48, 645, 0.40, arm, ab, arm_len=0.72)   # 手尖約到 cx+85，框右緣 cx+185
            d = ImageDraw.Draw(lay)
            d.text((cx, 915), act, font=f_act, fill=WHITE + (int(255 * ab),), anchor="mm")
            a3 = ease((t - t_imm) / 0.3)
            if a3 > 0:
                c3 = col + (int(255 * a3),)
                x0 = cx - 150
                arrow(d, x0, 1035 if up else 985, 985 if up else 1035, c3, w=9)
                d.text((x0 + 34, 1010), imm, font=f_imm, fill=c3, anchor="lm")
            a4 = ease((t - t_eng) / 0.3)
            if a4 > 0:
                sc = pop((t - t_eng) / 0.35)
                pw, ph = 250 * sc, 106 * sc
                fill = col if up else (70, 74, 86)
                d.rounded_rectangle([cx - pw / 2, 1120 - ph / 2, cx + pw / 2, 1120 + ph / 2], 53 * sc, fill=fill + (int(255 * a4),))
                d.text((cx, 1120), eng, font=f_eng, fill=(NAVY if up else WHITE) + (int(255 * a4),), anchor="mm")
        return lay

    def compare_frame(t):
        im = bg.copy().convert("RGBA")
        im.alpha_composite(compare(t))
        return im.convert("RGB")

    def observe(t):
        """對照圖（0–5.2 秒）→「John Diamond 博士還觀察到，不只是吃的東西」糖果 →（不放字幕）糖果縮到第一格、
        七個字卡一個一個出現 →「都會讓肌肉變強或變弱」字卡留著"""
        im = bg.copy().convert("RGBA")
        if t < CARD_T:
            im.alpha_composite(compare(t))
            return im.convert("RGB")
        t = t - CARD_T
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        k = ease((t - (OBS_NS - CARD_T + OBS_CANDY_END - 0.1)) / 0.5)   # 「吃的東西」講完，糖果移到第一格
        cx, cy = 540 + (SLOTS[0][0] - 540) * k, 720 + (SLOTS[0][1] - 720) * k
        if k > 0:
            chip(d, SLOTS[0][0], SLOTS[0][1], "", k, muted=True)
        sc = (1 - 0.6 * k) * pop((t - 0.15) / 0.45)
        col = tuple(int(g + (q - g) * k) for g, q in zip(GOLD, GRAYED))
        candy(d, cx, cy, sc, col, min(1.0, ease((t - 0.15) / 0.3)))
        for i, word in enumerate(CHIPS):
            st = OBS_NS - CARD_T + OBS_CHIPS[i] - 0.12     # 唸到那個詞就出現
            a = ease((t - st) / 0.3)
            if a > 0:
                chip(d, SLOTS[i + 1][0], SLOTS[i + 1][1], word, a, sc=pop((t - st) / 0.35))
        im.alpha_composite(lay)
        return im.convert("RGB")

    def question(t):
        """結尾問句（大字，不另外放字幕）：「肌肉力量的強弱／能分辨好壞真偽嗎？」
        → 金色按鈕「歡迎來報名課程，實際體驗」（使用者 2026/11/25 要加）"""
        im = bg.copy().convert("RGBA")
        d = ImageDraw.Draw(im)
        fo = 1 - ease((t - (QUESTION_DUR - 1.3)) / 0.3)   # 交叉淡化進片尾（1 秒）之前先收掉，大字不跟片尾 Logo 疊在一起
        for txt, y, st, col in [("肌肉力量的強弱", 640, Q_NS - 0.1, WHITE), ("能分辨好壞真偽嗎？", 790, Q_NS + Q_L2 - 0.1, GOLD)]:
            a = ease((t - st) / 0.45) * fo
            if a > 0:
                d.text((540, y + 30 * (1 - a)), txt, font=f_q, fill=col + (int(255 * a),), anchor="mm",
                       stroke_width=2, stroke_fill=NAVY + (int(255 * a),))
        a = ease((t - (Q_NS + Q_CTA - 0.1)) / 0.4) * fo
        if a > 0:
            sc = pop((t - (Q_NS + Q_CTA - 0.1)) / 0.45)
            bw, bh = 720 * sc, 116 * sc                   # x 約 180–900，避開右側按鈕
            d.rounded_rectangle([540 - bw / 2, 975 - bh / 2, 540 + bw / 2, 975 + bh / 2], 58 * sc, fill=GOLD + (int(255 * a),))
            d.text((540, 975), "歡迎來報名課程，實際體驗", font=f_cta, fill=NAVY + (int(255 * a),), anchor="mm")
        return im.convert("RGB")

    # deltoid（三角肌）使用者 2026/11/25 說刪掉，不再輸出（程式留著）
    jobs = [("compare.mp4", compare_frame, COMPARE_DUR), ("observe.mp4", observe, OBSERVE_DUR), ("question.mp4", question, QUESTION_DUR)]
    if args.preview:
        for name, fn, dur in jobs:
            for s in [float(x) for x in args.preview.split(",")]:
                if s <= dur:
                    fn(s).save(os.path.join(args.out, f"preview_{name[:-4]}_{s:05.2f}.png"))
        print("預覽：", args.out)
        return
    # 旁白：配音檔加快 1.12 倍、放在動畫的 OBS_NS／Q_NS 秒，前後補靜音到動畫長度
    vo = {}
    for name, line, start, dur in [("observe.mp4", "line01.wav", OBS_NS, OBSERVE_DUR), ("question.mp4", "line02.wav", Q_NS, QUESTION_DUR)]:
        src = os.path.join(args.vo, line)
        if os.path.exists(src):
            out = os.path.join(args.out, name.replace(".mp4", "_vo.wav"))
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-af", f"aresample=48000,atempo={VO_TEMPO}",
                                  "-ac", "2", "-f", "f32le", "-"], capture_output=True, check=True).stdout
            y = np.frombuffer(raw, np.float32).reshape(-1, 2)
            track = np.zeros((int((dur + 0.2) * 48000), 2), np.float32)
            i0 = int(start * 48000)
            track[i0:i0 + len(y)] = y[:len(track) - i0]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", "-", out],
                           input=track.tobytes(), check=True)
            vo[name] = out
    cmp_audio = os.path.join(args.out, "cmp_audio.mp4")
    if os.path.exists(cmp_audio):
        vo["compare.mp4"] = cmp_audio
    for name, fn, dur in jobs:
        write(os.path.join(args.out, name), fn, dur, audio=(vo[name], 0, dur) if name in vo else None)


# demo.mp4：聲音是 IMG_8497 5.10–19.58 一整段；畫面四段（素材, 入點, 長度）
DEMO_A = (5.10, 19.58)
DEMO_V = [("IMG_8497.MOV", 5.10, 2.65),     # 「人產生兩種反應」講師
          ("IMG_8496.MOV", 121.75, 2.65),   # 「一種東西放到嘴巴裡你的肌肉會撐住」：講師整個人壓上去，手臂還是撐住（124.1 最用力≈講到「撐住」）
          ("IMG_8496.MOV", 85.85, 2.60),    # 「一種是會掉下去」：87.3 手臂掉下去≈講到「掉」
          ("IMG_8497.MOV", 13.00, 6.58)]    # 「那什麼意思呢？就跟胸腺有關。胸腺是管免疫力荷爾蒙分泌的」講師
DEMO_DUR = DEMO_A[1] - DEMO_A[0]
DEMO_THYMUS_IN = 15.00 - DEMO_A[0]          # 「就跟胸腺有關」的「胸」（15.04）


def demo(px, out):
    ins, chains = [], []
    for i, (f, a, d) in enumerate(DEMO_V):
        ins += ["-ss", f"{a}", "-t", f"{d + 0.2}", "-i", os.path.join(px, f)]
        chains.append(f"[{i}:v]fps={FPS},trim=duration={d:.4f},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]")
    n = len(DEMO_V)
    ins += ["-ss", f"{DEMO_A[0]}", "-t", f"{DEMO_DUR + 0.2}", "-i", os.path.join(px, "IMG_8497.MOV")]
    g = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];" \
        f"[{n}:a]atrim=duration={DEMO_DUR:.4f},asetpts=PTS-STARTPTS[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", g, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-c:a", "aac", "-b:a", "192k", out], check=True)
    print(out, f"{DEMO_DUR:.2f}s")


CARD = (290, 1330, 790, 1620)   # 胸腺小卡：字幕（底邊 y 1260）下面、右側按鈕（x 920）左邊
GRAYED = (150, 150, 158)


def thymus_frames(F):
    """胸腺小卡（RGBA）：appear＝出現的時間（None＝一開始就在）；shrink＝(開始, 結束) 金色亮點縮小變灰；leave＝開始收掉的時間"""
    from PIL import ImageFilter
    x0, y0, x1, y1 = CARD
    cx, hy, ty = 420, 1408, 1508          # 剪影中線、頭、胸腺的位置
    f_lab = F(76, 900)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle(CARD, 30, fill=255)
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.ellipse([cx - 42, hy - 48, cx + 42, hy + 44], fill=(232, 234, 240, 235))           # 頭
    d.rounded_rectangle([cx - 20, hy + 30, cx + 20, hy + 70], 8, fill=(232, 234, 240, 235))  # 脖子
    d.rounded_rectangle([cx - 128, hy + 62, cx + 128, y1 + 120], 78, fill=(232, 234, 240, 235))  # 肩膀＋上半身
    body.putalpha(Image.fromarray(np.minimum(np.array(body.split()[3]), np.array(mask))))

    def fr(t, appear=None, shrink=None, leave=None):
        a = 1.0 if appear is None else ease((t - appear) / 0.35)
        if leave is not None:
            a *= 1 - ease((t - leave) / 0.3)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if a <= 0:
            return lay
        dy = int((1 - a) * 24)
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dc = ImageDraw.Draw(card)
        dc.rounded_rectangle(CARD, 30, fill=NAVY + (205,), outline=GOLD + (230,), width=4)
        card.alpha_composite(body)
        k = 0.0 if shrink is None else ease((t - shrink[0]) / (shrink[1] - shrink[0]))
        col = tuple(int(g + (q - g) * k) for g, q in zip(GOLD, GRAYED))
        r = 1.0 - 0.5 * k
        pulse = 1.0 + 0.08 * np.sin(t * 2 * np.pi / 1.6) * (1 - k)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([cx - 40 * r * pulse, ty - 46 * r * pulse, cx + 40 * r * pulse, ty + 46 * r * pulse],
                                     fill=GOLD + (int(170 * (1 - k)),))
        card.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
        dc = ImageDraw.Draw(card)
        dc.ellipse([cx - 19 * r, ty - 24 * r, cx + 19 * r, ty + 24 * r], fill=col + (255,))
        dc.line([(cx + 26, ty), (548, ty)], fill=GOLD + (220,), width=4)
        dc.text((566, ty), "胸腺", font=f_lab, fill=GOLD + (255,), anchor="lm", stroke_width=2, stroke_fill=NAVY + (255,))
        al = np.array(card.split()[3]).astype(np.float32) * a
        card.putalpha(Image.fromarray(al.astype(np.uint8)))
        lay.alpha_composite(card, (0, dy))
        return lay
    return fr


def write_overlay(out, frame, dur):
    """透明疊加層（qtrle，含 alpha），build_segment 的 overlay 用"""
    n = int(round(dur * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb", out], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print(out, f"{n / FPS:.2f}s")


def write(out, frame, dur, audio=None):
    """畫面逐格送進 ffmpeg；audio＝(素材, 入點, 出點) 時用那段原音，沒有就無聲"""
    n = int(round(dur * FPS))
    a_in = (["-ss", f"{audio[1]}", "-t", f"{n / FPS}", "-i", audio[0]] if audio
            else ["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={n / FPS}"])
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", *a_in, "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                          "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                          "-c:a", "aac", "-b:a", "192k", out], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print(out, f"{n / FPS:.2f}s")


if __name__ == "__main__":
    main()
