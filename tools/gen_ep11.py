"""編號 11（台中一日工作坊：學員推薦 BK 課程）剪輯清單。

素材：雲端「2026/04/19台中ㄧ日工作坊」（清單 cuts/taichung/files.txt）課後的學員訪問：
  IMG_6617 美國回來的女學員（第二次上）、IMG_6616 台南的科技業主管（第一次上，學姐推薦）、
  IMG_6608 台北做人資的學員（戴口罩）、IMG_6609 兩位年輕學員、IMG_6599 年輕男學員（第二次上，拿麥克風在教室裡講）。
腳本＝2026/11/27 提案（使用者：名牌打馬賽克、封面選 C「為什麼大家都推薦？／BK 一日工作坊」）。
訪問者的提問不放聲音，改成段落標籤（同編號 7：字幕下方金字）。自我介紹（名字、住哪、工作）、
讀書會／寺廟／神韻／App 等跟 BK 課程無關的段落、分數都不放。字幕照實際講的字（「安侯／安娜老師」→ 安和老師）。

工作檔：4K HDR 直拍，依 cuts/ep11/crops.json 裁切（訪問是近景，整張縮成 1080x1920 臉約 400–490 px；IMG_6599 鏡頭一邊講一邊移動，也用整張）再轉 SDR 30 格。頭頂太高的用 shift_y 往下移（SHIFT）。
名牌：成片做好後用 tools/badge_track.py 找位置、tools/mosaic.py 打碼（見 README 編號 11）。

用法：python3 tools/gen_ep11.py → cuts/ep11/seg_main.json、seg_end.json
      python3 tools/build_segment.py cuts/ep11/seg_main.json cuts/ep11/seg_end.json --src <工作檔資料夾> --font <字型資料夾> -o output/11_….mp4
"""
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cuts", "ep11")
STYLE = {"font": "Noto Sans TC", "size": 78, "outline": 4, "shadow": 1, "margin_v": 660,
         "title": "BK 測試｜學員分享", "note": "第七感人生智慧學"}

TARGET = -16.0
# 每個人用到的範圍量的響度（LUFS）；同一個人的片段用同一個增益（短片段自動量會忽大忽小）
LUFS = {"IMG_6617": -28.9, "IMG_6616": -27.2, "IMG_6608": -20.6, "IMG_6609": None, "IMG_6599": -26.0}
# 頭頂往下移到約 y 430（標題 y 288、小字 y 346 下面）；訪問近景臉約 400–490 px
SHIFT = {"IMG_6617": 140, "IMG_6616": 190, "IMG_6608": 150, "IMG_6599": 100}
LABEL = r"{\an5\pos(540,1350)\fs56\b1\c&H5AB4D9&\3c&H140F0B&\bord5\shad0\fad(%d,%d)}"   # 段落標籤：字幕下方、金色（同編號 7）
LABELS = {"H": "你會推薦別人來上嗎？", "A": "為什麼來上課？", "B": "上完覺得怎麼樣？", "C": "印象最深的是什麼？",
          "D": "生活上怎麼用？", "E": "你會推薦別人來上嗎？"}

# (代號, 工作檔, 入點, 出點, 字幕[(開始, 結束, 文字)]（素材秒數）, 額外設定)
CLIPS = [
    # 開頭鉤子：女學員回答「會推薦嗎？」（提問不放聲音，標籤代替）
    ("H1 當然會", "IMG_6617", 129.93, 137.10, [(129.98, 134.88, "當然會啊！我會介紹\\N我的親朋好友來上這個課"),
                                            (134.92, 137.30, "因為其實這個是\\N蠻實用的一堂課")], {"pad": 0.45}),   # 「親朋好友｜還有朋友｜來上」中間的「還有朋友」不放；句尾「對不對」不放
    # 為什麼來上課？
    ("A1 學姐推薦", "IMG_6616", 21.16, 34.42, [(21.18, 26.40, "有朋友上過這個\\NBK 測試的學姐"),
                                             (27.40, 34.60, "推薦我來聽，因為她覺得\\N這個工具非常的不錯")], {"pad": 0.4}),
    # 上完覺得怎麼樣？
    ("B1 超乎想像", "IMG_6608", 27.00, 29.40, [(27.04, 29.55, "我覺得很棒\\N因為超乎想像")], {"pad": 0.4}),
    ("B3 很幽默", "IMG_6617", 62.84, 68.04, [(62.86, 64.95, "就覺得老師上課很幽默"), (64.98, 66.75, "然後都不會想睡覺"),
                                          (66.78, 68.25, "這個課真的很棒")], {"pad": 0.4}),
    # 印象最深的是什麼？
    ("C1 修正技巧", "IMG_6616", 77.60, 98.70, [(77.62, 79.90, "其實一開始都會有點不太準"), (79.92, 84.20, "但是老師會根據你先去做"),
                                             (83.98, 86.50, "然後怎麼修正你的技巧"), (89.10, 90.30, "答案還會有所不同"), (90.86, 98.90, "我就覺得這個\\N很有來上課的收穫")],
     {"pad": 0.4}),
    ("C2 實作", "IMG_6608", 51.32, 58.30, [(51.34, 55.10, "現場有實作\\N然後可以體驗"), (56.00, 58.45, "比單純看書要好")], {"pad": 0.4}),
    # 生活上怎麼用？
    ("D1 超市", "IMG_6617", 77.30, 86.38, [(77.32, 79.30, "你去超市，那你要買東西"), (79.44, 80.90, "你即使五包東西"),
                                         (81.00, 84.12, "裡面可能每一包的\\N質量也不太一樣"), (84.20, 86.55, "你就可以測說\\N你要拿哪一包")],
     {"pad": 0.4}),
    # 你會推薦別人來上嗎？（收尾）
    ("E2 再來上", "IMG_6599", 55.30, 59.74, [(55.32, 56.75, "如果之後還有的話"), (56.84, 59.95, "還是會想再來上看看啦")],
     {"hold": 1.0}),
]

# 句子中間要拿掉的時間（素材秒數）："w"＝字（切點轉寫確認過，前後交疊淡入淡出）；"p"＝停頓（前後各留 KEEP 秒，縮成自然的小停頓）
KEEP = 0.11
REMOVE = {
    "H1": [(133.26, 133.66, "w")],                         # 「還有朋友」
    "A1": [(26.42, 27.38, "w"), (30.32, 30.92, "p"), (32.14, 33.96, "w")],   # 「學姐，｜然後就是｜推薦」（27.40 起才是「推」）、「工…具」中間的停頓、「非常的…嗯…不錯」的「嗯」
    "B3": [(65.52, 66.00, "p")],                           # 「然後都…不會想睡覺」
    "C1": [(81.56, 82.10, "p"), (86.56, 89.10, "w"), (90.18, 90.80, "w"), (93.40, 98.06, "w")],
    # 「根…據」中間的停頓、「技巧｜下去，呃，會｜答案」、「這樣子」、「來上課的｜那個，就是｜收穫」（「怎麼修正」是自然的講法，保留）
    "C2": [(53.62, 54.50, "p"), (55.14, 56.30, "p")],      # 「可以…體驗」、「體驗，…比單純」
}
JOIN_NEXT = set()


def clip(cid, src, a, b, subs, extra):
    tail = extra.get("pad", 0.0) + extra.get("hold", 0.0)
    s = [[round(max(t, a) - a, 2), round(min(e, b + tail) - a, 2), txt] for t, e, txt in subs if e > a and t < b + tail]
    c = {"id": f"#{cid}", "src": f"{src}.MOV", "in": a, "out": b, "subs": s}
    if LUFS.get(src) is not None:
        c.update(auto_gain=False, gain_db=round(TARGET - LUFS[src], 1))
    if SHIFT.get(src):
        c["shift_y"] = SHIFT[src]
    c.update(extra)
    if c.get("pad") or c.get("hold"):
        c["room"] = f"room_{src}.wav"
    return c


def expand(cid, src, a, b, subs, extra):
    """拿掉 REMOVE 裡的時間：一段拆成幾小段，句尾的 pad／hold 只放在最後一小段；拆開的地方聲音交疊淡入淡出"""
    key = cid.split()[0]
    cuts = []
    for r0, r1, kind in sorted(REMOVE.get(key, [])):
        if kind == "p":
            if r1 - r0 - 2 * KEEP >= 0.15:
                cuts.append((r0 + KEEP, r1 - KEEP))
        else:
            cuts.append((r0, r1))
    pieces, x = [], a
    for r0, r1 in cuts:
        pieces.append((round(x, 2), round(r0, 2)))
        x = r1
    pieces.append((round(x, 2), b))
    out = []
    for k, (p0, p1) in enumerate(pieces):
        last = k == len(pieces) - 1
        ex = extra if last else {kk: v for kk, v in extra.items() if kk not in ("pad", "hold")}
        c = clip(cid if k == 0 else f"{key}-{k + 1}", src, p0, p1, subs, ex)
        if k > 0:
            c["join"] = True
        out.append(c)
    return out


os.makedirs(OUT, exist_ok=True)
main = [p for c in CLIPS for p in expand(*c)]
# 段落標籤：同一段第一個片段淡入、最後一個片段淡出；最後一段的停格（hold）是交叉淡化進片尾的時間，標籤在那之前收掉
keys = [c["id"][1] for c in main]
for k, c in enumerate(main):
    lab = LABELS.get(keys[k])
    if not lab:
        continue
    first = k == 0 or keys[k - 1] != keys[k]
    last = k == len(main) - 1 or keys[k + 1] != keys[k]
    end = c["out"] + c.get("pad", 0.0) + (0.0 if k == len(main) - 1 else c.get("hold", 0.0))
    c["fx"] = [[c["in"], end, LABEL % (300 if first else 0, 300 if last else 0) + lab]]
json.dump({"name": "編號 11 台中一日工作坊：學員推薦", "style": STYLE, "clips": main},
          open(os.path.join(OUT, "seg_main.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump({"name": "片尾", "style": STYLE,
           "clips": [{"id": "#endcard", "src": "output/endcard.mp4", "in": 0.0, "out": 7.0, "no_overlay": True, "xfade": 1.0}]},
          open(os.path.join(OUT, "seg_end.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("主段落", round(sum(c["out"] - c["in"] + c.get("pad", 0) + c.get("hold", 0) for c in main), 1), "秒；片段", len(main))
