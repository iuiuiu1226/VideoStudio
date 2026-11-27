#!/usr/bin/env python3
"""名牌被手擋、badge_track 追不到時：用臉的位置推算名牌位置，產生 mosaic.py 用的框。

名牌中心＝臉中心＋(DX, DY)×臉寬，框大小 BW×BH 臉寬（放大一點保險）；臉的位置先中值濾波＋平滑，找不到臉的格內插。
用法：python3 tools/badge_face.py 成片.mp4 既有框.json 輸出.json '[[開始格,結束格),…]' DX,DY,BW,BH
例（編號 11 台南學員）：0.71,1.88,0.48,0.78
"""
import sys, json, subprocess, numpy as np, cv2
from scipy.ndimage import median_filter, uniform_filter1d
vid, base, out = sys.argv[1], sys.argv[2], sys.argv[3]
shots = json.loads(sys.argv[4]); DX, DY, BW, BH = map(float, sys.argv[5].split(","))
W, H = 1080, 1920
d = json.load(open(base)); boxes = d["boxes"]
fd = cv2.FaceDetectorYN.create("/home/user/VideoStudio/assets/models/face_detection_yunet_2023mar.onnx", "", (W // 2, H // 2), 0.6, 0.3, 50)
n = max(b for _, b in shots)
boxes += [None] * max(0, n - len(boxes))
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", vid, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
faces = []
for i in range(n):
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    im = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    _, fs = fd.detect(cv2.resize(im, (W // 2, H // 2)))
    faces.append([float(x) * 2 for x in fs[int(np.argmax(fs[:, 2] * fs[:, 3])), :4]] if fs is not None and len(fs) else None)
for a, b in shots:
    idx = [i for i in range(a, b) if faces[i]]
    arr = np.array([[faces[i][0] + faces[i][2] / 2, faces[i][1] + faces[i][3] / 2, faces[i][2]] for i in idx])
    arr = median_filter(arr, size=(9, 1), mode="nearest"); arr = uniform_filter1d(arr, 5, axis=0, mode="nearest")
    full = np.array([np.interp(range(a, b), idx, arr[:, j]) for j in range(3)]).T
    for k, i in enumerate(range(a, b)):
        cx, cy, fw = full[k]
        w, h = BW * fw, BH * fw
        boxes[i] = [round(cx + DX * fw - w / 2, 1), round(cy + DY * fw - h / 2, 1), round(w, 1), round(h, 1)]
    print("shot", a, b, "face found", len(idx), "/", b - a)
json.dump({"boxes": boxes}, open(out, "w"))
