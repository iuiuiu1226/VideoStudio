# VideoStudio

## 第七感｜BK 測試學員心得

腳本與分鏡在 `scripts/`（最新版為 v3），逐字稿在 `scripts/逐字稿_raw.txt`。

### 成片

| 版本 | 長度 | 用途 | 剪輯清單 |
|---|---|---|---|
| 完整版 v11（正式版，無配樂） | 93.5 秒 | Facebook、LINE | `cuts/seg1_hook.json` … `cuts/seg6_end.json` 依序接起來；配樂由使用者自行處理 |
| 完整版 v13（降噪改善） | 93.5 秒 | 同上 | 同 v11，`IMG_0632`（黃色毛衣）改用非穩態降噪（`cuts/denoise.json`），句間噪音少約 4 dB、字完整；配樂待選 |
| 完整版 v14（降噪加強） | 93.5 秒 | 同上 | 同 v13，`IMG_0632` 再加 RNNoise（混 70%）、看 RNNoise 判斷人聲的側鏈噪音門、收高頻嘶聲；講話時嘶聲少約 8 dB，全片逐字稿與 v13 相同 98%；目前下載頁的無配樂版，配樂待選 |
| 配樂版 v12（使用者不採用） | 93.5 秒 | 同上 | v11 加動感配樂 `assets/music/energetic_sport.mp3`（從 13 秒開始、`level_music.py` 拉平），`mix_bgm.py --rel -17 --no-duck --lufs -14`：配樂固定音量、比人聲低 17 dB，整支 -14 LUFS |
| 配樂版 v14＋S | 93.5 秒 | 同上 | v14 加配樂 S「放克銅管」`assets/music/funk_pop.mp3`（照使用者給的參考曲做的放克流行，從 0 秒開始、約 16 秒銅管進場；`level_music.py` 拉平），`mix_bgm.py --rel -19 --no-duck --lufs -14 --fade-out 2.5 --music-eq "equalizer=f=2200:t=q:w=1.0:g=-6,equalizer=f=1000:t=q:w=1.0:g=-4,equalizer=f=400:t=q:w=1.0:g=-2"`（放克的銅管、吉他在中頻，會蓋住黃色毛衣較小的人聲；讓出中頻＋小聲 2 dB 後，那段逐字稿相同度從 85% 回到 95%） |
| 配樂版 v14＋C | 93.5 秒 | 同上 | v14 加 105 拍新曲 C「拍擊貝斯」`assets/music/funk105_c.mp3`（從 0 秒開始、`level_music.py` 拉平），混音同配樂 S（`--rel -19`＋讓出中頻）；逐字稿與 v14 相同 95%、黃色毛衣段 91% |
| 配樂「保留1」 | — | — | 配樂 S 放慢到約 105 拍（`rubberband tempo=0.90`，音高不變）：`assets/music/keep1_funk_pop_105bpm.mp3`，使用者選定的速度，先保留；同速度新曲描述 `scripts/narration/music_prompt_funk105_*.txt` |
| 精簡版 | 討論中 | IG Reels、TikTok、YouTube Shorts | `cuts/short60.json`（舊版，暫停使用） |

段落：鉤子（龍是真的）→ 怎麼測出來的 → 肌肉連動潛意識 → 親身體驗 → 生活怎麼用 → 片尾動畫

## 第七感｜BK 測試生活應用

由主持人、講師分享 BK 測試在生活中的用法（學員本人的心得放「學員分享」系列）。
版面、片尾與學員分享相同，影片上方標題為「BK 測試｜生活應用」。

### VOL.01（`IMG_6532.MOV`，主持人課堂分享）

| 版本 | 長度 | 剪輯清單 |
|---|---|---|
| v3（無配樂，HDR 色調修正） | 91.5 秒 | `cuts/life01/seg1_hook.json` … `cuts/life01/seg5_end.json` 依序接起來 |
| 配樂版 v4 | 91.5 秒 | v3 加配樂 C「輕快放克」`assets/music/life01_light.mp3`（105 拍，從 0 秒開始、`level_music.py` 拉平），`mix_bgm.py --rel -16 --no-duck --lufs -14 --fade-out 2.5` 加讓出中頻的等化（同學員分享 VOL.01；使用者覺得 -19 太小聲，加大 3 dB）；逐字稿與 v3 相同 96%，遠處複訓段 98%（再加大到 -14 就開始吃字） |

段落：鉤子（直播賣的精品是真的嗎→很多是假的、為什麼要用身體測）→ 她怎麼學會的 →
學長姐舉手、「一堂課程可以讓那麼多人願意複訓」→ 片尾（與學員分享 VOL.01 相同）。
逐字稿在 `scripts/逐字稿_IMG_6532_raw.txt`；封面設定 `cuts/cover_life01.json`
（「直播買的精品／是真是假？」，副標「用身體就測得出來」，使用者從三個標題選定；冷白皮調色＋多格降雜點與銳利化，設定在 `prefilter`、`grade`）。

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
| 配樂版 v4 | 49 秒 | v3 加配樂 C「抖音節拍」`assets/music/tiktok_beat.mp3`（從 40 秒開始，避開 30–40 秒的休息段；`level_music.py` 拉平），`mix_bgm.py --rel -17 --no-duck --lufs -14` |

段落：前世今生、身邊的緣分 → 姊妹父母朋友，台下喊「寵物！」→「上輩子他是我的老婆或老公，這次有可能我當他的⋯」台下又喊「寵物！」（全場笑）→
都可以用能量測試測出來、也能測過去 → 學到這個技能可以回去自己測 → 片尾。逐字稿在 `scripts/逐字稿_IMG_6539_raw.txt`；封面設定 `cuts/cover_life02.json`（103.3 秒的畫面、拉遠讓頭小一點；「你家的寵物／上輩子是你老婆？」，副標「前世今生也測得出來」；原本膚色，只做降雜點與銳利化）。

- 搞笑元素只放在笑點：兩次台下喊「寵物！」彈出字＋貓掌、第二次時鏡頭推近、大笑時「哈哈哈」（`fx`）
- 主持人與手機距離一直變，大小用臉部追蹤平滑後逐格固定（`frame_keys`），音量用人聲頻段算出的音量曲線拉平（`gain_keys`），
  整支用線性響度（`style.loudness = "linear"`），笑聲比講話略大
- 降噪的噪音門改用絕對門檻（`gate_threshold`），以免把她較小聲的句子當成背景壓掉

## 第七感｜BK 測試課堂精華

講師在課堂上講觀念的片段（系列標題「BK 測試｜課堂精華」）。

### VOL.01（`IMG_6552.MOV`，講師：水結晶與正能量）

| 版本 | 長度 | 剪輯清單 |
|---|---|---|
| v1（無配樂） | 75.8 秒 | 開頭先講完江本勝的實驗結果，跟講師內容重複，使用者覺得穿插不順 |
| v2（無配樂） | 66.5 秒 | 開頭改拋問題、講師段落穿插動畫 |
| v3（無配樂） | 62.1 秒 | 交叉淡化轉場、穿插動畫移到字幕下方、結尾拿掉地球改人形善念／惡念 |
| v4（無配樂） | 63.0 秒 | 換上使用者提供的結晶圖、結晶旁不放星星、結尾多停並慢慢暗下來 |
| v5（無配樂） | 64.8 秒 | `cuts/class01/seg1_intro.json`、`seg2_water.json`、`seg3_outro.json`、`seg4_end.json`；書封換成使用者提供的 `IMG_1660.PNG`、結晶圓圖去掉原圖上緣白框、人形底色改深藍、最後一句「呢」尾音拉長 |
| v6（無配樂） | 65.7 秒 | 同上；開頭「有什麼關係呢？」的「呢」也拉長尾音（原本被切掉），字幕「我們就叫它正能量」改成「我們就叫它」，「正能量」交給下方放大的動畫字 |

段落：開頭拋問題（AI 旁白＋動畫，約 12 秒：這本書的作者做過水結晶實驗——到底是什麼實驗？水結晶跟能量有什麼關係？
上方標題「水結晶 × 能量」）→ 講師原段落（約 30 秒，字幕下方穿插：謝謝的結晶、煩死了的結晶、「正能量」、說好話／做好事／存善心）
→ 結尾延伸（約 15 秒：文字聲音念頭 → 人體六到七成是水 → 兩個人形，身體裡完整的結晶是善念、破碎的是惡念，
「是善念，還是惡念呢？」講完多停 2.6 秒並慢慢暗下來）→ 片尾。段落之間交叉淡化（build_segment 的 `xfade`）。

- 結晶圖：使用者放在雲端素材資料夾的 `IMG_1659.PNG`（「祈禱前／祈禱後的湖水結晶」對比圖），
  右半（x 680–1110, y 0–430）當完整結晶、左半（x 115–545, y 0–430）當破碎結晶，`life03_anim.py --good/--bad`；
  圖檔沒放進版控；裁切從第 12 列開始（原圖上緣 0–6 列是白框）
- 書封：使用者提供的 `IMG_1660.PNG`（《來自水的信息》，統一夢公園），`life03_anim.py --book`
- 最後一句「我們每天給出的，是善念，還是惡念呢？」：重配三次挑最慢的一次，不加快、不切尾音，「呢」單獨放慢 1.6 倍
  （`LINE_TEMPO`、`KEEP_TAIL`、`STRETCH_LAST`）；開頭「有什麼關係呢？」同樣不切尾音，整句加快 1.12 倍、「呢」放慢 1.8 倍
- 封面：標題 B「你每天給出的／是善念還是惡念？」（副標「從水結晶實驗看能量」），不放水結晶（IG 正方形會裁掉），
  畫面用講師有笑容的 25.0 秒（使用者從 23.4／25.0／29.2 三個笑容畫面選中間的），`cuts/cover_class01.json` →
  `output/BK課堂精華_VOL01_封面.jpg`；其他候選在 `cuts/cover_options/cover_class01_B_*.json`

- 配樂（使用者要「沉穩溫暖」）：三首 Lyria 候選 A 鋼琴弦樂 `class01_piano`、B 木吉他大提琴 `class01_guitar`、
  C 電鋼琴輕鼓 `class01_rhodes`（描述在 `scripts/narration/music_prompt_class01_*.txt`；前 70 秒人聲檢查都通過），先給 30 秒試聽待使用者選；
  三首都已先混好備用（`level_music.py` 拉平，`mix_bgm.py --rel -17 --no-duck --lufs -14 --fade-out 2.5`＋讓出中頻），
  分段逐字稿與無配樂版相同 94–100%
- 講師段落照原本順序剪，不重排；最後一句「那這關我們什麼事呢」依使用者要求刪掉；19.05–22.14 秒的口誤拿掉
- 拍攝時鏡頭一直推拉，用臉部追蹤把講師大小固定（臉高佔畫面 11%，`frame_keys`）；18–19 秒講師走到原畫面邊緣
- 降噪 `cuts/denoise.json` 的 `IMG_6552.MOV`（一般設定，空檔差距 24 → 42 dB，逐字稿不變）
- 旁白稿 `scripts/narration/life03_water_v2.txt`（Gemini TTS，女聲 Sulafat，加快 1.12 倍；「江本勝」配音稿寫「姜本勝／姜本聖」才唸得對），
  動畫 `tools/life03_anim.py`（開頭、結尾、講師段落的透明疊加層 `overlay1.mov`／`overlay2.mov`，用 build_segment 的 `overlay`）；
  書封、結晶照片取自投影片
- 江本勝的說法用中性寫法（「江本勝認為」），不寫「證明」；這類說法未獲主流科學認可
- 字幕「好的力量會把它弄成這個六角形」的「弄成」聽起來也像「揉成」，待使用者確認

## 短影音配音＋配樂流程（Gemini TTS＋Lyria）

稿子 → 配音 → 逐句檢查 → 配樂（已有就沿用）→ 合成 mp4，一行指令（新環境先跑一次 `sh tools/setup.sh`）：

```sh
tools/make_short.sh scripts/narration/test_3lines.txt scripts/narration/music_prompt_curious_warm.txt test3
```

**金鑰**：到 aistudio.google.com 建 API 金鑰，放在環境變數 `GEMINI_API_KEY`
（雲端環境：環境設定 → 網路密鑰，主機 `generativelanguage.googleapis.com`、header `x-goog-api-key`，
由網路代理自動加上金鑰，程式讀不到金鑰是正常的；自己的電腦：專案根目錄 `.env`，照 `.env.example`）。
不要寫進程式、不要上傳 git（`.env` 已在 `.gitignore`）。帳戶是預付制，要先在 AI Studio → Billing → Buy credits 儲值，
餘額 0 會回 HTTP 402。費用：80 秒旁白約台幣 1 元內；配樂一首約 0.08 美元。

| 步驟 | 工具 | 說明 |
|---|---|---|
| 配音 | `tools/voice_gemini.py` | Gemini TTS（`gemini-3.8-flash-tts`，預設男聲 Charon）。一行一句、一句一個 wav，唸錯用 `--only N` 只重配那句。風格說明寫在 `STYLE`：台灣口音、語速、語氣、只唸稿上的字 |
| 檢查 | `tools/check_voice.py` | 本機 faster-whisper 逐句辨識、跟稿子逐字比對（簡轉繁、去標點），列出唸錯／多字／漏字；逐字時間寫回 `lines.json` 給字幕對齊 |
| 配樂 | `tools/music_lyria.py` | Lyria（`lyria-3.5`，同一把金鑰）。英文描述寫風格、BPM、樂器、情緒走向，結尾 `Instrumental only, no vocals`。生成後自動檢查人聲，有就加 `_rejected` 淘汰；`--check 檔案` 可檢查任何音樂 |
| 合成 | `tools/narrate.py` | 每句剪頭尾空白、句間停頓 0.35 秒；字幕遇標點或 `|` 斷行；配樂循環、淡入淡出、比旁白低 18 dB；整支 -14 LUFS（兩段式 loudnorm）＋ alimiter 限幅 |

- 稿子格式：一行一句，`#` 開頭是註解；長句用 `|` 標字幕斷行（配音時會拿掉），斷在詞與詞之間
- 配樂人聲檢查：每 8 秒一段用 whisper 中英文各聽一次，「沒有人聲」機率低於 0.5 且不是常見幻聽字串
  （「感謝觀看」「字幕」「MING PAO」…）就算有人聲。實測純音樂全部通過，混進講話（與音樂一樣大）會被抓到
- 通過的配樂放 `assets/music/`，可以重複用在很多支影片；描述與檢查結果存在同名 `.json`

**授權注意（商用）**

- 不要用 F5-TTS 官方權重、Meta MusicGen 權重：授權是 CC-BY-NC，禁止商用
- 免費替代：微軟 Azure 語音免費層（F0，每月 50 萬字，台灣男聲 `zh-TW-YunJheNeural`）；
  本機開源可商用：BreezyVoice（聯發科，台灣口音）、Fun-CosyVoice3（Apache-2.0）
- 複製真人聲音要有本人書面同意；IG、YouTube 對逼真的 AI 聲音或影片有標示規定，上片時依平台規定勾選

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
