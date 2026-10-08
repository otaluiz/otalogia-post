"""
Filtro "quadro-negro" (aprovado 2026-10-08, na cor da marca): marcas de giz apagado (arcos borrados do apagador),
pó de giz, letras claras com falhas finas de giz e grão. A cor do fundo do slide é mantida. Determinístico (seed fixa).
Aplicado no slide 3 inteiro quando ele é só de texto.

Uso: python filtro_quadro.py <entrada> [saida]   (sem saida = sobrescreve)
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _manchas(rng, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for _ in range(14):
        cx, cy, r = rng.uniform(-200, w + 200), rng.uniform(-200, h + 200), rng.uniform(250, 700)
        a0 = rng.uniform(0, 360)
        d.arc([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], a0, a0 + rng.uniform(40, 140),
              fill=int(rng.uniform(40, 110)), width=int(rng.uniform(60, 160)))
    im = im.filter(ImageFilter.GaussianBlur(28))
    n = Image.fromarray((rng.random((h // 8, w // 8)) * 255).astype("uint8")).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    m = np.asarray(im) / 255 * (0.55 + 0.9 * np.asarray(n) / 255)
    nuvem = np.asarray(Image.fromarray((rng.random((h // 40, w // 40)) * 255).astype("uint8")).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))) / 255
    return np.clip(m * 0.9 + (nuvem - 0.5).clip(0) * 0.25, 0, 1)


def quadro(im, seed=5):
    rng = np.random.default_rng(seed)
    a = np.asarray(im.convert("RGB")).astype(float) / 255
    h, w = a.shape[:2]
    texto = (a @ [0.2126, 0.7152, 0.0722]) > 0.55  # letras e marca-texto claros = giz
    po = (rng.random((h, w)) > 0.985) * rng.uniform(0.05, 0.25, (h, w))
    giz = np.asarray(Image.fromarray((po * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.7))) / 255
    camada = _manchas(rng, w, h) * 0.34 + giz
    a = 1 - (1 - a) * (1 - camada[..., None])  # screen: pó branco sobre a lousa
    falha = np.asarray(Image.fromarray((rng.random((h, w)) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.9))) / 255
    a = a * np.where(texto, 0.72 + 0.34 * falha, 1)[..., None]
    a += rng.normal(0, 0.018, (h, w))[..., None]
    return Image.fromarray((a.clip(0, 1) * 255).astype("uint8"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    quadro(Image.open(sys.argv[1])).save(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
