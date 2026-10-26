"""Rebuild the Iowa audit table directly from preserved USDA/NOAA sources.

Verifies raw bytes, definitions, units, keys, and complete row-level agreement.
This is a provenance/fidelity check, not a new independent prediction test.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/reacquired';OUT=ROOT/'docs/q1_artifacts/reacquired_20261026'


def checked(path,record):
    content=path.read_bytes()
    if len(content)!=record['bytes'] or hashlib.sha256(content).hexdigest()!=record['sha256']:
        raise ValueError(f'Original-source integrity failure: {path.name}')
    return content


def main(allow_source_drift=False,verbose=True):
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((RAW/'nass/acquisition_manifest.json').read_text())
    p=ROOT/manifest['path'];checked(p,manifest)
    nass=pd.read_csv(p,dtype=str,keep_default_na=False)
    for col,val in {'Program':'SURVEY','Period':'YEAR','Geo Level':'COUNTY','State':'IOWA','State ANSI':'19',
                    'Commodity':'CORN','Data Item':'CORN, GRAIN - YIELD, MEASURED IN BU / ACRE','Domain':'TOTAL'}.items():
        if set(nass[col])!={val}:raise ValueError(f'Unexpected USDA definition: {col}')
    excluded=nass[nass['County ANSI'].eq('')].copy()
    if not excluded.County.str.contains('OTHER').all():raise ValueError('Unexplained missing county identifier')
    excluded['exclusion_reason']='combined-county estimate has no individual county ANSI'
    excluded.to_csv(OUT/'nass_excluded_aggregate_rows.csv',index=False)
    n=nass[nass['County ANSI'].ne('')].copy()
    n['fips']=n['State ANSI'].str.zfill(2)+n['County ANSI'].str.zfill(3)
    if not n.fips.str[-3:].astype(int).isin(range(1,200,2)).all():raise ValueError('Not an individual Iowa county')
    n['year']=n.Year.astype(int)
    n['yield_kg_ha']=pd.to_numeric(n.Value.str.replace(',',''),errors='raise')*62.77
    if n.duplicated(['year','fips']).any():raise ValueError('Duplicate observed county-year')
    n=n[['year','fips','County','yield_kg_ha']].rename(columns={'County':'county_name'})
    cm=json.loads((RAW/'noaa-cag/acquisition_manifest.json').read_text())
    if cm['errors']:raise ValueError('NOAA acquisition errors remain')
    if len(cm['files'])!=99*3:raise ValueError('Expected three original climate responses for 99 counties')
    rows=[]
    for rec in cm['files']:
        source=json.loads(checked(ROOT/rec['path'],rec));var=rec['variable']
        expected='Inches' if var=='pcp' else 'Degrees Fahrenheit'
        if source['description']['units']!=expected:raise ValueError(f'Wrong NOAA units: {rec["path"]}')
        for key,value in source['data'].items():
            if len(str(key))!=6 or not str(key).endswith('09'):raise ValueError('Wrong seasonal end month')
            year=int(str(key)[:4]);v=float(value['value'])
            if not 1990<=year<=2025 or not np.isfinite(v):raise ValueError('Invalid climate observation')
            rows.append({'year':year,'fips':rec['fips'],'variable':var,'value':v})
    long=pd.DataFrame(rows)
    if long.duplicated(['year','fips','variable']).any():raise ValueError('Duplicate NOAA source value')
    climate=long.pivot(index=['year','fips'],columns='variable',values='value').reset_index()
    if len(climate)!=99*36 or climate.isna().any().any():raise ValueError('Incomplete climate coverage')
    climate['season_temp_mean_c']=(climate.tavg-32)*5/9
    climate['season_tmax_mean_c']=(climate.tmax-32)*5/9
    climate['season_precip_mm']=climate.pcp*25.4
    rebuilt=n.merge(climate[['year','fips','season_temp_mean_c','season_tmax_mean_c','season_precip_mm']],on=['year','fips'],how='left',validate='one_to_one').sort_values(['year','fips'])
    rebuilt.to_csv(RAW/'cerespinn_county_rebuilt.csv',index=False)
    old=pd.read_csv(ROOT/'data/cerespinn_county_audit.csv',dtype={'fips':str})
    merged=old.merge(rebuilt,on=['year','fips'],suffixes=('_frozen','_reacquired'),how='outer',indicator=True,validate='one_to_one')
    report={'design':'New source reacquisition and retrospective row-level fidelity audit; not independent external validation',
            'usda_raw_rows':len(nass),'usda_excluded_combined_rows':len(excluded),'individual_county_years':len(rebuilt),
            'counties':rebuilt.fips.nunique(),'years':sorted(rebuilt.year.unique().tolist()),
            'noaa_raw_responses':len(cm['files']),'noaa_seasonal_values':len(rows),
            'noaa_season':'April-September; six months ending September',
            'unmatched_county_years':int(merged['_merge'].ne('both').sum()),'variables':{},
            'tolerance_abs':{'yield_kg_ha':1e-7,'climate':1e-7},
            'original_processed_data_unchanged':True,'national_legacy_raw_recovered':False,
            'scope_limit':'Confirms county-table numerical fidelity to currently downloaded public agency data, not old acquisition date or original raw bytes.'}
    for col in ['yield_kg_ha','season_temp_mean_c','season_tmax_mean_c','season_precip_mm']:
        diff=merged[col+'_reacquired']-merged[col+'_frozen'];merged[col+'_difference']=diff
        report['variables'][col]={'n_compared':int(diff.notna().sum()),'max_abs_difference':float(diff.abs().max()),
                                 'rows_within_tolerance':int(diff.abs().le(1e-7).sum())}
    report['verified']=report['unmatched_county_years']==0 and all(v['rows_within_tolerance']==len(old) for v in report['variables'].values())
    report['raw_file_integrity_verified']=True
    report['county_year_coverage_verified']=report['unmatched_county_years']==0
    report['yield_numerical_fidelity_verified']=report['variables']['yield_kg_ha']['rows_within_tolerance']==len(old)
    report['climate_exact_fidelity_verified']=all(report['variables'][c]['rows_within_tolerance']==len(old) for c in ['season_temp_mean_c','season_tmax_mean_c','season_precip_mm'])
    report['climate_difference_years']=sorted(merged.loc[merged[[c+'_difference' for c in ['season_temp_mean_c','season_tmax_mean_c','season_precip_mm']]].abs().gt(1e-7).any(axis=1),'year'].unique().tolist())
    report['drift_policy']='Differences disclosed and new-source benchmark allowed; frozen data untouched' if allow_source_drift else 'Strict comparison; any numerical difference fails exact-fidelity gate'
    merged.to_csv(OUT/'agency_source_comparison.csv',index=False)
    (OUT/'source_fidelity.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    if verbose:print(json.dumps(report,indent=2),flush=True)
    if not report['county_year_coverage_verified'] or not report['yield_numerical_fidelity_verified']:
        raise RuntimeError('Yield or county-year coverage differs; climate-drift permission cannot authorize a target change')
    if not report['verified'] and not allow_source_drift:raise RuntimeError('New climate source values differ; exact fidelity is not established. Use --allow-source-drift only for an explicitly separate source-version analysis.')
    return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-source-drift',action='store_true',help='Permit separate source-version analysis while retaining exact-fidelity=false')
    main(parser.parse_args().allow_source_drift)
