"""Atualiza no Drive o slide CTA (último PNG) dos carrosséis da otalogia já enviados, com o render atual do repo
(halftone no CTA inteiro). Procura a pasta pelo nome do carrossel em Clientes/otalogia/04-Carrosseis e em
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
        cta = f"slide-{len(json.loads(cj.read_text(encoding='utf-8'))['slides']):02d}.png"
        local = d / "png" / cta
        fid = filhos(svc, pastas[d.name]).get(cta)
        if not local.exists() or not fid:
            print("pula:", d.name, cta, "(sem arquivo local ou no Drive)")
            continue
        print("CTA:", d.name, cta)
        if not DRY:
            svc.files().update(fileId=fid, media_body=MediaFileUpload(str(local), mimetype="image/png")).execute()
        feitos += 1
    print("total:", feitos)


if __name__ == "__main__":
    main()
