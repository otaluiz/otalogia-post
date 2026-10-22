"""Entrega o carrossel com motion no Drive já na ordem de postagem, para a rotina de postagem
(otalogia-instagram-publisher) publicar sem mudança:

  slide-01.png  hook estático (capa que aparece pronta no feed)
  slide-02.mp4  hook animado (vídeo do slide 1)
  slide-03.mp4  ... um vídeo por slide do carrossel, na ordem original

O metadata.json da pasta passa a listar essa sequência (`formato_midia: motion-capa`) e guarda a lista original em
`slides_estatico`. O Instagram aceita no máximo 10 itens: com 10 slides, o hook animado sai e a capa estática fica.
Em `extras/` ficam os originais (PNG e MP4 com a numeração do carrossel) e a prévia completa; a raiz é sempre
remontada a partir deles, então rodar de novo não duplica nada. Vídeo que já existe vira nova revisão.

Uso:
  python automation/subir_motion_drive.py [slug ...]               # depois do render (workflow motion-drive.yml)
  python automation/subir_motion_drive.py --so-organizar [slug ...] # só reorganiza as pastas que já têm vídeo no Drive
"""
import io
import json
import sys
from pathlib import Path

from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

sys.path.insert(0, str(Path(__file__).parent))
from upload_drive import PASTA, achar, filhos, servico  # noqa: E402

LIMITE_IG = 10
VIDEO = (".mp4", ".mov", ".webm")


def subir(svc, caminho, nome, pasta, existentes, mime):
    media = MediaFileUpload(str(caminho), mimetype=mime, resumable=True)
    if nome in existentes:
        svc.files().update(fileId=existentes[nome], media_body=media).execute()
    else:
        svc.files().create(body={"name": nome, "parents": [pasta]}, media_body=media, fields="id").execute()


def sequencia(base, extras):
    """Ordem de postagem: capa PNG + um vídeo por slide (sem o hook animado se passar do limite)."""
    capa = base[0]["arquivo"]
    videos = [(s, Path(s["arquivo"]).stem + ".mp4") for s in base]
    if 1 + len(videos) > LIMITE_IG:
        videos = videos[1:]
    faltam = [n for n in [capa] + [v for _, v in videos] if n not in extras]
    if faltam:
        return None, faltam
    seq = [(dict(base[0], midia="imagem"), capa)]
    for s, v in videos:
        seq.append((dict(s, midia="video", papel="hook-animado" if s is base[0] else s.get("papel")), v))
    return seq, []


def organizar(svc, pasta, slug, out=None):
    no_drive = filhos(svc, pasta)
    if "metadata.json" not in no_drive:
        print("pula:", slug, "(sem metadata.json no Drive)")
        return
    meta = json.loads(svc.files().get_media(fileId=no_drive["metadata.json"]).execute())
    extras = filhos(svc, pasta, True).get("extras") or svc.files().create(
        body={"name": "extras", "mimeType": PASTA, "parents": [pasta]}, fields="id").execute()["id"]
    no_extras = filhos(svc, extras)

    # lista original do carrossel (numeração slide-NN do motor), com o PNG estático de cada slide
    base = meta.get("slides_estatico") or [
        dict(s, arquivo=Path(s["arquivo"]).stem + ".png") for s in meta.get("slides", [])]
    base = sorted(base, key=lambda s: s.get("ordem", 99))
    if not base:
        print("pula:", slug, "(metadata sem slides)")
        return

    # raiz -> extras/. Já organizada: os slide-* da raiz são cópias e vão para a lixeira.
    # Formato anterior: são os originais (PNG ou MP4 com a numeração do carrossel) e vão para extras/.
    ja_organizada = meta.get("formato_midia") == "motion-capa"
    for nome, fid in no_drive.items():
        if not nome.startswith("slide-"):
            continue
        if ja_organizada:
            svc.files().update(fileId=fid, body={"trashed": True}).execute()
            continue
        if nome in no_extras:  # vale a versão da raiz (pode ter sido atualizada depois)
            svc.files().update(fileId=no_extras[nome], body={"trashed": True}).execute()
        svc.files().update(fileId=fid, addParents=extras, removeParents=pasta, fields="id").execute()
    if "motion" in no_drive:  # subpasta motion/ de uma entrega antiga
        svc.files().update(fileId=no_drive["motion"], body={"trashed": True}).execute()

    # vídeos novos do render e a prévia
    no_extras = filhos(svc, extras)
    if out:
        for f in sorted(out.glob("slide-*.mp4")):
            subir(svc, f, f.name, extras, no_extras, "video/mp4")
        if (out / "completo.mp4").exists():
            subir(svc, out / "completo.mp4", "previa.mp4", extras, no_extras, "video/mp4")
        no_extras = filhos(svc, extras)

    seq, faltam = sequencia(base, no_extras)
    if faltam:
        print("pula:", slug, "(faltam em extras/:", ", ".join(faltam) + ")")
        return

    # raiz na ordem de postagem: cópias dos originais de extras/
    slides = []
    for pos, (s, origem) in enumerate(seq, 1):
        nome = f"slide-{pos:02d}{Path(origem).suffix}"
        svc.files().copy(fileId=no_extras[origem], body={"name": nome, "parents": [pasta]}, fields="id").execute()
        slides.append(dict(s, ordem=pos, arquivo=nome, origem=origem))

    meta.update(slides=slides, slides_estatico=base, formato_midia="motion-capa")
    corpo = MediaIoBaseUpload(io.BytesIO(json.dumps(meta, ensure_ascii=False, indent=2).encode()),
                              mimetype="application/json")
    svc.files().update(fileId=no_drive["metadata.json"], media_body=corpo).execute()
    print("organizado:", slug, "->", " ".join(s["arquivo"] for s in slides))


def main():
    args = sys.argv[1:]
    so_organizar = "--so-organizar" in args
    so = {a for a in args if not a.startswith("--")}
    svc = servico()
    pastas = dict(filhos(svc, achar(svc, "Clientes/otalogia/04-Carrosseis"), True))
    for nome, pid in filhos(svc, achar(svc, "Clientes/otalogia/06-Aprovados-para-Postar"), True).items():
        pastas.setdefault(nome, pid)
        for sub, sid in filhos(svc, pid, True).items():
            pastas.setdefault(sub, sid)

    if so_organizar:
        for slug, pid in sorted(pastas.items()):
            if so and slug not in so:
                continue
            nomes = set(filhos(svc, pid)) | set(filhos(svc, filhos(svc, pid, True).get("extras", pid)))
            if any(n.startswith("slide-") and n.endswith(VIDEO) for n in nomes):
                organizar(svc, pid, slug)
        return

    for out in sorted(Path("carrosseis").glob("*/motion/out")):
        slug = out.parent.parent.name
        if so and slug not in so:
            continue
        if slug not in pastas:
            print("pula:", slug, "(pasta não está no Drive)")
            continue
        organizar(svc, pastas[slug], slug, out)


if __name__ == "__main__":
    main()
