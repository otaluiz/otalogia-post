"""Sobe os vídeos do carrossel com motion (carrosseis/<slug>/motion/out/*.mp4, gerados por motor/hyperframes/render.sh)
para a subpasta "motion" da pasta do carrossel no Drive (Clientes/otalogia/04-Carrosseis ou 06-Aprovados-para-Postar
e subpastas). Arquivo que já existe vira nova revisão. Roda no GitHub Actions (workflow motion-drive.yml).

Uso: python automation/subir_motion_drive.py [slug ...]
"""
import sys
from pathlib import Path

from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).parent))
from upload_drive import PASTA, achar, filhos, servico  # noqa: E402


def main():
    svc = servico()
    pastas = dict(filhos(svc, achar(svc, "Clientes/otalogia/04-Carrosseis"), True))
    for nome, pid in filhos(svc, achar(svc, "Clientes/otalogia/06-Aprovados-para-Postar"), True).items():
        pastas.setdefault(nome, pid)
        for sub, sid in filhos(svc, pid, True).items():
            pastas.setdefault(sub, sid)
    so = set(sys.argv[1:])
    for out in sorted(Path("carrosseis").glob("*/motion/out")):
        slug = out.parent.parent.name
        if so and slug not in so:
            continue
        if slug not in pastas:
            print("pula:", slug, "(pasta não está no Drive)")
            continue
        motion = filhos(svc, pastas[slug], True).get("motion") or svc.files().create(
            body={"name": "motion", "mimeType": PASTA, "parents": [pastas[slug]]}, fields="id").execute()["id"]
        no_drive = filhos(svc, motion)
        for f in sorted(out.glob("*.mp4")):
            media = MediaFileUpload(str(f), mimetype="video/mp4", resumable=True)
            if f.name in no_drive:
                svc.files().update(fileId=no_drive[f.name], media_body=media).execute()
            else:
                svc.files().create(body={"name": f.name, "parents": [motion]}, media_body=media, fields="id").execute()
        print("enviado:", slug, len(list(out.glob("*.mp4"))), "vídeos")


if __name__ == "__main__":
    main()
