#!/usr/bin/env python3
"""Devolve uma pasta de 'publicados' para a fila do Drive (postado=false) e a coloca como próxima (ordem_fila=0)."""
import json, sys, urllib.parse, urllib.request
from gdrive_live import GoogleDriveLive

nome = sys.argv[1]
g = GoogleDriveLive()
g.authenticate()
pub = g.get_or_create_publicados_folder_id()
q = urllib.parse.quote(f"'{pub}' in parents and name = '{nome}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
fs = g._api_get(f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)")["files"]
if not fs:
    sys.exit(f"Pasta '{nome}' não encontrada em publicados")
fid = fs[0]["id"]
q = urllib.parse.quote(f"'{fid}' in parents and name = 'metadata.json' and trashed = false")
mid = g._api_get(f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id)")["files"][0]["id"]
req = urllib.request.Request(f"https://www.googleapis.com/drive/v3/files/{mid}?alt=media", headers={"Authorization": f"Bearer {g.access_token}"})
meta = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
meta.update(postado=False, postado_em=None, post_id=None, ordem_fila=0)
req = urllib.request.Request(f"https://www.googleapis.com/upload/drive/v3/files/{mid}?uploadType=media",
    data=json.dumps(meta, indent=2, ensure_ascii=False).encode("utf-8"),
    headers={"Authorization": f"Bearer {g.access_token}", "Content-Type": "application/json"}, method="PATCH")
urllib.request.urlopen(req)
req = urllib.request.Request(f"https://www.googleapis.com/drive/v3/files/{fid}?addParents={g.folder_id}&removeParents={pub}",
    headers={"Authorization": f"Bearer {g.access_token}"}, method="PATCH")
urllib.request.urlopen(req)
print(f"✅ '{nome}' voltou para a fila (postado=false, ordem_fila=0)")
