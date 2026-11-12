#!/usr/bin/env python3
"""Pré-checagem editorial de temas e PDFs por categoria, antes da criação.

Uso:
  python automation/avaliar_categorias.py --titulo "Lead que esfriou" --categoria ATENDIMENTO
  python automation/avaliar_categorias.py --titulo "Uma ideia para post" --categoria CONTEUDO --json

Não gera PDF e não modifica a fila. A decisão final sobre semântica é humana.
"""
from __future__ import annotations
import argparse, difflib, json, re, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / "iscas" / "categorias.json").exists())
CONFIG = ROOT / "iscas" / "categorias.json"
STOP = {"de","da","do","dos","das","um","uma","que","para","por","sem","com","na","no",
        "em","os","as","seu","sua","como","mais","isso","voce","ate","aos","pela"}

def norm(x: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", x.lower())
                   if not unicodedata.combining(c))

def tokens(x: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}",norm(x)) if t not in STOP}

def score(left: str, right: str) -> float:
    a,b=tokens(left),tokens(right)
    union=a|b
    jac=len(a&b)/len(union) if union else 0
    return round(.7*jac+.3*difflib.SequenceMatcher(None,norm(left),norm(right)).ratio(),3)

def all_posts():
    roots = [
      ROOT/"carrosseis", ROOT/"fila",
      ROOT/"agente aidealab"/"clientes"/"aidealab"/"carrosseis",
      ROOT/"agente aidealab"/"skills"/"post-instagram"/"queue"
    ]
    seen=set()
    seen_ids=set()
    for base in roots:
        if not base.exists():
            continue
        for path in [*base.glob("*/carrossel.json"),
                     *base.glob("*/png/metadata.json"),
                     *base.glob("**/metadata.json")]:
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            try: obj=json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError,OSError): continue
            ident=str(obj.get("carousel_id") or obj.get("id") or path.parent.name)
            tema=obj.get("tema") or ""
            if not tema:
                slides=obj.get("slides") or []
                headline=slides[0] if slides else {}
                tema=" ".join(headline.get("display",[])) if isinstance(headline,dict) else ""
            if tema and ident not in seen_ids:
                seen_ids.add(ident)
                yield {"id":ident,"tema":str(tema),"arquivo":str(path.relative_to(ROOT))}
    # Estado sincronizado do Drive registra posts em fila e publicados que
    # podem não ter todos os metadados no checkout local (ex.: Reels no Drive).
    for status_path in [
        ROOT/"agente aidealab"/"automation"/"cloud"/"estado-drive.json",
        ROOT/"automation"/"cloud"/"estado-drive.json",
    ]:
        if not status_path.exists():
            continue
        try:
            state=json.loads(status_path.read_text(encoding="utf-8-sig"))
        except (ValueError,OSError):
            continue
        for status in ("rascunhos_04","fila","postados"):
            for ident in state.get(status,[]):
                if ident in seen_ids or not isinstance(ident,str):
                    continue
                seen_ids.add(ident)
                titulo=re.sub(r"^\d{4}-\d{2}-\d{2}-", "", ident)
                titulo=re.sub(r"^Dia\d+-", "", titulo)
                titulo=titulo.replace("-"," ")
                yield {"id":ident,"tema":titulo,"arquivo":str(status_path.relative_to(ROOT))+"#"+status}

def decide(title,category,post_id="",minimum=.57):
    cfg=json.loads(CONFIG.read_text(encoding="utf-8"))
    cats=cfg["categorias"]
    cat=category.upper()
    if cat not in cats: raise ValueError("Categoria não cadastrada: "+cat)
    selected=cats[cat]
    near=sorted([
      dict(**post,similaridade=score(title,post["tema"]))
      for post in all_posts() if not post_id or post["id"]!=post_id
    ],key=lambda row:row["similaridade"],reverse=True)
    # Evita falsos positivos: mesmo tema já deve existir em posts semelhantes;
    # categoria igual não significa carrossel duplicado.
    duplicates=[x for x in near if x["similaridade"]>=minimum]
    guides=selected.get("guias",[])
    approved=[x for x in guides if x.get("status") in {"aprovado","publicado"}]
    if duplicates:
        action="REVISAR_POST_REPETIDO"
    elif approved:
        action="REUTILIZAR_GUIAS_DA_CATEGORIA"
    elif guides:
        action="APROVAR_OU_APROFUNDAR_PILOTO"
    else:
        action="PESQUISAR_NOVO_GUIA_APENAS_SE_NECESSARIO"
    return {"categoria":cat,"palavra":selected["palavra"],"acao":action,
            "posts_semelhantes":near[:7],"posts_possivelmente_duplicados":duplicates[:5],
            "guias_existentes":guides,
            "regra":"Não criar automaticamente; comparação semântica e pesquisa editorial obrigatórias."}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--titulo",required=True)
    ap.add_argument("--categoria",required=True)
    ap.add_argument("--post-id",default="")
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    report=decide(args.titulo,args.categoria,args.post_id)
    print(json.dumps(report,ensure_ascii=False,indent=2))
