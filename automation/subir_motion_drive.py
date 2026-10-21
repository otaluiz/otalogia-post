"""Entrega o carrossel com motion no Drive no mesmo formato da pasta estática, para a rotina de postagem usar sem
mudança: na pasta do carrossel (Clientes/otalogia/04-Carrosseis ou 06-Aprovados-para-Postar e subpastas) ficam
slide-NN.mp4 no lugar de slide-NN.png, o metadata.json com `arquivo` apontando para o .mp4 e a legenda.md.
Os PNG estáticos e o vídeo completo (prévia) vão para a subpasta "extras". Vídeo que já existe vira nova revisão.
Roda no GitHub Actions (workflow motion-drive.yml), depois do render.

Uso: python automation/subir_motion_drive.py [slug ...]
"""
import io
import json
import sys
from pathlib import Path

from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

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
        pasta = pastas[slug]
        no_drive = filhos(svc, pasta)
        extras = filhos(svc, pasta, True).get("extras") or svc.files().create(
            body={"name": "extras", "mimeType": PASTA, "parents": [pasta]}, fields="id").execute()["id"]
        no_extras = filhos(svc, extras)
        # slides em vídeo na raiz da pasta, no lugar dos PNG
        for f in sorted(out.glob("slide-*.mp4")):
            media = MediaFileUpload(str(f), mimetype="video/mp4", resumable=True)
            if f.name in no_drive:
                svc.files().update(fileId=no_drive[f.name], media_body=media).execute()
            else:
                svc.files().create(body={"name": f.name, "parents": [pasta]}, media_body=media, fields="id").execute()
        # PNG estáticos saem da raiz (ficam em extras/) e a prévia completa também vai para extras/
        for nome, fid in no_drive.items():
            if nome.startswith("slide-") and nome.endswith(".png"):
                if nome in no_extras:  # vale a versão da raiz (pode ter sido atualizada depois)
                    svc.files().update(fileId=no_extras[nome], body={"trashed": True}).execute()
                svc.files().update(fileId=fid, addParents=extras, removeParents=pasta, fields="id").execute()
        prev = MediaFileUpload(str(out / "completo.mp4"), mimetype="video/mp4", resumable=True)
        if "previa.mp4" in no_extras:
            svc.files().update(fileId=no_extras["previa.mp4"], media_body=prev).execute()
        else:
            svc.files().create(body={"name": "previa.mp4", "parents": [extras]}, media_body=prev, fields="id").execute()
        # metadata.json do Drive passa a apontar para os vídeos (mantém o resto, inclusive status/postado)
        if "metadata.json" in no_drive:
            meta = json.loads(svc.files().get_media(fileId=no_drive["metadata.json"]).execute())
            for sl in meta.get("slides", []):
                sl["arquivo"] = Path(sl["arquivo"]).stem + ".mp4"
            meta["formato_midia"] = "motion"
            corpo = MediaIoBaseUpload(io.BytesIO(json.dumps(meta, ensure_ascii=False, indent=2).encode()), mimetype="application/json")
            svc.files().update(fileId=no_drive["metadata.json"], media_body=corpo).execute()
        # subpasta motion/ do formato anterior desta entrega
        if "motion" in no_drive:
            svc.files().update(fileId=no_drive["motion"], body={"trashed": True}).execute()
        print("enviado:", slug, len(list(out.glob("slide-*.mp4"))), "slides em vídeo")


if __name__ == "__main__":
    main()
