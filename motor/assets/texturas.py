"""
Gera as texturas do renderer (1080x1440), procedurais e determinísticas (seed fixa):
- papel-dobra.png: dobra vertical + horizontal + vinco diagonal + amassado + fibra (soft-light, 50% = neutro)
- halftone.png: retícula ink a 45° que cresce para o canto inferior direito (alfa, multiply)
- pano.png: trama de tecido com fios irregulares (soft-light), usada no T1b
- led-grade.png: grade reta de pontos redondos (passo 9px), alfa = brilho suave (máscara; a cor vem do CSS via mask-image)

Uso: python texturas.py   (escreve na pasta deste arquivo)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

AQUI = Path(__file__).parent
W, H = 1080, 1440
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(float)


def smooth_noise(scale, amp):
    n = rng.normal(0, 1, (H // scale + 2, W // scale + 2))
    im = Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype("uint8"))
    im = im.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale / 3))
    return (np.asarray(im) / 255 - 0.5) * amp


def fold(dist, side, width=180, shadow=0.16, light=0.10):
    d = np.abs(dist)
    face = np.where(dist * side > 0, -shadow * np.exp(-d / width), light * np.exp(-d / (width * 1.4)))
    crease = -0.22 * np.exp(-(dist / 1.6) ** 2) + 0.14 * np.exp(-((dist - 3) / 1.8) ** 2)
    return face + crease


def papel_dobra():
    v = np.full((H, W), 0.5)
    v += fold(xx - W * 0.48, 1)
    v += fold(yy - H * 0.56, -1, width=150, shadow=0.12, light=0.08)
    v += fold((xx - yy * 0.35) - W * 0.78, 1, width=90, shadow=0.06, light=0.04)
    v += smooth_noise(60, 0.10) + smooth_noise(14, 0.04) + rng.normal(0, 0.012, (H, W))
    Image.fromarray((v.clip(0, 1) * 255).astype("uint8")).save(AQUI / "papel-dobra.png")


def halftone(cell=10):
    ang = np.deg2rad(45)
    u = (xx * np.cos(ang) + yy * np.sin(ang)) / cell
    w = (-xx * np.sin(ang) + yy * np.cos(ang)) / cell
    dist = np.sqrt((u - np.round(u)) ** 2 + (w - np.round(w)) ** 2)
    t = np.clip(((xx / W) * 0.55 + (yy / H) * 0.75) - 0.55, 0, 1) ** 1.3
    r = 0.08 + 0.42 * t
    a = np.clip((r - dist) * cell * 1.2, 0, 1) * (t > 0.02)
    rgba = np.zeros((H, W, 4), "uint8")
    rgba[..., :3] = (17, 17, 17)
    rgba[..., 3] = (a * 255).astype("uint8")
    Image.fromarray(rgba).save(AQUI / "halftone.png")


def pano(p=4.0):
    weft = np.sin(xx * 2 * np.pi / p) * 0.5 + 0.5
    warp = np.sin(yy * 2 * np.pi / p) * 0.5 + 0.5
    over = (np.floor(xx / p) + np.floor(yy / p)) % 2
    c = np.where(over > 0, weft * 0.7 + warp * 0.3, warp * 0.7 + weft * 0.3)
    c = 0.5 + (c - 0.5) * 0.35 + smooth_noise(30, 0.08) + smooth_noise(6, 0.05) + rng.normal(0, 0.02, (H, W))
    for _ in range(60):
        y0 = rng.integers(0, H)
        c[y0:y0 + 2, :] += rng.uniform(-0.05, 0.05)
    Image.fromarray((c.clip(0, 1) * 255).astype("uint8")).save(AQUI / "pano.png")


def led_grade(passo=9):
    """Máscara (alfa) da textura LED dos slides só de texto. Brilho baixo (~0.10) no miolo, onde fica o texto, e
    mais forte nas bordas longe do bloco (canto inferior direito e topo direito). Pontos chapados em 8 níveis."""
    def blob(cx, cy, r):
        return np.exp(-(((xx - cx) / r) ** 2 + ((yy - cy) / (r * 1.1)) ** 2))
    g = 0.10 + 0.75 * blob(W * 1.02, H * 1.0, 430) + 0.45 * blob(W * 1.0, H * 0.02, 300) + 0.30 * blob(0, H * 1.0, 260)
    g += 0.04 * np.sin(yy / 160.0 + xx / 380.0)
    g = np.round(g.clip(0, 1) * 7) / 7
    cel = Image.fromarray((g * 255).astype("uint8")).resize((W // passo, H // passo), Image.BOX).resize((W, H), Image.NEAREST)
    g = np.asarray(cel) / 255
    dy, dx = (yy % passo) - (passo - 1) / 2, (xx % passo) - (passo - 1) / 2
    ponto = np.clip((0.42 - np.sqrt(dx ** 2 + dy ** 2) / passo) * passo * 0.9, 0, 1)
    rgba = np.full((H, W, 4), 255, "uint8")
    rgba[..., 3] = (ponto * g * 255).astype("uint8")
    Image.fromarray(rgba).save(AQUI / "led-grade.png")


if __name__ == "__main__":
    led_grade()
    papel_dobra()
    halftone()
    pano()
    print("OK: texturas em", AQUI)
