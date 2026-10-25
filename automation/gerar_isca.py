"""Gera o PDF da isca de DM (o material que a palavra do CTA entrega) a partir de iscas/<slug>/isca.json,
com a arte da marca (tokens de design-system/tema/tema.css): capa em ink, miolo em papel, fecho em ink.
O PDF sai em iscas/<slug>/<slug>.pdf; o entregar.yml sobe para Clientes/otalogia/07-Iscas-DM e grava o link em iscas/links.md.

isca.json: {"palavra", "reel", "semana", "titulo", "subtitulo",
            "secoes": [{"titulo", "texto"?, "itens"?: [...], "codigo"?}], "fecho"}
Uso: python automation/gerar_isca.py iscas/<slug> [iscas/<slug> ...]
"""
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

TEMA = (Path(__file__).parent.parent / "design-system/tema/tema.css").read_text(encoding="utf-8")
e = html.escape

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;600;800&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono&display=swap');
@page { size: 1080px 1440px; margin: 0; }
* { box-sizing: border-box; margin: 0; }
body { font-family: var(--f-body); }
.pg { width: 1080px; height: 1440px; padding: 110px 96px; position: relative; overflow: hidden;
      page-break-after: always; display: flex; flex-direction: column; }
.ink { background: var(--ink); color: var(--branco); }
.papel { background: var(--papel); color: var(--grafite); }
.ink::after, .papel::after { content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .5;
  background-image: radial-gradient(rgba(127,127,127,.18) 1px, transparent 1px); background-size: 4px 4px; }
.selo { font-family: var(--f-mono); font-size: 24px; letter-spacing: .12em; text-transform: uppercase; opacity: .7; }
.capa h1 { font-family: var(--f-display); font-weight: 800; font-size: 104px; line-height: .95; letter-spacing: -.03em;
           margin-top: auto; text-transform: uppercase; }
.capa .sub { font-family: var(--f-serif); font-style: italic; font-size: 52px; line-height: 1.15; margin-top: 40px; color: var(--quente); }
.capa .tag { margin-top: 64px; display: inline-block; align-self: flex-start; border: 2px solid var(--quente); color: var(--quente);
             font-family: var(--f-mono); font-size: 26px; padding: 14px 24px; border-radius: 999px; }
.rod { font-family: var(--f-mono); font-size: 22px; opacity: .6; margin-top: auto; padding-top: 48px;
       display: flex; justify-content: space-between; }
.sec + .sec { margin-top: 64px; }
.sec .n { font-family: var(--f-mono); font-size: 26px; color: var(--quente-papel); }
.sec h2 { font-family: var(--f-display); font-weight: 800; font-size: 60px; line-height: 1.02; letter-spacing: -.02em; margin: 12px 0 24px; }
.sec p { font-size: 34px; line-height: 1.4; }
.sec ul { list-style: none; padding: 0; margin-top: 16px; }
.sec li { font-size: 32px; line-height: 1.38; padding: 18px 0 18px 56px; position: relative; border-top: 1px solid rgba(17,17,17,.15); }
.sec li::before { content: ""; position: absolute; left: 0; top: 26px; width: 30px; height: 30px; border: 3px solid var(--quente-papel); border-radius: 6px; }
.sec pre { font-family: var(--f-mono); font-size: 25px; line-height: 1.5; white-space: pre-wrap; background: var(--ink); color: var(--branco);
           padding: 36px 40px; border-radius: 18px; margin-top: 16px; border-left: 8px solid var(--quente); }
.fecho h2 { font-family: var(--f-display); font-weight: 800; font-size: 88px; line-height: .98; letter-spacing: -.03em; margin-top: auto; }
.fecho h2 em { font-family: var(--f-serif); font-weight: 400; color: var(--quente); }
.fecho p { font-size: 36px; line-height: 1.4; margin-top: 40px; opacity: .85; }
"""


def secao(i, s):
    corpo = f"<p>{e(s['texto'])}</p>" if s.get("texto") else ""
    corpo += "<ul>" + "".join(f"<li>{e(x)}</li>" for x in s["itens"]) + "</ul>" if s.get("itens") else ""
    corpo += f"<pre>{e(s['codigo'])}</pre>" if s.get("codigo") else ""
    return f'<div class="sec"><div class="n">{i:02d}</div><h2>{e(s["titulo"])}</h2>{corpo}</div>'


def montar(d):
    rod = f'<div class="rod"><span>@otalogia</span><span>{e(d["palavra"])}</span></div>'
    capa = (f'<section class="pg ink capa"><div class="selo">material · {e(d["reel"])} · @otalogia</div>'
            f'<h1>{e(d["titulo"])}</h1><div class="sub">{e(d["subtitulo"])}</div>'
            f'<div class="tag">você comentou {e(d["palavra"])}</div>{rod}</section>')
    # uma seção por página, ou duas quando são curtas (sem código e até 4 itens)
    paginas, atual = [], []
    for i, s in enumerate(d["secoes"], 1):
        curta = not s.get("codigo") and len(s.get("itens", [])) <= 4 and len(s.get("texto", "")) < 260
        if atual and not (curta and atual[-1][1] and len(atual) < 2):
            paginas.append(atual)
            atual = []
        atual.append((secao(i, s), curta))
    paginas += [atual] if atual else []
    miolo = "".join(f'<section class="pg papel">{"".join(h for h, _ in p)}{rod}</section>' for p in paginas)
    fecho = (f'<section class="pg ink fecho"><div class="selo">otalogia · site, automação e vídeo</div>'
             f'<h2>Quer isso <em>funcionando</em> no seu negócio?</h2><p>{e(d["fecho"])}</p>'
             f'<div class="rod"><span>instagram.com/otalogia</span><span>me chama no direct</span></div></section>')
    return f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>{TEMA}{CSS}</style></head><body>{capa}{miolo}{fecho}</body></html>"


def main():
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page()
        for pasta in map(Path, sys.argv[1:]):
            d = json.loads((pasta / "isca.json").read_text(encoding="utf-8"))
            pg.set_content(montar(d), wait_until="networkidle")
            saida = pasta / f"{pasta.name}.pdf"
            pg.pdf(path=str(saida), width="1080px", height="1440px", print_background=True)
            print("pdf:", saida)
        nav.close()


if __name__ == "__main__":
    main()
