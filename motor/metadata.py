"""
Gera o metadata.json de um carrossel no schema da skill post-instagram
(D:/claude/agente aidealab/skills/post-instagram/references/metadata-schema.md),
para postagem automática via Graph API da Meta.

Uso: python metadata.py <carrossel.json> <ordem_fila> --tema <pasta_do_tema> [hashtag ...]
(cliente, handle e familia_cor vêm do tema.json; tema também via env CARROSSEL_TEMA)
Lê o carrossel.json e o legenda.md da mesma pasta; escreve metadata.json na pasta png/
(junto dos slides). Se o metadata.json já existir, preserva postado/postado_em/post_id.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

PAPEIS = {"T1": "hook", "T1b": "hook", "T4": "cta"}


def limpar(t):
    # tira os marcadores [quente] e {marca-texto}; " / " vira quebra
    return re.sub(r"[\[\]{}]", "", t).replace(" / ", " ")


def texto_slide(s):
    partes = [" ".join(s.get("display", []))]
    if s.get("emocao"):
        partes.append(s["emocao"]["texto"])
    partes += s.get("lista", [])
    if s.get("cta"):
        partes += [s["cta"]["acao"], s["cta"].get("texto", "")]
    return limpar(" ".join(p for p in partes if p)).strip()


def gerar(json_path, tema, ordem_fila=None, hashtags=()):
    json_path = Path(json_path)
    d = json.loads(json_path.read_text(encoding="utf-8"))
    pasta = json_path.parent
    png = pasta / "png"
    slides = d["slides"]
    n = len(slides)
    legenda_md = pasta / "legenda.md"
    meta = {
        "carousel_id": d["id"],
        "cliente": tema["marca"],
        "data_criacao": date.today().isoformat(),
        "status": "aprovado",
        "postado": False,
        "postado_em": None,
        "post_id": None,
        "ordem_fila": ordem_fila,
        "serie": d["meta"]["serie"],
        "tema": limpar(" ".join(slides[0]["display"]) + " " + slides[0].get("emocao", {}).get("texto", "")).strip(),
        "familia_cor": tema["familia_cor"],
        "template": "-".join(s["template"] for s in slides),
        "formato": "1080x1440",
        "slides": [
            {
                "ordem": i + 1,
                "arquivo": f"slide-{i + 1:02d}.png",
                "papel": PAPEIS.get(s["template"], "desenvolvimento") if i != 1 else "tensao",
                "texto": texto_slide(s),
            }
            for i, s in enumerate(slides)
        ],
        "legenda": legenda_md.read_text(encoding="utf-8").strip() if legenda_md.exists() else "",
        "hashtags": list(hashtags),
        "handle": tema["handle"],
    }
    for sl in meta["slides"]:
        assert (png / sl["arquivo"]).exists(), f"falta {sl['arquivo']} em {png}"
    destino = png / "metadata.json"
    if destino.exists():
        antigo = json.loads(destino.read_text(encoding="utf-8"))
        for k in ("postado", "postado_em", "post_id", "data_criacao"):
            if k in antigo:
                meta[k] = antigo[k]
    destino.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


if __name__ == "__main__":
    args = sys.argv[1:]
    tema_dir = os.environ.get("CARROSSEL_TEMA")
    if "--tema" in args:
        i = args.index("--tema")
        tema_dir = args[i + 1]
        del args[i:i + 2]
    if not args or not tema_dir:
        sys.exit("uso: python metadata.py <carrossel.json> <ordem_fila> --tema <pasta_do_tema> [#tags ...]")
    tema = json.loads((Path(tema_dir) / "tema.json").read_text(encoding="utf-8"))
    ordem = int(args[1]) if len(args) > 1 else None
    print("OK:", gerar(args[0], tema, ordem, args[2:]))
