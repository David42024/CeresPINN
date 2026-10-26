"""Acquire and checksum the public USDA Colorado 2012–2013 field experiment."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import requests
import sys

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS='--previous' in sys.argv
OUT=ROOT/('data/external/colorado_irrigation_2008_2011' if PREVIOUS else 'data/external/colorado_irrigation_2012_2013')
URL='https://api.figshare.com/v2/articles/'+('24660372' if PREVIOUS else '24662391')
DOI='10.15482/USDA.ADC/1254006' if PREVIOUS else '10.15482/USDA.ADC/1439968'


def main():
    if '--verify-only' in sys.argv:
        manifest=json.loads((OUT/'acquisition_manifest.json').read_text(encoding='utf-8'))
        for rec in manifest['files']:
            path=OUT/rec['name']
            if path.parent!=OUT or not path.is_file():raise ValueError('Missing or invalid source file')
            data=path.read_bytes()
            if len(data)!=rec['bytes'] or hashlib.md5(data).hexdigest()!=rec['official_md5'] or hashlib.sha256(data).hexdigest()!=rec['sha256']:
                raise ValueError('Checksum mismatch: '+rec['name'])
        print(f'Verified {len(manifest["files"])} preserved source files without network access.')
        return
    OUT.mkdir(parents=True,exist_ok=True)
    response=requests.get(URL,timeout=60);response.raise_for_status();article=response.json()
    if article.get('doi')!=DOI:raise ValueError('Unexpected dataset identity')
    records=[]
    for file in article['files']:
        path=OUT/file['name']
        if not path.exists() or hashlib.md5(path.read_bytes()).hexdigest()!=file['computed_md5']:
            result=requests.get(file['download_url'],timeout=120);result.raise_for_status()
            data=result.content
            if len(data)!=file['size'] or hashlib.md5(data).hexdigest()!=file['computed_md5']:
                raise ValueError('Source checksum mismatch: '+file['name'])
            path.write_bytes(data)
        data=path.read_bytes()
        records.append({'name':file['name'],'file_id':file['id'],'url':file['download_url'],
                        'bytes':len(data),'official_md5':file['computed_md5'],
                        'sha256':hashlib.sha256(data).hexdigest()})
    manifest={'source':URL,'dataset_url':article['url_public_html'],'doi':article['doi'],
              'title':article['title'],'license':article['license'],
              'retrieved_utc':datetime.now(timezone.utc).isoformat(),
              'scope':'New independent public source; not the historical national training download',
              'files':records}
    (OUT/'acquisition_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Verified {len(records)} original public files ({sum(x["bytes"] for x in records)} bytes).')


if __name__=='__main__':main()
