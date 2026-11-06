"""編號 8（台南精進班：學員真實心得「BK 測試準不準？」）剪輯清單——第一版只剪＋字幕＋問題標籤，配樂、封面之後再說。

素材：雲端「2026/06/28台南精進班」IMG_8223（俊傑，側臉、另一間教室）、IMG_8228（白襯衫學員）、IMG_8249（輔導員）、
IMG_8253（助教示範 BK 測試）。跟編號 7 是同一批人。腳本是 2026/11/06 提案裡我建議的句子（使用者說「先剪出來看看」）。

- 訪問者的提問不放聲音，每一段開頭在標題下面跳出金色問題標籤（樣式同編號 6 的「第一款糖果能量測試」），一直留到那段講完
- 標籤在 y 446，人臉頂端原本在 y 430，所以整支 shift_y 120 把人往下移，標籤才不會壓到頭
- 句中拿掉的字（「就是」「然後」、訪問者插話「OK OK」、重講的「一般的」、聽不清楚的一個字）：每段都轉寫確認過，
  聲音很小的段落單獨轉寫常聽錯，一律連前後句一起轉寫確認（$S/ep8/verify2.py、p8a–p8c.json）
- 輔導員「其實（不）是最準」三次轉寫有一次聽成「不是」，意思相反，改用他後面講得清楚的「不要帶著主觀去測，那是最準的」
- 剪接點照編號 7 第四版的做法：句中剪接 join（聲音交疊淡入淡出）、補停頓用原片背景聲 room（tools/roomtone.py）

工作檔：4K HDR 原檔依 cuts/ep08/crops.json 裁切（臉高約 320 px，跟之前影片一致；示範那段要看得到手臂，不放大）
再轉 1080x1920 SDR 30 格。
用法：python3 tools/gen_ep08.py → cuts/ep08/seg_main.json、seg_end.json
      python3 tools/build_segment.py cuts/ep08/seg_main.json cuts/ep08/seg_end.json --src <工作檔資料夾> --font <字型資料夾> -o output/08_….mp4
"""
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cuts", "ep08")
STYLE = {"font": "Noto Sans TC", "size": 78, "outline": 4, "shadow": 1, "margin_v": 660,
         "title": "BK 測試｜學員分享", "note": "第七感人生智慧學", "shift_y": 120}

TARGET = -16.0
# 每個人用到的範圍整段量的響度（LUFS）；同一個人的片段用同一個增益
LUFS = {"IMG_8223": -33.1, "IMG_8228": -29.2, "IMG_8249": -26.7, "IMG_8253": -21.6}

# 問題標籤：標題下面、頭頂上面，金色粗字＋深色描邊（同編號 6）
LABEL = r"{\an5\pos(540,446)\fs68\b1\c&H5AB4D9&\3c&H140F0B&\bord6\shad0\fad(%d,%d)}"

# (代號, 素材, 片段[(入, 出)…], 字幕[(開始, 結束, 文字)]（素材秒數）, 額外設定, 問題標籤)
# 同一段裡的片段之間是句中剪接（join）；pad＝句尾補停頓（用背景聲）
SECTIONS = [
    # 開頭鉤子
    ("H 鉤子", "IMG_8228", [(65.55, 71.30)],
     [(65.55, 68.90, "現在有很多\\N自稱為大師的"), (69.15, 71.55, "用 BK 測一下\\N就知道了")], {"pad": 0.45}, None),
    # 為什麼來上 BK？（白襯衫學員）
    ("Q1 為什麼", "IMG_8228", [(4.15, 10.35), (11.60, 13.15)],
     [(4.15, 5.90, "因為我上過課"), (5.95, 10.35, "我有加入 Seven 老師的\\N那個群組"), (11.60, 13.40, "想說再精進一下")],
     {"pad": 0.35, "xfade": 0.3}, "為什麼來上 BK？"),     # 中間訪問者的「OK OK」和「啊」不放；鉤子同一個人，交叉淡化 0.3 秒避免跳一下
    # 上完覺得怎麼樣？（俊傑）
    ("Q2 神奇", "IMG_8223", [(22.30, 24.10), (24.32, 24.55), (24.90, 31.08), (31.40, 32.38), (34.08, 36.25)],
     [(22.30, 24.20, "就是會覺得還蠻神奇的"), (24.32, 28.00, "因為它是藉由\\N人的身體去做一個"), (28.00, 31.08, "就是有點像\\N蠻直覺的一個反應"),
      (31.40, 36.50, "就會覺得跟一般的方法\\N好像是不太一樣的")],
     {"pad": 0.3}, "上完覺得怎麼樣？"),                    # 「神奇的｜就是｜因為」的「就是」、「因為…它」的停頓、「然後」、重講的「欸，一般的」不放（開頭的「就是」跟「會」黏在一起，剪了會傷到「會」，保留）
    # BK 測試怎麼測？（助教示範）
    ("DM 示範", "IMG_8253", [(0.00, 3.96), (6.12, 9.60)],
     [(0.00, 1.74, "稍微感受一下\\N一、二、三，抵抗"), (1.76, 3.96, "OK，很標準，出力了"), (6.12, 7.40, "你有感覺我出很大力嗎？"),
      (7.95, 8.42, "沒有"), (8.45, 9.85, "就稍微頂一下")],
     {"pad": 0.25}, "BK 測試怎麼測？"),                    # 中間一句聽不清楚（「等一下就…」）不放
    # 準嗎？（俊傑）
    ("Q3 準", "IMG_8223", [(39.62, 40.42), (55.20, 56.05), (57.50, 58.40), (59.05, 60.85), (61.66, 63.70)],
     [(39.62, 40.62, "還蠻準的"), (55.20, 58.65, "之前有一些東西\\N沒有很確定"), (59.05, 60.95, "到底是真的還是假的"),
      (61.66, 63.95, "測試完之後\\N發現好像真的是這樣")],
     {"pad": 0.35}, "測得準嗎？"),                         # 訪問者的追問、「就是」「也」「然後」不放
    # 印象最深的是什麼？（白襯衫學員）
    ("Q4 印象", "IMG_8228", [(30.40, 32.80), (33.30, 36.75), (51.25, 54.65), (60.40, 63.00), (63.42, 65.45)],
     [(30.40, 32.80, "比較深刻的部分\\N應該就是說"), (33.30, 37.00, "對於既定印象的打破"), (51.25, 54.85, "每個人都有\\N屬於他的能量等級"),
      (60.40, 61.85, "就用 BK 來測試"), (61.85, 65.70, "不是說\\N我能量多高就多高")],
     {"pad": 0.35}, "印象最深的是什麼？"),                 # 「比如說像那個…愛因斯坦、希特勒…就是說」不放（「破」後面緊接「比如」，聽起來像「吧」，出點切在「破」）；「不是 X 說」中間聽不清楚的字不放
    # 怎麼測才準？（輔導員）
    ("Q5 練習", "IMG_8249", [(22.05, 24.62), (25.48, 28.70), (30.42, 31.15), (31.85, 32.95)],
     [(22.05, 24.85, "不要帶著主觀去測\\N那是最準的"), (25.48, 31.35, "我們要再練習很多次\\N去找出受力點"),
      (31.85, 33.20, "我們就是要練習這個")],
     {"pad": 0.4, "hold": 1.0}, "怎麼測才準？"),           # 「那個…那個什麼」不放
]
EXTRA_GAIN = {("Q3 準", 0): 5.0}   # 「還蠻準的」講得很小聲（比旁邊訪問者小 10 dB 以上），單獨加大一點
# 頭髮比較高的人再往下移，不碰到問題標籤（整支預設 shift_y 120）
SRC_SHIFT = {"IMG_8223": 160, "IMG_8249": 270}


def build():
    clips = []
    for sid, src, pieces, subs, extra, label in SECTIONS:
        n = len(pieces)
        for k, (a, b) in enumerate(pieces):
            last = k == n - 1
            ex = {kk: v for kk, v in extra.items() if last or kk not in ("pad", "hold")}
            if k > 0:
                ex.pop("xfade", None)
            tail = (ex.get("pad", 0.0) + ex.get("hold", 0.0)) if last else 0.0
            s = [[round(max(t, a) - a, 2), round(min(e, b + tail) - a, 2), txt] for t, e, txt in subs if e > a and t < b + tail]
            c = {"id": f"#{sid}" if k == 0 else f"#{sid.split()[0]}-{k + 1}", "src": f"{src}.MOV", "in": a, "out": b, "subs": s,
                 "auto_gain": False, "gain_db": round(TARGET - LUFS[src] + EXTRA_GAIN.get((sid, k), 0.0), 1)}
            if src in SRC_SHIFT:
                c["shift_y"] = SRC_SHIFT[src]
            c.update(ex)
            if k > 0:
                c["join"] = True
            if c.get("pad") or c.get("hold"):
                c["room"] = f"room_{src}.wav"
            if label:
                fin, fout = k == 0, last
                # 最後一段的停格（hold）是交叉淡化進片尾的時間，標籤在那之前收掉，才不會疊在片尾 Logo 上
                end = b + (ex.get("pad", 0.0) if last else 0.0) + (0.0 if last else 1.0)
                c["fx"] = [[a, end, LABEL % (250 if fin else 0, 250 if fout else 0) + label]]
            clips.append(c)
    return clips


os.makedirs(OUT, exist_ok=True)
main = build()
json.dump({"name": "編號 8 學員真實心得（台南精進班）", "style": STYLE, "clips": main},
          open(os.path.join(OUT, "seg_main.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump({"name": "片尾", "style": STYLE,
           "clips": [{"id": "#endcard", "src": "output/endcard.mp4", "in": 0.0, "out": 7.0, "no_overlay": True, "xfade": 1.0}]},
          open(os.path.join(OUT, "seg_end.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("主段落", round(sum(c["out"] - c["in"] + c.get("pad", 0) + c.get("hold", 0) - c.get("xfade", 0) for c in main), 1), "秒；片段", len(main))
