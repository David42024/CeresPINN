"""Preserve public USDA Bushland metadata and explicitly selected research files.

No inference or numerical values are reconstructed from article summaries.
Every downloaded file retains its official name, size, URL and checksums.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/external/bushland'
ARTICLE_IDS=[24855909,24855957,25316164,25316362]


def fetch(url, payload=None):
    request=Request(url,data=json.dumps(payload).encode() if payload is not None else None,
                    headers={'User-Agent':'CeresPINN-public-research-data/1.0','Content-Type':'application/json'})
    for attempt in range(3):
        try:
            with urlopen(request,timeout=90) as response:return response.read()
        except Exception:
            if attempt==2:raise
            time.sleep(2*(attempt+1))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--article',type=int,action='append')
    parser.add_argument('--file-id',type=int,action='append')
    parser.add_argument('--search')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.search:
        result=json.loads(fetch('https://api.figshare.com/v2/articles/search',{'search_for':args.search,'limit':10}))
        print(json.dumps([{'id':a['id'],'title':a['title'],'doi':a.get('doi')} for a in result],indent=2))
        return
    manifest=[]
    for article_id in args.article or ARTICLE_IDS:
        api=f'https://api.figshare.com/v2/articles/{article_id}'
        raw=fetch(api);article=json.loads(raw)
        target=OUT/str(article_id);target.mkdir(exist_ok=True)
        (target/'metadata.json').write_bytes(raw)
        print(article_id,article['title'],article.get('doi'),article.get('license'),flush=True)
        for file in article.get('files',[]):
            record={'article_id':article_id,'doi':article.get('doi'),'license':article.get('license'),
                    'article_version':article.get('version'),'file_id':file['id'],'name':file['name'],
                    'bytes':file['size'],'url':file['download_url'],'official_md5':file.get('computed_md5')}
            print('FILE',file['id'],file['name'],file['size'],flush=True)
            if args.download and (not args.file_id or file['id'] in args.file_id):
                filename=Path(file['name']).name
                path=target/filename
                content=path.read_bytes() if path.exists() else fetch(file['download_url'])
                if len(content)!=file['size']:raise ValueError(f'Size mismatch: {filename}')
                md5=hashlib.md5(content).hexdigest()
                if file.get('computed_md5') and md5!=file['computed_md5']:
                    raise ValueError(f'MD5 mismatch: {filename}')
                path.write_bytes(content)
                record['sha256']=hashlib.sha256(content).hexdigest()
                record['local_path']=path.relative_to(ROOT).as_posix()
                record['downloaded_at_utc']=datetime.now(timezone.utc).isoformat()
            manifest.append(record)
    old=OUT/'acquisition_manifest.json'
    if old.exists():
        records={r['file_id']:r for r in json.loads(old.read_text())['files']}
        for record in manifest:records[record['file_id']]={**records.get(record['file_id'],{}),**record}
        manifest=list(records.values())
    old.write_text(json.dumps({'files':manifest},indent=2),encoding='utf-8')


if __name__=='__main__':main()
