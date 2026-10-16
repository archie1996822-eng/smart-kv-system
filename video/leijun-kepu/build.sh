#!/usr/bin/env bash
# 一键复现：TTS → 混音 → 渲染 → 合成。产物：out/leijun_kepu_9x16.mp4
set -euo pipefail
cd "$(dirname "$0")"
python3 tts.py
python3 audio.py
python3 render.py "$@"
