#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gdrive_live.py
--------------
Integração direta em tempo real com a Google Drive API para o publicador da Otalogia:
1. Autentica via OAuth 2.0 (refresh_token permanente).
2. Varre a pasta '06-Aprovados-para-Postar' diretamente nos servidores do Google.
3. Lê os arquivos metadata.json de cada carrossel e identifica o próximo pendente (respeitando ordem_fila).
4. Faz download dos assets mais recentes (slides e legenda) direto do Drive para a máquina de execução.
5. Após o post bem-sucedido, atualiza o metadata.json no Google Drive com 'postado': true, data e post_id.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


class GoogleDriveLive:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        folder_id: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("GDRIVE_CLIENT_ID", "").strip()
        self.client_secret = client_secret or os.getenv("GDRIVE_CLIENT_SECRET", "").strip()
        self.refresh_token = refresh_token or os.getenv("GDRIVE_REFRESH_TOKEN", "").strip()
        self.folder_id = folder_id or (os.getenv("GDRIVE_FOLDER_ID_OTALOGIA") or "13GZEPJrWJaf9rWB4RFQXf5Hh0wRp27D6").strip()
        self.access_token = None

        # Fallback local se não estiver no env
        if not (self.client_id and self.client_secret and self.refresh_token):
            token_path = Path(r"D:\antigravity\gerador-prompt\token.json")
            if token_path.exists():
                try:
                    c = json.loads(token_path.read_text(encoding="utf-8"))
                    self.client_id = self.client_id or c.get("client_id", "")
                    self.client_secret = self.client_secret or c.get("client_secret", "")
                    self.refresh_token = self.refresh_token or c.get("refresh_token", "")
                except Exception:
                    pass

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token and self.folder_id)

    def authenticate(self) -> str:
        """Renova o token de acesso temporário usando o refresh_token."""
        if not self.is_configured():
            raise RuntimeError("Credenciais do Google Drive não configuradas no ambiente.")

        token_url = "https://oauth2.googleapis.com/token"
        payload = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }).encode("utf-8")

        req = urllib.request.Request(token_url, data=payload)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.access_token = data.get("access_token")
            return self.access_token

    def _api_get(self, url: str) -> Dict[str, Any]:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.access_token}"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _download_file(self, file_id: str, dest_path: Path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.access_token}"})
        with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
            while chunk := resp.read(65536):
                f.write(chunk)

    def fetch_live_queue(self) -> list:
        """Busca todas as pastas na pasta 06-Aprovados-para-Postar e ordena a fila."""
        if not self.access_token:
            self.authenticate()

        q = urllib.parse.quote(f"'{self.folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        url = f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)"
        res = self._api_get(url)
        folders = res.get("files", [])

        queue = []
        for folder in folders:
            fid = folder["id"]
            fname = folder["name"]

            # Ignora pasta de publicados ou pastas do sistema
            if fname.lower() in ["publicados", "07-publicados", "postados", "lixeira"]:
                continue

            # Localiza metadata.json dentro da pasta
            q_meta = urllib.parse.quote(f"'{fid}' in parents and name = 'metadata.json' and trashed = false")
            meta_res = self._api_get(f"https://www.googleapis.com/drive/v3/files?q={q_meta}&fields=files(id,name)")
            meta_files = meta_res.get("files", [])

            if meta_files:
                meta_id = meta_files[0]["id"]
                down_url = f"https://www.googleapis.com/drive/v3/files/{meta_id}?alt=media"
                req_down = urllib.request.Request(down_url, headers={"Authorization": f"Bearer {self.access_token}"})
                try:
                    with urllib.request.urlopen(req_down) as r:
                        meta_data = json.loads(r.read().decode("utf-8"))
                except Exception as e:
                    print(f"⚠️ Erro ao ler metadata.json de {fname}: {e}")
                    continue

                status = meta_data.get("status")
                postado = meta_data.get("postado", False)
                ordem = meta_data.get("ordem_fila")
                ordem_val = int(ordem) if (isinstance(ordem, int) or (isinstance(ordem, str) and str(ordem).isdigit())) else 9999

                queue.append({
                    "folder_name": fname,
                    "folder_id": fid,
                    "meta_file_id": meta_id,
                    "metadata": meta_data,
                    "status": status,
                    "postado": postado,
                    "ordem_fila": ordem,
                    "ordem_val": ordem_val,
                })

        queue.sort(key=lambda x: (x["ordem_val"], x["folder_name"]))
        return queue

    def download_next_carousel(self, target_base_dir: Path, prefer: Optional[str] = None) -> Optional[Tuple[Path, str, str, Dict[str, Any]]]:
        """
        Seleciona o próximo carrossel aprovado e não postado e baixa todos os seus arquivos.
        Retorna (pasta_local, meta_file_id, gdrive_folder_id, metadata).
        """
        queue = self.fetch_live_queue()
        # Qualquer carrossel dentro da pasta '06-Aprovados-para-Postar' que não tenha sido postado e não esteja rejeitado é considerado aprovado
        pendentes = [item for item in queue if item.get("status") != "rejeitado" and not item.get("postado")]
        # `cliente` no metadata é só rótulo: a conta de destino vem dos secrets (sempre @otalogia). Só avisa.
        for i in pendentes:
            cli = (i["metadata"].get("cliente") or "otalogia").lower()
            if cli != "otalogia":
                print(f"ℹ️ {i['folder_name']}: metadata com cliente '{cli}' (será publicado no @otalogia)")
        reels = [i for i in pendentes if i["metadata"].get("tipo") == "reel"]
        # Carrossel só animado (pasta montada pelo motion-drive do otalogia-post). Estático espera o motion;
        # PERMITIR_ESTATICO=1 libera o estático quando não houver nenhum animado na fila.
        carr = [i for i in pendentes if i["metadata"].get("tipo") != "reel"]
        animados = [i for i in carr if i["metadata"].get("formato_midia") == "motion-capa"]
        for i in carr:
            if i not in animados:
                print(f"⏸️ Pulado (sem motion ainda): {i['folder_name']}")
        if animados or os.environ.get("PERMITIR_ESTATICO") != "1":
            carr = animados
        por_tipo = {"reel": reels, "carrossel": carr}
        outro = "carrossel" if prefer == "reel" else "reel"
        pendentes = por_tipo.get(prefer, []) + por_tipo.get(outro, []) if prefer else sorted(reels + carr, key=lambda x: (x["ordem_val"], x["folder_name"]))

        if not pendentes:
            print("✨ Nenhum carrossel pendente no Google Drive no momento.")
            return None

        chosen = pendentes[0]
        folder_name = chosen["folder_name"]
        folder_id = chosen["folder_id"]
        meta_file_id = chosen["meta_file_id"]

        print(f"\n☁️ [Google Drive API] Selecionado para publicação: {folder_name} (Ordem: {chosen['ordem_fila']})")
        print(f"📥 Baixando arquivos mais recentes diretamente do Google Drive...")

        local_carousel_dir = target_base_dir / folder_name
        local_carousel_dir.mkdir(parents=True, exist_ok=True)

        # Baixa todos os arquivos da pasta e eventuais subpastas recursivamente (ex: motion/)
        def _download_folder_contents(current_folder_id: str, current_dest_dir: Path):
            q_files = urllib.parse.quote(f"'{current_folder_id}' in parents and trashed = false")
            files_res = self._api_get(f"https://www.googleapis.com/drive/v3/files?q={q_files}&fields=files(id,name,mimeType)")
            for item in files_res.get("files", []):
                iname = item["name"]
                if iname.lower() == "desktop.ini":
                    continue
                if item.get("mimeType") == "application/vnd.google-apps.folder":
                    sub_dest = current_dest_dir / iname
                    sub_dest.mkdir(parents=True, exist_ok=True)
                    _download_folder_contents(item["id"], sub_dest)
                else:
                    dest_file = current_dest_dir / iname
                    print(f"  ⬇️ Baixando: {dest_file.relative_to(local_carousel_dir)}...")
                    self._download_file(item["id"], dest_file)

        _download_folder_contents(folder_id, local_carousel_dir)

        print(f"✅ Todos os arquivos do carrossel baixados com sucesso em: {local_carousel_dir}")
        return local_carousel_dir, meta_file_id, folder_id, chosen["metadata"]

    def mark_carousel_as_posted(self, meta_file_id: str, post_id: str, posted_at: str):
        """Atualiza o metadata.json no Google Drive com o status de publicado."""
        if not self.access_token:
            self.authenticate()

        down_url = f"https://www.googleapis.com/drive/v3/files/{meta_file_id}?alt=media"
        req_down = urllib.request.Request(down_url, headers={"Authorization": f"Bearer {self.access_token}"})
        with urllib.request.urlopen(req_down) as r:
            meta = json.loads(r.read().decode("utf-8"))

        meta["postado"] = True
        meta["postado_em"] = posted_at
        meta["post_id"] = post_id

        upload_url = f"https://www.googleapis.com/upload/drive/v3/files/{meta_file_id}?uploadType=media"
        payload = json.dumps(meta, indent=2, ensure_ascii=False).encode("utf-8")
        req_patch = urllib.request.Request(
            upload_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            method="PATCH",
        )
        with urllib.request.urlopen(req_patch) as resp:
            print(f"☁️ [Google Drive API] Sucesso! metadata.json atualizado na nuvem (postado: True, id: {post_id}).")

    def get_or_create_publicados_folder_id(self) -> str:
        """Localiza ou cria a pasta 'publicados' dentro da pasta de carrosséis da Otalogia."""
        if not self.access_token:
            self.authenticate()

        q = urllib.parse.quote(f"'{self.folder_id}' in parents and name = 'publicados' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        res = self._api_get(f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)")
        files = res.get("files", [])
        if files:
            return files[0]["id"]

        create_url = "https://www.googleapis.com/drive/v3/files"
        body = json.dumps({
            "name": "publicados",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [self.folder_id]
        }).encode("utf-8")
        req = urllib.request.Request(
            create_url,
            data=body,
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["id"]

    def move_carousel_to_published(self, carousel_folder_id: str):
        """Move a pasta do carrossel para a pasta 'publicados' no Google Drive."""
        if not self.access_token:
            self.authenticate()

        publicados_id = self.get_or_create_publicados_folder_id()
        url = f"https://www.googleapis.com/drive/v3/files/{carousel_folder_id}?addParents={publicados_id}&removeParents={self.folder_id}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.access_token}"}, method="PATCH")
        with urllib.request.urlopen(req) as resp:
            print("📦 [Google Drive API] Pasta do carrossel movida automaticamente para 'publicados'!")


if __name__ == "__main__":
    print("==================================================")
    print(" FILA EM TEMPO REAL: GOOGLE DRIVE (OTALOGIA)")
    print("==================================================")
    gdrive = GoogleDriveLive()
    try:
        q = gdrive.fetch_live_queue()
        for item in q:
            icon = "✅ Postado" if item["postado"] else ("⏳ Pendente" if item["status"] == "aprovado" else "⏸️ Outro")
            print(f"[{item['ordem_val']}] {item['folder_name']} -> {icon} (ordem_fila={item['ordem_fila']})")
            print(f"    Tema: {item['metadata'].get('tema')}")
        pendentes = [i for i in q if i["status"] == "aprovado" and not i["postado"]]
        if pendentes:
            print(f"\n🎯 PRÓXIMO DA FILA: {pendentes[0]['folder_name']} (Ordem: {pendentes[0]['ordem_fila']})")
        else:
            print("\n✨ Nenhum carrossel pendente na fila.")
    except Exception as e:
        print(f"❌ Erro ao consultar fila: {e}")
