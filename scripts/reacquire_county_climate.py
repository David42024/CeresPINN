"""Preserve complete public NOAA CAG responses for the Iowa county audit.

New acquisition, not a claim to recover the original extraction bytes.
Does not change the frozen checkpoint inputs or select a forecasting model.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,time
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/reacquired/noaa-cag'


def acquire(fips,var,start,end):
    if len(fips)!=5 or not fips.startswith('19') or int(fips[2:]) not in range(1,200,2):
        raise ValueError(f'Not an individual Iowa county: {fips}')
    url=f'https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/county/time-series/IA-{fips[2:]}/{var}/6/9/{start}-{end}.json'
    path=OUT/f'{fips}_{var}_{start}_{end}_apr_sep.json'
    record_path=path.with_suffix('.provenance.json')
    if path.exists() and record_path.exists():
        content=path.read_bytes();record=json.loads(record_path.read_text())
        if hashlib.sha256(content).hexdigest()!=record['sha256']:raise ValueError('Raw source checksum mismatch')
        if record['url']!=url:raise ValueError('Query differs from saved source')
    else:
        for attempt in range(3):
            try:
                req=Request(url,headers={'User-Agent':'CeresPINN-research-reproducibility/1.0'})
                with urlopen(req,timeout=30) as r:
                    content=r.read();status=r.status;headers={k:r.headers.get(k) for k in ['Content-Type','ETag','Last-Modified','Date']}
                break
            except Exception:
                if attempt==2:raise
                time.sleep(1+attempt)
        parsed=json.loads(content)
        if not parsed.get('data'):raise ValueError(f'Empty NOAA observations: {fips} {var}')
        path.write_bytes(content)
        record={'url':url,'downloaded_at_utc':datetime.now(timezone.utc).isoformat(),'http_status':status,
                'response_headers':headers,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content),
                'path':path.relative_to(ROOT).as_posix(),'fips':fips,'variable':var,
                'season':'6-month aggregate ending September (April-September)',
                'source_metadata':{k:v for k,v in parsed.items() if k!='data'}}
        record_path.write_text(json.dumps(record,indent=2))
    parsed=json.loads(content);rows=[]
    for key,r in parsed['data'].items():
        if str(key).endswith('09') and start<=int(str(key)[:4])<=end:
            rows.append({'year':int(str(key)[:4]),'fips':fips,'variable':var,'source_value':float(r['value']),
                         'source_path':path.relative_to(ROOT).as_posix()})
    if len(rows)!=end-start+1:raise ValueError(f'Incomplete seasonal record {fips} {var}: {len(rows)}')
    return record,rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fips',action='append')
    p.add_argument('--start',type=int,default=1990);p.add_argument('--end',type=int,default=2025)
    p.add_argument('--workers',type=int,default=3);args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    fips=args.fips or sorted(pd.read_csv(ROOT/'data/cerespinn_county_audit.csv',dtype={'fips':str}).fips.unique())
    records=[];rows=[];errors=[];work=[(f,v) for f in fips for v in ['tavg','tmax','pcp']]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(acquire,f,v,args.start,args.end):(f,v) for f,v in work}
        for i,future in enumerate(as_completed(futures),1):
            try:r,rs=future.result();records.append(r);rows.extend(rs)
            except Exception as e:errors.append({'fips':futures[future][0],'variable':futures[future][1],'error':str(e)})
            if i%15==0 or i==len(work):print(f'NOAA sources processed: {i}/{len(work)}; errors: {len(errors)}',flush=True)
    manifest={'downloaded_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'new public-source fidelity audit',
              'start_year':args.start,'end_year':args.end,'files':sorted(records,key=lambda r:r['path']),'errors':errors}
    (OUT/'acquisition_manifest.json').write_text(json.dumps(manifest,indent=2))
    pd.DataFrame(rows).sort_values(['fips','year','variable']).to_csv(OUT/'seasonal_source_values.csv',index=False)
    if errors:raise RuntimeError(f'{len(errors)} incomplete NOAA sources; inspect acquisition_manifest.json')
    print(f'Complete: {len(records)} original responses, {len(rows)} seasonal values',flush=True)


if __name__=='__main__':main()
