#!/usr/bin/env python3
"""Libera SOMENTE PDFs aprovados por edição humana em iscas/categorias.json.
Checa ID/pasta/mimeType antes de conceder permissão anyone:reader (links enviados apenas após verificação de follow no webhook).
Não publica novos PDFs e não permite compartilhar arquivo fora de 07-Iscas-DM.
"""
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BRAND = os.environ["DM_BRAND"]
if BRAND not in ("aidealab", "otalogia"):
    raise SystemExit("Invalid DM_BRAND")
CONFIG = json.loads(Path("iscas/categorias.json").read_text("utf-8"))
PARENT_IDS = {
    "aidealab": "1Iy1SbNJ21j0ZbDIKgm38iOI4rZAVVBwW",
    "otalogia": "1pLmTAQ5rkwxhoQRBll78UepQ8I9BYcVf"
}
creds = Credentials(None, refresh_token=os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.environ["GOOGLE_DRIVE_CLIENT_ID"],
                    client_secret=os.environ["GOOGLE_DRIVE_CLIENT_SECRET"],
                    scopes=["https://www.googleapis.com/auth/drive"])
creds.refresh(Request())
svc = build("drive", "v3", credentials=creds, cache_discovery=False)

approved = 0
for category, data in CONFIG["categorias"].items():
    for guide in data.get("guias", []):
        if guide.get("status") not in ("aprovado", "publicado"):
            continue
        fid = guide.get("drive_file_id")
        if not fid:
            raise RuntimeError(f"{category}: guia aprovado sem drive_file_id")
        found = svc.files().get(fileId=fid, fields="id,name,mimeType,parents,webViewLink").execute()
        if found.get("mimeType") != "application/pdf" or PARENT_IDS[BRAND] not in found.get("parents", []):
            raise RuntimeError(f"{category}: arquivo não corresponde ao PDF da pasta autorizada")
        perms = svc.permissions().list(fileId=fid, fields="permissions(id,type,role)").execute()
        if not any(p["type"] == "anyone" and p["role"] in ("reader","writer") for p in perms.get("permissions", [])):
            svc.permissions().create(fileId=fid, body={"type": "anyone", "role": "reader"},
                                     fields="id").execute()
        verified = svc.permissions().list(fileId=fid, fields="permissions(type,role)").execute()
        if not any(p["type"]=="anyone" and p["role"] in ("reader","writer") for p in verified.get("permissions",[])):
            raise RuntimeError(f"{category}: leitura por link não confirmada")
        approved += 1
        print(f"OK {BRAND}/{category}: PDF pronto para ser enviado por DM ({fid})")
if not approved:
    raise RuntimeError("Nenhum PDF aprovado nesta marca")
print(f"Total {approved} documentos aprovados com acesso por link.")
