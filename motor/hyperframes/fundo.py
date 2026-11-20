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
if img.shape[:2] != alfa.shape[:2]:  # foto _orig inteira: mesmo corte cover do compor (centro) para casar com o recorte
    H, W = alfa.shape[:2]
    k = max(W / img.shape[1], H / img.shape[0])
    img = cv2.resize(img, (round(img.shape[1] * k), round(img.shape[0] * k)), interpolation=cv2.INTER_AREA)
    y0, x0 = (img.shape[0] - H) // 2, (img.shape[1] - W) // 2
    img = img[y0:y0 + H, x0:x0 + W]
h, w = img.shape[:2]
mask = cv2.dilate((alfa > 24).astype(np.uint8) * 255, np.ones((25, 25), np.uint8))
# inpaint em meia resolução (área grande fica mais suave e rápida) e devolve só onde havia sujeito
peq = cv2.inpaint(cv2.resize(img, (w // 2, h // 2)), cv2.resize(mask, (w // 2, h // 2)), 12, cv2.INPAINT_TELEA)
cheio = cv2.GaussianBlur(cv2.resize(peq, (w, h)), (0, 0), 6)
m = cv2.GaussianBlur(mask, (0, 0), 8)[:, :, None] / 255.0
cv2.imwrite(foto, (img * (1 - m) + cheio * m).astype(np.uint8))
