"""編號 10「BK 是什麼？」剪輯清單（課堂精華：講師講觀念＋自製動畫，同編號 4 水結晶的做法）。

第一版先不配旁白（Gemini 配音帳戶沒有餘額，使用者 2026/11/11 說先看整體內容和流暢度再決定要不要儲值）：
旁白的位置先用字幕代替，長度照預估的配音速度（約每秒 5 個字）；之後配音時字幕不變、把旁白混進那幾段。

素材（工作檔 1080x1920、30 格，暫存資料夾 ep10/px，tools 外的 topx.py 轉檔）：
  Nina 資料夾（2026/09/21 BK 一日工作坊）：IMG_8495 安和老師「BK 就是 Behavioral Kinesiology」、IMG_8498 預防醫學／鑽石博士／第一本書、
    IMG_8493 主持人「不要急著相信，也不要急著否定」（主持人名牌打碼）
  Lana 資料夾：IMG_4747 安和老師教怎麼壓（4K 遠景，裁講師與學員那一塊）、IMG_4742／4725／4736／4740 學員練習（沒講話，當畫面）
  宗翰拍的資料夾（2026/08/30）：PXL_20260830_063118308 安和老師「BK 衡量的是意識能量水準、分數表」
  自製動畫（tools/ep10_anim.py）：timeline.mp4（1960 年代應用肌動學 → 1970 年代預防醫學的醫生）、book.mp4（投影片上的《BK》書封＋1979，聲音是 IMG_8498 的原音）
結構：開頭（旁白拋問題）→ BK 是什麼？ → 從哪裡來？ → 怎麼測？ → 測的是什麼？ → 主持人「要正向地懷疑」→ 片尾
說法照編號 4 的原則：旁白只講事實、用中性寫法，不寫成「證明」或醫療功效（README「BK 背景資料」）。

用法：python3 tools/gen_ep10.py → cuts/ep10/seg_main.json、seg_end.json、badge_mosaic.json
      python3 tools/build_segment.py cuts/ep10/seg_main.json cuts/ep10/seg_end.json --src <ep10/px> --font <字型資料夾> -o output/10_….mp4
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "cuts", "ep10")
STYLE = {"font": "Noto Sans TC", "size": 78, "outline": 4, "shadow": 1, "margin_v": 660,
         "title": "BK 測試｜課堂精華", "note": "第七感人生智慧學"}
LABEL = r"{\an5\pos(540,1350)\fs56\b1\c&H5AB4D9&\3c&H140F0B&\bord5\shad0\fad(%d,%d)}"   # 段落標籤：字幕下方、金色（同編號 7）
BIG = r"{\an5\pos(540,1470)\fs230\b1\c&H5AB4D9&\3c&H140F0B&\bord8\shad0\fad(150,200)\fscx60\fscy60\t(0,180,\fscx106\fscy106)\t(180,300,\fscx100\fscy100)}"
BROLL = {"auto_gain": False, "gain_db": -14.0}   # 學員練習畫面：沒講話，現場聲音壓低墊著

# (代號, 素材, 入點, 出點, 字幕[(開始, 結束, 文字)]（素材秒數；動畫段從 0 起算）, 段落標籤, 額外設定)
CLIPS = [
    # 開頭：旁白拋問題（目前用字幕代替旁白）
    ("V1 開頭", "IMG_4742.MOV", 0.30, 4.50, [(0.45, 4.35, "壓一壓手臂，就能知道\\N一個東西適不適合你？")], None, BROLL),
    ("V1b", "IMG_4725.MOV", 0.20, 2.40, [(0.25, 2.35, "這個方法，叫做 BK")], None,
     dict(BROLL, fx=[[1.30, 2.40, BIG + "BK"]])),
    # BK 是什麼？（入點 5.30：前面「因為大家一看 BK 不知道是什麼…上網去查」不放；出點 14.84「它簡稱 BK」講完）
    ("N95 是什麼", "IMG_8495.MOV", 5.30, 14.84, [(5.48, 8.40, "BK 就是\\NBehavioral Kinesiology"), (8.45, 10.82, "一種行為上的肌肉動力學"),
                                               (10.82, 12.30, "就是它原本的學名"), (12.34, 14.90, "它簡稱 BK")],
     "BK 是什麼？", {"pad": 0.3, "room": "room_IMG_8495.wav"}),
    # 從哪裡來？：時間軸動畫（旁白先用字幕）→ 講師
    ("V2 時間軸", "work/ep10_anim/timeline.mp4", 0.0, 7.60, [(0.25, 3.45, "它的源頭\\N是 1960 年代的應用肌動學"),
                                                         (3.60, 7.30, "後來，預防醫學的醫生\\N加進了情緒和心理的因素")],
     "從哪裡來？", {"auto_gain": False}),
    ("N98a 預防醫學", "IMG_8498.MOV", 61.20, 69.86, [(61.42, 63.30, "預防醫學的醫生就是"), (63.40, 66.00, "可不可以不要那麼常跑醫院"),
                                                  (66.30, 69.95, "不然你只要生病\\N看醫生都來不及了")],
     "從哪裡來？", {"pad": 0.3, "room": "room_IMG_8498.wav", "xfade": 0.4}),   # 「忍到」聽不清楚，字幕不寫
    ("N98b 鑽石博士", "IMG_8498.MOV", 100.15, 106.69, [(100.31, 103.95, "這是當時這個\\N國際預防醫學學會"), (104.00, 106.75, "John Diamond\\N鑽石博士")],
     "從哪裡來？", {"pad": 0.25, "room": "room_IMG_8498.wav"}),
    ("V3 書封", "work/ep10_anim/book.mp4", 0.0, 3.93, [(0.10, 2.75, "這本是他第一本出的書"), (2.80, 4.25, "就是叫 BK")],
     "從哪裡來？", {"pad": 0.35, "room": "room_IMG_8498.wav", "xfade": 0.3}),   # 聲音＝IMG_8498 134.00–137.95
    # 怎麼測？：學員練習畫面（旁白先用字幕）→ 講師
    ("V4 怎麼測", "IMG_4736.MOV", 0.0, 3.30, [(0.10, 3.20, "測的時候\\N一個人把手臂平舉")], "怎麼測？", BROLL),
    ("V4b", "IMG_4740.MOV", 0.50, 4.20, [(0.60, 2.40, "另一個人輕輕往下壓"), (2.45, 4.15, "看是撐得住\\N還是掉下去")], "怎麼測？", BROLL),
    ("L47a 力氣", "IMG_4747.MOV", 82.80, 91.74, [(83.05, 84.95, "所以你在壓人的時候"), (85.30, 87.95, "真的跟力氣沒有關係"),
                                              (88.30, 91.80, "是跟他鎖不鎖得住的關係")],
     "怎麼測？", {"pad": 0.25, "room": "room_IMG_4747.wav"}),
    ("L47b 越小力", "IMG_4747.MOV", 113.40, 118.95, [(113.60, 116.00, "所以你其實是越小力"), (116.00, 119.05, "然後越緩慢越好")],
     "怎麼測？", {"pad": 0.35, "room": "room_IMG_4747.wav"}),
    # 測的是什麼？（最後兩秒投影片換成分數表）
    ("Z63 意識能量", "PXL_063118308.MOV", 22.10, 38.00, [(22.40, 26.10, "那在 BK 裡面\\N我們的能量是衡量什麼呢？"),
                                                    (26.90, 31.50, "我們最主要就是衡量\\N你在意識能量水準的位置"),
                                                    (32.40, 35.95, "就你在那個分數表裡面\\N你站在哪裡？"), (36.40, 38.05, "你這個在哪裡？")],
     "測的是什麼？", {"pad": 0.35, "room": "room_PXL_063118308.wav"}),
    # 結尾：主持人（名牌打碼）；講完停一下再接片尾
    ("N93 結尾", "IMG_8493.MOV", 0.0, 5.28, [(0.0, 3.05, "我們不要急著相信\\N但是也不要急著否定"), (3.10, 5.45, "我們要正向地懷疑")],
     None, {"hold": 2.0, "rx": 0.06, "room": "room_IMG_8493.wav"}),
]


# 主持人（IMG_8493）名牌打碼：人工標框（N93 入點後第幾格, x0, y0, x1, y1），中間逐格內插；最後一格之後（停格＋交叉淡化進片尾）沿用最後的框
BADGE = [(0, 458, 1073, 534, 1160), (15, 493, 1073, 572, 1160), (30, 483, 1083, 557, 1162), (45, 463, 1063, 542, 1142),
         (60, 453, 1048, 532, 1137), (75, 438, 1043, 522, 1132), (90, 458, 1053, 527, 1137), (105, 478, 1073, 542, 1152),
         (120, 488, 1088, 562, 1172), (135, 518, 1098, 582, 1177), (150, 510, 1118, 577, 1202), (158, 513, 1123, 580, 1207)]


def badge_boxes(main, fps=30):
    """N93 在成片裡從第幾格開始（跟 build_segment 一樣：每段以格取整、xfade 讓這段提早開始）"""
    t0 = 0
    for c in main:
        t0 -= round(c.get("xfade", 0.0) * fps)
        if c["id"].startswith("#N93"):
            end = t0 + round((c["out"] - c["in"]) * fps) + round(c.get("pad", 0.0) * fps) + round(c.get("hold", 0.0) * fps)
            break
        t0 += round((c["out"] - c["in"]) * fps) + round(c.get("pad", 0.0) * fps) + round(c.get("hold", 0.0) * fps)
    boxes = [None] * end
    keys = BADGE + [(end - t0 - 1,) + BADGE[-1][1:]]
    for (f0, *b0), (f1, *b1) in zip(keys, keys[1:]):
        for f in range(f0, f1 + 1):
            u = (f - f0) / max(f1 - f0, 1)
            x0, y0, x1, y1 = [p + (q - p) * u for p, q in zip(b0, b1)]
            boxes[t0 + f] = [round(x0), round(y0), round(x1 - x0), round(y1 - y0)]
    return boxes, t0


def build():
    main = []
    for k, (cid, src, a, b, subs, lab, extra) in enumerate(CLIPS):
        tail = extra.get("pad", 0.0) + extra.get("hold", 0.0)
        s = [[round(max(t, a) - a, 2), round(min(e, b + tail) - a, 2), txt] for t, e, txt in subs if e > a and t < b + tail]
        c = {"id": f"#{cid}", "src": src, "in": a, "out": b, "subs": s}
        c.update({kk: v for kk, v in extra.items() if kk != "fx"})
        fx = list(extra.get("fx", []))
        if lab:
            first = k == 0 or CLIPS[k - 1][5] != lab
            last = k == len(CLIPS) - 1 or CLIPS[k + 1][5] != lab
            fx.append([a, b + tail, LABEL % (300 if first else 0, 300 if last else 0) + lab])
        if fx:
            c["fx"] = fx
        main.append(c)
    return main


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    main = build()
    json.dump({"name": "編號 10 BK 是什麼？", "style": STYLE, "clips": main},
              open(os.path.join(OUT, "seg_main.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump({"name": "片尾", "style": STYLE,
               "clips": [{"id": "#endcard", "src": "output/endcard.mp4", "in": 0.0, "out": 6.0, "no_overlay": True, "xfade": 1.0}]},
              open(os.path.join(OUT, "seg_end.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    bx, f0 = badge_boxes(main)
    json.dump({"boxes": bx}, open(os.path.join(OUT, "badge_mosaic.json"), "w"))
    print("主持人名牌打碼：第", f0, "格起，共", sum(1 for b in bx if b), "格")
    t = 0.0
    for c in main:
        t += round((c["out"] - c["in"]) * 30) / 30 + round(c.get("pad", 0) * 30) / 30 + round(c.get("hold", 0) * 30) / 30 - c.get("xfade", 0)
    print("主段落", round(t, 1), "秒＋片尾 5 秒＝", round(t + 5, 1), "秒；片段", len(main))
