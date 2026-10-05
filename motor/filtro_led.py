"""
Filtro "painel de LED": duotone/gradient map nas cores da marca + retícula de pontos em grade reta,
como a referência #42 do banco do aidealab. Aplica na FOTO (capa/CTA), antes do recorte, para o
sujeito recortado sair com a mesma textura.

Uso: python filtro_led.py <entrada> <saida> [--mapa "#05081A,#1B2BD1,#3D6BFF,#6EC9F7,#F4FBFF"] [--passo 9] [--forca 1.0]
- mapa: cores do escuro para o claro (gradient map)
- passo: distância entre os pontos em px (no 1080x1440)
- forca: 0 = só o duotone, 1 = pontos bem marcados
- gama: < 1 clareia as sombras (ex.: 0.65), 1 = neutro
"""
import argparse

import numpy as np
from PIL import Image, ImageFilter


def hex2rgb(h):
    h = h.strip().lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def gradient_map(lum, cores):
    pos = np.linspace(0, 1, len(cores))
    out = np.zeros(lum.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(lum, pos, [k[c] for k in cores])
    return out


def led(im, cores, passo=9, forca=1.0, gama=1.0):
    rgb = np.asarray(im.convert("RGB")).astype(float) / 255
    lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])
    lum = np.clip((lum - np.percentile(lum, 2)) / max(np.percentile(lum, 98) - np.percentile(lum, 2), 1e-6), 0, 1)
    lum = lum ** gama                           # gama < 1 clareia as sombras (desenho mais visível)
    lum = lum * lum * (3 - 2 * lum)            # curva S: mais contraste, tons mais chapados
    lum = np.round(lum * 7) / 7                 # posteriza em 8 níveis, como painel de LED
    h, w = lum.shape
    # amostra a cor de cada célula (média) para os pontos ficarem "chapados", como LED
    hs, ws = h // passo, w // passo
    cel = Image.fromarray((lum * 255).astype("uint8")).resize((ws, hs), Image.BOX).resize((w, h), Image.NEAREST)
    lum_c = np.asarray(cel).astype(float) / 255
    cor = gradient_map(lum_c, cores)
    base = gradient_map(lum, cores)
    # máscara de pontos: círculo em cada célula, raio ~42% do passo
    yy, xx = np.mgrid[0:h, 0:w]
    dy = (yy % passo) - (passo - 1) / 2
    dx = (xx % passo) - (passo - 1) / 2
    d = np.sqrt(dx ** 2 + dy ** 2) / passo
    ponto = np.clip((0.42 - d) * passo * 0.9, 0, 1)[..., None]
    fundo = cores[0] * 0.45 + base * 0.55          # entre os pontos: escuro com um pouco da imagem
    led_img = cor * ponto + fundo * (1 - ponto)
    out = base * (1 - forca) + led_img * forca
    res = Image.fromarray(np.clip(out, 0, 255).astype("uint8"))
    return res.filter(ImageFilter.UnsharpMask(1, 40, 2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("saida")
    ap.add_argument("--mapa", default="#05081A,#1B2BD1,#3D6BFF,#6EC9F7,#F4FBFF")
    ap.add_argument("--passo", type=int, default=9)
    ap.add_argument("--forca", type=float, default=1.0)
    ap.add_argument("--gama", type=float, default=1.0)
    a = ap.parse_args()
    cores = [hex2rgb(c) for c in a.mapa.split(",")]
    led(Image.open(a.entrada), cores, a.passo, a.forca, a.gama).save(a.saida)
    print("OK:", a.saida)
