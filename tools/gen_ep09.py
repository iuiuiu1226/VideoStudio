"""編號 9（Nina 資料夾 IMG_8502：安和老師「胸腺在哪裡？敲三下、哈三聲」）剪輯清單。

素材：BK 一日工作坊（2026/09/21，跟編號 6 同一場），1080x1920 SDR 60 格（iPhone 直拍、轉 90 度），工作檔 30 格。
安和老師是 BK 課程講師（名牌不用打碼）；學員名字不放：字幕裡念到學員名字的句子（「來，像○○那裡」「○○不錯」「謝謝○○的示範」）
剪掉，學員名牌打碼（學員敲給大家看那段，BADGE 人工標框 → cuts/ep09/badge_mosaic.json → tools/mosaic.py）。
腳本（使用者 2026/11/10 選這部）：
  鉤子「今天就學一個口訣，這個是蠻賺的，免費的」→ 胸腺在哪裡（胸骨下面、乳頭連線中間往下一指幅）→ 怎麼短時間提升？刺激胸腺
  → 學員示範敲：「像這樣子也是沒有用的」→ CPR 要很用力壓才刺激得到心臟，同理要敲才能穿透胸骨
  （第三版使用者改：第一個學員示範用按的整段刪掉、第二個學員示範敲移到這裡）
  → 關鍵是口訣：從丹田吐一個哈，敲一下哈一聲、敲兩下哈兩聲、敲三下哈三聲（畫面上放大的金色口訣，這三句不另外上字幕）
  → 老師示範（苦練多年；第三版刪「不然有點凹凸…」「拳面放平，然後放在胸腺上面」「我等一下倒數五六七八之後大家一起」）→ 全場一起「五六七八，哈哈哈」「很整齊耶」
「提升免疫力」是老師的說法，影片字幕照講的字，標題、封面不寫成保證有效。
這支現場聲音很吵（台下說話），聲音曲線看不出停頓，切點都用逐字轉錄（region 重轉、句首時間偏早）＋接起來轉錄確認。
畫面：老師在講台上走動、攝影機也會移動，用逐格裁切框（frame_keys）跟著老師的臉（tools 裡的臉部偵測，每 0.25 秒一筆、平滑），
臉高約 270 px、臉頂約 y 480；學員敲給大家看那段不跟臉、整個畫面。

用法：python3 tools/gen_ep09.py → cuts/ep09/seg_main.json、seg_end.json
      python3 tools/build_segment.py cuts/ep09/seg_main.json cuts/ep09/seg_end.json --src <工作檔資料夾> --font <字型資料夾> -o output/09_….mp4
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "cuts", "ep09")
FACES = os.environ.get("EP09_FACES", os.path.join(OUT, "faces.json"))   # (秒數, [[x, y, w, h, 信心], …])，1080x1920 座標
SRC = "IMG_8502.MOV"
STYLE = {"font": "Noto Sans TC", "size": 78, "outline": 4, "shadow": 1, "margin_v": 660,
         "title": "BK 測試｜生活應用", "note": "第七感人生智慧學"}
FACE_H, FACE_TOP, MAX_Z = 270, 480, 1.45
# 口訣：放大的金色字，一句一句跳出來（字幕下面）
KF = r"{\an5\pos(540,%d)\fs84\b1\c&H5AB4D9&\3c&H140F0B&\bord6\shad0\fad(180,250)\fscx60\fscy60\t(0,180,\fscx104\fscy104)\t(180,300,\fscx100\fscy100)}"

# (代號, 入點, 出點, 字幕[(開始, 結束, 文字)]（素材秒數）, 額外設定)
CLIPS = [
    ("H 鉤子", 106.85, 113.62, [(106.98, 110.95, "今天就學一個口訣\\N這個是蠻賺的"), (111.10, 113.70, "免費的")], {"pad": 0.35}),   # 出點在「的」尾音之後、「短時間」之前
    ("A1 胸腺", 0.95, 11.75, [(1.00, 3.45, "這裡是你的胸骨的下面"), (3.96, 6.85, "如果你要很精準的位置的話"),
                             (6.86, 9.15, "就來個乳頭相加除以二"), (9.20, 11.75, "然後往下面大概移一個指幅")], {}),
    ("A2", 14.57, 26.20, [(14.66, 16.25, "胸骨下面就是胸腺了"), (16.30, 19.65, "它是你分泌免疫力\\N荷爾蒙非常重要的單位"),
                          (19.78, 21.70, "那我們要怎麼樣能夠"), (21.76, 24.85, "短時間的提升你的\\N免疫力荷爾蒙分泌呢？"),
                          (24.76, 26.40, "就是刺激胸腺")], {"join": True, "pad": 0.35, "fade_in": 0.02}),
    # 「這個位置，下面，」不放；入點 14.57（14.30 會帶到「下面」的「面」尾音，接起來轉錄聽成「面胸」）
    # 第三版（使用者 2026/11/10）：第一個學員示範（用按的，37.45–54.6）整段刪掉，第二個學員示範（用敲的）移到這裡，接著 CPR
    ("D1 用敲的", 86.95, 93.85, [(87.06, 88.90, "請起立，敲給大家看一下"), (89.42, 91.40, "你往後轉一下\\N敲給大家看"),
                               (91.46, 94.00, "要噗噗噗噗噗的聲音")], {"pad": 0.2, "wide": True}),   # 前面「○○不錯」不放
    ("D2", 96.28, 97.95, [(96.34, 98.20, "像這樣子也是沒有用的")], {"pad": 0.35}),                # 前面「謝謝○○的示範」不放
    ("B2 CPR", 54.85, 83.80, [(55.06, 56.50, "你們學過那個 CPR 嗎？"), (57.10, 59.85, "CPR 要很用力壓"),
                             (59.88, 61.90, "我那時候的那個教官說"), (61.94, 64.00, "你壓到胸骨斷掉\\N都沒關係"),
                             (68.90, 70.95, "你才能夠刺激到\\N下面的心臟"), (70.96, 73.44, "同理可證\\N我們要刺激到胸腺"),
                             (73.46, 77.55, "也要很大力\\N才能穿透胸骨"), (77.60, 79.60, "所以用按的是沒有用的"),
                             (79.60, 84.00, "所以你要敲它\\N用力一點的敲它")], {"pad": 0.35}),
    # 入點 54.85：「因為你要按在胸骨上面」講完的空檔（54.62–55.04），「你們學過」55.05 開口
    ("E 關鍵", 103.60, 105.30, [(103.66, 105.50, "關鍵是要配合口訣")], {"pad": 0.3}),
    # 前面 100.0–101.3 是「都可以聽到」（不是「關鍵」，接起來會多出一句），不放
    ("F1 口訣", 120.55, 125.32, [(120.66, 122.10, "口訣很簡單"), (122.24, 125.50, "口訣就是從你的丹田\\N吐一個哈")], {"pad": 0.25}),
    ("F2 示範", 128.85, 170.84, [(134.84, 136.30, "三聲見效"), (136.58, 138.95, "所以也不用多\\N敲三下就夠了"),
                               (139.08, 141.10, "可是你要從丹田吐出來"), (141.34, 142.75, "那我示範一下"),
                               (143.08, 144.95, "我示範一次就換大家一起"), (145.48, 146.05, "就是這樣"),
                               (146.18, 148.55, "握個拳頭，拳面放平"), (155.26, 157.25, "敲三下哈三聲"),
                               (157.56, 158.85, "然後像這樣"), (158.86, 160.50, "哈！哈哈哈！"),
                               (162.78, 165.10, "好，有點回音的感覺"), (165.46, 167.40, "這個我苦練多年了"),
                               (167.84, 169.05, "大家也要練習一下"), (169.20, 170.80, "來來來，手放到胸腺上面")],
     # 第三版：「然後我等一下倒數五六七八之後大家一起」刪掉，出點 170.84（「上面」講完、後面安靜）
     {"pad": 0.3, "fx": [[128.96, 141.10, KF % 1330 + "敲一下　哈一聲"], [131.60, 141.10, KF % 1430 + "敲兩下　哈兩聲"],
                         [133.06, 141.10, KF % 1530 + "敲三下　哈三聲"]]}),   # 口訣三句用放大字，不另外上字幕
    ("H3 全場", 180.00, 189.45, [(180.20, 181.45, "好，來預備"), (182.00, 183.95, "五、六、七、八"),
                               (184.10, 185.40, "（全場）哈！哈！哈！"), (185.72, 189.70, "很整齊耶")], {"hold": 1.0}),
]
# 句子中間要拿掉的時間："w"＝字（切點轉寫確認過，前後交疊淡入淡出）、"p"＝停頓（前後各留 KEEP 秒，縮短成自然的小停頓）、
# "s"＝整句拿掉、前後是不同句子：前一段補 SENT_PAD 秒背景聲當句間停頓，後一段不交疊（交疊會多拿入點前 0.03 秒，帶到前一個字的尾音）
KEEP = 0.15
SENT_PAD = 0.15
REMOVE = {
    "H": [(111.70, 112.70, "p")],          # 「免……費的」中間的停頓縮短（留一點，聽得出老師故意拉長）
    "B2": [(64.00, 68.86, "w")],           # 「他不能告你，因為你要為了要救他嘛，所以你要壓得這麼用力，壓到胸骨斷掉」不放（太長）；68.86 在「掉」之後、「你」之前
    "F2": [(148.62, 155.23, "s"),          # 第三版：「不然有點凹凸，敲下去真的很痛／拳面放平，然後放在胸腺上面」刪掉；
                                           # 155.23 在「上面」的「面」之後（155.0、155.15 都還帶到「面」），「敲」開頭完整；
                                           # 用 "s"（交疊淡入會從 155.20 開始拿聲音，接起來又聽到「面」）
           (160.68, 162.74, "w")],         # 示範完後聽不清楚的幾個字（「三聲…出來」）不放；162.74 在「出來」之後
}

# 學員名牌打碼：D1 遠景裡學員轉身、正面敲胸腺那幾秒。自動追蹤（badge_track.py）在這段抓不穩（轉身、手擋、字幕壓到），
# 改成人工標框：(D1 入點後第幾格, x0, y0, x1, y1)（成片 1080x1920 座標，留約 12 px 邊），中間逐格內插。
# 剪輯改動後 D1 在成片的位置會變，這裡依片段長度（跟 build_segment 一樣以格取整）重新算，寫 cuts/ep09/badge_mosaic.json。
BADGE = [(113, 212, 1170, 255, 1235), (114, 212, 1170, 255, 1235), (116, 238, 1148, 282, 1228), (118, 262, 1138, 312, 1222),
         (120, 296, 1133, 362, 1212), (122, 328, 1138, 422, 1222), (124, 380, 1133, 530, 1215), (126, 380, 1133, 540, 1215),
         (128, 440, 1133, 590, 1215), (130, 478, 1133, 612, 1222), (132, 468, 1138, 615, 1222), (134, 513, 1138, 672, 1235),
         (138, 513, 1143, 677, 1247), (142, 518, 1153, 682, 1252), (146, 518, 1163, 682, 1277), (150, 513, 1168, 677, 1287),
         (154, 498, 1198, 662, 1297), (158, 483, 1203, 642, 1292), (162, 468, 1203, 622, 1297), (166, 458, 1203, 602, 1302),
         (170, 443, 1233, 592, 1317), (174, 433, 1243, 557, 1322), (178, 378, 1243, 492, 1317), (182, 383, 1233, 452, 1292),
         (186, 363, 1238, 417, 1297), (189, 355, 1238, 410, 1297)]


def badge_boxes(main, fps=30):
    t0 = 0
    for c in main:
        if c["id"].startswith("#D1"):
            break
        t0 += round((c["out"] - c["in"]) * fps) + round(c.get("pad", 0.0) * fps) + round(c.get("hold", 0.0) * fps)
    boxes = [None] * (t0 + BADGE[-1][0] + 1)
    for (f0, *b0), (f1, *b1) in zip(BADGE, BADGE[1:]):
        for f in range(f0, f1 + 1):
            u = (f - f0) / (f1 - f0)
            x0, y0, x1, y1 = [p + (q - p) * u for p, q in zip(b0, b1)]
            boxes[t0 + f] = [round(x0), round(y0), round(x1 - x0), round(y1 - y0)]
    return boxes, t0


def track():
    """每 0.25 秒老師臉的位置（cx, top, h）：挑信心高、夠大的臉，離上一筆最近；缺的內插，再平滑"""
    data = json.load(open(FACES))
    pts, prev = [], None
    for t, fs in data:
        fs = [f for f in fs if f[4] >= 0.85 and f[3] >= 140]
        if not fs:
            pts.append((t, None)); continue
        if prev is None:
            f = max(fs, key=lambda f: f[3])
        else:
            f = min(fs, key=lambda f: abs(f[0] + f[2] / 2 - prev[0]) + abs(f[1] - prev[1]))
        prev = (f[0] + f[2] / 2, f[1], f[3])
        pts.append((t, prev))
    known = [(t, p) for t, p in pts if p]
    full = []
    for t, p in pts:
        if p is None:
            a = max((k for k in known if k[0] <= t), default=known[0], key=lambda k: k[0])
            b = min((k for k in known if k[0] >= t), default=known[-1], key=lambda k: k[0])
            r = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
            p = tuple(a[1][i] + (b[1][i] - a[1][i]) * r for i in range(3))
        full.append((t, p))
    sm = []
    for i, (t, _) in enumerate(full):
        win = [full[j][1] for j in range(max(0, i - 3), min(len(full), i + 4))]
        sm.append((t, tuple(sum(w[k] for w in win) / len(win) for k in range(3))))
    return sm


TR = None


def at(t):
    i = min(range(len(TR)), key=lambda k: abs(TR[k][0] - t))
    return TR[i][1]


def zoom_for(a, b):
    """同一段（剪開的幾小段一起算）固定放大倍數：用中位數臉高，接點才不會忽大忽小"""
    hs = sorted(at(a + k * 0.25)[2] for k in range(int((b - a) / 0.25) + 1))
    return max(1.0, min(MAX_Z, FACE_H / hs[len(hs) // 2]))


def keys_for(a, b, z):
    """這段的逐格裁切框：位置跟著臉"""
    h = round(1920 / z / 2) * 2
    w = h * 9 / 16
    ks, t = [], a
    while t < b + 0.26:
        cx, top, _ = at(min(t, b))
        x = min(max(cx - w / 2, 0), 1080 - w)
        y = min(max(top - FACE_TOP / z, 0), 1920 - h)
        ks.append({"t": round(min(t, b), 2), "x": round(x, 1), "y": round(y, 1), "h": h})
        t += 0.5
    return ks


def clip(cid, a, b, subs, extra, z=1.0):
    tail = extra.get("pad", 0.0) + extra.get("hold", 0.0)
    s = [[round(max(t, a) - a, 2), round(min(e, b + tail) - a, 2), txt] for t, e, txt in subs if e > a and t < b + tail]
    c = {"id": f"#{cid}", "src": SRC, "in": a, "out": b, "subs": s}
    ex = {k: v for k, v in extra.items() if k not in ("wide",)}
    c.update(ex)
    if not extra.get("wide"):
        c["frame_keys"] = keys_for(a, b + tail, z)
    if c.get("pad") or c.get("hold"):
        c["room"] = "room_IMG_8502.wav"
    return c


def expand(cid, a, b, subs, extra):
    key = cid.split()[0]
    cuts = []
    for r0, r1, kind in sorted(REMOVE.get(key, [])):
        cuts.append((r0 + KEEP, r1 - KEEP, kind) if kind == "p" else (r0, r1, kind))
    pieces, x = [], a
    for r0, r1, kind in cuts:
        pieces.append((round(x, 2), round(r0, 2), kind)); x = r1
    pieces.append((round(x, 2), b, None))
    z = zoom_for(a, b)
    out, prev = [], None
    for k, (p0, p1, brk) in enumerate(pieces):
        last = k == len(pieces) - 1
        ex = extra if last else {kk: v for kk, v in extra.items() if kk not in ("pad", "hold")}
        if brk == "s":
            ex = dict(ex, pad=SENT_PAD)
        c = clip(cid if k == 0 else f"{key}-{k + 1}", p0, p1, subs, ex, z)
        if k > 0 and prev != "s":
            c["join"] = True
        out.append(c)
        prev = brk
    return out


if __name__ == "__main__":
    TR = track()
    os.makedirs(OUT, exist_ok=True)
    main = [p for c in CLIPS for p in expand(*c)]
    # A1→A2 是同一句話中間剪開（join），用同一個放大倍數
    za = zoom_for(0.95, 26.20)
    for c in main:
        if c["id"].split()[0] in ("#A1", "#A2"):
            c["frame_keys"] = keys_for(c["in"], c["out"] + c.get("pad", 0.0), za)
    json.dump({"name": "編號 9 胸腺在哪裡？敲三下、哈三聲", "style": STYLE, "clips": main},
              open(os.path.join(OUT, "seg_main.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump({"name": "片尾", "style": STYLE,
               "clips": [{"id": "#endcard", "src": "output/endcard.mp4", "in": 0.0, "out": 7.0, "no_overlay": True, "xfade": 1.0}]},
              open(os.path.join(OUT, "seg_end.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    bx, d1 = badge_boxes(main)
    json.dump({"boxes": bx}, open(os.path.join(OUT, "badge_mosaic.json"), "w"))
    print("名牌打碼：D1 從第", d1, "格開始，打碼格數", sum(1 for b in bx if b))
    print("主段落", round(sum(c["out"] - c["in"] + c.get("pad", 0) + c.get("hold", 0) for c in main), 1), "秒；片段", len(main))
