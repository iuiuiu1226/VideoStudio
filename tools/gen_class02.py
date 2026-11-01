"""產生課堂精華 VOL.02（IMG_8235／IMG_8236，講師：能量看不見，但真實存在）剪輯清單。
開頭問題卡「看不見、摸不到的東西，就不存在嗎？」、講師段落（字幕下方小圖示）、結尾收尾卡、片尾。片段與重點字時間在 cuts/class02/clips.json；
動畫先跑 tools/class02_anim.py（輸出 work/class02_anim/，durations.json 記開頭與結尾的長度）。"""
import json, os

OUT = "/home/user/VideoStudio/cuts/class02"
ANIM = "work/class02_anim"
STYLE = {"font": "Noto Sans TC", "size": 78, "outline": 4, "shadow": 1, "margin_v": 660,
         "title": "BK 測試｜課堂精華", "note": "第七感人生智慧學"}
SHIFT = 90          # 講師頭頂偏高，畫面往下移才不會被標題壓到（開頭、結尾動畫不移）
clips = json.load(open(os.path.join(OUT, "clips.json"), encoding="utf-8"))
dur = json.load(open(os.path.join("/home/user/VideoStudio", ANIM, "durations.json")))

# 字幕（素材秒數）：起點用逐字時間，終點接下一句起點或片段結尾
SUBS = {
    "A": [(0.00, "看不著 摸不到"), (2.20, "但是客觀存在"), (4.20, "而且是真實存在的")],
    "B": [(15.03, "比如說現在"), (15.62, "請問空氣中現在有水嗎？")],
    "C": [(19.95, "有！水蒸氣"), (22.08, "你看不到啊"), (22.95, "但它真實存在 對吧？")],
    "D": [(0.00, "物質跟能量"), (0.72, "是百分百有關係的"), (1.88, "因為能量會變成物質"), (4.02, "物質會變成能量")],
    # 「它從能量變成物質」拿掉：水蒸氣凝結成水是物質換狀態，不是能量變成物質
    "E": [(16.08, "當冷氣開始降溫"), (17.85, "降到零度"), (18.75, "請問空氣中的水"), (20.60, "會不會出現？")],
    "F": [(26.95, "再降到零下 20 度"), (28.80, "水會變什麼？"), (30.75, "冰塊"), (31.50, "它從液體變成固體了")],
    "G": [(52.42, "冰塊加溫變成水"), (54.80, "再加溫變成水蒸氣")],
    "H": [(85.85, "所以能量跟物質"), (87.25, "是絕對互相存在的"), (89.80, "因為它們就是"), (90.50, "一個轉化的過程")],
    "I": [(105.14, "物體也會受"), (106.00, "能量的改變所影響"), (107.55, "所以為什麼"), (108.05, "BK 測試這麼好用？"),
          (109.75, "為什麼提升能量這麼重要？"), (111.45, "原因就在這邊"), (112.35, "一切的一切"), (113.35, "都是能量構成")],
}

def lecture_clip(cid):
    c = clips[cid]
    s = SUBS[cid]
    subs = [[round(max(a, c["in"]) - c["in"], 2), round((s[k + 1][0] if k + 1 < len(s) else c["out"]) - c["in"], 2), txt]
            for k, (a, txt) in enumerate(s)]
    out = {"id": f"#{cid}", "src": c["src"], "in": c["in"], "out": c["out"], "subs": subs, "shift_y": SHIFT}
    if c.get("ov"):
        out["overlay"] = f"{ANIM}/ov_{cid}.mov"
    return out

seg = lambda name, cl: json.dump({"name": name, "style": STYLE, "clips": cl},
                                 open(os.path.join(OUT, name.split("｜")[0] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
lect = [lecture_clip(k) for k in "ABCDEFGHI"]
lect[0]["xfade"] = 0.5            # 開頭問題卡交叉淡化進講師
lect[-1]["hold"] = 0.6            # 最後一句講完停格一下，留給下一段的交叉淡化
seg("seg1_intro｜開頭問題：看不見、摸不到的東西，就不存在嗎？",
    [{"id": "#intro", "src": f"{ANIM}/intro.mp4", "in": 0.0, "out": dur["intro"], "subs": []}])
seg("seg2_lecture｜講師：能量看不見，但真實存在（IMG_8235、IMG_8236）", lect)
seg("seg3_outro｜收尾：看不見，不代表不存在", [{"id": "#outro", "src": f"{ANIM}/outro.mp4", "in": 0.0, "out": dur["outro"], "subs": [], "xfade": 0.5}])
seg("seg4_end｜片尾", [{"id": "#endcard", "src": "output/endcard.mp4", "in": 0.0, "out": 7.0, "no_overlay": True, "xfade": 1.0}])
print("ok", sum(c["out"] - c["in"] for c in lect), "秒講師段落")
