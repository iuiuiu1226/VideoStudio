#!/usr/bin/env python3
"""BK 學員分享系列封面（固定版型，直式 1080x1920）。

版型：學員畫面當背景（下方漸層轉深色）→ 上方「Logo＋系列標籤」一列 → 中下方標題 → 副標。
     標題與副標都在畫面正中的 1:1 範圍內（y 420–1500），IG／FB 格狀牆不論裁成 3:4
     或正方形都不會被切到；Logo 與系列標籤那列在 3:4 內完整，正方形時整列裁掉、不會只剩一半。
每一集只要換設定檔裡的畫面、標題（lines）與副標。

用法：
  python3 tools/cover.py cuts/cover_vol01.json --src <素材資料夾> --font <字型檔> -o output/cover_vol01.jpg
"""
import argparse
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from build_segment import is_hdr, tonemap_chain

W, H = 1080, 1920
GOLD = (217, 180, 90)
NAVY = (13, 16, 24)
MAX_TEXT_W = 960


def grab(src, t, frame):
    vf = f"crop={frame['w']}:{frame['h']}:{frame['x']}:{frame['y']},scale={W}:{H}:flags=lanczos"
    trc = is_hdr(src)
    if trc:
        vf += "," + tonemap_chain(trc).rstrip(",")  # HDR 素材先轉成一般畫面，顏色才不會偏亮偏淡
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1",
                          "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return Image.frombuffer("RGB", (W, H), raw)


def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    f.set_variation_by_axes([weight])
    return f


def text_shadow(img, xy, txt, f, fill, anchor="mm", spacing=0, blur=10, alpha=170):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0], xy[1] + 4), txt, font=f, fill=(0, 0, 0, alpha), anchor=anchor,
                            spacing=spacing, align="center")
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text(xy, txt, font=f, fill=fill, anchor=anchor, spacing=spacing, align="center")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--src", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    cfg = json.load(open(args.config, encoding="utf-8"))

    img = grab(f"{args.src}/{cfg['src']}", cfg["t"], cfg["frame"]).convert("RGBA")
    # 漸層：上方略暗，中段以下逐漸轉成深藍黑，讓文字清楚
    y = np.linspace(0, 1, H)[:, None]
    a = np.clip(0.25 + np.maximum(0, (y - 0.42) / 0.38) * 0.75, 0, 0.94)
    a[: int(H * 0.2)] = np.maximum(a[: int(H * 0.2)], 0.35 * (1 - y[: int(H * 0.2)] / 0.2))
    ov = np.zeros((H, W, 4), np.uint8)
    ov[..., :3] = NAVY
    ov[..., 3] = (np.repeat(a, W, axis=1) * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(ov, "RGBA"))
    d = ImageDraw.Draw(img)

    # 系列標籤列：小 Logo＋「BK 測試｜學員分享」，整組置中（在 3:4 範圍內，正方形時整列裁掉）
    f_tag = font(args.font, 44, 700)
    tag = cfg.get("series", "BK 測試｜學員分享")
    ty = cfg.get("tag_y", 345)
    logo = Image.open(cfg["logo"]).convert("RGBA")
    lh2 = cfg.get("logo_h", 72)
    logo = logo.resize((int(logo.width * lh2 / logo.height), lh2), Image.LANCZOS)
    tw = d.textlength(tag, font=f_tag)
    gap = 18
    x0 = int(W / 2 - (logo.width + gap + tw) / 2)
    img.alpha_composite(logo, (x0, ty - lh2 // 2))
    text_shadow(img, (x0 + logo.width + gap, ty), tag, f_tag, GOLD, anchor="lm", blur=6)

    # 標題：多行、每行可設大小與顏色（white / gold），太寬會自動縮小到 MAX_TEXT_W 內
    y = cfg.get("quote_top", 1000)
    for ln in cfg["lines"]:
        size = ln.get("size", 110)
        f = font(args.font, size, ln.get("weight", 900))
        while d.textlength(ln["text"], font=f) > MAX_TEXT_W and size > 40:
            size -= 2
            f = font(args.font, size, ln.get("weight", 900))
        color = GOLD if ln.get("color") == "gold" else (255, 255, 255)
        y += int(size * 0.5)
        text_shadow(img, (W // 2, y), ln["text"], f, color, blur=14, alpha=200)
        y += int(size * 0.5) + ln.get("gap", 26)
    # 副標
    if cfg.get("sub"):
        y += 24
        text_shadow(img, (W // 2, y + 25), cfg["sub"], font(args.font, 48, 500), (225, 228, 235), blur=8)

    # 品牌文字預設不放（片尾與版權小字已有），需要時設 "brand"
    if cfg.get("brand"):
        text_shadow(img, (W // 2, cfg.get("brand_y", 1440)), cfg["brand"], font(args.font, 40, 600), GOLD,
                    blur=6)

    img.convert("RGB").save(args.out, quality=93)
    print(args.out)


if __name__ == "__main__":
    main()
