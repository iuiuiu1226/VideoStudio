# VideoStudio

## 第七感｜BK 測試學員心得

腳本與分鏡在 `scripts/`（最新版為 v3），逐字稿在 `scripts/逐字稿_raw.txt`。

### 成片

| 版本 | 長度 | 用途 | 剪輯清單 |
|---|---|---|---|
| 完整版 | 約 94 秒 | Facebook、LINE | `cuts/seg1_hook.json` … `cuts/seg6_end.json` 依序接起來 |
| 精簡版 | 討論中 | IG Reels、TikTok、YouTube Shorts | `cuts/short60.json`（舊版，暫停使用） |

段落：鉤子（龍是真的）→ 怎麼測出來的 → 肌肉連動潛意識 → 親身體驗 → 生活怎麼用 → 片尾動畫

版面：字幕在胸口高度、上方常駐標題「BK 測試｜學員分享」與淡版權小字；Logo 放在片尾動畫（`assets/logo.png`）。

### 在自己的電腦上使用（本地版 Claude Code）

給在筆電上執行的 Claude：請照下列步驟準備環境（macOS 為例，Windows 用 winget / pip 對應安裝）。

1. 影音與 Python：`brew install ffmpeg python@3.12`；
   `pip3 install numpy scipy opencv-python-headless noisereduce "qrcode[pil]" zxing-cpp faster-whisper gdown`
2. 字型：Noto Sans TC（`https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf`），
   放在 `assets/fonts/`（不進版控）。
3. 臉部偵測模型：`https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx`，
   放在 `assets/models/`（不進版控）。
4. 素材與成品：安裝「Google 雲端硬碟電腦版」，素材直接讀同步資料夾
   「第七感影片剪輯素材」，成品直接輸出到其中的「成品」資料夾（會自動上傳，沒有檔案大小限制，
   不需要再用下載頁或壓縮版）。
5. 轉逐字稿用 faster-whisper 的 `large-v3`（第一次執行會自動下載模型）。

### 雲端資料夾

- 素材：Google 雲端「第七感影片剪輯素材」（需維持「知道連結的人都能查看」，才能下載影片）
- 成品：同資料夾底下的「成品」子資料夾（id `1G9t80ewuoVaK74KBOiPiojHsbNsOlpJm`）。
  腳本等文字檔可透過 Google Drive 連接器直接存入；影片太大無法經過對話，
  改由下載頁（Artifact）上的按鈕在瀏覽器端上傳（單檔 16 MB 以內，需先輸出壓縮版）。

### 工具

需要 `ffmpeg`、Python 套件 `numpy`、`scipy`、`opencv-python-headless`、`noisereduce`、`qrcode[pil]`，
字型為 Noto Sans TC，臉部偵測模型為 OpenCV YuNet（`face_detection_yunet_2023mar.onnx`）。

```sh
# 0. 素材降噪（輸出到另一個資料夾，之後 --src 指到這裡）
python3 tools/denoise.py --src <素材資料夾> --out <降噪後資料夾> --config cuts/denoise.json

# 1. 句尾留氣口（依音訊調整切點，可重複執行）
python3 tools/breathe.py cuts/seg*.json --src <素材資料夾>

# 2. 自動構圖（同一人各段大小、位置一致）
python3 tools/autoframe.py cuts/seg*.json --src <素材資料夾> --model <yunet.onnx>

# 3. 片尾動畫（Logo、活動資訊、聯絡方式寫在 cuts/endcard.json）
python3 tools/endcard.py cuts/endcard.json --font <字型資料夾> -o output/endcard.mp4

# LINE 官方樣式 QR code（片尾用）
python3 tools/line_qr.py --url https://lin.ee/Q2k2s7M --color black --font <字型檔> -o assets/line_qr.png

# 封面（固定版型，每集換 cuts/cover_volXX.json）
python3 tools/cover.py cuts/cover_vol01.json --src <素材資料夾> --font <字型檔> -o output/cover_vol01.jpg

# 4. 輸出（可給多個剪輯清單，依序接成一支）
python3 tools/build_segment.py cuts/seg1_hook.json cuts/seg2_how.json cuts/seg3_why.json \
    cuts/seg4_feel.json cuts/seg5_use.json cuts/seg6_end.json \
    --src <降噪後資料夾> --font <字型資料夾> -o output/完整版.mp4

# 檢查每段響度是否一致（建議差距 2 dB 以內）
python3 tools/check_loudness.py output/完整版.mp4 cuts/seg1_hook.json cuts/seg2_how.json cuts/seg3_why.json cuts/seg4_feel.json cuts/seg5_use.json

# 5. 背景音樂（原創合成，無版權問題）並混音：講話時自動壓低，片尾浮上來
python3 tools/bgm.py --dur <成片秒數> --outro <片尾開始秒數> -o output/bgm.wav
python3 tools/mix_bgm.py output/完整版.mp4 output/bgm.wav -o output/完整版_配樂.mp4
```

剪輯清單欄位：`src` 素材檔、`in`/`out` 切點（秒）、`subs` 字幕（時間以片段開頭為 0）、
`frame` 裁切框（由 autoframe 產生）、`in0`/`out0` 加氣口前的原始切點、
`tail`/`lead` 氣口上限覆寫、`gain_db` 逐段音量微調、`card`/`dur` 純文字字卡、`no_overlay` 不放標題（片尾用）。
`style` 裡可設 `title`、`note`、`logo` 等常駐元素。
