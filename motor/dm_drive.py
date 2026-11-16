"""Audita PDFs das filas no Drive ou atualiza versões revisadas mantendo IDs/links."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

FOLDER = 'application/vnd.google-apps.folder'
PROFILES = {
    'aidealab': {'queue':'1u8FlKUuMT9hKfXz4rcj7kFRyioGC8TB1','guides':'1Iy1SbNJ21j0ZbDIKgm38iOI4rZAVVBwW'},
    'otalogia': {'queue':'13GZEPJrWJaf9rWB4RFQXf5Hh0wRp27D6','guides':'1pLmTAQ5rkwxhoQRBll78UepQ8I9BYcVf'},
}


def service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    names=['GOOGLE_DRIVE_CLIENT_ID','GOOGLE_DRIVE_CLIENT_SECRET','GOOGLE_DRIVE_REFRESH_TOKEN']
    missing=[n for n in names if not os.getenv(n)]
    if missing:raise ValueError('Secrets ausentes: '+', '.join(missing))
    creds=Credentials(None,client_id=os.environ[names[0]],client_secret=os.environ[names[1]],refresh_token=os.environ[names[2]],token_uri='https://oauth2.googleapis.com/token',scopes=['https://www.googleapis.com/auth/drive'])
    creds.refresh(Request())
    return build('drive','v3',credentials=creds,cache_discovery=False)


def children(svc,parent):
    token=None
    while True:
        rsp=svc.files().list(q=f"'{parent}' in parents and trashed = false",fields='nextPageToken,files(id,name,mimeType,parents,md5Checksum,size)',pageSize=1000,pageToken=token).execute()
        yield from rsp.get('files',[])
        token=rsp.get('nextPageToken')
        if not token:break


def pending(svc,parent,path='',seen=None):
    seen=set() if seen is None else seen
    if parent in seen:raise ValueError('Ciclo de pastas na fila')
    seen.add(parent)
    for f in children(svc,parent):
        label=path+'/'+f['name']
        if f['mimeType']==FOLDER and f['name'].casefold() not in ('publicados','postados','_arquivo-postados'):
            yield from pending(svc,f['id'],label,seen)
        elif f['name']=='metadata.json':
            meta=json.loads(svc.files().get_media(fileId=f['id']).execute())
            if meta.get('postado') or meta.get('post_id') or meta.get('postado_em') or meta.get('status') in ('publicado','postado'):
                continue
            yield {'pasta':path,'metadata_id':f['id'],'metadata':meta}


def guide_names(meta):
    dm=meta.get('dm') or {}
    value=dm.get('material_pdf') or meta.get('material_pdf')
    if isinstance(value,dict):value=value.get('arquivo')
    return {value} if isinstance(value,str) and value.endswith('.pdf') else set()


def download(svc,fid,dest):
    from googleapiclient.http import MediaIoBaseDownload
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('wb') as out:
        dl=MediaIoBaseDownload(out,svc.files().get_media(fileId=fid));done=False
        while not done:_,done=dl.next_chunk()


def audit(svc,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report={'origem':'leitura ao vivo do Drive','perfis':{},'pdfs':[]}
    libraries={}
    for brand,ids in PROFILES.items():
        libraries[brand]=[f for f in children(svc,ids['guides']) if f['mimeType']=='application/pdf']
        queue=list(pending(svc,ids['queue']))
        report['perfis'][brand]={'fila':queue,'pdfs_na_biblioteca':libraries[brand]}
    # Baixar todas as iscas existentes permite comparar PDFs canônicos mesmo
    # quando o post referencia só a categoria privada em vez do nome do arquivo.
    for brand,files in libraries.items():
        for f in files:
            dest=out/'originais'/brand/(f['id']+'.pdf')
            download(svc,f['id'],dest)
            report['pdfs'].append({'perfil':brand,'id':f['id'],'nome':f['name'],'md5':hashlib.md5(dest.read_bytes()).hexdigest(),'arquivo':str(dest.relative_to(out))})
    (out/'auditoria.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Auditoria salva:',sum(len(v['fila']) for v in report['perfis'].values()),'posts pendentes;',len(report['pdfs']),'PDFs. Nenhum arquivo remoto alterado.')
    return report


def preflight(svc,manifest):
    """Valida lote completo antes de qualquer escrita. Manifesto revisado no repo."""
    from pypdf import PdfReader
    manifest=Path(manifest).resolve();data=json.loads(manifest.read_text())
    items=data.get('arquivos')
    if not isinstance(items,list) or not items:raise ValueError('Manifesto sem arquivos')
    prepared=[];seen=set()
    for item in items:
        if item.get('revisado') is not True:raise ValueError('PDF sem revisão explícita no manifesto')
        brand=item['perfil']
        if brand not in PROFILES:raise ValueError('Perfil inválido')
        path=(manifest.parent/item['arquivo']).resolve()
        if not path.is_relative_to(manifest.parent) or not path.is_file():raise ValueError('PDF deve existir dentro da pasta do manifesto')
        pdf=PdfReader(path)
        if not pdf.pages:raise ValueError('PDF vazio')
        text=' '.join(p.extract_text() or '' for p in pdf.pages).casefold()
        if 'aidealab' not in text or 'otalogia' in text:raise ValueError('PDF precisa usar somente a assinatura aidealab')
        fid=item['drive_id']
        if fid in seen:raise ValueError('ID duplicado no lote')
        seen.add(fid)
        remote=svc.files().get(fileId=fid,fields='id,name,mimeType,parents,md5Checksum,trashed,capabilities(canEdit)').execute()
        if remote.get('trashed') or remote['mimeType']!='application/pdf' or PROFILES[brand]['guides'] not in remote.get('parents',[]):raise ValueError('Destino fora da biblioteca de iscas autorizada')
        if remote['name']!=item['nome_drive']:raise ValueError('Nome do destino divergente')
        if not remote.get('capabilities',{}).get('canEdit'):raise ValueError('PDF sem permissão de edição')
        if not item.get('md5_original') or remote.get('md5Checksum')!=item['md5_original']:raise ValueError('PDF mudou desde a auditoria; recupere e revise a versão atual')
        prepared.append((item,path,remote))
    return prepared


def apply(svc,manifest,out):
    from googleapiclient.http import MediaFileUpload
    prepared=preflight(svc,manifest)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    # Backup de todo o lote antes da primeira alteração.
    for item,path,remote in prepared:
        backup=out/'backup'/f'{remote["id"]}.pdf';download(svc,remote['id'],backup)
        if hashlib.md5(backup.read_bytes()).hexdigest()!=item['md5_original']:raise ValueError('Backup diverge da auditoria; nenhuma alteração iniciada')
    changes=[]
    for item,path,remote in prepared:
        # Impede sobrescrever mudanças posteriores ao backup; preservar ID, nome,
        # parents e permissões. Não publica posts nem altera catálogo ou legendas.
        current=svc.files().get(fileId=remote['id'],fields='md5Checksum').execute()
        if current.get('md5Checksum')!=item['md5_original']:raise ValueError('Mudança concorrente no Drive; lote interrompido. Consulte os backups e o relatório parcial.')
        result=svc.files().update(fileId=remote['id'],media_body=MediaFileUpload(str(path),mimetype='application/pdf',resumable=True),fields='id,name,md5Checksum').execute()
        if result.get('md5Checksum')!=hashlib.md5(path.read_bytes()).hexdigest():raise ValueError('Checksum remoto não corresponde ao PDF enviado')
        changes.append(result)
        (out/'atualizados.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
    print(len(changes),'PDFs atualizados mantendo IDs e links. Posts e catálogo não foram alterados.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('modo',choices=['auditar','atualizar'])
    parser.add_argument('--saida',type=Path,default=Path('artefatos-dm'))
    parser.add_argument('--manifesto',type=Path)
    args=parser.parse_args()
    if args.modo=='atualizar' and not args.manifesto:parser.error('Atualização requer --manifesto revisado')
    svc=service()
    if args.modo=='auditar':audit(svc,args.saida)
    else:apply(svc,args.manifesto,args.saida)


if __name__=='__main__':main()
