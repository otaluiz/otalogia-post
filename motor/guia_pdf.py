"""PDF editorial aidealab: fonte independente, layout validado e nenhuma publicação remota."""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlparse

ASSETS = Path(__file__).resolve().parent / 'pdf'
TEMPLATE_VERSION = 'aidealab-azul-laranja-v1'


def texto(value):
    return html.escape(str(value))


def url_segura(url):
    parsed = urlparse(url)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f'URL de referência inválida: {url!r}')
    return html.escape(url, quote=True)


def validar(d):
    for key in ('titulo', 'subtitulo', 'categoria'):
        if not isinstance(d.get(key), str) or not d[key].strip():
            raise ValueError(f'Guia precisa de {key}')
    if not re.fullmatch(r'[A-Z0-9]{3,24}', d['categoria']):
        raise ValueError('categoria deve ter 3–24 caracteres A-Z/0-9')
    if not isinstance(d.get('paginas'), list) or not d['paginas']:
        raise ValueError('Guia precisa de paginas editoriais independentes dos slides')
    for i, page in enumerate(d['paginas'], 1):
        if not isinstance(page, dict) or not isinstance(page.get('titulo'), str) or not page['titulo'].strip():
            raise ValueError(f'Página {i}: titulo ausente')
        if not any(page.get(k) for k in ('texto', 'itens', 'recursos', 'codigo')):
            raise ValueError(f'Página {i}: conteúdo vazio')
        for key in ('itens', 'recursos'):
            if key in page and not isinstance(page[key], list):
                raise ValueError(f'Página {i}: {key} precisa ser lista')
        for r in page.get('recursos', []):
            if not all(isinstance(r.get(k), str) and r[k].strip() for k in ('nome', 'url', 'descricao')):
                raise ValueError(f'Página {i}: recurso incompleto')
            url_segura(r['url'])
    refs = d.get('fontes', [])
    if not isinstance(refs, list) or not refs:
        raise ValueError('Inclua fontes com titulo e url, conferidas na pesquisa editorial')
    for ref in refs:
        if not ref.get('titulo'):
            raise ValueError('Fonte sem titulo')
        url_segura(ref['url'])


def montar(d):
    validar(d)
    css = (ASSETS / 'template.css').read_text(encoding='utf-8')
    for name in ('InterTight.ttf', 'InstrumentSerif-Italic.ttf'):
        data = base64.b64encode((ASSETS / 'fonts' / name).read_bytes()).decode()
        css = css.replace(f'fonts/{name}', f'data:font/ttf;base64,{data}')
    # O template não depende de fontes ou assets externos.
    total = len(d['paginas']) + 3  # capa, mapa e referências
    brand = '<div class="brand">aidealab</div>'
    def top(label):
        return f'<div class="top">{brand}<div class="eyebrow">{texto(label)}</div></div>'
    def footer(i):
        return f'<div class="footer"><span>AIDEALAB · GUIA {texto(d["categoria"])}</span><span><b>{i:02d}</b> / {total:02d}</span></div>'
    pages = [f'<section class="page cover">{top("Guia prático")}<div class="cover-label eyebrow">Biblioteca de materiais · {texto(d["categoria"])}</div><div class="guide-intro"><h1 class="guide-title">{texto(d["titulo"])}</h1><p>{texto(d["subtitulo"])}</p></div><div class="cover-stat">{len(d["paginas"]):02d}<small>capítulos para consultar e aplicar</small></div>{footer(1)}</section>']
    toc = ''.join(f'<a href="#capitulo-{i}"><span class="tocno">{i:02d}</span><span>{texto(p["titulo"])}</span><span class="tocpage">{i+2:02d} ↗</span></a>' for i,p in enumerate(d['paginas'],1))
    pages.append(f'<section class="page">{top("Mapa do guia")}<div class="intro"><h2>Da ideia<br/>à <span class="serif">prática.</span></h2></div><nav class="toc">{toc}</nav><div class="tip"><strong>Como usar</strong>{texto(d.get("como_usar", "Escolha uma etapa, aplique no seu contexto e confira o resultado antes de continuar."))}</div>{footer(2)}</section>')
    for i,p in enumerate(d['paginas'],1):
        body = ''.join(f'<p>{texto(t)}</p>' for t in p.get('texto','').split('\n\n') if t)
        if p.get('itens'):
            body += '<ul>'+''.join(f'<li>{texto(t)}</li>' for t in p['itens'])+'</ul>'
        if p.get('codigo'):
            body += f'<pre>{texto(p["codigo"])}</pre>'
        cards = ''
        if p.get('recursos'):
            for j,r in enumerate(p['recursos'],1):
                cards += f'<a class="card" href="{url_segura(r["url"])}"><div class="card-top"><span class="badge">RECURSO {j:02d}</span><span class="arrow">↗</span></div><h3>{texto(r["nome"])}</h3><p>{texto(r["descricao"])}</p><span class="domain">{texto(urlparse(r["url"]).netloc)}</span></a>'
            cards = f'<div class="cards">{cards}</div>'
        tip = f'<div class="tip"><strong>Na prática</strong>{texto(p["dica"])}</div>' if p.get('dica') else ''
        pages.append(f'<section class="page {"dense" if len(p.get("recursos",[]))>6 else ""}" id="capitulo-{i}">{top("Biblioteca de recursos" if cards else "Passo a passo")}<div class="chapter-head"><span class="chapter-num">{i:02d} / {len(d["paginas"]):02d}</span><span class="chapter-type">{texto(d["categoria"])}</span></div><h2>{texto(p["titulo"])}</h2><div class="content">{body}</div>{cards}{tip}{footer(i+2)}</section>')
    # Referências têm páginas próprias, com limite verificado no navegador.
    refs = ''.join(f'<a class="source" href="{url_segura(r["url"])}"><b>{texto(r["titulo"])}</b><span>{texto(r["url"])}</span></a>' for r in d['fontes'])
    pages.append(f'<section class="page end">{top("Referências")}<div class="intro"><h2>Para consultar<br/>e <span class="serif">aprofundar.</span></h2></div><div class="content">{refs}</div><div class="tip">{texto(d.get("nota_fontes", "Consulte as condições e atualizações de cada fonte antes de aplicar. Exemplos ilustrativos não representam resultados medidos."))}</div>{footer(total)}</section>')
    return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>AIDEALAB — '+texto(d['titulo'])+'</title><style>'+css+'</style></head><body>'+''.join(pages)+'</body></html>', total


def gerar(fonte, destino=None, previews=None):
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader
    fonte = Path(fonte).resolve()
    raw = fonte.read_bytes()
    d = json.loads(raw)
    document, total = montar(d)
    destino = Path(destino or fonte.with_suffix('.pdf')).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    previews = Path(previews or fonte.parent / 'previews')
    with tempfile.TemporaryDirectory(prefix='guia-pdf-') as temp:
        temp = Path(temp)
        with sync_playwright() as pw:
            browser_path = os.getenv('PDF_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
            options = {'executable_path': browser_path} if browser_path else {}
            browser = pw.chromium.launch(headless=True, **options)
            page = browser.new_page(viewport={'width':681,'height':945}, device_scale_factor=1.4)
            page.set_content(document)
            page.evaluate('document.fonts.ready')
            page.emulate_media(media='print')
            issues = page.evaluate('''() => [...document.querySelectorAll('.page')].flatMap((p,i)=>{
              const footer=p.querySelector('.footer').getBoundingClientRect(), bounds=p.getBoundingClientRect();
              return [...p.children].filter(e=>!e.classList.contains('footer') && (e.getBoundingClientRect().bottom>footer.top-8 || e.getBoundingClientRect().right>bounds.right || e.scrollWidth>e.clientWidth+1)).map(e=>({pagina:i+1,bloco:e.className}));
            })''')
            if issues:
                raise ValueError(f'Conteúdo não cabe no template. Divida a página ou encurte os blocos: {issues}')
            assert page.evaluate('document.fonts.check(\'700 20px "Inter"\')'), 'Fonte Inter não carregou'
            page.pdf(path=str(temp/'guia.pdf'), prefer_css_page_size=True, print_background=True)
            pdf = PdfReader(temp/'guia.pdf')
            if len(pdf.pages) != total:
                raise ValueError('Paginação divergente; PDF não substituído')
            (temp/'previews').mkdir()
            # Keep all pages in the viewport: element screenshots must not scroll
            # a print-media layout and clip preceding headers.
            page.set_viewport_size({'width':681, 'height':page.evaluate('document.body.scrollHeight')})
            for i in range(total):
                page.locator('.page').nth(i).screenshot(path=str(temp/'previews'/f'pagina-{i+1:02d}.png'))
            browser.close()
        # Só substitui PDF/HTML após validação completa. A revisão editorial continua humana.
        shutil.copyfile(temp/'guia.pdf', destino)
        destino.with_suffix('.html').write_text(document, encoding='utf-8')
        previews.mkdir(parents=True, exist_ok=True)
        for p in previews.glob('pagina-*.png'):
            p.unlink()
        for p in (temp/'previews').glob('*.png'):
            shutil.copyfile(p, previews/p.name)
    return {'arquivo':destino.name, 'titulo':d['titulo'], 'categoria':d['categoria'], 'marca':'aidealab',
            'template':TEMPLATE_VERSION, 'paginas':total, 'fonte_sha256':hashlib.sha256(raw).hexdigest(),
            'status':'rascunho', 'revisao_visual':'pendente'}


def preparar_material(json_path, antigo=None):
    """Cria o PDF junto dos metadados; mantém conteúdo legado e publicação intactos."""
    pasta = Path(json_path).resolve().parent
    data = json.loads(Path(json_path).read_text(encoding='utf-8'))
    config = data.get('meta', {}).get('guia', {})
    if not isinstance(config, dict):
        raise ValueError('meta.guia deve ser objeto com fonte ou reutilizar')
    fonte = pasta / config.get('fonte', 'guia/guia.json')
    destino = pasta / 'png' / 'guia.pdf'
    if config.get('reutilizar'):
        from pypdf import PdfReader
        origem = (pasta/config['reutilizar']).resolve()
        if origem == destino.resolve():
            raise ValueError('Reutilizar deve apontar para o guia canônico, fora do destino')
        pdf = PdfReader(origem)
        if not pdf.pages:
            raise ValueError('PDF reutilizado vazio')
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, destino)
        return {'arquivo':'guia.pdf','marca':'aidealab','status':'reutilizado','origem':config['reutilizar'],
                'fonte_sha256':hashlib.sha256(origem.read_bytes()).hexdigest()}
    if fonte.is_file():
        return gerar(fonte, destino, pasta/'guia'/'previews')
    if antigo is not None and not config:
        return antigo.get('material_pdf')
    raise ValueError('Novo conteúdo requer guia/guia.json editorial ou meta.guia.reutilizar com PDF existente. Não gere o PDF a partir dos slides.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fonte', type=Path)
    parser.add_argument('--saida', type=Path)
    parser.add_argument('--previews', type=Path)
    args = parser.parse_args()
    print(json.dumps(gerar(args.fonte,args.saida,args.previews),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
