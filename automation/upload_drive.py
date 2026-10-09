"""Sobe para o Drive (Clientes/otalogia/04-Carrosseis) todo carrossel com status "rascunho"
que ainda não tem pasta lá nem em 06-Aprovados-para-Postar, e cada roteiro semanal (roteiros/*.md)
que ainda não está em Clientes/otalogia/03-Roteiros, convertido em Google Doc. Roda no GitHub Actions (secrets GOOGLE_DRIVE_*); substitui o sync-drive.ps1 do PC.

Uso: python automation/upload_drive.py
"""
import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PASTA = "application/vnd.google-apps.folder"


def servico():
    c = Credentials(None, refresh_token=os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.environ["GOOGLE_DRIVE_CLIENT_ID"],
                    client_secret=os.environ["GOOGLE_DRIVE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive", "v3", credentials=c, cache_discovery=False)


def filhos(svc, pai, so_pastas=False):
    q = f"'{pai}' in parents and trashed = false" + (f" and mimeType = '{PASTA}'" if so_pastas else "")
    r = svc.files().list(q=q, fields="files(id,name)", pageSize=1000).execute()
    return {f["name"]: f["id"] for f in r["files"]}


def achar(svc, caminho):
    """Caminho de pastas a partir da raiz do Meu Drive, ex. Clientes/otalogia/04-Carrosseis."""
    atual = "root"
    for nome in caminho.split("/"):
        atual = filhos(svc, atual, True).get(nome) or sys.exit(f"pasta não encontrada no Drive: {nome}")
    return atual


def main():
    svc = servico()
    destino = achar(svc, "Clientes/otalogia/04-Carrosseis")
    # já enviado = existe em 04 (rascunhos) ou em 06 (aprovado e movido sem mudar o status no repo)
    no_drive = {**filhos(svc, destino, True), **filhos(svc, achar(svc, "Clientes/otalogia/06-Aprovados-para-Postar"), True)}
    enviados = 0
    for d in sorted(Path("carrosseis").iterdir()):
        meta = d / "png" / "metadata.json"
        if not meta.exists() or d.name in no_drive:
            continue
        if json.loads(meta.read_text(encoding="utf-8")).get("status") != "rascunho":
            continue
        pasta = svc.files().create(body={"name": d.name, "mimeType": PASTA, "parents": [destino]}, fields="id").execute()["id"]
        arquivos = sorted((d / "png").iterdir()) + ([d / "legenda.md"] if (d / "legenda.md").exists() else [])
        for f in arquivos:
            svc.files().create(body={"name": f.name, "parents": [pasta]}, media_body=MediaFileUpload(str(f), resumable=True), fields="id").execute()
        print("enviado:", d.name, len(arquivos), "arquivos")
        enviados += 1
    print("total enviados:", enviados)

    pasta_roteiros = achar(svc, "Clientes/otalogia/03-Roteiros")
    ja = filhos(svc, pasta_roteiros)
    for f in sorted(Path("roteiros").glob("*.md")):
        nome = f"Roteiro {f.stem}"
        if nome in ja:
            continue
        svc.files().create(body={"name": nome, "parents": [pasta_roteiros], "mimeType": "application/vnd.google-apps.document"},
                           media_body=MediaFileUpload(str(f), mimetype="text/markdown"), fields="id").execute()
        print("roteiro enviado:", nome)


if __name__ == "__main__":
    main()
