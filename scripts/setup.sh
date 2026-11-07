#!/usr/bin/env bash
# Prepara un entorno en la nube para renderizar reels. Uso: bash scripts/setup.sh
set -e
command -v ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -qq ffmpeg)
command -v tesseract >/dev/null || (apt-get update -qq && apt-get install -y -qq tesseract-ocr)
pip install -q --break-system-packages kokoro-onnx soundfile opencv-python-headless pytesseract pillow numpy 2>/dev/null \
  || pip install -q kokoro-onnx soundfile opencv-python-headless pytesseract pillow numpy

DIR="${KOKORO_DIR:-$HOME/models}"
mkdir -p "$DIR"
URL=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s "$DIR/$f" ] || curl -sSL -o "$DIR/$f" "$URL/$f"
done

# efectos: si no están, se generan
ls assets/sonidos/*.wav >/dev/null 2>&1 || python3 scripts/generar_sonidos.py
echo "Listo. Modelos en $DIR"
