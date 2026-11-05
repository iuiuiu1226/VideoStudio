#!/usr/bin/env python3
"""在成片上逐格打馬賽克（例如人物身上的名牌），其他畫面、字幕、聲音都不動。

追蹤檔（JSON）：{"boxes": [[x, y, w, h] 或 null, …]}，一格一筆（成片的格數），null 表示那一格不打；
座標是成片 1080x1920 的像素。可加 "block"（格子大小，預設依框的高度自動算，約框高的 1/5、最小 8 px）。
聲音直接複製；畫面用高畫質重新編碼（crf 16），顏色標記照原片（bt709）。

字幕、特效字剛好壓在名牌上時，加 --ass（build_segment.py --ass-only 輸出的同一份字幕檔）：
把字幕分別畫在黑底、白底上算出字幕層的透明度，打碼只糊字幕底下的畫面，字幕原樣疊回去、不會跟著糊掉。

用法：
  python3 tools/build_segment.py cuts/life02/seg1_joke.json … --src <素材> --font <字型> --ass-only /tmp/subs.ass
  python3 tools/mosaic.py output/BK生活應用_VOL02_v5_配樂.mp4 cuts/life02/badge_mosaic.json --ass /tmp/subs.ass --font <字型> -o output/03_….mp4
"""
import argparse
import json
import subprocess

import cv2
import numpy as np


def pixelate(img, x, y, w, h, block=None, sub_b=None, sub_w=None):
    """sub_b、sub_w：字幕畫在黑底、白底的同一格（沒有字幕時不給）"""
    H, W = img.shape[:2]
    x0, y0 = max(0, int(round(x))), max(0, int(round(y)))
    x1, y1 = min(W, int(round(x + w))), min(H, int(round(y + h)))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    b = block or max(8, int(round((y1 - y0) / 5)))
    size = (max(1, round((x1 - x0) / b)), max(1, round((y1 - y0) / b)))
    reg = img[y0:y1, x0:x1].astype(np.float32)
    if sub_b is None:
        a = np.zeros(reg.shape[:2] + (1,), np.float32)
        sb = np.zeros_like(reg)
    else:
        sb = sub_b[y0:y1, x0:x1].astype(np.float32)
        a = np.clip(1 - (sub_w[y0:y1, x0:x1].astype(np.float32) - sb).mean(2, keepdims=True) / 255, 0, 1)
    # 字幕底下的原畫面：成片 =底圖×(1-a)+字幕(黑底)，反推底圖；字幕幾乎不透明的地方不拿來算平均
    base = np.clip((reg - sb) / np.maximum(1 - a, 0.05), 0, 255)
    wt = np.where(a < 0.6, 1 - a, 0).astype(np.float32)
    num = cv2.resize(base * wt, size, interpolation=cv2.INTER_AREA)
    den = cv2.resize(wt[..., 0], size, interpolation=cv2.INTER_AREA)[..., None]
    plain = cv2.resize(reg, size, interpolation=cv2.INTER_AREA)
    small = np.where(den > 0.05, num / np.maximum(den, 1e-6), plain)
    m = cv2.resize(small, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST)
    img[y0:y1, x0:x1] = np.clip(m * (1 - a) + sb, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("track")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--crf", default="16")
    ap.add_argument("--ass", help="成片燒進去的同一份字幕檔（build_segment.py --ass-only），字幕壓到打碼範圍時保護字幕")
    ap.add_argument("--font", help="字型資料夾（跟 build_segment 的 --font 相同），配 --ass 用")
    args = ap.parse_args()
    tr = json.load(open(args.track, encoding="utf-8"))
    boxes = tr["boxes"]
    W, H = 1080, 1920
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", args.video], capture_output=True, text=True, check=True).stdout.strip()
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", args.video, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", fps, "-i", "-", "-i", args.video, "-map", "0:v", "-map", "1:a?", "-c:a", "copy",
                            "-c:v", "libx264", "-preset", "slow", "-crf", args.crf, "-pix_fmt", "yuv420p",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-color_range", "tv", "-movflags", "+faststart", args.out], stdin=subprocess.PIPE)
    subs = []
    if args.ass:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    args.video], capture_output=True, text=True, check=True).stdout) + 1
        for bg in ("black", "white"):
            sv = f"format=rgb24,subtitles={args.ass}" + (f":fontsdir={args.font}" if args.font else "")
            subs.append(subprocess.Popen(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                                          f"color=c={bg}:s={W}x{H}:r={fps}:d={dur:.2f}", "-vf", sv,
                                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE))
    n = 0
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        f = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
        sb = sw = None
        if subs:
            sb = np.frombuffer(subs[0].stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
            sw = np.frombuffer(subs[1].stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if n < len(boxes) and boxes[n]:
            for bx in (boxes[n] if isinstance(boxes[n][0], list) else [boxes[n]]):
                pixelate(f, *bx[:4], block=tr.get("block"), sub_b=sb, sub_w=sw)
        enc.stdin.write(f.tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    for p in subs:
        p.kill()
    print("格數", n, "；有打碼的格數", sum(1 for k in range(min(n, len(boxes))) if boxes[k]))


if __name__ == "__main__":
    main()
