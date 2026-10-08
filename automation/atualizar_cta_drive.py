"""Atualiza no Drive o slide CTA (último PNG, halftone) e o slide 3 só de texto (quadro-negro) dos carrosséis da
otalogia já enviados, com o render atual do repo. Procura a pasta pelo nome do carrossel em Clientes/otalogia/04-Carrosseis e em
06-Aprovados-para-Postar (e nas subpastas dela) e sobe o PNG como nova revisão do mesmo arquivo (o histórico do
Drive guarda a versão anterior). Roda no GitHub Actions (workflow atualizar-cta-drive.yml, secrets GOOGLE_DRIVE_*).

Uso: python automation/atualizar_cta_drive.py [--dry-run]
"""
import json
import sys
from pathlib import Path

from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).parent))
from upload_drive import achar, filhos, servico  # noqa: E402

DRY = "--dry-run" in sys.argv


def main():
    svc = servico()
    pastas = dict(filhos(svc, achar(svc, "Clientes/otalogia/04-Carrosseis"), True))
    seis = achar(svc, "Clientes/otalogia/06-Aprovados-para-Postar")
    for nome, pid in filhos(svc, seis, True).items():
        pastas.setdefault(nome, pid)
        for sub, sid in filhos(svc, pid, True).items():  # FILA/POSTADOS, se existirem
            pastas.setdefault(sub, sid)
    feitos = 0
    for d in sorted(Path("carrosseis").iterdir()):
        cj = d / "carrossel.json"
        if not cj.exists() or d.name not in pastas:
            continue
        slides = json.loads(cj.read_text(encoding="utf-8"))["slides"]
        alvos = [f"slide-{len(slides):02d}.png"]
        if len(slides) > 3 and slides[2].get("template") in ("T2", "T2c", "T3") and not slides[2].get("imagem"):
            alvos.append("slide-03.png")
        no_drive = filhos(svc, pastas[d.name])
        for arq in alvos:
            local, fid = d / "png" / arq, no_drive.get(arq)
            if not local.exists() or not fid:
                print("pula:", d.name, arq, "(sem arquivo local ou no Drive)")
                continue
            print("atualiza:", d.name, arq)
            if not DRY:
                svc.files().update(fileId=fid, media_body=MediaFileUpload(str(local), mimetype="image/png")).execute()
            feitos += 1
    print("total:", feitos)


if __name__ == "__main__":
    main()
