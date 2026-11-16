#!/usr/bin/env bash
# Regenera todo: voz, música, vídeos, miniaturas, metadatos y marca del canal.
# Requisitos: ffmpeg, Node con Playwright + Chromium, Python 3 con piper-tts y numpy.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
VOICE=pipeline/voices/es_ES-davefx-medium.onnx
BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx
mkdir -p pipeline/voices
[ -f "$VOICE" ] || curl -fsSL -o "$VOICE" "$BASE"
[ -f "$VOICE.json" ] || curl -fsSL -o "$VOICE.json" "$BASE.json"
npm install --silent
IDS=$($PY -c "import json;print(' '.join(v['id'] for v in json.load(open('content/videos.json'))['videos']))")
$PY pipeline/tts.py
$PY pipeline/music.py
for i in $IDS; do node pipeline/render.js "$i" --thumb; done
printf '%s\n' $IDS | xargs -P "${JOBS:-4}" -I{} node pipeline/render.js {}
$PY pipeline/meta.py
node pipeline/brand.js
