#!/usr/bin/env python3
"""自動構圖：讓同一個人在不同片段裡的大小、位置一致。

手持拍攝時攝影者會前後移動、左右晃，同一個人在不同時間點的畫面大小不一。
這個工具在每個片段抽幾格畫面做臉部偵測，取臉的中位數大小與位置，
再依「同一支素材＝同一個人」分組，算出每段的裁切框，寫回剪輯清單的 "frame" 欄位：
  - 同一人每段的臉，在成片裡都是同樣高度、同樣位置（取該人各段的中位數位置，保留原構圖）
  - 以該人臉最大的片段為基準，其他片段放大補齊（只放大不縮小，畫面不會出現黑邊）

用法：
  python3 tools/autoframe.py cuts/seg*.json --src <素材資料夾> --model <yunet.onnx>
"""
import argparse
import json
import statistics
import subprocess
from collections import defaultdict

import cv2
import numpy as np

W, H = 1080, 1920
SAMPLES = 7
MAX_ZOOM = 1.15


def grab(src, t):
    # ffmpeg 會依旋轉資訊轉正，輸出與成片同尺寸的直式畫面
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src,
                          "-frames:v", "1", "-vf", f"scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def face_of(det, img):
    small = cv2.resize(img, (W // 2, H // 2))
    det.setInputSize((W // 2, H // 2))
    _, faces = det.detect(small)
    if faces is None or len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])[:4] * 2
    return x + w / 2, y + h / 2, h


def measure(det, src, t_in, t_out):
    pts = []
    for k in range(SAMPLES):
        t = t_in + (t_out - t_in) * (k + 0.5) / SAMPLES
        f = face_of(det, grab(src, t))
        if f:
            pts.append(f)
    if not pts:
        return None
    return tuple(float(statistics.median(p[i] for p in pts)) for i in range(3))


def plan(faces):
    """faces: [(cx, cy, h)] 同一人的各段。回傳每段 (x0, y0, cw, ch)。"""
    h_ref = max(f[2] for f in faces)
    # 成片中臉的目標位置：取各段的中位數，保留原本的構圖，只修正飄移
    tx = statistics.median(f[0] for f in faces)
    ty = statistics.median(f[1] for f in faces)
    for base in np.arange(1.0, MAX_ZOOM + 1e-6, 0.01):
        out, ok = [], True
        for cx, cy, h in faces:
            z = min(base * h_ref / h, MAX_ZOOM)
            cw, ch = W / z, H / z
            x0 = cx - tx / z
            y0 = cy - ty / z
            cx0 = min(max(x0, 0), W - cw)
            cy0 = min(max(y0, 0), H - ch)
            # 允許些微誤差（成片中約 12px）
            if abs(cx0 - x0) * z > 12 or abs(cy0 - y0) * z > 12:
                ok = False
            out.append((cx0, cy0, cw, ch))
        if ok:
            return out, base
    return out, base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlists", nargs="+")
    ap.add_argument("--src", required=True)
    ap.add_argument("--model", required=True)
    args = ap.parse_args()

    det = cv2.FaceDetectorYN.create(args.model, "", (W // 2, H // 2), 0.6)
    specs = {p: json.load(open(p, encoding="utf-8")) for p in args.cutlists}
    groups = defaultdict(list)
    for p, sp in specs.items():
        for c in sp["clips"]:
            if "card" in c:
                continue
            f = measure(det, f"{args.src}/{c['src']}", c["in"], c["out"])
            if f is None:
                print(f"  {c['id']}: 偵測不到臉，維持原畫面")
                c.pop("frame", None)
                continue
            groups[c["src"]].append((c, f))

    for src, items in groups.items():
        frames, base = plan([f for _, f in items])
        print(f"{src}: 基準放大 {base:.2f}")
        for (c, f), (x0, y0, cw, ch) in zip(items, frames):
            c["frame"] = {"x": round(x0, 1), "y": round(y0, 1),
                          "w": round(cw, 1), "h": round(ch, 1)}
            c.pop("zoom", None)
            print(f"  {c['id']}: 臉高 {f[2]:.0f}px 中心 ({f[0]:.0f},{f[1]:.0f}) → 放大 {W / cw:.2f}")

    for p, sp in specs.items():
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(sp, fh, ensure_ascii=False, indent=2)
            fh.write("\n")


if __name__ == "__main__":
    main()
