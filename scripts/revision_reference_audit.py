"""Resolve original bibliographic entries against Crossref without auto-accepting candidates."""
import concurrent.futures
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

from docx import Document

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/q1_artifacts/revision_20261026'


def entries():
    source=ROOT/'manuscript_source.docx'
    if not source.exists():source=Path(r'C:\Users\USERJSSV\Downloads\CeresPINN_LucanoNieves_RojasVillgas.docx')
    d=Document(source)
    text='\n'.join(p.text for p in d.paragraphs[124:])
    text=re.sub(r'\[(?:10|20)\]\s*','\n',text)
    lines=[]
    for line in text.splitlines():
        if re.match(r"^[A-Za-zÀ-ž][^\n]*?\(20\d{2}\)\.",line):lines.append(line)
        elif lines:lines[-1]+=' '+line
    if len(lines)!=41:raise ValueError(f'Expected 41 references, got {len(lines)}')
    return lines


def resolve(item):
    i,entry=item
    try:
        url='https://api.crossref.org/works?'+urlencode({'query.bibliographic':entry,'rows':3})
        req=Request(url,headers={'User-Agent':'CeresPINN-reference-audit/1.0'})
        with urlopen(req,timeout=45) as r: data=json.load(r)['message']['items']
        candidates=[{k:x.get(k) for k in ['title','DOI','author','container-title','volume','issue','page','article-number','published','type','URL','score']} for x in data]
        return {'number':i+1,'original':entry,'status':'candidate requires author-title-year check','candidates':candidates}
    except Exception as exc:return {'number':i+1,'original':entry,'status':'unresolved','error':str(exc)}


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(resolve,enumerate(entries())))
    (OUT/'reference_candidates.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    for x in results:
        top=x.get('candidates',[{}])[0]
        print(x['number'],top.get('title'),top.get('DOI'),top.get('published'),flush=True)
