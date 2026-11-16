import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

MOTOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MOTOR))
import guia_pdf as g
import metadata as m
from pypdf import PdfReader


class GuiaPDFTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = json.loads((MOTOR/'pdf/exemplo-guia.json').read_text())

    def fonte(self):
        p = self.root/'guia/guia.json'
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(self.data))
        return p

    def carrossel(self):
        p = self.root/'carrossel.json'
        p.write_text(json.dumps({'id':'teste','meta':{'serie':'TESTE'},'slides':[{'template':'T1','display':['Um projeto real']}]}))
        png = self.root/'png'
        png.mkdir(exist_ok=True)
        (png/'slide-01.png').write_bytes(b'image-fixture')
        (self.root/'legenda.md').write_text('Legenda do perfil original.')
        return p

    def test_schema_e_fontes_obrigatorios(self):
        for key in ['titulo','categoria','paginas','fontes']:
            with self.subTest(key=key):
                d=copy.deepcopy(self.data);d.pop(key)
                with self.assertRaises(ValueError):g.validar(d)

    def test_rejeita_urls_executaveis(self):
        self.data['fontes'][0]['url']='javascript:alert(1)'
        with self.assertRaises(ValueError):g.validar(self.data)

    def test_html_escapa_conteudo_e_incorpora_fontes(self):
        self.data['titulo']='<script>alert(1)</script>'
        doc,n=g.montar(self.data)
        self.assertNotIn('<script>',doc)
        self.assertIn('&lt;script&gt;',doc)
        self.assertIn('data:font/ttf;base64,',doc)
        self.assertNotIn('otalogia',doc.lower())
        self.assertEqual(n,5)

    def test_novo_conteudo_sem_guia_falha_sem_metadata(self):
        p=self.carrossel()
        with self.assertRaisesRegex(ValueError,'Novo conteúdo requer'):
            m.gerar(p,{'marca':'otalogia','handle':'@otalogia','familia_cor':'ink-laranja'})
        self.assertFalse((self.root/'png/metadata.json').exists())

    def test_publicado_preservado_sem_render(self):
        p=self.carrossel();meta=self.root/'png/metadata.json'
        raw=json.dumps({'postado':True,'post_id':'123','legenda':'não alterar'})
        meta.write_text(raw)
        self.assertEqual(m.gerar(p,{}),meta)
        self.assertEqual(meta.read_text(),raw)
        self.assertFalse((self.root/'png/guia.pdf').exists())

    def test_legado_preserva_dm_e_status(self):
        p=self.carrossel();meta=self.root/'png/metadata.json'
        meta.write_text(json.dumps({'postado':False,'status':'aprovado','dm':{'palavra':'SITE'}}))
        m.gerar(p,{'marca':'otalogia','handle':'@otalogia','familia_cor':'ink-laranja'})
        d=json.loads(meta.read_text());self.assertEqual(d['status'],'aprovado');self.assertEqual(d['dm']['palavra'],'SITE')

    def test_integracao_metadata_pdf_links_previews_reuso(self):
        p=self.carrossel();self.fonte()
        tema={'marca':'otalogia','handle':'@otalogia','familia_cor':'ink-laranja'}
        meta=m.gerar(p,tema);d=json.loads(meta.read_text())
        self.assertEqual(d['status'],'rascunho');self.assertEqual(d['handle'],'@otalogia')
        self.assertEqual(d['material_pdf']['marca'],'aidealab');self.assertNotIn('dm',d)
        pdf=PdfReader(self.root/'png/guia.pdf');self.assertEqual(len(pdf.pages),5)
        text=' '.join(page.extract_text() or '' for page in pdf.pages)
        self.assertIn('aidealab',text);self.assertNotIn('otalogia',text)
        links=[a.get_object().get('/A',{}).get('/URI') for page in pdf.pages for a in page.get('/Annots',[])]
        self.assertIn(self.data['fontes'][0]['url'],links)
        self.assertEqual(len(list((self.root/'guia/previews').glob('*.png'))),5)
        # Repeated metadata generation works; reusing the approved file needs no source render.
        source_hash=d['material_pdf']['fonte_sha256']
        m.gerar(p,tema);self.assertEqual(json.loads(meta.read_text())['material_pdf']['fonte_sha256'],source_hash)
        canonical=self.root/'canonica.pdf';canonical.write_bytes((self.root/'png/guia.pdf').read_bytes())
        car=json.loads(p.read_text());car['meta']['guia']={'reutilizar':'canonica.pdf'};p.write_text(json.dumps(car))
        m.gerar(p,tema)
        self.assertEqual(json.loads(meta.read_text())['material_pdf']['status'],'reutilizado')
        self.assertEqual(canonical.read_bytes(),(self.root/'png/guia.pdf').read_bytes())

    def test_overflow_bloqueia_sem_substituir_pdf(self):
        self.data['paginas'][0]['texto']='Texto extenso para validar o limite da página. '*600
        source=self.fonte();dest=self.root/'anterior.pdf';dest.write_bytes(b'preservar')
        with self.assertRaisesRegex(ValueError,'não cabe'):
            g.gerar(source,dest)
        self.assertEqual(dest.read_bytes(),b'preservar')


if __name__=='__main__':unittest.main()
