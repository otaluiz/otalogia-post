import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dm_drive as d


def request(result):
    r=Mock();r.execute.return_value=result;return r


class DriveTests(unittest.TestCase):
    def test_paginacao(self):
        svc=Mock();svc.files().list.side_effect=[request({'files':[{'id':'1'}],'nextPageToken':'p2'}),request({'files':[{'id':'2'}]})]
        self.assertEqual([f['id'] for f in d.children(svc,'folder')],['1','2'])
        self.assertEqual(svc.files().list.call_args_list[1].kwargs['pageToken'],'p2')

    def test_exclui_publicados_e_pastas_arquivo(self):
        svc=Mock()
        folders={'root':[{'id':'old','name':'POSTADOS','mimeType':d.FOLDER},{'id':'new','name':'novo','mimeType':d.FOLDER}],
                 'new':[{'id':'meta','name':'metadata.json','mimeType':'application/json'}]}
        svc.files().get_media.return_value=request(json.dumps({'postado':False}).encode())
        with patch.object(d,'children',side_effect=lambda s,p:iter(folders[p])) as c:
            self.assertEqual(len(list(d.pending(svc,'root'))),1)
            self.assertNotIn('old',[call.args[1] for call in c.call_args_list])
        svc.files().get_media.return_value=request(json.dumps({'postado':True}).encode())
        with patch.object(d,'children',side_effect=lambda s,p:iter(folders[p])):
            self.assertEqual(list(d.pending(svc,'root')),[])

    def test_preflight_rejeita_sem_revisao_antes_de_escrever(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'manifesto.json';f.write_text(json.dumps({'arquivos':[{'revisado':False}]}))
            svc=Mock()
            with self.assertRaisesRegex(ValueError,'revisão'):d.preflight(svc,f)
            svc.files().update.assert_not_called()

    def test_preflight_rejeita_destino_fora_da_biblioteca(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'final.pdf').write_bytes(b'pdf')
            manifest=root/'manifesto.json';manifest.write_text(json.dumps({'arquivos':[{'revisado':True,'perfil':'aidealab','arquivo':'final.pdf','drive_id':'123','nome_drive':'final.pdf','md5_original':'abc'}]}))
            svc=Mock();svc.files().get.return_value=request({'id':'123','name':'final.pdf','mimeType':'application/pdf','parents':['pasta-nao-autorizada']})
            pdf=Mock();pdf.pages=[Mock()];pdf.pages[0].extract_text.return_value='aidealab'
            with patch('pypdf.PdfReader',return_value=pdf):
                with self.assertRaisesRegex(ValueError,'fora da biblioteca'):d.preflight(svc,manifest)
            svc.files().update.assert_not_called()

    def test_backup_divergente_bloqueia_todo_lote(self):
        with tempfile.TemporaryDirectory() as t:
            svc=Mock();item={'md5_original':'nao-corresponde'}
            with patch.object(d,'preflight',return_value=[(item,Path(t)/'final.pdf',{'id':'123'})]),patch.object(d,'download',side_effect=lambda s,f,p:p.parent.mkdir(parents=True,exist_ok=True) or p.write_bytes(b'mudou')):
                with self.assertRaisesRegex(ValueError,'Backup diverge'):d.apply(svc,'manifesto.json',t)
            svc.files().update.assert_not_called()


if __name__=='__main__':unittest.main()
