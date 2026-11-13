#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
instagram_publisher.py
----------------------
Módulo e utilitário CLI para publicação automática de Carrosséis no Instagram
via Instagram Graph API (Meta), lendo pastas e metadados gerados no Google Drive / local.

Fluxo da Instagram Graph API para Carrossel (3 etapas):
1. Cria containers individuais para cada slide (is_carousel_item=true)
2. Cria o container do Carrossel referenciando todos os IDs filhos + Legenda
3. Publica o container (media_publish)

Requisitos de Imagens do Instagram:
- URLs acessíveis publicamente via HTTPS (JPEG / PNG).
- Proporção recomendada: 4:5 (1080x1350), 3:4 (1080x1440) ou 1:1 (1080x1080).
- Limite de slides: 2 a 10 imagens por carrossel.
"""

import os
import sys
import json
import time
import shutil
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Carrega variáveis do arquivo .env local se existir
ENV_PATH = Path(__file__).resolve().parent / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

FILA_DIR = Path(__file__).resolve().parent.parent / "fila"  # fila de publicação (só metadata/legenda no git; mídia vem do Drive)

GRAPH_API_VERSION = os.getenv("META_GRAPH_VERSION", "v21.0")
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def exchange_and_setup_token(user_token: str) -> Dict[str, Any]:
    """
    Converte um User Token temporário em:
    1. Long-Lived User Token (60 dias)
    2. Page Access Token permanente (nunca expira) vinculado ao Instagram da Otalogia
    3. Salva automaticamente no .env
    """
    app_id = os.getenv("META_APP_ID", "").strip()
    app_secret = os.getenv("META_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise SystemExit("Defina META_APP_ID e META_APP_SECRET no .env")

    print("🔄 [Passo 1/3] Convertendo token temporário para Token de Longa Duração (60 dias)...")
    res = requests.get(
        f"{GRAPH_BASE_URL}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": user_token,
        },
        timeout=15,
    )
    data = res.json()
    if "error" in data:
        raise RuntimeError(f"Erro ao trocar token: {data['error'].get('message')}")

    long_lived_token = data.get("access_token", user_token)
    print("  ✅ Token de longa duração gerado com sucesso!")

    print("🔍 [Passo 2/3] Localizando Páginas e Contas do Instagram vinculadas...")
    res_pages = requests.get(
        f"{GRAPH_BASE_URL}/me/accounts",
        params={
            "fields": "id,name,access_token,instagram_business_account{id,username,name}",
            "access_token": long_lived_token,
        },
        timeout=15,
    )
    pages_data = res_pages.json()
    if "error" in pages_data:
        raise RuntimeError(f"Erro ao buscar páginas: {pages_data['error'].get('message')}")

    pages = pages_data.get("data", [])
    if not pages:
        raise RuntimeError(
            "Nenhuma Página do Facebook encontrada para este usuário. "
            "Certifique-se de que você é Administrador da Página da Otalogia e autorizou-a no popup."
        )

    # Procura página com conta do Instagram conectada
    selected_page = None
    ig_account = None

    for p in pages:
        ig = p.get("instagram_business_account")
        if ig:
            selected_page = p
            ig_account = ig
            break

    if not selected_page:
        # Se nenhuma tiver o Instagram vinculado ainda, pega a primeira página
        selected_page = pages[0]
        print(f"⚠️ Página '{selected_page.get('name')}' encontrada, mas ainda sem Instagram vinculado nela.")
    else:
        print(f"  ✅ Página encontrada: {selected_page.get('name')} (ID: {selected_page.get('id')})")
        print(f"  ✨ Instagram detectado: @{ig_account.get('username')} (ID: {ig_account.get('id')})")

    # O Page Access Token derivado de um Long-Lived Token NUNCA EXPIRA!
    permanent_token = selected_page.get("access_token", long_lived_token)
    ig_id = ig_account.get("id") if ig_account else ""

    print("💾 [Passo 3/3] Gravando configurações permanentes no arquivo .env...")
    env_content = f"""# Meta Developer App Credentials (API_POST)
META_APP_ID={app_id}
META_APP_SECRET={app_secret}

# Instagram & Meta Access Token Permanente
META_ACCESS_TOKEN={permanent_token}
INSTAGRAM_ACCOUNT_ID={ig_id}

# Supabase Storage (para servir imagens do carrossel ao Instagram)
NEXT_PUBLIC_SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
INSTAGRAM_MEDIA_BUCKET=instagram-carousels
"""
    ENV_PATH.write_text(env_content, encoding="utf-8")
    os.environ["META_ACCESS_TOKEN"] = permanent_token
    if ig_id:
        os.environ["INSTAGRAM_ACCOUNT_ID"] = ig_id

    print("🎉 Configuração concluída com sucesso no .env!")
    return {
        "page_name": selected_page.get("name"),
        "ig_username": ig_account.get("username") if ig_account else None,
        "ig_id": ig_id,
        "token_sample": f"{permanent_token[:15]}...{permanent_token[-6:]}",
    }



class InstagramClient:
    """Cliente oficial para interação com a Instagram Graph API."""

    def __init__(self, access_token: Optional[str] = None, ig_user_id: Optional[str] = None):
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN", "").strip()
        self.ig_user_id = ig_user_id or os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip()

        if not self.access_token:
            raise ValueError(
                "Access Token não informado. Defina META_ACCESS_TOKEN nas variáveis de ambiente ou passe no construtor."
            )

    def validate_connection(self) -> Dict[str, Any]:
        """Testa o token e retorna informações da conta do Instagram conectada."""
        if not self.ig_user_id:
            # Tenta descobrir o ID procurando nas contas associadas
            print("🔍 Buscando contas do Instagram associadas ao token...")
            res = requests.get(
                f"{GRAPH_BASE_URL}/me/accounts",
                params={
                    "fields": "id,name,instagram_business_account{id,username,name}",
                    "access_token": self.access_token,
                },
                timeout=15,
            )
            data = res.json()
            if "error" in data:
                raise RuntimeError(f"Erro ao consultar contas: {data['error'].get('message')}")

            pages = data.get("data", [])
            ig_accounts = []
            for p in pages:
                ig_info = p.get("instagram_business_account")
                if ig_info:
                    ig_accounts.append({
                        "page_name": p.get("name"),
                        "page_id": p.get("id"),
                        "ig_id": ig_info.get("id"),
                        "ig_username": ig_info.get("username"),
                    })

            if not ig_accounts:
                raise RuntimeError(
                    "Nenhuma conta de Instagram Business/Creator vinculada encontrada nas páginas deste token."
                )

            # Usa a primeira encontrada
            self.ig_user_id = ig_accounts[0]["ig_id"]
            print(f"✅ Conta encontrada: @{ig_accounts[0]['ig_username']} (ID: {self.ig_user_id})")
            return {"status": "ok", "accounts": ig_accounts, "active_id": self.ig_user_id}

        # Valida o ig_user_id fornecido
        res = requests.get(
            f"{GRAPH_BASE_URL}/{self.ig_user_id}",
            params={
                "fields": "id,username,name,profile_picture_url",
                "access_token": self.access_token,
            },
            timeout=15,
        )
        data = res.json()
        if "error" in data:
            raise RuntimeError(f"Erro ao validar conta {self.ig_user_id}: {data['error'].get('message')}")

        return {"status": "ok", "account": data}

    def create_item_container(self, media_url: str, is_video: bool = False) -> str:
        """Etapa 1: Cria container para 1 slide do carrossel (imagem ou vídeo)."""
        payload = {
            "is_carousel_item": "true",
            "access_token": self.access_token,
        }
        if is_video:
            payload["media_type"] = "VIDEO"
            payload["video_url"] = media_url
        else:
            payload["image_url"] = media_url

        res = requests.post(f"{GRAPH_BASE_URL}/{self.ig_user_id}/media", data=payload, timeout=45)
        data = res.json()
        if "error" in data:
            raise RuntimeError(f"Erro ao criar container de slide: {data['error'].get('message')}")
        
        container_id = data["id"]

        # Se for vídeo, é obrigatório aguardar a Meta transcodificar e marcar como FINISHED
        if is_video:
            self.wait_for_container_finished(container_id)

        return container_id

    def wait_for_container_finished(self, container_id: str, max_retries: int = 30, interval: int = 5) -> None:
        """Verifica periodicamente se o processamento do vídeo no Instagram foi concluído (status_code == FINISHED)."""
        print(f"    ⏳ Aguardando processamento do vídeo na Meta (ID: {container_id})...")
        for attempt in range(1, max_retries + 1):
            time.sleep(interval)
            res = requests.get(
                f"{GRAPH_BASE_URL}/{container_id}",
                params={"fields": "status_code", "access_token": self.access_token},
                timeout=15,
            )
            data = res.json()
            status_code = data.get("status_code")
            if status_code == "FINISHED":
                print(f"    ✅ Vídeo processado pela Meta com sucesso!")
                return
            elif status_code == "ERROR":
                err_msg = data.get("status", "Erro desconhecido no processamento do vídeo")
                raise RuntimeError(f"Erro no processamento do vídeo pelo Instagram: {err_msg}")
            elif status_code == "EXPIRED":
                raise RuntimeError("O container de vídeo expirou antes de ser publicado.")
            print(f"    ⏳ Processando vídeo na Meta... ({attempt}/{max_retries} - status: {status_code})")

        raise TimeoutError(f"Tempo limite excedido aguardando processamento do vídeo {container_id}")

    def create_carousel_container(self, children_ids: List[str], caption: str) -> str:
        """Etapa 2: Cria o container pai do Carrossel reunindo os slides filhos."""
        if not (2 <= len(children_ids) <= 10):
            raise ValueError(f"Um carrossel do Instagram deve conter de 2 a 10 slides. Recebido: {len(children_ids)}")

        payload = {
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": self.access_token,
        }
        res = requests.post(f"{GRAPH_BASE_URL}/{self.ig_user_id}/media", data=payload, timeout=30)
        data = res.json()
        if "error" in data:
            raise RuntimeError(f"Erro ao criar container do carrossel: {data['error'].get('message')}")
        return data["id"]

    def publish_container(self, creation_id: str, max_retries: int = 15, retry_interval: int = 5) -> str:
        """Etapa 3: Publica o container no Feed do Instagram com checagem de processamento."""
        payload = {
            "creation_id": creation_id,
            "access_token": self.access_token,
        }

        # O Instagram pode precisar de alguns instantes para processar todas as imagens/vídeos do carrossel
        for attempt in range(1, max_retries + 1):
            res = requests.post(f"{GRAPH_BASE_URL}/{self.ig_user_id}/media_publish", data=payload, timeout=30)
            data = res.json()

            if "id" in data:
                return data["id"]

            error = data.get("error", {})
            err_subcode = error.get("error_subcode")
            # Subcode 2207027 = Mídia ainda não terminou de ser processada
            if err_subcode == 2207027 or "ready" in error.get("message", "").lower():
                print(f"⏳ Processando mídias no Instagram... aguardando {retry_interval}s (tentativa {attempt}/{max_retries})")
                time.sleep(retry_interval)
                continue

            raise RuntimeError(f"Erro ao publicar carrossel: {error.get('message')}")

        raise TimeoutError("Tempo limite esgotado esperando processamento do carrossel no Instagram.")

    def publish_reel(self, video_url: str, caption: str, cover_url: Optional[str] = None) -> str:
        """Publica um Reel (vídeo único, também no feed)."""
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": self.access_token,
        }
        if cover_url:
            payload["cover_url"] = cover_url
        print("\n🎬 Criando container do Reel...")
        data = requests.post(f"{GRAPH_BASE_URL}/{self.ig_user_id}/media", data=payload, timeout=60).json()
        if "error" in data:
            raise RuntimeError(f"Erro ao criar container do Reel: {data['error'].get('message')}")
        self.wait_for_container_finished(data["id"], max_retries=72, interval=5)
        time.sleep(3)
        post_id = self.publish_container(data["id"])
        print(f"  ✅ Reel publicado! Post ID: {post_id}")
        return post_id

    def publish_reel_resumable(self, video_path: Path, caption: str, cover_url: Optional[str] = None) -> str:
        """Reel grande: envia o arquivo direto ao Instagram (rupload), sem passar pelo Supabase (limite de tamanho)."""
        payload = {
            "media_type": "REELS", "upload_type": "resumable", "caption": caption,
            "share_to_feed": "true", "access_token": self.access_token,
        }
        if cover_url:
            payload["cover_url"] = cover_url
        print("\n🎬 Criando container do Reel (upload resumível direto no Instagram)...")
        data = requests.post(f"{GRAPH_BASE_URL}/{self.ig_user_id}/media", data=payload, timeout=60).json()
        if "error" in data:
            raise RuntimeError(f"Erro ao criar container do Reel: {data['error'].get('message')}")
        container_id, uri = data["id"], data.get("uri")
        if not uri:
            raise RuntimeError(f"Instagram não devolveu a URL de upload resumível: {data}")
        size = video_path.stat().st_size
        print(f"  ⬆️ Enviando {size // 1_000_000} MB ao Instagram...")
        with open(video_path, "rb") as f:
            up = requests.post(uri, data=f, timeout=1800, headers={
                "Authorization": f"OAuth {self.access_token}", "offset": "0", "file_size": str(size)})
        if up.status_code != 200 or not up.json().get("success"):
            raise RuntimeError(f"Falha no upload resumível ({up.status_code}): {up.text[:300]}")
        self.wait_for_container_finished(container_id, max_retries=120, interval=5)
        time.sleep(3)
        post_id = self.publish_container(container_id)
        print(f"  ✅ Reel publicado! Post ID: {post_id}")
        return post_id

    def publish_carousel(self, media_items: List[Any], caption: str) -> str:
        """Orquestra as 3 etapas de publicação de um carrossel completo (imagens e/ou vídeos)."""
        print(f"\n🚀 Iniciando publicação de Carrossel com {len(media_items)} slides...")

        # 1. Cria cada container de slide
        item_ids = []
        for idx, item in enumerate(media_items, start=1):
            if isinstance(item, dict):
                url = item.get("url") or item.get("public_url")
                is_vid = item.get("is_video", False)
                label = "vídeo (motion)" if is_vid else "imagem"
            else:
                url = str(item)
                is_vid = any(url.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm"])
                label = "vídeo (motion)" if is_vid else "imagem"

            print(f"  📤 Enviando slide {idx}/{len(media_items)} [{label}]: {url[:60]}...")
            item_id = self.create_item_container(url, is_video=is_vid)
            item_ids.append(item_id)
            time.sleep(1)  # Intervalo de cortesia para evitar throttling

        # 2. Cria container pai
        print("  📦 Agrupando slides no container do Carrossel...")
        carousel_id = self.create_carousel_container(item_ids, caption)

        # 3. Aguarda 3 segundos para propagação dos servidores da Meta
        time.sleep(3)

        # 4. Publica
        print("  🎉 Disparando publicação final...")
        published_post_id = self.publish_container(carousel_id)
        print(f"  ✅ Post publicado com sucesso! Post ID: {published_post_id}")
        return published_post_id


# Supabase Storage para hospedar mídias públicas com HTTPS exigidas pelo Instagram
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
REEL_MAX_SUPABASE = 45 * 1024 * 1024  # acima disso o reel vai direto ao Instagram (limite padrão do Supabase: 50 MB)
STORAGE_BUCKET = os.getenv("INSTAGRAM_MEDIA_BUCKET", "instagram-carousels")


def upload_image_to_public_storage(file_path: Path, remote_folder: str = "queue") -> str:
    """Faz upload de imagem ou vídeo local para o Supabase Storage e retorna a URL pública HTTPS."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Defina NEXT_PUBLIC_SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY")
    file_name = file_path.name
    remote_path = f"{remote_folder}/{int(time.time())}_{file_name}"
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{remote_path}"

    ext = file_path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        content_type = "image/jpeg"
    elif ext == ".png":
        content_type = "image/png"
    elif ext == ".webp":
        content_type = "image/webp"
    elif ext == ".mp4":
        content_type = "video/mp4"
    elif ext == ".mov":
        content_type = "video/quicktime"
    elif ext == ".webm":
        content_type = "video/webm"
    else:
        content_type = "application/octet-stream"

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": content_type,
    }

    with open(file_path, "rb") as f:  # streaming: reels passam de 100 MB
        res = requests.post(upload_url, data=f, headers=headers, timeout=600)
    if res.status_code not in (200, 201):
        raise RuntimeError(f"Falha no upload para o storage ({res.status_code}): {res.text}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{remote_path}"
    return public_url


def load_carousel_metadata(carousel_dir: Path) -> Optional[Dict[str, Any]]:
    """Carrega o arquivo metadata.json de uma pasta de carrossel."""
    meta_file = carousel_dir / "metadata.json"
    if not meta_file.exists():
        return None
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler {meta_file}: {e}")
        return None


def save_carousel_metadata(carousel_dir: Path, data: Dict[str, Any]) -> None:
    """Atualiza o metadata.json após publicação."""
    meta_file = carousel_dir / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def format_caption(meta: Dict[str, Any], custom_caption: Optional[str] = None) -> str:
    """Formata a legenda combinando texto e hashtags (suporta string ou array)."""
    if custom_caption:
        return custom_caption

    legenda = meta.get("legenda", "").strip()
    hashtags_data = meta.get("hashtags", "")

    if isinstance(hashtags_data, list):
        hashtags_str = " ".join(hashtags_data).strip()
    else:
        hashtags_str = str(hashtags_data).strip()

    # reels já trazem as hashtags dentro de "legenda": não duplica
    if hashtags_str and not all(h in legenda for h in hashtags_str.split()):
        return f"{legenda}\n\n{hashtags_str}"
    return legenda


def find_next_carousel_to_post(base_path: Path) -> Optional[Path]:
    """Varre pastas em busca do próximo carrossel aprovado e não postado, respeitando ordem_fila."""
    if not base_path.exists():
        return None

    candidates = []
    for folder in base_path.iterdir():
        if not folder.is_dir() or folder.name.lower() in ["publicados", "07-publicados", "postados", "lixeira"]:
            continue
        meta = load_carousel_metadata(folder)
        if meta and meta.get("status") != "rejeitado" and not meta.get("postado"):
            ordem = meta.get("ordem_fila")
            ordem_val = int(ordem) if (isinstance(ordem, int) or (isinstance(ordem, str) and str(ordem).isdigit())) else 9999
            candidates.append((ordem_val, folder.name, folder))

    if not candidates:
        return None

    # Ordena prioritariamente pela ordem_fila definida e secundariamente pelo nome da pasta
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]


def check_already_posted_today(account_id: str, access_token: str) -> bool:
    """Consulta a API do Instagram e verifica se já houve publicação hoje (no fuso de Cuiabá, UTC-4)."""
    if not account_id or not access_token:
        return False
    try:
        import datetime
        cuiaba_tz = datetime.timezone(datetime.timedelta(hours=-4))
        cuiaba_today = datetime.datetime.now(cuiaba_tz).strftime("%Y-%m-%d")

        url = f"{GRAPH_BASE_URL}/{account_id}/media"
        params = {
            "fields": "id,timestamp,caption",
            "limit": "5",
            "access_token": access_token
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            posts = resp.json().get("data", [])
            for p in posts:
                ts = p.get("timestamp")
                if ts:
                    dt_utc = datetime.datetime.fromisoformat(ts.replace("+0000", "+00:00"))
                    dt_cuiaba = dt_utc.astimezone(cuiaba_tz)
                    if dt_cuiaba.strftime("%Y-%m-%d") == cuiaba_today:
                        print(f"🔒 [Trava Diária] Publicação já realizada hoje às {dt_cuiaba.strftime('%H:%M:%S')} (Horário de Cuiabá) | Post ID: {p.get('id')}")
                        return True
    except Exception as e:
        print(f"⚠️ Aviso ao verificar limite diário na Meta API: {e}")
    return False


def last_post_kind(account_id: str, access_token: str) -> Optional[str]:
    """Tipo do último post do perfil ('reel' ou 'carrossel'), para alternar. None se não der pra saber."""
    try:
        r = requests.get(f"{GRAPH_BASE_URL}/{account_id}/media",
                         params={"fields": "media_product_type,media_type", "limit": "1", "access_token": access_token}, timeout=15)
        d = r.json().get("data", [])
        if r.status_code == 200 and d:
            return "reel" if d[0].get("media_product_type") == "REELS" else "carrossel"
    except Exception as e:
        print(f"⚠️ Não foi possível ler o último post: {e}")
    return None


def publish_reel_from_dir(target_dir: Path, meta: Dict[str, Any], caption: str) -> str:
    video = target_dir / meta.get("video", "reel.mp4")
    if not video.exists():
        print(f"❌ Vídeo do reel não encontrado: {video}")
        sys.exit(1)
    slug = meta.get("carousel_id", target_dir.name)
    print(f"\n🎬 Reel: {slug} ({video.stat().st_size // 1_000_000} MB)")
    capa = target_dir / meta["capa"] if meta.get("capa") else None
    cover_url = upload_image_to_public_storage(capa, remote_folder=f"otalogia/{slug}") if capa and capa.exists() else None
    if video.stat().st_size > REEL_MAX_SUPABASE:
        return InstagramClient().publish_reel_resumable(video, caption, cover_url)
    print("  ☁️ Gerando link público do vídeo...")
    video_url = upload_image_to_public_storage(video, remote_folder=f"otalogia/{slug}")
    return InstagramClient().publish_reel(video_url, caption, cover_url)


def test_meta_connection():
    """Função de teste para validar credenciais e imprimir diagnóstico."""
    print("==================================================")
    print(" DIAGNÓSTICO: INSTAGRAM GRAPH API / META SOCIAL")
    print(" Perfil Alvo: @otalogia")
    print("==================================================")
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip()

    if not token:
        print("⚠️ META_ACCESS_TOKEN não está definido.")
        print("   Adicione META_ACCESS_TOKEN nas variáveis de ambiente.")
        return

    print(f"🔑 Token detectado: {token[:10]}...{token[-5:]} (tamanho: {len(token)})")
    if ig_id:
        print(f"🆔 Instagram Account ID: {ig_id}")
    else:
        print("🆔 Instagram Account ID não definido (tentando detectar automaticamente via páginas)...")

    try:
        client = InstagramClient(token, ig_id)
        info = client.validate_connection()
        print("\n✨ CONEXÃO ESTABELECIDA COM SUCESSO!")
        print(json.dumps(info, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Falha na conexão: {e}")


def publish_carousel_from_dir(target_dir: Path, meta: Dict[str, Any], caption: str, args) -> str:
    # Coleta e ordena os slides
    slides = meta.get("slides", [])
    slides_sorted = sorted(slides, key=lambda s: s.get("ordem", 99))

    print(f"\n📂 Processando carrossel: {meta.get('carousel_id', target_dir.name)}")
    print(f"📝 Slides identificados: {len(slides_sorted)}")

    # Identifica formato dos slides (Motion / Vídeo vs Estático / Imagem)
    motion_dir = target_dir / "motion"
    has_motion_dir = motion_dir.is_dir() and not getattr(args, "static", False)

    media_items = []
    carousel_slug = meta.get("carousel_id", target_dir.name)
    is_any_video = False

    for s in slides_sorted:
        ordem = s.get("ordem", 1)
        orig_filename = s.get("arquivo", f"slide-{ordem:02d}.png")

        # Candidatos de arquivo em ordem de prioridade (Motion tem prioridade a menos que --static seja passado):
        # 1. Pasta motion/slide-01.mp4 ou motion/slide-1.mp4
        # 2. Raiz target_dir/slide-01.mp4
        # 3. Caminho especificado no metadata
        motion_cand_1 = motion_dir / f"slide-{ordem:02d}.mp4"
        motion_cand_2 = motion_dir / f"slide-{ordem}.mp4"
        root_mp4_cand = target_dir / f"slide-{ordem:02d}.mp4"
        explicit_cand = target_dir / orig_filename

        chosen_path = None
        if meta.get("formato_midia") == "motion-capa":
            # pasta já na ordem de postagem (capa PNG + vídeos): vale exatamente o que o metadata lista
            if not explicit_cand.exists():
                print(f"❌ Slide {ordem} não encontrado: {explicit_cand}")
                sys.exit(1)
            chosen_path = explicit_cand
        elif has_motion_dir and motion_cand_1.exists():
            chosen_path = motion_cand_1
        elif has_motion_dir and motion_cand_2.exists():
            chosen_path = motion_cand_2
        elif not getattr(args, "static", False) and root_mp4_cand.exists():
            chosen_path = root_mp4_cand
        elif explicit_cand.exists():
            chosen_path = explicit_cand
        else:
            print(f"❌ Slide não encontrado para ordem {ordem} em {target_dir}")
            sys.exit(1)

        is_video = chosen_path.suffix.lower() in [".mp4", ".mov", ".webm"]
        if is_video:
            is_any_video = True

        media_items.append({
            "path": chosen_path,
            "filename": chosen_path.name,
            "is_video": is_video,
            "ordem": ordem,
        })

    # carrossel animado: capa estática (PNG do hook, aparece pronta no feed) antes do hook animado.
    # A API aceita até 10 itens; com 10 slides, a capa estática entra no lugar do hook animado.
    if media_items and media_items[0]["is_video"]:
        s0 = slides_sorted[0]
        capa = target_dir / s0.get("arquivo", f"slide-{s0.get('ordem', 1):02d}.png")
        if capa.exists() and capa.suffix.lower() not in [".mp4", ".mov", ".webm"]:
            item_capa = {"path": capa, "filename": capa.name, "is_video": False, "ordem": s0.get("ordem", 1)}
            media_items = [item_capa] + (media_items if len(media_items) < 10 else media_items[1:])

    if is_any_video:
        print(f"🎬 Carrossel Animado (Motion) detectado! Slides em vídeo serão publicados.")
    else:
        print(f"🖼️ Carrossel Estático detectado! Slides em imagem serão publicados.")

    # Faz upload das mídias para o Storage público
    for item in media_items:
        tipo_str = "vídeo" if item["is_video"] else "imagem"
        print(f"  ☁️ Gerando link público para slide {item['ordem']} [{tipo_str}]: {item['filename']}...")
        public_url = upload_image_to_public_storage(item["path"], remote_folder=f"otalogia/{carousel_slug}")
        item["url"] = public_url

    # Publica na Meta Graph API
    return InstagramClient().publish_carousel(media_items, caption)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publicador de Carrosséis no Instagram via Meta Graph API (@otalogia)")
    parser.add_argument("--test", action="store_true", help="Testa a conexão e valida o token com a Meta")
    parser.add_argument("--setup-token", type=str, help="Token do usuário gerado no Graph Explorer para converter em token permanente")
    parser.add_argument("--dir", type=str, help="Caminho da pasta do carrossel para postar")
    parser.add_argument("--auto-next", action="store_true", help="Busca automaticamente o próximo carrossel da fila")
    parser.add_argument("--queue-dir", type=str, help="Diretório da fila (padrão: 06-Aprovados-para-Postar de otalogia)")
    parser.add_argument("--caption", type=str, help="Legenda customizada (sobrescreve metadata.json)")
    parser.add_argument("--force", action="store_true", help="Ignora a trava de 1 post por dia e força a publicação")
    parser.add_argument("--tipo", choices=["auto", "reel", "carrossel"], default="auto", help="auto = alterna com o último post; reel/carrossel = força o tipo")
    parser.add_argument("--no-wait", action="store_true", help="Não aguarda a janela das 06:00 se executado antes desse horário")
    parser.add_argument("--motion", action="store_true", help="Força o uso de slides em vídeo (motion)")
    parser.add_argument("--static", action="store_true", help="Força o uso de imagens estáticas ignorando vídeos")

    args = parser.parse_args()

    if args.setup_token:
        try:
            res = exchange_and_setup_token(args.setup_token.strip())
            print("\nResultado:")
            print(json.dumps(res, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erro ao configurar token: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.test or len(sys.argv) == 1:
        test_meta_connection()
        sys.exit(0)

    # 🔒 TRAVA DE SEGURANÇA: Garante estritamente apenas 1 post por dia (Horário de Cuiabá)
    if not args.force:
        token = os.getenv("META_ACCESS_TOKEN", "").strip()
        ig_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip()
        if check_already_posted_today(ig_id, token):
            import datetime
            cuiaba_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))
            print("======================================================================")
            print(f"🛑 TRAVA DIÁRIA ATIVADA ({cuiaba_now.strftime('%d/%m/%Y %H:%M:%S')} Cuiabá)")
            print("   Já existe 1 post publicado hoje no perfil @otalogia!")
            print("   Para evitar postagens duplicadas, apenas 1 post por dia é permitido.")
            print("   (Para forçar uma publicação extra no mesmo dia, use a flag --force).")
            print("======================================================================")
            sys.exit(0)

    # ⏰ GARANTIA DA JANELA (06:00 - 08:00 Cuiabá): Se disparado antes das 06:00 para contornar filas, aguarda até as 06:00
    if not args.force and not getattr(args, "no_wait", False):
        import datetime
        cuiaba_tz = datetime.timezone(datetime.timedelta(hours=-4))
        now_cuiaba = datetime.datetime.now(cuiaba_tz)
        if now_cuiaba.hour < 6:
            target_time = now_cuiaba.replace(hour=6, minute=0, second=5, microsecond=0)
            wait_seconds = (target_time - now_cuiaba).total_seconds()
            if 0 < wait_seconds <= 3600:
                print(f"⏳ Horário atual em Cuiabá ({now_cuiaba.strftime('%H:%M:%S')}) é anterior às 06:00.")
                print(f"   Aguardando {int(wait_seconds)}s ({int(wait_seconds/60)} min) para publicar pontualmente na abertura da janela (06:00)...")
                time.sleep(wait_seconds)

    target_dir = None
    gdrive_meta_file_id = None
    gdrive_carousel_folder_id = None
    gdrive_client = None

    if args.dir:
        target_dir = Path(args.dir)
    elif args.auto_next:
        # Se credenciais do Google Drive estiverem disponíveis, busca em tempo real na nuvem do Drive
        from gdrive_live import GoogleDriveLive
        gdrive = GoogleDriveLive()
        if gdrive.is_configured():
            print("🌐 [Modo Nuvem] Conectando diretamente à API do Google Drive em tempo real...")
            base_temp = FILA_DIR
            prefer = args.tipo
            if prefer == "auto":
                ult = last_post_kind(os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip(), os.getenv("META_ACCESS_TOKEN", "").strip())
                prefer = {"reel": "carrossel", "carrossel": "reel"}.get(ult)
                print(f"🔁 Último post: {ult or 'desconhecido'} → preferência de hoje: {prefer or 'qualquer'}")
            gdrive_res = gdrive.download_next_carousel(base_temp, prefer=prefer)
            if not gdrive_res:
                print("✨ Nenhum carrossel pendente no Google Drive no momento.")
                sys.exit(0)
            target_dir, gdrive_meta_file_id, gdrive_carousel_folder_id, _ = gdrive_res
            gdrive_client = gdrive
        else:
            drive_path = Path(r"C:\Users\luizr\Meu Drive (aidealabbr@gmail.com)\Clientes\otalogia\06-Aprovados-para-Postar")
            repo_path = FILA_DIR

            if args.queue_dir:
                default_queue = Path(args.queue_dir)
            elif drive_path.exists():
                default_queue = drive_path
            elif repo_path.exists():
                default_queue = repo_path
            else:
                default_queue = FILA_DIR

            print(f"🔍 Procurando próximo carrossel pendente em: {default_queue}")
            target_dir = find_next_carousel_to_post(default_queue)
            if not target_dir:
                print("✨ Nenhum carrossel pendente na fila no momento.")
                sys.exit(0)
            print(f"🎯 Próximo carrossel selecionado: {target_dir.name}")

    if not target_dir or not target_dir.is_dir():
        print(f"❌ Diretório inválido ou não especificado: {target_dir}")
        sys.exit(1)

    meta = load_carousel_metadata(target_dir)
    if not meta:
        print(f"❌ metadata.json não encontrado em {target_dir}")
        sys.exit(1)

    if meta.get("postado"):
        print(f"ℹ️ Este carrossel já foi postado anteriormente em {meta.get('postado_em') or meta.get('data_postagem')}.")
        sys.exit(0)

    # Monta a legenda completa com hashtags
    caption = format_caption(meta, args.caption)

    if meta.get("tipo") == "reel":
        post_id = publish_reel_from_dir(target_dir, meta, caption)
    else:
        post_id = publish_carousel_from_dir(target_dir, meta, caption, args)

    # Atualiza metadados locais
    now_iso = time.strftime("%Y-%m-%d %H:%M:%S")
    meta["postado"] = True
    meta["postado_em"] = now_iso
    meta["post_id"] = post_id
    save_carousel_metadata(target_dir, meta)
    print(f"\n🎉 Post publicado com sucesso no perfil @otalogia!")
    print(f"🆔 Post ID: {post_id}")
    print(f"💾 Metadados salvos localmente em: {target_dir / 'metadata.json'}")

    # Atualiza diretamente no Google Drive se foi puxado da nuvem do Drive
    if gdrive_client and gdrive_meta_file_id:
        try:
            print("☁️ Atualizando status de 'postado' diretamente no Google Drive...")
            gdrive_client.mark_carousel_as_posted(gdrive_meta_file_id, post_id, now_iso)
            if gdrive_carousel_folder_id:
                print("📦 Movendo pasta do carrossel para 'publicados' no Google Drive...")
                gdrive_client.move_carousel_to_published(gdrive_carousel_folder_id)
        except Exception as e:
            print(f"⚠️ Aviso ao atualizar/mover carrossel no Google Drive: {e}")

    # Organiza a pasta localmente para a subpasta 'publicados'
    try:
        local_pub_dir = target_dir.parent / "publicados"
        local_pub_dir.mkdir(parents=True, exist_ok=True)
        dest_local = local_pub_dir / target_dir.name
        if dest_local.exists():
            shutil.rmtree(dest_local)
        shutil.move(str(target_dir), str(dest_local))
        print(f"📦 Carrossel movido localmente para: {dest_local}")
    except Exception as e:
        print(f"⚠️ Aviso ao mover localmente para publicados: {e}")

