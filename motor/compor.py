"""
compor.py — composição em camadas para os slides com foto (capa, slide 2 e CTA) de um carrossel.

Uso: python compor.py <carrossel.json ...> [--led capa,cta,slide2] [--sem-recorte]

Para cada slide 1, 2 e último com `imagem`:
1. Foto: usa `<nome>_orig.png` ao lado do JSON, se existir (foto inteira, o sujeito nunca encolhe); senão a própria `imagem`.
   Redimensiona por cover para 1080x1440 se preciso. `--led` aplica filtro_led.led nos slides listados
   (grava `<nome>_led.png`); o alfa do recorte sai da foto limpa, ANTES do filtro, e o RGB da foto filtrada.
2. Recorte (rembg) só se limpo: recorte.avaliar com área máxima 0.85. Limpo → grava `<nome>_recorte.png` e define
   `recorte`. Sujo (ou --sem-recorte) → sem recorte (foto + texto; T1b vira T1) e o motivo vai para o log.
3. Máscara do sujeito -> `sujeito.caixa` e `sujeito.cabeca` (faixa do topo da máscara: 22% da altura, largura dos pixels
   da faixa, +4%); rostos por Haar (frontal, perfil, perfil espelhado; +15%) -> `sujeito.rostos` (rosto do próprio sujeito
   recortado já está em `cabeca`, então sai da lista). Nenhum texto pode cobrir cabeça nem rosto.
4. Escolhe `bloco` {y, alinhar, largura}: y em 200..1000 (passo 100) x esquerda/direita x largura 936/720/560.
   Rejeita: bloco que toca cabeça/rosto (+24u), fora de 190..1280 (meta em y<150, rodapé em y>1318), display com mais de 40% sob o
   sujeito (precisa ficar >= 60% visível). Pontua: agitação da imagem (Sobel médio na área visível do bloco), display
   encolhido, e, sem recorte, sobreposição com o sujeito. Com recorte, sobrepor 10-35% do display ganha bônus
   (profundidade). No T4 o bloco inclui a pill (+200u).
Slides só de texto: `textura: "led"` nos de `lista` e no de conclusão (último texto antes do CTA).
Guarda carrossel.json.bak uma vez (o original; re-rodar parte dele). Ajustes manuais que sobrevivem a re-rodar:
`sujeito.rostos_manual` (caixas extras), `sujeito.rostos_so_manual: true` (ignora o Haar), `sujeito.cabeca_manual` (caixa da cabeça) e `bloco.manual: true` (bloco mantido).
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

from filtro_led import hex2rgb, led
from recorte import avaliar

# OpenCV 5.x não traz mais os cascades Haar: usa .vendor_cv4 (pip install --target .vendor_cv4 opencv-python-headless==4.10.0.84)
_v = Path(__file__).resolve().parent / ".vendor_cv4"
if _v.exists():
    sys.path.insert(0, str(_v))

W, H = 1080, 1440
MAPA_LED = "#05081A,#1B2BD1,#3D6BFF,#6EC9F7,#F4FBFF"


def carregar(p):
    im = Image.open(p).convert("RGB")
    if im.size != (W, H):  # cover + corte central (nunca encolhe o sujeito além do necessário)
        k = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        l, t = (im.width - W) // 2, (im.height - H) // 2
        im = im.crop((l, t, l + W, t + H))
    return im


def mascara(rgba):
    a = np.asarray(rgba.split()[-1]) > 128
    rot, n = ndimage.label(a)
    if not n:
        return a
    return rot == (np.argmax(np.bincount(rot.ravel())[1:]) + 1)


def caixa_cabeca(m):
    ys, xs = np.where(m)
    if not len(ys):
        return None, None
    y0, y1 = ys.min(), ys.max()
    banda = xs[ys <= y0 + 0.22 * (y1 - y0)]
    bx0, bx1, by1 = banda.min(), banda.max(), y0 + 0.22 * (y1 - y0)
    px, py = 0.04 * (bx1 - bx0), 0.04 * (by1 - y0)
    cab = [bx0 - px, y0 - py, bx1 + px, by1 + py]
    return [int(v) for v in (xs.min(), y0, xs.max(), y1)], [int(max(0, cab[0])), int(max(0, cab[1])), int(min(W, cab[2])), int(min(H, cab[3]))]


def rostos_haar(im):
    """Haar frontal + perfil (e perfil espelhado). Cada rosto +15%. Estilizados/3D escapam: revisão visual."""
    import cv2 as cv
    g = cv.cvtColor(np.asarray(im), cv.COLOR_RGB2GRAY)
    g = cv.equalizeHist(g)
    achados = []
    for nome, flip in (("haarcascade_frontalface_default.xml", False), ("haarcascade_profileface.xml", False),
                       ("haarcascade_profileface.xml", True)):
        c = cv.CascadeClassifier(cv.data.haarcascades + nome)
        gg = cv.flip(g, 1) if flip else g
        for x, y, w, h in c.detectMultiScale(gg, 1.1, 6, minSize=(70, 70)):
            if flip:
                x = W - x - w
            achados.append([x, y, x + w, y + h])
    out = []
    for b in achados:
        w, h = b[2] - b[0], b[3] - b[1]
        b = [max(0, b[0] - .15 * w), max(0, b[1] - .15 * h), min(W, b[2] + .15 * w), min(H, b[3] + .15 * h)]
        for o in out:  # funde duplicatas
            if cruza(b, o) and inter_area(b, o) > .3 * min(area(b), area(o)):
                o[:] = [min(o[0], b[0]), min(o[1], b[1]), max(o[2], b[2]), max(o[3], b[3])]
                break
        else:
            out.append(b)
    return [[int(v) for v in b] for b in out]


def area(b): return max(0, b[2] - b[0]) * max(0, b[3] - b[1])
def cruza(a, b, m=0): return a[0] < b[2] + m and a[2] > b[0] - m and a[1] < b[3] + m and a[3] > b[1] - m
def inter_area(a, b): return area([max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])])


def _limpo(t):
    return t.replace("[", "").replace("]", "").replace("{", "").replace("}", "")


def estimar(s, larg, fs0):
    """Geometria do bloco em u, relativa ao topo do bloco (mesma regra de encolhimento do JS):
    fs, linhas do display [(texto, w, y0, y1)], emocao (w, y0, y1) ou None, h total e h da parte à frente (cta/corpo)."""
    disp = [_limpo(l) for l in (s.get("display") or [])]
    mx = max((len(l) for l in disp), default=1)
    fs = min(fs0, larg / (0.64 * mx))
    dh = 0.9 * fs
    e = s.get("emocao")
    emo = None
    if e:
        ls = [_limpo(x) for x in e["texto"].split(" / ")]
        el = max(len(x) for x in ls)
        efs = min(fs * 1.1, larg / (0.38 * el))
        emo = (el * 0.38 * efs, len(ls) * 0.95 * efs)
    y = 0.0
    eg = None
    if emo and e["posicao"] == "antes":
        eg = (emo[0], y, y + emo[1]); y += emo[1] + 0.1 * fs
    linhas = []
    for l in disp:
        linhas.append((l, len(l) * 0.64 * fs, y, y + dh)); y += dh
    if emo and e["posicao"] != "antes":
        y += 0.14 * fs
        eg = (emo[0], y, y + emo[1]); y += emo[1]
    f0 = y
    if s.get("corpo"):
        y += 40 + 41 * (1 + len(s["corpo"]) // 55)
    if s.get("cta"):
        y += 200
    return {"fs": fs, "linhas": linhas, "emo": eg, "h": y, "frente0": f0, "w": max([w for _, w, _, _ in linhas] + ([eg[0]] if eg else []))}


def escolher(s, template, fs0, mask, sob, cab, rostos, recorte, propr=()):
    ii_s = np.pad(np.cumsum(np.cumsum(sob * (~mask if recorte else 1), 0), 1), ((1, 0), (1, 0)))
    ii_c = np.pad(np.cumsum(np.cumsum((~mask if recorte else np.ones_like(mask)).astype(float), 0), 1), ((1, 0), (1, 0)))
    ii_m = np.pad(np.cumsum(np.cumsum(mask.astype(float), 0), 1), ((1, 0), (1, 0)))

    def soma(ii, b):
        x0, y0, x1, y1 = [int(round(v)) for v in b]
        x0, x1, y0, y1 = max(0, x0), min(W, x1), max(0, y0), min(H, y1)
        if x1 <= x0 or y1 <= y0:
            return 0.0
        return ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]

    todos = ([cab] if cab else []) + list(rostos) + list(propr)
    # display atrás do sujeito pode passar pela cabeça do recorte (a cabeça fica por cima); texto à frente (emocao/pill) não:
    # o JS desloca, então aqui é só penalidade. Sem recorte, o bloco inteiro evita cabeça e rostos.
    melhor = None
    for larg in (936, 720, 560):
        g = estimar(s, larg, fs0)
        fs = g["fs"]
        for y in range(200, 1001, 100):
            for al in ("esquerda", "direita"):
                if y < 190 or y + g["h"] > 1280:
                    continue
                X = (lambda w: 72) if al == "esquerda" else (lambda w: 1008 - w)
                rd = []  # retângulos do display (por linha) e das palavras
                for txt, w, y0, y1 in g["linhas"]:
                    rd.append(([X(w), y + y0, X(w) + w, y + y1], txt))
                fr = []  # parte à frente: emoção + corpo/cta
                if g["emo"]:
                    w, y0, y1 = g["emo"]; fr.append([X(w), y + y0, X(w) + w, y + y1])
                if g["h"] > g["frente0"]:
                    fr.append([72 if al == "esquerda" else 1008 - 400, y + g["frente0"], (72 if al == "esquerda" else 1008) + (400 if al == "esquerda" else 0), y + g["h"]])
                if any(cruza(b, f, 24) for b, _ in rd for f in rostos + ([] if recorte else list(propr) + ([cab] if cab else []))):
                    continue
                pen = 0.0
                if any(cruza(b, f, 24) for b in fr for f in todos):
                    if recorte:
                        pen += 0.6
                    else:
                        continue
                # visibilidade do display atrás do sujeito: por palavra (nenhuma palavra > 12% coberta)
                cov_max, cov_tot, atot = 0.0, 0.0, 0.0
                for b, txt in rd:
                    lw = b[2] - b[0]
                    pos = 0
                    for palavra in txt.split(" "):
                        a = b[0] + lw * pos / max(len(txt), 1)
                        z = b[0] + lw * (pos + len(palavra)) / max(len(txt), 1)
                        wb = [a, b[1] + 0.05 * (b[3] - b[1]), z, b[3] - 0.15 * (b[3] - b[1])]  # altura das maiúsculas
                        c = soma(ii_m, wb) / max(area(wb), 1)
                        cov_max = max(cov_max, c)
                        cov_tot += soma(ii_m, wb); atot += area(wb)
                        pos += len(palavra) + 1
                cov = cov_tot / max(atot, 1)
                if recorte and (cov_max > 0.12 or cov > 0.25):
                    continue
                bb = [72 if al == "esquerda" else 1008 - g["w"], y, (72 if al == "esquerda" else 1008) , y + g["h"]]
                bb = [bb[0], y, bb[0] + g["w"], y + g["h"]]
                vis = soma(ii_c, bb)
                busy = (soma(ii_s, bb) / max(vis, 1)) / 40.0
                sc = busy + pen + 0.8 * (1 - fs / fs0)
                if recorte:
                    sc -= 0.15 * min(cov, 0.35) / 0.35 if cov >= 0.10 else 0
                else:
                    sc += 1.5 * soma(ii_m, bb) / max(area(bb), 1)
                sc += 0.02 * (al == "direita") + 0.0003 * y
                if melhor is None or sc < melhor[0]:
                    melhor = (sc, y, al, larg, round(busy, 2), round(cov, 2), round(fs))
    return melhor


_sessao = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json", nargs="+", help="um ou mais carrossel.json (compartilham --led e --sem-recorte)")
    ap.add_argument("--led", default="")
    ap.add_argument("--sem-recorte", action="store_true")
    a = ap.parse_args()
    for j in a.json:
        print(f"== {j}")
        compor(Path(j).resolve(), a)


def compor(jp, a):
    pasta = jp.parent
    bak = Path(str(jp) + ".bak")
    atual = json.loads(jp.read_text(encoding="utf-8"))
    if not bak.exists():
        shutil.copy(jp, bak)
    data = json.loads(bak.read_text(encoding="utf-8"))
    n = len(data["slides"])
    alvo_led = set()
    for t in filter(None, a.led.split(",")):
        alvo_led.add({"capa": 0, "slide2": 1, "cta": n - 1}.get(t, int(t) - 1 if t.isdigit() else -9))
    from rembg import new_session, remove
    cores = [hex2rgb(c) for c in MAPA_LED.split(",")]

    for i in sorted({0, 1, n - 1}):
        s, at = data["slides"][i], atual["slides"][i]
        if not s.get("imagem"):
            print(f"slide {i + 1}: sem imagem, ignorado")
            continue
        stem = Path(s["imagem"]).stem
        if stem.endswith("_orig"):
            stem = stem[:-5]
        orig = pasta / f"{stem}_orig.png"
        fonte = orig if orig.exists() else pasta / s["imagem"]
        limpa = carregar(fonte)
        foto, rel_foto = limpa, (orig.name if orig.exists() else s["imagem"])
        if i in alvo_led:
            foto = led(limpa, cores)
            rel_foto = f"{stem}_led.png"
            foto.save(pasta / rel_foto)
        s["imagem"] = rel_foto
        # alfa SEMPRE da foto limpa; cache por conteúdo (rembg em CPU leva minutos por foto)
        cache = pasta / ".compor_cache" / (hashlib.sha1(limpa.tobytes()).hexdigest()[:16] + ".png")
        if cache.exists():
            rgba = Image.open(cache).convert("RGBA")
        else:
            if not _sessao:
                _sessao.append(new_session())
            rgba = remove(limpa, session=_sessao[0])
            cache.parent.mkdir(exist_ok=True)
            rgba.save(cache)
        m_ruim, met = avaliar(rgba, area_max=0.85)
        mask = mascara(rgba)
        recorte = False
        s.pop("recorte", None)
        if a.sem_recorte or (at.get("sujeito") or {}).get("sem_recorte"):
            motivo = "--sem-recorte" if a.sem_recorte else "sem_recorte manual (revisão visual)"
        elif m_ruim:
            motivo = "recorte sujo: " + "; ".join(m_ruim)
        else:
            motivo = ""
            saida = Image.merge("RGBA", (*foto.split(), rgba.split()[-1]))
            rn = f"{stem}_recorte.png"
            saida.save(pasta / rn)
            s["recorte"] = rn
            recorte = True
        caixa, cab0 = caixa_cabeca(mask)
        am = at.get("sujeito") or {}
        faces = [] if am.get("rostos_so_manual") else rostos_haar(limpa)  # Haar com falso positivo: só as caixas manuais
        manual = am.get("rostos_manual", [])
        if am.get("cabeca_manual"):  # máscara com cabeça errada (capacete, cabelo): caixa manual
            cab0 = am["cabeca_manual"]
        g = np.asarray(limpa.convert("L").filter(ImageFilter.GaussianBlur(2))).astype(float)
        sob = np.hypot(ndimage.sobel(g, 0), ndimage.sobel(g, 1)) / 8
        t0 = s["template"]
        fs0 = 220 if t0 in ("T1", "T1b") else (140 if len(s["display"]) <= 2 else 120 if len(s["display"]) == 3 else 100)
        manual_bloco = (at.get("bloco") or {}).get("manual")

        def classificar(rec):
            cab, rostos = (list(cab0) if cab0 else None), [list(f) for f in faces]
            if rec and cab:  # rosto do próprio sujeito (>= 50% dentro da cabeça) é fundido na cabeça
                for r in [r for r in rostos if inter_area(r, cab) >= .5 * area(r)]:
                    cab = [min(cab[0], r[0]), min(cab[1], r[1]), max(cab[2], r[2]), max(cab[3], r[3])]
                    rostos.remove(r)
            rostos += [list(m) for m in manual]
            propr = []
            if rec:  # rosto com centro dentro do recorte = do próprio sujeito: o display passa por trás, o texto à frente não
                propr = [r for r in rostos if mask[min(H - 1, (r[1] + r[3]) // 2), min(W - 1, (r[0] + r[2]) // 2)]]
                rostos = [r for r in rostos if r not in propr]
            return cab, rostos, propr

        cab, rostos, propr = classificar(recorte)
        r = None if manual_bloco else escolher(s, t0, fs0, mask, sob, cab, rostos, recorte, propr)
        if recorte and not manual_bloco and not r:
            # sem lugar para o display atrás do sujeito (cabeça/corpo ocupam o quadro): foto inteira + texto, sem recorte
            recorte, motivo = False, "sem espaço para o display atrás do sujeito (palavras ficariam cobertas)"
            s.pop("recorte", None)
            cab, rostos, propr = classificar(False)
            r = escolher(s, t0, fs0, mask, sob, cab, rostos, False, propr)
        if not recorte and s["template"] == "T1b":
            s["template"] = "T1"  # T1b sem recorte seria retrato em caixa; T1 = foto sangrada + texto
            for k in ("fundo", "tecido"):
                s.pop(k, None)
            if s.get("emocao"):
                s["emocao"].pop("top", None)
        s.pop("texto", None)  # T4 "texto":"topo" antigo (âncora)
        suj = {"rostos": rostos}
        if propr:
            suj["rostos_sujeito"] = propr
        if cab:
            suj.update(cabeca=cab, caixa=caixa)
        if manual:
            suj["rostos_manual"] = manual
        for k in ("rostos_so_manual", "cabeca_manual", "sem_recorte"):
            if am.get(k):
                suj[k] = am[k]
        s["sujeito"] = suj
        t = s["template"]
        if manual_bloco:
            s["bloco"] = at["bloco"]
            dec = f"bloco manual {s['bloco']}"
        elif r:
            s["bloco"] = {"y": r[1], "alinhar": r[2], "largura": r[3]}
            dec = f"bloco y={r[1]} {r[2]} larg={r[3]} (agitação {r[4]}, display sob sujeito {r[5]:.0%}, fonte ~{r[6]})"
        else:
            s.pop("bloco", None)
            dec = "SEM posição livre (cabeça/rostos ocupam o quadro): bloco padrão do template, revisar à mão"
        print(f"slide {i + 1} [{t}] {rel_foto}{' +LED' if i in alvo_led else ''}: "
              f"{'recorte OK ' + str(met) if recorte else 'sem recorte (' + motivo + ') ' + str(met)}; "
              f"cabeca={cab} rostos={len(rostos)}; {dec}")
    # textura LED de fundo nos slides só de texto: os de lista e o de conclusão (último texto antes do CTA)
    txt = [k for k, x in enumerate(data["slides"]) if x["template"] in ("T2", "T2c", "T3") and "imagem" not in x]
    marcados = {k for k in txt if data["slides"][k].get("lista")}
    ult = [k for k in txt if k < n - 1]
    if ult and ult[-1] == max(k for k, x in enumerate(data["slides"][:n - 1]) if x["template"] != "T5"):
        marcados.add(ult[-1])
    for k, x in enumerate(data["slides"]):
        x.pop("textura", None)
        if k == 2 and k in txt:
            x["textura"] = "grain"  # slide 3: gradiente granulado (padrão das marcas desde 2026-10-05)
        elif k in marcados:
            x["textura"] = "led"
    print("textura led nos slides:", sorted(k + 1 for k in marcados if k != 2), "| grain no slide 3" if 2 in txt else "")
    jp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
