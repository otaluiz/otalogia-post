"""
carrossel-engine — renderiza um carrossel (JSON) em PNGs 1080x1440, um por slide.

Uso: python render.py <carrossel.json> [out_dir] --tema <pasta_do_tema>
  (o tema também pode vir da variável de ambiente CARROSSEL_TEMA)
  out_dir padrao = pasta com o nome do "id" do JSON, ao lado do JSON.
  Tema = pasta com tema.css (só custom properties) e tema.json (marca, strings, google_fonts, fontes).

Fluxo: injeta window.__CARROSSEL e window.__TEMA (+ __TEMA_CSS), abre carrossel.html?slide=N para cada
slide, espera o title 'READY:{...}' (fontes carregadas + ajuste do display) e tira o screenshot (os PNGs só são gravados no fim, se todos os slides passarem).
Falha DURO (sem escrever PNG) se: a validacao tem erros, uma das fontes do tema nao carregou
(fallback silencioso = falha), o .slide nao mede exatamente 1080x1440, ou (modo camadas) texto cobre cabeca/rosto (colisao).

Setup: pip install playwright pillow && playwright install chromium
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

W, H = 1080, 1440
AQUI = Path(__file__).resolve().parent


def falhar(msg):
    print("ERRO:", msg, file=sys.stderr)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    tema_dir = os.environ.get("CARROSSEL_TEMA")
    if "--tema" in args:
        i = args.index("--tema")
        if i + 1 >= len(args):
            falhar("--tema precisa de uma pasta")
        tema_dir = args[i + 1]
        del args[i:i + 2]
    if not args or not tema_dir:
        falhar("uso: python render.py <carrossel.json> [out_dir] --tema <pasta_do_tema>  (ou env CARROSSEL_TEMA)")
    tema_dir = Path(tema_dir).resolve()
    if not (tema_dir / "tema.json").exists() or not (tema_dir / "tema.css").exists():
        falhar(f"tema invalido: faltam tema.json/tema.css em {tema_dir}")
    tema = json.loads((tema_dir / "tema.json").read_text(encoding="utf-8"))
    fontes = tema.get("fontes", [])
    json_path = Path(args[0]).resolve()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    out_dir = Path(args[1]) if len(args) > 1 else json_path.parent / data["id"]

    # imagem relativa ao JSON -> URI absoluta file:///; null continua null
    for s in data["slides"]:
        for k in ("imagem", "recorte"):
            if s.get(k):
                s[k] = (json_path.parent / s[k]).resolve().as_uri()
        # T5: print do site, também relativo ao JSON
        ref = s.get("referencia")
        if ref and ref.get("print"):
            ref["print"] = (json_path.parent / ref["print"]).resolve().as_uri()

    url = (AQUI / "carrossel.html").as_uri()
    n = len(data["slides"])
    shots = []
    pngs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.add_init_script(
            f"window.__CARROSSEL = {json.dumps(data)}; window.__TEMA = {json.dumps(tema)}; "
            f"window.__TEMA_CSS = {json.dumps((tema_dir / 'tema.css').as_uri())};")
        page.on("pageerror", lambda e: print("pageerror:", e, file=sys.stderr))
        try:
            for i in range(1, n + 1):
                page.goto(f"{url}?slide={i}", wait_until="load", timeout=20000)
                try:
                    page.wait_for_function("document.title.startsWith('READY:')", timeout=15000)
                except Exception:
                    falhar(f"slide {i}: a pagina nunca setou document.title = 'READY:...' (fontes offline? erro de JS?)")
                rel = json.loads(page.title()[len("READY:"):])
                if i == 1:
                    if rel["errors"]:
                        print("Validacao com erros, nenhum PNG escrito:", file=sys.stderr)
                        for e in rel["errors"]:
                            print("  -", e, file=sys.stderr)
                        sys.exit(1)
                    for w in rel["warnings"]:
                        print("AVISO:", w)
                faltando = [f for f in fontes if not page.evaluate("f => document.fonts.check(f)", f)]
                if faltando:
                    falhar(f"slide {i}: fontes nao carregaram (fallback silencioso): {faltando}")
                box = page.evaluate("() => { const r = document.querySelector('.slide').getBoundingClientRect(); return [r.width, r.height]; }")
                if [round(box[0]), round(box[1])] != [W, H]:
                    falhar(f"slide {i}: .slide mede {box}, esperado {W}x{H}")
                # camadas: texto na frente (ou display) sobre cabeça/rosto = erro bloqueante, nenhum PNG escrito
                for f in rel.get("fit", []):
                    c = f.get("camadas")
                    if c and c.get("colisao"):
                        falhar(f"slide {i}: texto cobre cabeca/rosto (colisao): {json.dumps(c)}")
                    if c:
                        print(f"slide {i}: camadas ok, movidos={c.get('movidos')} emocao={c.get('emocao')} display={c.get('display')}")
                shots.append(page.screenshot(clip={"x": 0, "y": 0, "width": W, "height": H}))
        finally:
            browser.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    for i, b in enumerate(shots, 1):
        png = out_dir / f"slide-{i:02d}.png"
        png.write_bytes(b)
        pngs.append(png)
    for png in pngs:
        assert Image.open(png).size == (W, H), f"{png} fora de {W}x{H}"
    print(f"OK: {len(pngs)} PNGs {W}x{H} em {out_dir}")


if __name__ == "__main__":
    main()
