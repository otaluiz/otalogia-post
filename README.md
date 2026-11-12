# otalogia-brand

Marca otalogia: design system (`design-system/`), carrosséis (`carrosseis/`) e roteiro (`roteiro-carrosseis.md`).

## Motor de carrossel

O motor genérico (`carrossel-engine`) vem copiado em `motor/` (sem submódulo, para a rotina na nuvem clonar um repositório só); a marca entra como tema em `design-system/tema/`.

```
bash automation/setup-cloud.sh            # nuvem/Linux: Playwright, rembg, OpenCV 4
cd carrosseis/<id> && python ../../motor/compor.py carrossel.json
python ../../motor/render.py carrossel.json png --tema ../../design-system/tema
python ../../motor/metadata.py carrossel.json <ordem_fila> --tema ../../design-system/tema #tags
```

Rotinas: `automation/daily-carousel-prompt.txt` (local, Windows) e `automation/cloud-carousel-prompt.md` (nuvem).
O motor é mantido em `D:/claude/carrossel-engine`; ao mudar lá, copie os arquivos para `motor/` aqui.

## Publicação no Instagram (@otalogia)

Criação e publicação vivem neste repositório (antes: `otalogia-instagram-publisher`).

```
carrosseis/<id>/  -> criação (motor, png, motion) -> entregar.yml sobe p/ Drive 04-Carrosseis
Drive 06-Aprovados-para-Postar (portão humano)
publicador/       -> instagram_publisher.py, gdrive_live.py, sync_semanal_drive.py (+ windows/)
fila/             -> metadata.json/legenda.md dos itens da fila e fila/publicados/ (mídia vem do Drive)
.github/workflows/post-instagram.yml -> publica 1 carrossel/dia via Graph API
```

Secrets do repo: `META_ACCESS_TOKEN`, `INSTAGRAM_ACCOUNT_ID`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GDRIVE_FOLDER_ID_OTALOGIA` (opcional); o Drive reutiliza `GOOGLE_DRIVE_*`.
Local: `cp publicador/.env.example publicador/.env`; `python publicador/instagram_publisher.py --test`.
