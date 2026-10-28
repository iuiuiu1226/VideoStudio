#!/bin/sh
# 新環境準備（新的雲端工作階段或新電腦第一次用）：Python 套件、字型、臉部偵測模型
# 用法：sh tools/setup.sh
set -e
cd "$(dirname "$0")/.."
pip install -q numpy scipy opencv-python-headless noisereduce "qrcode[pil]" zxing-cpp faster-whisper gdown \
    librosa opencc-python-reimplemented
mkdir -p assets/fonts assets/models
[ -f assets/fonts/NotoSansTC.ttf ] || curl -sSL -o assets/fonts/NotoSansTC.ttf \
    "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
[ -f assets/models/face_detection_yunet_2023mar.onnx ] || curl -sSL -o assets/models/face_detection_yunet_2023mar.onnx \
    "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx"
echo "準備完成：字型在 assets/fonts/，模型在 assets/models/（faster-whisper large-v3 第一次執行時會自動下載）"
