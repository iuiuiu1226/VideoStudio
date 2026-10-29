"""（剪輯清單產生器；臉部追蹤檔在暫存資料夾，重新產生前要先跑追蹤）
產生課堂精華 VOL.01（IMG_6552，講師：水結晶與正能量）剪輯清單。字幕、關鍵框都用素材秒數。"""
import json, os
import numpy as np
from scipy.ndimage import gaussian_filter1d

OUT = "/home/user/VideoStudio/cuts/class01"
TRACK = "/tmp/claude-0/-home-user-VideoStudio/44fa75cb-1119-5d5b-9fd9-fcc63d88909d/scratchpad/v7/track.json"
STYLE = {"font": "Noto Sans TC", "size": 78, "outline": 4, "shadow": 1, "margin_v": 660,
         "title": "BK 測試｜課堂精華", "note": "第七感人生智慧學"}
SW, SH = 2160, 3840
F, CY = 0.11, 0.33          # 臉高佔畫面比例（固定＝補償拍攝時的推拉）、臉中心高度

tr = json.load(open(TRACK))
T = np.array([t for t, _ in tr])
def series(k):
    v = np.array([f[k] if f else np.nan for _, f in tr], float)
    ok = ~np.isnan(v)
    return np.interp(T, T[ok], v[ok])
CX, CYs = (gaussian_filter1d(series(k), 10) for k in (0, 1))   # 位置約 1 秒平滑
FH = gaussian_filter1d(series(2), 4)                            # 臉大小約 0.4 秒平滑，鏡頭推拉時跟得上

def rect_at(t):
    cx, cy, fh = (float(np.interp(t, T, a)) for a in (CX, CYs, FH))
    h = min(fh * SH / F, SH); w = h * 9 / 16
    x = min(max(cx * SW - w / 2, 0), SW - w); y = min(max(cy * SH - CY * h, 0), SH - h)
    return {"x": round(x, 1), "y": round(y, 1), "h": round(h, 1)}

def keys(a, b):
    ts = list(np.arange(a, b, 0.25)) + [b]
    return [{"t": round(float(t), 2), **rect_at(t)} for t in ts]

def clip(cid, i, o, subs, **kw):
    s = [[round(a - i, 2), round(b - i, 2), t] for a, b, t in subs]
    c = {"id": cid, "src": "IMG_6552.MOV", "in": i, "out": o, "in0": i, "out0": o, "subs": s, "subs_orig": s,
         "frame_keys": keys(i, o)}
    c.update(kw)
    return c

os.makedirs(OUT, exist_ok=True)
clips = [
    clip("#1 水結晶會被力量改變", 0.0, 19.05, [
        (0.00, 2.68, "結晶是會被某些力量改變的"), (2.72, 4.84, "好的力量會把它弄成"), (4.86, 6.50, "這個六角形"),
        (6.70, 7.76, "不好的力量"), (7.76, 9.40, "會把水結晶打散"), (9.90, 10.96, "所以這其實就是"),
        (10.98, 13.30, "一種能量的體現"), (14.44, 16.28, "那能讓水結晶"), (16.30, 17.62, "結成完整六角形的"),
        (17.66, 19.05, "我們就叫它正能量")], tail=0.0, overlay="work/life03_anim/overlay1.mov"),
    # 19.05–22.14 是口誤（「這種就會讓它這個負，所以少⋯」），拿掉
    clip("#2 說好話 做好事 存善心", 22.14, 33.25, [
        (22.30, 23.50, "盡量不要罵人"), (23.80, 26.02, "之前會有人推展"), (26.02, 27.20, "說好話"),
        (27.40, 29.76, "做好事 存善心之類的"), (29.76, 31.56, "都是希望我們的水結晶"),
        (31.58, 33.10, "都能變得漂漂亮亮的")], lead=0.0, tail=0.0, overlay="work/life03_anim/overlay2.mov"),
]
json.dump({"name": "課堂精華 VOL.01 段落 2｜水結晶與正能量（IMG_6552 原順序，刪最後一句「那這關我們什麼事呢」）",
           "style": STYLE, "clips": clips}, open(os.path.join(OUT, "seg2_water.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump({"name": "課堂精華 VOL.01 片尾（與學員分享 VOL.01 相同）", "style": STYLE,
           "clips": [{"id": "#endcard", "src": "output/endcard.mp4", "in": 0.0, "out": 7.0, "no_overlay": True}]},
          open(os.path.join(OUT, "seg4_end.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for t in (0, 5, 9, 10, 12, 16, 18.5, 22.5, 26, 29, 32):
    print(t, rect_at(t))

# 開頭、結尾的自製段落（tools/life03_anim.py 產生的旁白＋動畫）
ANIM = json.load(open("/home/user/VideoStudio/work/life03_anim/subs.json", encoding="utf-8"))
for fname, key, cid, title in (("seg1_intro.json", "intro", "#0 開頭：水結晶實驗是什麼？", "課堂精華 VOL.01 段落 1｜開頭拋問題（AI 旁白＋動畫）"),
                               ("seg3_outro.json", "outro", "#3 結尾：善念還是惡念", "課堂精華 VOL.01 段落 3｜結尾延伸（AI 旁白＋動畫）")):
    a = ANIM[key]
    json.dump({"name": title, "style": STYLE, "clips": [{
        "id": cid, "src": f"work/life03_anim/{key}.mp4", "in": 0.0, "out": a["dur"], "subs": a["subs"]}]},
        open(os.path.join(OUT, fname), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
