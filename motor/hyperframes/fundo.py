"""Placa de fundo para o parallax: apaga o sujeito da foto (inpaint do OpenCV na área do recorte, dilatada) para o
recorte poder andar mais rápido que a foto sem deixar um "fantasma" atrás. Só mexe na cópia em motion/img.

Uso: python fundo.py <foto.png> <recorte.png>   (sobrescreve <foto.png>)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".vendor_cv4"))
import cv2  # noqa: E402
import numpy as np  # noqa: E402

foto, rec = sys.argv[1], sys.argv[2]
img = cv2.imread(foto)
alfa = cv2.imread(rec, cv2.IMREAD_UNCHANGED)[:, :, 3]
h, w = img.shape[:2]
mask = cv2.dilate((alfa > 24).astype(np.uint8) * 255, np.ones((25, 25), np.uint8))
# inpaint em meia resolução (área grande fica mais suave e rápida) e devolve só onde havia sujeito
peq = cv2.inpaint(cv2.resize(img, (w // 2, h // 2)), cv2.resize(mask, (w // 2, h // 2)), 12, cv2.INPAINT_TELEA)
cheio = cv2.GaussianBlur(cv2.resize(peq, (w, h)), (0, 0), 6)
m = cv2.GaussianBlur(mask, (0, 0), 8)[:, :, None] / 255.0
cv2.imwrite(foto, (img * (1 - m) + cheio * m).astype(np.uint8))
