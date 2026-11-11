#!/usr/bin/env python3
"""編號 10「BK 是什麼？」的自製動畫段落（跟課堂精華 VOL.01 水結晶同一套深藍底＋金色）。

timeline.mp4：「從哪裡來」的時間軸，配合旁白（目前還沒配音，旁白先用字幕代替，秒數照預估的配音長度）
  1960 年代｜應用肌動學（壓手臂，看肌肉的力氣）→ 線往下長 → 1970 年代｜預防醫學的醫生（加進情緒、心理的因素）
  書（《BK》1979）不放在動畫裡：講師下一段自己會講，畫面是講師投影片上的書封（真的照片）
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
    args = ap.parse_args()
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
    write(os.path.join(args.out, "timeline.mp4"), frame, args.dur)
    if args.book_src:
        write(os.path.join(args.out, "book.mp4"), book_frame, args.a_out - args.a_in,
              audio=(args.book_src, args.a_in, args.a_out))


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
