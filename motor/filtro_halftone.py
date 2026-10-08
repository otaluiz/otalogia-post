"""
Filtro "impresso halftone" (ref. post HALFTONE TEXTURE, aprovado 2026-10-06): retícula AM fina a 45° modulando a
luminância (média zero: o tom da foto se mantém), pretos levantados, leve dessaturação/aquecimento e grão.
O render.py aplica no slide CTA inteiro (letras incluídas) quando o tema.json tem "halftone_cta": true.

Uso: python filtro_halftone.py <entrada> [saida]   (sem saida = sobrescreve)
"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def halftone(im, cell=6, ang=45, forca=0.45, grao=0.035, seed=7):
    rgb = np.asarray(im.convert("RGB")).astype(float) / 255
    h, w = rgb.shape[:2]
    cell = cell * w / 1080
    lum = rgb @ [0.2126, 0.7152, 0.0722]
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    a = np.deg2rad(ang)
    u = (xx * np.cos(a) + yy * np.sin(a)) / cell
    v = (-xx * np.sin(a) + yy * np.cos(a)) / cell
    d = np.hypot(u - np.round(u), v - np.round(v)) / 0.7071          # 0 centro .. 1 canto da célula
    tela = np.clip((d ** 2 - (1 - lum)) * cell * 0.9 + 0.5, 0, 1)      # 1 = papel, 0 = tinta (ponto cresce na sombra)
    media = np.asarray(Image.fromarray((tela * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(cell))) / 255
    out = rgb * (1 + forca * (tela - media) * 1.6)[..., None]
    g = out @ [0.2126, 0.7152, 0.0722]
    out = out * 0.85 + g[..., None] * 0.15                              # dessatura um pouco
    out = 0.035 + out * 0.95 * np.array([1.0, 0.985, 0.95])             # pretos levantados, tinta quente
    out += np.random.default_rng(seed).normal(0, grao, (h, w))[..., None]
    res = Image.fromarray((out.clip(0, 1) * 255).astype("uint8"))
    return res.filter(ImageFilter.GaussianBlur(0.35 * w / 1080))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    halftone(Image.open(sys.argv[1])).save(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
    print("OK:", sys.argv[-1])
