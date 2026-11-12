#!/usr/bin/env python3
"""Prepara PDFs e palavras-chave dos posts em aprovação, sem publicar nem enviar DMs.

Executado após o upload para o Drive, com GOOGLE_DRIVE_CLIENT_ID/SECRET/REFRESH_TOKEN.
Para posts na fila (06), atualiza legenda/metadata no Drive e cria material em 07-Iscas-DM.
Para novos rascunhos em 04, atua APENAS quando metadata.dm.palavra estiver definido.
Mantém o histórico de links: comentários em posts antigos continuam funcionando.
"""
import hashlib
import io
import json
import os
import re
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether

BRAND = os.environ.get("DM_BRAND", "").strip().lower()
if BRAND not in {"aidealab", "otalogia"}:
    raise SystemExit("DM_BRAND precisa ser aidealab ou otalogia")
PATH_LINKS = Path("iscas/links.json")
FOLDER = "application/vnd.google-apps.folder"
ACCENT = colors.HexColor("#09B3C5" if BRAND == "aidealab" else "#D2410F")
TXT = colors.HexColor("#192331" if BRAND == "aidealab" else "#221A16")
EXCLUDE = {"COMENTA", "COMENTE", "DIRECT", "PDF", "GUIA", "LINK", "MATERIAL", "DM", "ME", "NO"}


def service():
    creds = Credentials(None, refresh_token=os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["GOOGLE_DRIVE_CLIENT_ID"],
                        client_secret=os.environ["GOOGLE_DRIVE_CLIENT_SECRET"])
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def entries(svc, folder):
    result, page = {}, None
    while True:
        data = svc.files().list(
            q=f"'{folder}' in parents and trashed = false",
            fields="nextPageToken,files(id,name,mimeType,webViewLink,appProperties)",
            pageSize=1000, pageToken=page).execute()
        result.update({item["name"]: item for item in data.get("files", [])})
        page = data.get("nextPageToken")
        if not page:
            return result


def folder(svc, path, create=False):
    current = "root"
    for name in path.split("/"):
        found = entries(svc, current).get(name)
        if found is None and create:
            found = svc.files().create(
                body={"name": name, "mimeType": FOLDER, "parents": [current]},
                fields="id,name,mimeType").execute()
        if found is None or found.get("mimeType") != FOLDER:
            raise RuntimeError(f"Pasta não encontrada no Drive: {path} ({name})")
        current = found["id"]
    return current


def content(svc, item):
    return svc.files().get_media(fileId=item["id"]).execute().decode("utf-8-sig")


def save_text(svc, item, text, mimetype):
    media = MediaIoBaseUpload(io.BytesIO(text.encode("utf-8")), mimetype=mimetype, resumable=False)
    svc.files().update(fileId=item["id"], media_body=media).execute()


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.upper())
                   if not unicodedata.combining(c))


def choose_word(meta, caption, taken, old):
    old_word = normalize(str((meta.get("dm") or {}).get("palavra", "")).strip())
    found = re.search(r"\b(?:comenta|comente|responda)\s+([A-Za-zÀ-ÿ0-9_-]{2,32})\b", caption, re.I)
    proposal = old_word or (normalize(found.group(1)) if found else "")
    if not re.fullmatch(r"[A-Z0-9_]{3,24}", proposal or "") or proposal in EXCLUDE:
        tokens = re.findall(r"[A-Z0-9]{4,}", normalize(str(meta.get("tema") or "")))
        proposal = next((w[:18] for w in tokens if w not in EXCLUDE), "MATERIAL")
    # Nunca reutilizar palavra de outra isca: a DM não pode devolver o PDF errado.
    base = proposal[:19]
    keyword = base
    count = 2
    while keyword in taken and taken[keyword].get("carousel_id") != old:
        keyword = f"{base}{count}"
        count += 1
    return keyword


def cta(caption, keyword):
    desired = f"Comente {keyword} para receber o material gratuito em PDF por DM."
    lines = caption.splitlines()
    pattern = re.compile(r"^\s*(?:comenta|comente|responda)\s+[A-Za-zÀ-ÿ0-9_-]+\b", re.I)
    replaced = False
    for idx, line in enumerate(lines):
        if pattern.search(line):
            lines[idx] = desired
            replaced = True
    if not replaced:
        # Antes das hashtags, para preservar a estrutura da legenda.
        at = next((i for i, line in enumerate(lines) if line.strip().startswith("#")), len(lines))
        lines[at:at] = ["", desired, ""]
    return "\n".join(lines).strip() + "\n"


def brief(meta, caption):
    # Somente frases extraídas do conteúdo da publicação; nunca cria estatísticas ou promessas.
    raw = [x.strip(" \t-•") for x in re.split(r"[\r\n]+", caption) if x.strip()]
    raw = [x for x in raw if not x.startswith("#") and not re.match(r"(?i)^(comenta|comente|responda)\b", x)]
    slides = [str(x.get("texto") or "").strip() for x in meta.get("slides", [])
              if isinstance(x, dict) and x.get("papel") not in ("cta", "hook")]
    lines = []
    seen = set()
    for item in (slides or raw):
        clean = re.sub(r"\s+", " ", item).strip()
        key = normalize(clean)
        if len(clean) > 12 and key not in seen:
            lines.append(clean[:280])
            seen.add(key)
        if len(lines) >= 7:
            break
    if not lines:
        lines = raw[:5]
    return raw[:3], lines[:7]


def generate_pdf(meta, caption, keyword):
    title = str((meta.get("dm") or {}).get("titulo") or meta.get("tema") or "Material de apoio")
    intro, steps = brief(meta, caption)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BrandTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                              fontSize=24, leading=29, textColor=TXT, spaceAfter=22))
    styles.add(ParagraphStyle(name="BrandSub", parent=styles["Heading2"], fontSize=14, leading=19,
                              spaceBefore=15, spaceAfter=12, textColor=ACCENT))
    styles.add(ParagraphStyle(name="BrandBody", parent=styles["BodyText"], fontSize=10.5, leading=16,
                              spaceAfter=11, textColor=TXT))
    styles.add(ParagraphStyle(name="BrandMark", parent=styles["Normal"], alignment=TA_CENTER,
                              fontSize=10, leading=14, textColor=ACCENT, spaceAfter=20))
    story = [Paragraph(f"@{'idea_lab7' if BRAND == 'aidealab' else 'otalogia'}  |  MATERIAL EXCLUSIVO",
                       styles["BrandMark"]),
             Spacer(1, .45*cm), Paragraph(escape(title), styles["BrandTitle"]),
             Paragraph(f"Guia complementar ao conteúdo do Instagram. Palavra-chave: {escape(keyword)}",
                       styles["BrandBody"]), Spacer(1, .25*cm),
             Paragraph("O ponto de partida", styles["BrandSub"])]
    for value in intro:
        story.append(Paragraph(escape(value), styles["BrandBody"]))
    story.append(Paragraph("Checklist para colocar em prática", styles["BrandSub"]))
    for i, value in enumerate(steps, 1):
        story.append(Paragraph(f"{i:02d}. {escape(value)}", styles["BrandBody"]))
    story += [Paragraph("Seu próximo passo", styles["BrandSub"]),
              Paragraph("Revise cada item acima e anote: o que já faz, o que falta testar e qual mudança "
                        "vai aplicar primeiro. Compare o resultado com o objetivo do post.", styles["BrandBody"]),
              Spacer(1, 1*cm),
              Paragraph(f"Conteúdo de apoio produzido para @{ 'idea_lab7' if BRAND == 'aidealab' else 'otalogia' }. "
                        "Material informativo; adapte à realidade do seu negócio.", styles["BrandBody"])]
    bio = io.BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=(21*cm, 29.7*cm),
                            leftMargin=2.3*cm, rightMargin=2.3*cm,
                            topMargin=2.4*cm, bottomMargin=2.4*cm)
    doc.build(story)
    return bio.getvalue(), title


def ensure_pdf(svc, pdf_folder, existing, identifier, meta, original_caption, keyword):
    pdf_name = f"dm-{identifier}.pdf"
    digest = hashlib.sha256(json.dumps({
        "tema": meta.get("tema"), "slides": [(s.get("texto"), s.get("papel")) for s in meta.get("slides", [])
               if isinstance(s, dict)], "legenda": original_caption, "keyword": keyword,
        "dm": meta.get("dm", {}),
    }, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    current = existing.get(pdf_name)
    if current and (current.get("appProperties") or {}).get("sha256") == digest:
        return f"https://drive.google.com/file/d/{current['id']}/view"
    pdf_bytes, title = generate_pdf(meta, original_caption, keyword)
    media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype="application/pdf", resumable=False)
    if current:
        svc.files().update(fileId=current["id"], media_body=media,
                           body={"appProperties": {"sha256": digest}}, fields="id").execute()
        fid = current["id"]
    else:
        new = svc.files().create(
            body={"name": pdf_name, "parents": [pdf_folder], "appProperties": {"sha256": digest}},
            media_body=media, fields="id").execute()
        fid = new["id"]
        svc.permissions().create(fileId=fid, body={"type": "anyone", "role": "reader"},
                                 fields="id").execute()
        existing[pdf_name] = {"id": fid, "appProperties": {"sha256": digest}}
    print(f"pdf {'atualizado' if current else 'criado'}: {identifier} ({len(pdf_bytes)} bytes)")
    return f"https://drive.google.com/file/d/{fid}/view"


def main():
    svc = service()
    base = f"Clientes/{BRAND}"
    dest = folder(svc, base + "/07-Iscas-DM", create=True)
    known = entries(svc, dest)
    registry = json.loads(PATH_LINKS.read_text(encoding="utf-8")) if PATH_LINKS.exists() else {}
    if not isinstance(registry, dict):
        raise ValueError("iscas/links.json inválido")
    # 04 só entra caso o criador tenha solicitado isca em dm.palavra.
    source = [(folder(svc, base + "/04-Carrosseis"), False)]
    approved = folder(svc, base + "/06-Aprovados-para-Postar")
    subdirs = entries(svc, approved)
    if BRAND == "aidealab":
        source.append((subdirs["FILA"]["id"], True))
    else:
        source.append((approved, True))
    done, errors = 0, []
    for root, in_queue in source:
        for name, item in sorted(entries(svc, root).items()):
            if item.get("mimeType") != FOLDER or name.upper() in {"POSTADOS", "PUBLICADOS", "FILA"}:
                continue
            files = entries(svc, item["id"])
            if "metadata.json" not in files:
                continue
            try:
                meta = json.loads(content(svc, files["metadata.json"]))
                if not in_queue and not (meta.get("dm") or {}).get("palavra"):
                    continue
                identifier = re.sub(r"[^a-zA-Z0-9_-]", "-", str(meta.get("carousel_id") or name))[:100]
                caption = content(svc, files["legenda.md"]) if "legenda.md" in files else meta.get("legenda", "")
                if not caption.strip() or not meta.get("tema"):
                    raise ValueError("sem tema ou legenda; revisão manual necessária")
                keyword = choose_word(meta, caption, registry, identifier)
                # A revisão humana permanece no fluxo original: não movemos nem publicamos nada.
                link = ensure_pdf(svc, dest, known, identifier, meta, caption, keyword)
                title = str((meta.get("dm") or {}).get("titulo") or meta["tema"])
                registry[keyword] = {"link": link, "titulo": title, "carousel_id": identifier,
                                     "perfil": BRAND}
                if in_queue:
                    new_caption = cta(caption, keyword)
                    if "legenda.md" in files and new_caption != caption:
                        save_text(svc, files["legenda.md"], new_caption, "text/markdown")
                    dm = dict(meta.get("dm") or {})
                    dm.update({"palavra": keyword, "titulo": title, "link": link})
                    meta["dm"] = dm
                    meta["legenda"] = new_caption
                    save_text(svc, files["metadata.json"],
                              json.dumps(meta, ensure_ascii=False, indent=2) + "\n", "application/json")
                print(f"{BRAND}: {name} -> {keyword}")
                done += 1
            except Exception as exc:
                errors.append(f"{name}: {exc}")
    PATH_LINKS.parent.mkdir(parents=True, exist_ok=True)
    PATH_LINKS.write_text(json.dumps(dict(sorted(registry.items())), ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(f"Concluído: {done} materiais; {len(errors)} erros")
    if errors:
        raise RuntimeError("Erros (não publicar sem corrigir): " + "; ".join(errors))


if __name__ == "__main__":
    main()
