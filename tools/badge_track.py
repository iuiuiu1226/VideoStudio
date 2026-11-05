#!/usr/bin/env python3
"""在成片裡逐格找人物身上的名牌，算出打馬賽克的框（給 tools/mosaic.py 用）。

做法：
1. 每格先用 YuNet 找臉，只在臉下方的範圍找名牌（名牌寬約臉寬的 0.7 倍）。
2. 用 SIFT 特徵點比對名牌樣本，RANSAC 求出位置、大小、角度；名牌被手或麥克風擋住一半也找得到。
   （試過整張樣板比對，會把眼睛、麥克風當成名牌，不能用。）
3. 不合理的偵測剔除（點太少、大小跟臉不成比例、跟前後格差太多）；臉偶爾認錯（手、背景）也剔除。
4. 找不到的格（擋住、模糊、轉身）用「相對於臉的位置」從前後偵測內插，離偵測越遠框放越大。
5. 一個鏡頭一段（shots），剪接點不內插；名牌太小看不清楚的鏡頭（遠景、掃全場）不用列進去。
6. 自動結果要用 --sheet 輸出的檢查圖逐格確認，跑掉的格用 --fixes 手動指定位置。
   打碼後可以拿成品再跑一次本程式，偵測不到名牌（合理大小）才算通過。

樣本（--exemplar，可給多個）：影片:格數:x0:y0:x1:y1，框住名牌（稍微留邊），框的中心當名牌中心。

用法（編號 3 的例子）：
  python3 tools/badge_track.py output/BK生活應用_VOL02_v5_配樂.mp4 --model <yunet.onnx> \\
      --exemplar output/BK生活應用_VOL01_v6_配樂.mp4:90:505:870:620:945 \\
      --exemplar output/BK生活應用_VOL02_v5_配樂.mp4:870:590:1055:765:1160 \\
      --up 1.4 --shots '[[0,764],[764,1152],[1152,1272]]' --fixes cuts/life02/badge_fixes.json \\
      --det /tmp/det.json -o cuts/life02/badge_mosaic.json
  （--det 存在就直接讀，不重新偵測；名牌小的影片 --up 2 放大再比對）
"""
import argparse
import json
import os
import subprocess

import cv2
import numpy as np

W, H = 1080, 1920


def grab(vid, f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(f / 30), "-i", vid, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W)


def detect(video, n_frames, exemplars, up, model):
    sift = cv2.SIFT_create(contrastThreshold=0.02)
    ex = []
    for e in exemplars:
        vid, f, x0, y0, x1, y1 = e.rsplit(":", 5)
        g = grab(vid, int(f))[int(y0):int(y1), int(x0):int(x1)]
        k = 230.0 / g.shape[1]   # 樣本都放大到寬 230 px
        g2 = cv2.resize(g, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
        kp, d = sift.detectAndCompute(g2, None)
        ex.append((kp, d, g2.shape[1], g2.shape[0], k, int(x1) - int(x0), int(y1) - int(y0)))
    fd = cv2.FaceDetectorYN.create(model, "", (W // 2, H // 2), 0.6, 0.3, 50)
    bf = cv2.BFMatcher()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-frames:v", str(n_frames), "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    faces, dets, last = [], [], None
    for _ in range(n_frames):
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        im = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        _, fs = fd.detect(cv2.resize(im, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
        face = None
        if fs is not None and len(fs):
            k = int(np.argmax(fs[:, 2] * fs[:, 3]))
            face = [float(x) * 2 for x in fs[k, :4]]
        faces.append(face)
        use = face or last
        if face:
            last = face
        if use:
            fx, fy, fw, fh = use
            x0, x1 = int(max(0, fx + fw / 2 - 1.1 * fw)), int(min(W, fx + fw / 2 + 1.9 * fw))
            y0, y1 = int(max(0, fy + fh * 0.9)), int(min(H, fy + fh * 3.3))
        else:
            x0, x1, y0, y1 = 0, W, 600, 1500
        g = cv2.resize(cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY), None, fx=up, fy=up,
                       interpolation=cv2.INTER_CUBIC)
        kp, d = sift.detectAndCompute(g, None)
        best = None
        if d is not None and len(kp) >= 4:
            for kp0, d0, ew, eh, ek, ow, oh in ex:
                ms = bf.knnMatch(d0, d, k=2)
                good = [m[0] for m in ms if len(m) == 2 and m[0].distance < 0.8 * m[1].distance]
                if len(good) < 4:
                    continue
                src = np.float32([kp0[m.queryIdx].pt for m in good])
                dst = np.float32([kp[m.trainIdx].pt for m in good])
                M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=6 * up)
                if M is None:
                    continue
                n = int(inl.sum())
                sc = np.hypot(M[0, 0], M[1, 0]) / up * ek
                ang = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
                c = M @ np.array([ew / 2, eh / 2, 1.0])
                cand = [n, x0 + c[0] / up, y0 + c[1] / up, ow * sc, oh * sc, ang, len(good)]
                if best is None or n > best[0]:
                    best = [float(v) for v in cand]
        dets.append(best)
    p.kill()
    return {"faces": faces, "dets": dets}


def smooth(x, k):
    x = np.asarray(x, float)
    if k <= 1 or len(x) < 3:
        return x
    return np.convolve(np.pad(x, (k // 2, k // 2), mode="edge"), np.ones(k) / k, mode="valid")


def boxes_from(d, shots, fixes):
    faces = [f[:] if f else None for f in d["faces"]]
    dets = d["dets"]
    n = len(dets)
    boxes = [None] * n
    gapframes = []
    report = []
    for f0, f1 in shots:
        f1 = min(f1, n)
        L = f1 - f0
        # 臉偶爾會認錯：跟前後 ±7 格的中位數比，位置或大小差太多的丟掉，再內插
        idx = [k for k in range(f0, f1) if faces[k]]
        bad = []
        for k in idx:
            nb = [j for j in idx if abs(j - k) <= 7]
            C = np.array([[faces[j][0] + faces[j][2] / 2, faces[j][1] + faces[j][3] / 2, faces[j][2]] for j in nb])
            mx, my, mw = np.median(C, 0)
            cx, cy, w = faces[k][0] + faces[k][2] / 2, faces[k][1] + faces[k][3] / 2, faces[k][2]
            if np.hypot(cx - mx, cy - my) > 0.45 * mw or abs(w / mw - 1) > 0.3:
                bad.append(k)
        for k in bad:
            faces[k] = None
        idx = [k for k in range(f0, f1) if faces[k]]
        FC = None
        if idx:
            F = np.array([faces[k] for k in idx])
            FC = np.array([[np.interp(k, idx, F[:, c]) for c in range(4)] for k in range(f0, f1)])
        acc = {}
        for k in range(L):
            i = f0 + k
            fx = fixes.get(str(i))
            if fx == "drop":
                continue
            if isinstance(fx, list):
                acc[k] = [fx[0], fx[1], fx[2] if len(fx) > 3 else None, fx[3] if len(fx) > 3 else None, 0.0, True]
                continue
            dt = dets[i]
            if not dt:
                continue
            ni, cx, cy, w, h, ang, ng = dt
            if ni < 5 and not (ni >= 4 and ni / ng >= 0.6):
                continue
            if FC is not None and not (0.45 * FC[k, 2] <= w <= 1.25 * FC[k, 2]):
                continue
            if abs(ang) > 35:
                continue
            acc[k] = [cx, cy, w, h, ang, False]
        ks = sorted(acc)
        for _ in range(2):
            rm = []
            for k in ks:
                if acc[k][5]:
                    continue
                nb = [j for j in ks if abs(j - k) <= 6]
                mx, my = np.median([acc[j][0] for j in nb]), np.median([acc[j][1] for j in nb])
                mw = np.median([acc[j][2] for j in nb if acc[j][2]] or [acc[k][2]])
                if np.hypot(acc[k][0] - mx, acc[k][1] - my) > 0.35 * mw:
                    rm.append(k)
            for k in rm:
                acc.pop(k)
            ks = sorted(acc)
        if not ks:
            report.append((f0, f1, 0, L, len(bad)))
            continue
        for k in ks:
            if acc[k][2] is None:
                near = min([j for j in ks if acc[j][2] is not None] or [k], key=lambda j: abs(j - k))
                acc[k][2], acc[k][3] = acc[near][2] or 100, acc[near][3] or 65
        ka = np.array(ks)
        if FC is not None:
            rel = np.array([[(acc[k][0] - (FC[k, 0] + FC[k, 2] / 2)) / FC[k, 2], (acc[k][1] - (FC[k, 1] + FC[k, 3])) / FC[k, 3],
                             acc[k][2] / FC[k, 2], acc[k][3] / FC[k, 2], acc[k][4]] for k in ks])
        X, Y, BW, BH, A, GAP = [], [], [], [], [], []
        for k in range(L):
            if k in acc:
                c = acc[k]
                X.append(c[0]); Y.append(c[1]); BW.append(c[2]); BH.append(c[3]); A.append(c[4]); GAP.append(0)
                continue
            GAP.append(min(int(abs(ka - k).min()), 30))
            if FC is not None:
                r = [np.interp(k, ka, rel[:, c]) for c in range(5)]
                fx_, fy_, fw_, fh_ = FC[k]
                X.append(fx_ + fw_ / 2 + r[0] * fw_); Y.append(fy_ + fh_ + r[1] * fh_)
                BW.append(r[2] * fw_); BH.append(r[3] * fw_); A.append(r[4])
            else:
                X.append(np.interp(k, ka, [acc[j][0] for j in ks])); Y.append(np.interp(k, ka, [acc[j][1] for j in ks]))
                BW.append(np.interp(k, ka, [acc[j][2] for j in ks])); BH.append(np.interp(k, ka, [acc[j][3] for j in ks]))
                A.append(0.0)
        X, Y = smooth(X, 3), smooth(Y, 3)
        BW, BH, A = smooth(BW, 9), smooth(BH, 9), smooth(A, 9)
        for k in range(L):
            ar = np.radians(A[k])
            bw = BW[k] * abs(np.cos(ar)) + BH[k] * abs(np.sin(ar))
            bh = BW[k] * abs(np.sin(ar)) + BH[k] * abs(np.cos(ar))
            grow = 1.0 + 0.012 * GAP[k]          # 離偵測越遠，框放越大（最多 +36%）
            bw, bh = bw * 1.08 * grow + 8, bh * 1.12 * grow + 8
            boxes[f0 + k] = [round(float(X[k] - bw / 2), 1), round(float(Y[k] - bh / 2), 1), round(float(bw), 1), round(float(bh), 1)]
        gapframes += [f0 + k for k in range(L) if GAP[k] > 0]
        report.append((f0, f1, len(ks), L, len(bad)))
    return boxes, gapframes, report


def sheet(video, boxes, frames, out, crop=300, tile=150):
    """檢查圖：以打碼框為中心裁 crop、畫框，10 欄、每頁 100 張"""
    want, tiles = set(frames), []
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-frames:v", str(max(frames) + 1), "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    for i in range(max(frames) + 1):
        b = p.stdout.read(W * H * 3)
        if i not in want or not boxes[i]:
            continue
        f = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
        x, y, w, h = boxes[i]
        cv2.rectangle(f, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 255), 2)
        x0 = int(min(max(x + w / 2 - crop / 2, 0), W - crop))
        y0 = int(min(max(y + h / 2 - crop / 2, 0), H - crop))
        t = cv2.resize(f[y0:y0 + crop, x0:x0 + crop], (tile, tile), interpolation=cv2.INTER_AREA)
        cv2.putText(t, str(i), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        tiles.append(t)
    root, ext = os.path.splitext(out)
    for pg in range(0, len(tiles), 100):
        ts = tiles[pg:pg + 100]
        while len(ts) % 10:
            ts.append(np.zeros((tile, tile, 3), np.uint8))
        cv2.imwrite(f"{root}_{pg // 100}{ext or '.jpg'}", np.vstack([np.hstack(ts[r:r + 10]) for r in range(0, len(ts), 10)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--model", required=True, help="YuNet 臉部偵測模型（face_detection_yunet_2023mar.onnx）")
    ap.add_argument("--exemplar", action="append", required=True)
    ap.add_argument("--up", type=float, default=1.0, help="比對前放大倍數（名牌小時用 2）")
    ap.add_argument("--shots", required=True, help="要打碼的鏡頭 [[開始格, 結束格), …]")
    ap.add_argument("--fixes", help="手動補正 {格數: [cx, cy, w, h] 或 \"drop\"}")
    ap.add_argument("--det", help="偵測結果暫存檔（存在就直接讀）")
    ap.add_argument("--sheet", help="輸出檢查圖（每 3 格一張）")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    shots = json.loads(args.shots)
    if args.det and os.path.exists(args.det):
        d = json.load(open(args.det))
    else:
        d = detect(args.video, max(b for _, b in shots), args.exemplar, args.up, args.model)
        if args.det:
            json.dump(d, open(args.det, "w"))
    fixes = json.load(open(args.fixes)) if args.fixes else {}
    boxes, gaps, report = boxes_from(d, shots, fixes)
    json.dump({"boxes": boxes}, open(args.out, "w"))
    for f0, f1, nd, L, nb in report:
        print(f"鏡頭 {f0}–{f1}：偵測到 {nd}/{L} 格，丟掉認錯的臉 {nb} 格")
    print("內插補出來的格數", len(gaps))
    if args.sheet:
        fr = [i for i in range(len(boxes)) if boxes[i]][::3]
        sheet(args.video, boxes, fr, args.sheet)


if __name__ == "__main__":
    main()
