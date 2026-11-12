#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
sync_semanal_drive.py
---------------------
Sincronizador automático inteligente entre o Google Drive e o Repositório Nuvem (GitHub):
1. Faz 'git pull' para baixar os status de postagens que a nuvem executou.
2. Atualiza os arquivos metadata.json no Google Drive com o status de postado.
3. Identifica novos carrosséis em '06-Aprovados-para-Postar' do Drive e copia metadata/legenda para 'fila/'.
4. Faz 'git push' para a nuvem do GitHub com os novos carrosséis da semana.
"""

import os
import sys
import json
import shutil
import subprocess
import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

REPO_DIR = Path(__file__).resolve().parent.parent
REPO_CARROSSEIS = REPO_DIR / "fila"
TEXTO = {".json", ".md"}  # só texto vai pro git; a mídia fica no Drive
DRIVE_DIR = Path(r"C:\Users\luizr\Meu Drive (aidealabbr@gmail.com)\Clientes\otalogia\06-Aprovados-para-Postar")
LOGS_DIR = REPO_DIR / "automation" / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "sync_history.log"


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def run_git(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(REPO_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )


def sync():
    log("=== INICIANDO SINCRONIZAÇÃO SEMANAL: DRIVE <-> NUVEM ===")

    # 1. Puxa atualizações que a nuvem do GitHub Actions fez
    log("📥 Passo 1: Puxando atualizações recentes da nuvem (git pull)...")
    pull_res = run_git(["pull", "origin", "main"])
    if pull_res.returncode != 0:
        log(f"⚠️ Aviso no git pull: {pull_res.stderr.strip()}")
    else:
        log("✅ Repositório local atualizado com a nuvem.")

    # 2. Sincroniza metadados postados de volta para o Google Drive
    if DRIVE_DIR.exists() and REPO_CARROSSEIS.exists():
        log("🔄 Passo 2: Sincronizando status de postagem para o Google Drive...")
        for repo_folder in REPO_CARROSSEIS.iterdir():
            if repo_folder.is_dir():
                drive_folder = DRIVE_DIR / repo_folder.name
                if drive_folder.exists():
                    repo_meta = repo_folder / "metadata.json"
                    drive_meta = drive_folder / "metadata.json"
                    if repo_meta.exists() and drive_meta.exists():
                        try:
                            r_data = json.loads(repo_meta.read_text(encoding="utf-8"))
                            d_data = json.loads(drive_meta.read_text(encoding="utf-8"))
                            # Se a nuvem postou com sucesso, atualiza apenas os campos de status no Drive
                            if r_data.get("postado") and r_data.get("post_id"):
                                d_data["postado"] = r_data["postado"]
                                d_data["postado_em"] = r_data.get("postado_em")
                                d_data["post_id"] = r_data.get("post_id")
                                drive_meta.write_text(json.dumps(d_data, indent=2, ensure_ascii=False), encoding="utf-8")
                        except Exception as e:
                            log(f"⚠️ Erro ao atualizar {drive_meta}: {e}")

    # 3. Detecta novos carrosséis no Google Drive e copia para o repositório
    if not DRIVE_DIR.exists():
        log(f"❌ Pasta do Google Drive não encontrada: {DRIVE_DIR}")
        return

    log("📤 Passo 3: Verificando novos carrosséis aprovados no Google Drive...")
    REPO_CARROSSEIS.mkdir(exist_ok=True)

    def copiar_texto(src, dst):
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.iterdir():
            if f.is_file() and f.suffix.lower() in TEXTO:
                shutil.copy2(f, dst / f.name)
    novos_adicionados = 0

    for drive_item in DRIVE_DIR.iterdir():
        if drive_item.is_dir():
            if drive_item.name.lower() in ["publicados", "07-publicados", "postados", "lixeira"]:
                continue
            target_repo_item = REPO_CARROSSEIS / drive_item.name
            if not target_repo_item.exists():
                log(f"  ✨ Novo carrossel identificado: {drive_item.name}")
                copiar_texto(drive_item, target_repo_item)
                novos_adicionados += 1
            else:
                # Copia arquivos novos OU modificados (imagens atualizadas, legendas editadas, etc.)
                for subfile in drive_item.iterdir():
                    if subfile.suffix.lower() not in TEXTO:
                        continue
                    target_subfile = target_repo_item / subfile.name
                    if not target_subfile.exists():
                        if subfile.is_file():
                            shutil.copy2(subfile, target_subfile)
                            log(f"  📎 Novo arquivo copiado: {subfile.name} em {drive_item.name}")
                            novos_adicionados += 1
                    elif subfile.is_file():
                        # Detecta se o arquivo foi alterado por tamanho ou data de modificação
                        if subfile.stat().st_size != target_subfile.stat().st_size or subfile.stat().st_mtime > target_subfile.stat().st_mtime:
                            shutil.copy2(subfile, target_subfile)
                            log(f"  🔄 Arquivo atualizado copiado: {subfile.name} em {drive_item.name}")
                            novos_adicionados += 1

    # 4. Se houver novidades, comita e envia para o GitHub Actions
    log("💾 Passo 4: Verificando alterações pendentes no git...")
    status_res = run_git(["status", "--porcelain"])
    if status_res.stdout.strip():
        log("🚀 Enviando novos carrosséis para a nuvem do GitHub Actions...")
        run_git(["add", "fila/"])
        run_git(["commit", "-m", "chore(sync): sincronizar fila semanal de carrosseis aprovados do Google Drive"])
        push_res = run_git(["push", "origin", "main"])
        if push_res.returncode == 0:
            log("🎉 SUCESSO! A nuvem do GitHub Actions foi abastecida com a nova fila da semana!")
        else:
            log(f"❌ Falha no push: {push_res.stderr.strip()}")
    else:
        log("✨ A nuvem já está 100% atualizada. Nenhuma novidade para enviar.")

    log("=== SINCRONIZAÇÃO CONCLUÍDA ===")


if __name__ == "__main__":
    sync()
