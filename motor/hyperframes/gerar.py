"""Gera carrosseis/<slug>/motion/index.html (HyperFrames) a partir do carrossel.json do motor.

Uso (da pasta do carrossel): python ../../motor/hyperframes/gerar.py carrossel.json [--force]

Cada template ganha o motion padrão do tema (otalogia.js): foto acendendo com push-in e brasas (T1/T1b/T2 com foto/T4),
título em cascata, frase manuscrita se escrevendo, marca-texto varrendo, lista em cascata, navegador nos T5 e pílula
pulsando no CTA. Gestos específicos de um carrossel (busca digitando, toque etc.) entram editando o index.html gerado;
sem --force o arquivo existente não é sobrescrito.
"""
import html
import json
import re
import sys
from pathlib import Path

S = 6  # segundos por slide
FOTO = {"T1", "T1b", "T2", "T4"}


def marcar(txt):
    """[x] -> cor quente; {x} -> marca-texto."""
    t = html.escape(txt)
    t = re.sub(r"\[(.+?)\]", r'<span class="hot">\1</span>', t)
    return re.sub(r"\{(.+?)\}", r'<span class="hl">\1</span>', t)


def slide_html(i, s, n, meta):
    tp, sid = s["template"], f"s{i + 1}"
    foto = tp in FOTO and s.get("imagem")
    papel = not foto and tp in ("T2", "T2c")
    bloco = s.get("bloco", {})
    classes = ["slide", "clip"] + (["com-foto"] if foto else []) + (["papel"] if papel else [])
    out = [f'  <section id="{sid}" class="{" ".join(classes)}" data-start="{i * S}" data-duration="{S}" data-track-index="0">']

    if foto:
        img = f"img/{s['imagem']}"
        out += [f'    <img class="foto" src="{img}" alt="" />', f'    <img class="bloom" src="{img}" alt="" />']
        if tp in ("T2", "T4"):
            out.append('    <div class="vinheta"></div>')
        if s.get("recorte") and s.get("texto_frente"):
            out.append(f'    <img class="recorte" src="img/{s["recorte"]}" alt="" style="z-index: 2" />')
        out.append('    <div class="brasas" data-layout-allow-overflow></div>')
    if papel:
        out.append('    <div class="dobra"></div>')
    if s.get("textura") == "led":
        out.append('    <div class="led" data-layout-allow-overflow></div>')
    if tp == "T2c":
        out += ['    <div class="margem"></div>', '    <div class="jogo">#</div>']

    disp = "".join(f'<span class="linha"><span>{marcar(l)}</span></span>' for l in s.get("display", []))
    if tp == "T5":
        ref = s["referencia"]
        out += [
            '    <div class="chip">REFERÊNCIA</div>',
            f'    <div class="ref-titulo">{"<br />".join(html.escape(l) for l in s["display"])}</div>',
            '    <div class="navegador">',
            f'      <div class="barra-nav"><i class="d1"></i><i class="d2"></i><i class="d3"></i><span class="url">{html.escape(ref["site"])}</span></div>',
            f'      <div class="tela"><img src="img/{ref["print"]}" alt="" /></div>',
            f'      <div class="info"><div class="nome">{html.escape(ref["nome"])}</div><div class="desc">{html.escape(ref["descricao"])}</div></div>',
            "    </div>",
        ]
    else:
        # posição: bloco.y do json quando houver; senão o lugar do PNG estático por template
        lista = bool(s.get("lista"))
        top = bloco.get("y") or {"T1": 380, "T1b": 200, "T2": 200 if foto else 520, "T2c": 640, "T3": 380 if lista else 600, "T4": 600}[tp]
        larg = bloco.get("largura", 760 if tp == "T2c" else 936)
        left = 230 if tp == "T2c" else 72
        tag = "h1" if i == 0 else "h2"
        out.append(f'    <div class="conteudo" style="top: {top}px; left: {left}px; width: {larg}px">')
        out.append(f'      <{tag} class="display" data-layout-allow-overflow data-layout-allow-occlusion>{disp}</{tag}>')
        if s.get("emocao"):
            out.append(f'      <p class="emocao">{marcar(s["emocao"]["texto"])}</p>')
        if lista:
            itens = "".join(f'<li><i class="fio"></i><span class="n">{k + 1:02d}</span><span class="t">{marcar(t)}</span></li>' for k, t in enumerate(s["lista"]))
            out.append(f'      <ul class="lista">{itens}</ul>')
        if s.get("cta"):
            out.append(f'      <div class="cta"><div class="pill">{html.escape(s["cta"]["acao"])}</div><p class="cta-txt">{html.escape(s["cta"]["texto"])}</p></div>')
        out.append("    </div>")
        if foto and s.get("recorte") and not s.get("texto_frente"):
            out.append(f'    <img data-layout-allow-occlusion class="recorte" src="img/{s["recorte"]}" alt="" />')
        if i == 0:
            out.append('    <div class="base"><div class="arrasta">arrasta <b></b></div></div>')

    dots = "".join('<i class="on"></i>' if k == i else "<i></i>" for k in range(n))
    out += [
        f'    <div class="topo"><span>otalogia</span><span>{html.escape(meta.get("serie", "").lower())}</span><span>{html.escape(meta.get("data", ""))}</span></div>',
        f'    <div class="rodape"><span>@otalogia</span><span class="salva">salva pra depois</span><span class="dots">{dots}</span></div>',
        '    <svg class="grao" width="100%" height="100%"><rect width="100%" height="100%" filter="url(#ruido)" /></svg>',
        "  </section>",
    ]
    return "\n".join(out)


def slide_js(i, s):
    tp, sid, t = s["template"], f"s{i + 1}", i * S
    foto = tp in FOTO and s.get("imagem")
    if tp == "T5":
        return f'  m.referencia("{sid}", {t});'
    js = []
    if foto:
        js.append(f'  m.foto("{sid}", {t}, {{ z: {1.06 if s.get("recorte") else 1.14}, brasas: {40 if tp in ("T1", "T1b") else 28} }});')
    if s.get("textura") == "led":
        js.append(f'  m.respira("#{sid} .led", {t});')
    if tp == "T2c":
        js.append(f'  tl.fromTo("#{sid} .margem", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 1.2, ease: "expo.out" }}, {t + 0.1});')
        js.append(f'  m.sobe("#{sid} .jogo", {t + 0.3}, 0.6);')
    if i == 0:
        js.append(f'  m.chrome("{sid}", {t});')
    t0 = t + (0.45 if foto else 0.15)
    nl = len(s.get("display", []))
    js.append(f'  m.linhas("{sid}", {t0});')
    t_txt = round(t0 + 0.6 + nl * 0.12, 2)
    js.append(f'  m.marcas("#{sid} .display .hl", {t_txt});')
    if s.get("emocao"):
        js.append(f'  m.escreve("#{sid} .emocao", {t_txt + 0.1});')
        js.append(f'  m.marcas("#{sid} .emocao .hl", {round(t_txt + 1.1, 2)});')
    if s.get("lista"):
        js.append(f'  m.lista("{sid}", {round(t_txt + 0.2, 2)});')
    if s.get("cta"):
        js.append(f'  m.pill("#{sid} .pill", {round(t_txt + 0.9, 2)});')
        js.append(f'  m.sobe("#{sid} .cta-txt", {round(t_txt + 1.3, 2)});')
    if i == 0:
        js.append(f'  m.sobe("#{sid} .arrasta", {t + 2.6});')
        js.append(f'  tl.fromTo("#{sid} .arrasta b", {{ x: 0 }}, {{ x: 14, duration: 0.6, ease: "sine.inOut", yoyo: true, repeat: 3 }}, {t + 3.1});')
    return "\n".join(js)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = Path(args[0] if args else "carrossel.json").resolve()
    dest = src.parent / "motion" / "index.html"
    if dest.exists() and "--force" not in sys.argv:
        sys.exit(f"{dest} já existe (use --force para sobrescrever)")
    c = json.loads(src.read_text(encoding="utf-8"))
    slides, meta = c["slides"], c.get("meta", {})
    n = len(slides)
    capa = slides[0]
    titulo = " ".join(capa.get("display", [])).capitalize()
    corpo = "\n\n".join(slide_html(i, s, n, meta) for i, s in enumerate(slides))
    timeline = "\n\n".join(slide_js(i, s) for i, s in enumerate(slides))
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1440" />
<title>{html.escape(titulo)} (motion)</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<link rel="stylesheet" href="otalogia.css" />
<script src="otalogia.js"></script>
<style>
  #s1 .display {{ font-size: 132px; }}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute">
  <filter id="ruido"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="7" stitchTiles="stitch" /><feColorMatrix type="saturate" values="0" /></filter>
</svg>

<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1440" data-duration="{n * S}">

{corpo}
</div>

<script>
  const tl = gsap.timeline({{ paused: true }});
  const S = {S}, m = otaMotion(tl, S);
  m.ajusta();

{timeline}

  m.parallaxTodos();
  window.__timelines["main"] = tl;
</script>
</body>
</html>
""", encoding="utf-8")
    print(f"ok: {dest} ({n} slides, {n * S} s)")


if __name__ == "__main__":
    main()
