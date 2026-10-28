# VideoStudio

## 第七感｜BK 測試學員心得

腳本與分鏡在 `scripts/`（最新版為 v3），逐字稿在 `scripts/逐字稿_raw.txt`。

### 成片

| 版本 | 長度 | 用途 | 剪輯清單 |
|---|---|---|---|
| 完整版 v11（正式版，無配樂） | 93.5 秒 | Facebook、LINE | `cuts/seg1_hook.json` … `cuts/seg6_end.json` 依序接起來；配樂由使用者自行處理 |
| 精簡版 | 討論中 | IG Reels、TikTok、YouTube Shorts | `cuts/short60.json`（舊版，暫停使用） |

段落：鉤子（龍是真的）→ 怎麼測出來的 → 肌肉連動潛意識 → 親身體驗 → 生活怎麼用 → 片尾動畫

## 第七感｜BK 測試生活應用

由主持人、講師分享 BK 測試在生活中的用法（學員本人的心得放「學員分享」系列）。
版面、片尾與學員分享相同，影片上方標題為「BK 測試｜生活應用」。

### VOL.01（`IMG_6532.MOV`，主持人課堂分享）

| 版本 | 長度 | 剪輯清單 |
|---|---|---|
| v3（無配樂，HDR 色調修正） | 91.5 秒 | `cuts/life01/seg1_hook.json` … `cuts/life01/seg5_end.json` 依序接起來 |

段落：鉤子（直播賣的精品是真的嗎→很多是假的、為什麼要用身體測）→ 她怎麼學會的 →
學長姐舉手、「一堂課程可以讓那麼多人願意複訓」→ 片尾（與學員分享 VOL.01 相同）。
逐字稿在 `scripts/逐字稿_IMG_6532_raw.txt`；封面設定 `cuts/cover_life01.json`
（「直播賣的精品／測完很多是假的」，副標「用身體測出真假跟好壞」）。

- 字幕不寫平台名稱：「蝦皮」「臉書」改成「某購物平台」「某社群平台」（口白不變）
- 素材是 4K，主畫面三段共用同一個裁切框（約 1.35 倍），背景不動、只有人在走
- 「它會不會是一個好課程」那句拍攝時鏡頭有拉近，用 `frame_keys` 逐格補償，人物大小不變
- 「一堂課程，可以讓那麼多人願意複訓」聲音先進，畫面停在鏡頭掃過全場舉手（`v_in`）
- 降噪：一般設定 `IMG_6532.MOV`；她走到遠處的複訓段落用溫和設定 `IMG_6532_soft.MOV`
  （素材做一個同內容、檔名加 `_soft` 的連結，兩個都放進 `--src` 資料夾後一起降噪）

### VOL.02（`IMG_6539.MOV`，主持人：前世今生）

| 版本 | 長度 | 剪輯清單 |
|---|---|---|
| v3（無配樂） | 49 秒 | `cuts/life02/seg1_joke.json`、`cuts/life02/seg2_test.json`、`cuts/life02/seg3_end.json` |

段落：前世今生、身邊的緣分 → 姊妹父母朋友，台下喊「寵物！」→「上輩子他是我的老婆或老公，這次有可能我當他的⋯」台下又喊「寵物！」（全場笑）→
都可以用能量測試測出來、也能測過去 → 學到這個技能可以回去自己測 → 片尾。逐字稿在 `scripts/逐字稿_IMG_6539_raw.txt`。

- 搞笑元素只放在笑點：兩次台下喊「寵物！」彈出字＋貓掌、第二次時鏡頭推近、大笑時「哈哈哈」（`fx`）
- 主持人與手機距離一直變，大小用臉部追蹤平滑後逐格固定（`frame_keys`），音量用人聲頻段算出的音量曲線拉平（`gain_keys`），
  整支用線性響度（`style.loudness = "linear"`），笑聲比講話略大
- 降噪的噪音門改用絕對門檻（`gate_threshold`），以免把她較小聲的句子當成背景壓掉

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
- 成品：同資料夾底下的「成品」子資料夾（id `1tAapoJCH3AXD3qeVh-ilhmJWmHyis_WZ`）。
  腳本等文字檔可透過 Google Drive 連接器直接存入；影片太大無法經過對話，
  改由下載頁（Artifact）上的按鈕在瀏覽器端上傳（單檔 16 MB 以內，需先輸出壓縮版）。

### HDR 素材

iPhone 預設拍 HDR（HLG、BT.2020，例如 `IMG_6532`、`IMG_6539`）。`tools/build_segment.py` 與 `tools/cover.py`
會自動偵測，用 mobius 色調映射（亮度基準 600 nits）轉成一般 SDR／BT.709；沒轉的話畫面會偏亮、偏淡。
學員分享 VOL.01 的素材本來就是 SDR，不受影響。

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

# 5. 背景音樂並混音：講話時自動壓低，片尾浮上來
#    （正式版 v11 不放配樂。以下為曾試過的做法，供之後參考）
#    v13 試做版用 Pixabay「Clockwork Pulse」（trangiahung159，117 BPM、G 小調），
#    從 24.03 秒的小節起點開始，讓曲子自然的結尾落在片尾；音樂響度先調到 -18 LUFS，
#    再用 tools/level_music.py 拉平段落音量（--keep-tail 1.5），
#    混音參數 --no-duck --music-db -18.1 --music-eq "equalizer=f=2200:t=q:w=1.0:g=-5,equalizer=f=1000:t=q:w=1.2:g=-3"
#    （音樂固定音量、不隨人聲忽大忽小，約比人聲低 18 dB，當單純的背景）
#    也可用原創合成：tools/bgm.py、tools/bgm_bright.py、tools/bgm_reveal.py
python3 tools/bgm.py --dur <成片秒數> --outro <片尾開始秒數> -o output/bgm.wav
python3 tools/mix_bgm.py output/完整版.mp4 output/bgm.wav -o output/完整版_配樂.mp4
```

剪輯清單欄位：`src` 素材檔、`in`/`out` 切點（秒）、`subs` 字幕（時間以片段開頭為 0）、
`frame` 裁切框（由 autoframe 產生）、`frame_keys` 逐格裁切框（`t` 為素材秒數，之間線性內插，用來補償拍攝時的推拉鏡頭）、`v_in` 畫面改取自這個時間點（聲音仍從 `in` 開始）、`fx` 特效字（素材秒數，可含 ASS 動畫標籤）、`gain_keys` 段落內音量曲線、`auto_gain` 設 false 時不自動對齊音量、`in0`/`out0` 加氣口前的原始切點、
`tail`/`lead` 氣口上限覆寫、`gain_db` 逐段音量微調、`card`/`dur` 純文字字卡、`no_overlay` 不放標題（片尾用）。
`style` 裡可設 `title`、`note`、`logo` 等常駐元素。
