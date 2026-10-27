#!/usr/bin/env python3
"""產生 LINE 官方樣式的 QR code（綠色圓點、圓角定位框、中央 LINE 字樣、白色圓角底）。

用法：
  python3 tools/line_qr.py --id @191cgbjs --font <字型檔> -o assets/line_qr.png
"""
import argparse
import urllib.parse

import qrcode
from PIL import Image, ImageDraw, ImageFont

GREEN = (6, 199, 85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="LINE 官方帳號 ID，例如 @191cgbjs")
    ap.add_argument("--font", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--box", type=int, default=24, help="每一格的像素")
    args = ap.parse_args()

    url = "https://line.me/R/ti/p/" + urllib.parse.quote(args.id)
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    n, b = len(m), args.box
    pad = b * 3
    size = n * b + pad * 2
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=b * 3, fill="white")

    def in_finder(r, c):
        return any(r0 <= r < r0 + 7 and c0 <= c < c0 + 7 for r0, c0 in [(0, 0), (0, n - 7), (n - 7, 0)])

    # 中央 LINE 字樣的留白區（H 等級容錯可承受）
    hole = int(n * 0.24) | 1
    h0 = (n - hole) // 2
    for r in range(n):
        for c in range(n):
            if not m[r][c] or in_finder(r, c) or (h0 <= r < h0 + hole and h0 <= c < h0 + hole):
                continue
            x, y = pad + c * b, pad + r * b
            g = b * 0.1
            d.rounded_rectangle([x + g, y + g, x + b - g, y + b - g], radius=b * 0.3, fill=GREEN)
    for r0, c0 in [(0, 0), (0, n - 7), (n - 7, 0)]:
        x, y = pad + c0 * b, pad + r0 * b
        d.rounded_rectangle([x, y, x + 7 * b, y + 7 * b], radius=b * 2, fill=GREEN)
        d.rounded_rectangle([x + b, y + b, x + 6 * b, y + 6 * b], radius=b * 1.4, fill="white")
        d.rounded_rectangle([x + 2 * b, y + 2 * b, x + 5 * b, y + 5 * b], radius=b * 0.9, fill=GREEN)
    font = ImageFont.truetype(args.font, int(b * hole * 0.36))
    font.set_variation_by_axes([800])
    cx = cy = size / 2
    d.text((cx, cy), "LINE", font=font, fill=GREEN, anchor="mm")
    img.save(args.out)
    print(args.out, img.size, url)


if __name__ == "__main__":
    main()
