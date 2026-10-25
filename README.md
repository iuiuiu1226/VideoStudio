# VideoStudio

## 第七感｜BK 測試學員心得

腳本與分鏡在 `scripts/`（最新版為 v3），逐字稿在 `scripts/逐字稿_raw.txt`。

### 成片

| 版本 | 長度 | 用途 | 剪輯清單 |
|---|---|---|---|
| 完整版 | 約 101 秒 | Facebook、LINE | `cuts/seg1_hook.json` … `cuts/seg6_end.json` 依序接起來 |
| 精簡版 | 60 秒 | IG Reels、TikTok、YouTube Shorts | `cuts/short60.json`（片段取自 seg1–seg6） |

段落：鉤子（龍是真的）→ 怎麼測出來的 → 肌肉連動潛意識 → 親身體驗 → 生活怎麼用 → 收尾＋片尾卡

### 工具

需要 `ffmpeg`、Python 套件 `numpy`、`opencv-python-headless`，
字型為 Noto Sans TC，臉部偵測模型為 OpenCV YuNet（`face_detection_yunet_2023mar.onnx`）。

```sh
# 1. 句尾留氣口（依音訊調整切點，可重複執行）
python3 tools/breathe.py cuts/seg*.json --src <素材資料夾>

# 2. 自動構圖（同一人各段大小、位置一致）
python3 tools/autoframe.py cuts/seg*.json --src <素材資料夾> --model <yunet.onnx>

# 3. 輸出（可給多個剪輯清單，依序接成一支）
python3 tools/build_segment.py cuts/seg1_hook.json cuts/seg2_how.json cuts/seg3_why.json \
    cuts/seg4_feel.json cuts/seg5_use.json cuts/seg6_end.json \
    --src <素材資料夾> --font <字型資料夾> -o output/完整版.mp4
```

剪輯清單欄位：`src` 素材檔、`in`/`out` 切點（秒）、`subs` 字幕（時間以片段開頭為 0）、
`frame` 裁切框（由 autoframe 產生）、`in0`/`out0` 加氣口前的原始切點、
`tail`/`lead` 氣口上限覆寫、`card`/`dur` 純文字字卡。
