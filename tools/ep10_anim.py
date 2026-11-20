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
    args = ap.parse_args()
    if args.v2:
        NODES[1] = ("1970 年代", "預防醫學的醫生", "在生病之前預防", 880)
    if args.book_src:
        # 書封：IMG_8498 104.6 秒投影片左邊那本《BK》（真的照片，不用網路圖）
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{args.book_t}", "-i", args.book_src, "-frames:v", "1",
                              "-vf", "crop=362:684:2:292", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        cover = Image.frombuffer("RGB", (362, 684), raw).copy()
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
        """書封放中間（字幕上面），慢慢放大一點；右上角金色「1979」"""
        dur = args.a_out - args.a_in
        im = bg.copy().convert("RGBA")
        s = 1.0 + 0.04 * min(t / dur, 1.0)
        a = ease(t / 0.35)
        w = int(430 * s * (0.94 + 0.06 * a))
        h = int(w * cover.height / cover.width)
        cx, cy = W // 2, 780
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
            px, py = cx + w // 2 - 20, cy - h // 2 - 6
            d.rounded_rectangle([px - 90, py - 36, px + 90, py + 36], 36, fill=GOLD + (int(255 * pa),))
            d.text((px, py), "1979", font=f_pill, fill=NAVY + (int(255 * pa),), anchor="mm")
        return im.convert("RGB")

    if args.preview:
        for s in [float(x) for x in args.preview.split(",")]:
            frame(s).save(os.path.join(args.out, f"preview_{s:05.2f}.png"))
            if args.book_src:
                book_frame(s).save(os.path.join(args.out, f"preview_book_{s:05.2f}.png"))
        print("預覽：", args.out)
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
