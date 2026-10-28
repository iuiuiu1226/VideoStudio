#!/bin/sh
# 短影音配音＋配樂一鍵流程：稿子 → Gemini TTS 配音 → 逐句檢查 → Lyria 配樂（已有就沿用）→ 合成 mp4
#
# 用法：
#   tools/make_short.sh <稿子.txt> <配樂描述.txt> <輸出名稱> [字型資料夾]
#   例：tools/make_short.sh scripts/narration/test_3lines.txt scripts/narration/music_prompt_curious_warm.txt test3
#
# 需要 GEMINI_API_KEY（環境變數或專案根目錄的 .env）。中間檔在 work/<輸出名稱>/，成品在 output/<輸出名稱>.mp4。
# 配樂檔名取自描述檔名（music_prompt_xxx.txt → assets/music/xxx.mp3），做好一首可以重複用。
set -e
cd "$(dirname "$0")/.."
SCRIPT=$1
PROMPT=$2
NAME=$3
FONT=${4:-assets/fonts}
[ -n "$NAME" ] || { echo "用法：tools/make_short.sh <稿子.txt> <配樂描述.txt> <輸出名稱> [字型資料夾]"; exit 1; }

MUSIC_NAME=$(basename "$PROMPT" .txt | sed 's/^music_prompt_//')
MUSIC=$(ls assets/music/"$MUSIC_NAME".mp3 assets/music/"$MUSIC_NAME".wav 2>/dev/null | head -1 || true)

python3 tools/voice_gemini.py "$SCRIPT" --out "work/$NAME/vo"
python3 tools/check_voice.py "work/$NAME/vo"

if [ -z "$MUSIC" ]; then
  python3 tools/music_lyria.py "$(cat "$PROMPT")" --name "$MUSIC_NAME" -o assets/music
  MUSIC=$(ls assets/music/"$MUSIC_NAME".mp3 assets/music/"$MUSIC_NAME".wav 2>/dev/null | head -1 || true)
  [ -n "$MUSIC" ] || { echo "配樂有人聲被淘汰了，請再跑一次（會重新生成）或改描述"; exit 1; }
fi

python3 tools/narrate.py "work/$NAME/vo" --music "$MUSIC" --font "$FONT" -o "output/$NAME.mp4"
