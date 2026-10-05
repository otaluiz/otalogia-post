"""
Recorte de sujeito com rembg (open-source, local ou nuvem: pip install rembg) + checagem de limpeza.

Uso: python recorte.py <foto.png> <saida_recorte.png>
Sai com código 0 e escreve o recorte só se o recorte for limpo; senão sai com 2 e explica.
Critérios (calibrados nos carrosséis de 2026-10):
- sujeito ocupa entre 4% e 70% do quadro (area_max ajustável; compor.py usa 85%) (nem migalha, nem foto inteira);
- uma peça principal: o maior componente opaco tem >= 85% da área opaca;
- borda nítida: pixels semitransparentes (alfa 20-235) <= 12% da área opaca.
"""
import sys

import numpy as np
from PIL import Image
from rembg import remove
from scipy import ndimage


def avaliar(rgba, area_max=0.70):
    a = np.asarray(rgba.split()[-1]).astype(int)
    opaco = a > 235
    area = opaco.mean()
    semi = ((a > 20) & (a <= 235)).sum() / max(opaco.sum(), 1)
    rot, n = ndimage.label(opaco)
    maior = np.bincount(rot.ravel())[1:].max() / max(opaco.sum(), 1) if n else 0
    motivos = []
    if not 0.04 <= area <= area_max:
        motivos.append(f"sujeito ocupa {area:.0%} do quadro")
    if maior < 0.85:
        motivos.append(f"recorte fragmentado ({n} peças, maior = {maior:.0%})")
    if semi > 0.12:
        motivos.append(f"borda borrada ({semi:.0%} semitransparente)")
    return motivos, {"area": round(area, 3), "pecas": int(n), "maior": round(float(maior), 3), "semi": round(float(semi), 3)}


if __name__ == "__main__":
    rgba = remove(Image.open(sys.argv[1]).convert("RGB"))
    motivos, m = avaliar(rgba)
    print("metricas:", m)
    if motivos:
        print("RECORTE SUJO:", "; ".join(motivos))
        sys.exit(2)
    rgba.save(sys.argv[2])
    print("OK:", sys.argv[2])
