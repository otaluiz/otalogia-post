#!/usr/bin/env bash
# Prepara um ambiente Linux limpo (rotina na nuvem) para gerar carrosséis do otalogia.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install -q playwright pillow numpy scipy "rembg[cpu]"
python -m playwright install --with-deps chromium
# compor.py precisa dos cascades Haar do OpenCV 4 (o 5 não traz mais)
[ -d motor/.vendor_cv4/cv2 ] || python -m pip install -q --target motor/.vendor_cv4 opencv-python-headless==4.10.0.84
# baixa o modelo do rembg uma vez (primeira chamada demora)
python -c "from rembg import new_session; new_session('u2net')"
echo "setup ok"
