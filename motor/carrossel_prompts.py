"""
carrossel_prompts.py — monta um carrossel de PROMPTS (imagem -> prompt que a gerou) e o PDF da DM.

Regra fixa: todo conteúdo de prompt usa a categoria PROMPT de iscas/categorias.json, e a palavra do CTA
é a palavra dessa categoria ("PROMPT"). Os PDFs de prompt são únicos (os da aidealab, que o otalogia reaproveita) e registrados nessa categoria, e a DM
manda os PDFs da categoria pela mesma palavra. Nunca criar palavra nova por post.

Uso (na raiz do repo): python motor/carrossel_prompts.py <spec.json> --marca otalogia|aidealab
spec.json:
  slug, ordem, tema ("tema" | "tema-gta"), tags [5], capa {display[2], emocao},
  fotos: [capa, slide3, slide5, cta] -> {id, url, prompt}   (imagens já geradas; nada é gerado aqui)
  pares[3]: {titulo, nome, lista[4], guia, dica, display[2]?, emocao?}  (o par 0 usa a capa como imagem)
  guia_titulo, guia_sub, legenda, blocos? {idx: bloco}, sujeitos? {idx: sujeito}
Fluxo: baixa as fotos, escreve carrossel.json / guia/guia.json (prompts em "codigo") / legenda.md,
roda compor (--sem-recorte: título nunca atrás da cabeça), render, metadata e, no otalogia, o motion.
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CATEGORIA = "PROMPT"
MARCAS = {
    "otalogia": {"pasta": "carrosseis/{mes}-{slug}", "tema": "design-system/{tema}", "cta": "que eu te mando no direct"},
    "aidealab": {"pasta": "agente aidealab/clientes/aidealab/carrosseis/{slug}",
                 "tema": "agente aidealab/clientes/aidealab/design-system/{tema}", "cta": "a aidealab te manda no direct"},
}
FONTES = [{"titulo": "OpenAI: guia de geração de imagens (GPT Image)", "url": "https://platform.openai.com/docs/guides/image-generation"},
          {"titulo": "Higgsfield: geração de imagem com personagem de referência", "url": "https://higgsfield.ai"}]


def limpa(p):
    """Tira nome/ID de personagem do prompt: vira [sua foto de referência]."""
    p = re.sub(r"<<<[^>]+>>>|A man \(Luiz\)|Luiz,|Luiz|a young man with short dark textured hair|"
               r"a young man with dark curly hair and a beard|a (?:young |middle-aged )?(?:adult )?Latino ?/ ?Hispanic "
               r"(?:adult )?(?:man|male)(?:, approximately in his 20s| in his early 20s|, estimated in his mid-20s)?",
               "[sua foto de referência]", p)
    return p.replace("Keep his own short dark textured hair fully visible, ", "Keep the person's own hair fully visible, ")


def palavra_prompt():
    cat = json.loads((RAIZ / "iscas/categorias.json").read_text(encoding="utf-8"))["categorias"].get(CATEGORIA)
    if not cat:
        sys.exit(f"iscas/categorias.json sem a categoria {CATEGORIA}")
    return cat["palavra"]


def registrar(slug, titulo, pasta):
    """Registra o PDF e o post na categoria PROMPT (status rascunho até a aprovação humana)."""
    p = RAIZ / "iscas/categorias.json"
    cfg = json.loads(p.read_text(encoding="utf-8"))
    cat = cfg["categorias"][CATEGORIA]
    nome = slug.upper().replace("PROMPT-", "").replace("-", "_")
    gid = "prompt-" + nome.lower()
    if not any(g.get("id") == gid for g in cat["guias"]):
        g = {"id": gid, "titulo": titulo, "arquivo": f"PROMPT_{nome}.pdf", "status": "piloto_aguardando_aprovacao"}
        # PDF de prompt é um só: o da aidealab (07-Iscas-DM). O otalogia aponta para o mesmo arquivo, sem cópia.
        g["origem"] = f"{pasta}/png/guia.pdf" if RAIZ.name.startswith("aidealab") or (RAIZ / "agente aidealab").exists() else "Google Drive/Clientes/aidealab/07-Iscas-DM"
        cat["guias"].append(g)
    if slug not in cat.setdefault("posts_relevantes", []):
        cat["posts_relevantes"].append(slug)
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--marca", required=True, choices=MARCAS)
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    cfg = MARCAS[a.marca]
    palavra = palavra_prompt()
    rel = cfg["pasta"].format(mes=spec.get("mes", "2026-11"), slug=spec["slug"])
    d = RAIZ / rel
    (d / "guia").mkdir(parents=True, exist_ok=True)
    tema = str(RAIZ / cfg["tema"].format(tema=spec.get("tema", "tema")))
    fotos = spec["fotos"]
    for nome, f in zip(("capa", "slide3", "slide5", "cta"), fotos):
        if not (d / f"{nome}_orig.png").exists():
            urllib.request.urlretrieve(f["url"], d / f"{nome}_orig.png")
    P = spec["pares"]
    slides = [{"template": "T1", "display": spec["capa"]["display"], "emocao": {"texto": spec["capa"]["emocao"], "posicao": "depois"}, "imagem": "capa_orig.png"},
              {"template": "T3", "display": ["PROMPT 1", P[0]["titulo"]], "lista": P[0]["lista"], "imagem": None}]
    for k, img in ((1, "slide3_orig.png"), (2, "slide5_orig.png")):
        slides += [{"template": "T2", "display": P[k]["display"], "emocao": {"texto": P[k]["emocao"], "posicao": "depois"}, "imagem": img},
                   {"template": "T3", "display": [f"PROMPT {k + 1}", P[k]["titulo"]], "lista": P[k]["lista"]}]
    slides.append({"template": "T4", "display": ["QUER OS", "3 PROMPTS?"], "cta": {"acao": f"Comenta {palavra}", "texto": cfg["cta"]}, "imagem": "cta_orig.png"})
    for k, b in spec.get("blocos", {}).items():
        slides[int(k)]["bloco"] = b
    for k, s in spec.get("sujeitos", {}).items():
        slides[int(k)]["sujeito"] = s
    cid = f"{spec.get('mes', '2026-11')}-{spec['slug']}"
    (d / "carrossel.json").write_text(json.dumps({"id": cid, "meta": {"serie": "PROMPTS", "data": spec.get("mes", "2026-11").replace("-", "/"),
                                      "personagem": spec.get("personagem", "luizota"), "guia": {"fonte": "guia/guia.json"}}, "slides": slides},
                                     ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "carrossel.json.bak").unlink(missing_ok=True)
    paginas = [{"titulo": f"Prompt {k + 1}: {P[k]['nome']}", "texto": P[k]["guia"], "codigo": limpa(fotos[k]["prompt"]), "dica": P[k]["dica"]} for k in range(3)]
    paginas.append({"titulo": "Como usar os prompts", "texto": "Funciona em qualquer gerador que aceite foto de referência (GPT Image no ChatGPT, Higgsfield, Nano Banana).",
                    "itens": ["Anexe uma foto sua, de frente, com boa luz", "Cole o prompt e troque [sua foto de referência] pela foto anexada",
                              "Formato 3:4 e qualidade alta", "Mude uma coisa por vez: pose, roupa ou objeto"],
                    "dica": "Se for uma mulher, troque he/his por she/her."})
    guia = {"marca": a.marca, "titulo": spec["guia_titulo"], "subtitulo": spec["guia_sub"], "categoria": CATEGORIA,
            "como_usar": "Cole um prompt por vez, com a foto anexada, e só depois ajuste.", "fontes": FONTES,
            "nota_fontes": f"Material editorial {a.marca}, prompts usados nas imagens do carrossel. Resultados variam por modelo.", "paginas": paginas}
    (d / "guia/guia.json").write_text(json.dumps(guia, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "legenda.md").write_text(spec["legenda"].replace("{PALAVRA}", palavra).strip() + "\n", encoding="utf-8")
    run = lambda *c, **k: subprocess.run([sys.executable, *c], check=True, **k)
    run(str(RAIZ / "motor/compor.py"), str(d / "carrossel.json"), "--alfa-duro", "--sem-recorte", stdout=subprocess.DEVNULL)
    run(str(RAIZ / "motor/render.py"), "carrossel.json", "png", "--tema", tema, cwd=d)
    run(str(RAIZ / "motor/metadata.py"), "carrossel.json", str(spec.get("ordem", 0)), "--tema", tema, *spec["tags"], cwd=d)
    (d / "png/guia.html").unlink(missing_ok=True)
    if (RAIZ / "motor/hyperframes/gerar.py").exists():
        run(str(RAIZ / "motor/hyperframes/gerar.py"), "carrossel.json", "--force", cwd=d, stdout=subprocess.DEVNULL)
    registrar(spec["slug"], spec["guia_titulo"], rel)
    print(f"ok {a.marca} {rel} (palavra {palavra}, categoria {CATEGORIA})")


if __name__ == "__main__":
    main()
