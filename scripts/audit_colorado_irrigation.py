"""Retrospective block-paired irrigation contrasts and measured-state transfer.

This is a two-year, one-site study. It does not calibrate the software's
management multipliers, nor validate the national checkpoint or process model.
"""
from pathlib import Path
import hashlib
import itertools
import json
import re
import sys
import numpy as np
import openpyxl
import pandas as pd
from scipy.stats import t
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/external/colorado_irrigation_2012_2013'
OUT=ROOT/'docs/q1_artifacts/colorado_irrigation_20261026_v3'
WORKBOOK='2012-2013_Maize_Compiled database 06012018.xlsx'
PROTOCOL={
 'version':1,'study':'USDA ARS Greeley, Colorado, 2012–2013; one site; randomized treatments within blocks',
 'retrospective':'Source metadata and example rows were inspected before protocol; not preregistered.',
 'design':'Four block-paired observations per treatment per year; first plot digit is the block. The letter identifies field section and treatments were randomized across sections, per the source dictionary.',
 'planned_contrasts':['100/50 minus 100/100','80/80 minus 100/100'],
 'interpretation':'Percentages denote target ET replacement during late vegetative / grain-filling periods, not 75% of total water.',
 'yield':'Grain kg/ha at 15.5% moisture for treatment contrasts; dry mass is 0.845 times standard-moisture yield.',
 'statistics':'Within-year complete paired block differences; paired t interval with n-1 degrees of freedom; exact two-sided sign randomization; Holm adjustment over four comparisons. Missing yields excluded explicitly; descriptive two-year study, not a new field recommendation.',
 'state_transfer':'2013 end-of-season biomass is absent. Fit a one-feature Ridge on 2012 maximum observed LAI and dry grain; evaluate available 2013 plots. Maximum LAI uses measurements across the season, so this conditional state-to-yield comparison is not an early forecast or full process-model validation. Do not reconstruct missing biomass from observed grain and harvest index.',
 'split':{'fit_year':2012,'evaluation_year':2013},
 'caveat':'One site and two years; 2013 already in archived source. Replicated plots are not independent sites or years. No cultivar or planting date contrast is evaluated.',
}


def extract():
    meta=json.loads((RAW/'acquisition_manifest.json').read_text(encoding='utf-8'))
    rec=next(r for r in meta['files'] if r['name']==WORKBOOK)
    path=RAW/WORKBOOK
    if hashlib.sha256(path.read_bytes()).hexdigest()!=rec['sha256']:raise ValueError('Source workbook hash changed')
    book=openpyxl.load_workbook(path,read_only=True,data_only=True)
    sheet=book['Annual data by plot'];records=[]
    for index,row in enumerate(sheet.iter_rows(min_row=3,values_only=True),3):
        if row[0] not in (2012,2013):continue
        year,plot,code,treatment,hi,biomass,lai,density,yield15,et=row[:10]
        if not re.fullmatch(r'[ABCD]\d\d',str(plot)):raise ValueError(f'Invalid plot identifier {plot}')
        def number(value):
            return float(value) if isinstance(value,(float,int)) and np.isfinite(value) else np.nan
        records.append({'year':int(year),'plot':plot,'section':plot[0],'block':plot[1],'treatment_code':int(code),
                        'treatment':treatment,'biomass_dry_kg_ha':number(biomass),'lai_max':number(lai),
                        'yield_15_5pct_kg_ha':number(yield15),'yield_dry_kg_ha':number(yield15)*0.845,
                        'harvest_index':number(hi),'annual_et_mm':number(et),'source_row':index})
    book.close();df=pd.DataFrame(records)
    if len(df)!=96 or df.duplicated(['year','plot']).any():raise ValueError('Expected 96 unique plot-years')
    counts=df.groupby(['year','block','treatment']).size()
    if len(counts)!=96 or not counts.eq(1).all():raise ValueError('Block-treatment design is not complete')
    if df.groupby(['year','treatment']).size().ne(4).any():raise ValueError('Expected four blocks per treatment-year')
    return df,rec


def paired_contrast(df,year,treatment):
    sub=df[df.year==year]
    control=sub[sub.treatment=='100/100'].set_index('block')['yield_15_5pct_kg_ha']
    treated=sub[sub.treatment==treatment].set_index('block')['yield_15_5pct_kg_ha']
    if set(control.index)!=set(treated.index) or len(control)!=4:raise ValueError('Unpaired block assignments')
    pairs=pd.concat([control.rename('control'),treated.rename('treated')],axis=1).dropna()
    if len(pairs)<2:raise ValueError('Too few complete paired blocks')
    delta=(pairs.treated-pairs.control).to_numpy()
    mean=float(delta.mean());se=float(delta.std(ddof=1)/np.sqrt(len(delta)))
    half=float(t.ppf(.975,len(delta)-1)*se)
    samples=np.array(list(itertools.product([-1,1],repeat=len(delta))))*delta
    p=float(np.mean(np.abs(samples.mean(axis=1))>=abs(mean)-1e-10))
    return {'year':year,'treatment':treatment,'control':'100/100','n_blocks':len(delta),
            'difference_kg_ha':mean,'paired_t_95_ci_kg_ha':[mean-half,mean+half],
            'exact_sign_p':p,'control_mean_kg_ha':float(pairs.control.mean()),
            'treated_mean_kg_ha':float(pairs.treated.mean()),'paired_blocks':pairs.index.tolist(),
            'missing_blocks':sorted(set(control.index)-set(pairs.index)), 'paired_differences_kg_ha':delta.tolist()}


def score(y,p):
    y=np.asarray(y);p=np.asarray(p)
    return {'n':len(y),'rmse_kg_ha':float(np.sqrt(np.mean((p-y)**2))),
            'mae_kg_ha':float(np.mean(abs(p-y))),'bias_kg_ha':float(np.mean(p-y)),
            'r2':float(1-np.sum((p-y)**2)/np.sum((y-y.mean())**2))}


def main():
    OUT.mkdir(parents=True,exist_ok=True);protocol=OUT/'protocol.json'
    if protocol.exists() and json.loads(protocol.read_text(encoding='utf-8'))!=PROTOCOL:
        raise ValueError('Protocol mismatch; preserve old protocol and start a distinct analysis directory')
    if not protocol.exists():protocol.write_text(json.dumps(PROTOCOL,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    df,source=extract();df.to_csv(OUT/'plot_observations.csv',index=False)
    contrasts=[paired_contrast(df,year,treatment) for year in (2012,2013) for treatment in ('100/50','80/80')]
    previous=0
    for rank,i in enumerate(np.argsort([row['exact_sign_p'] for row in contrasts])):
        previous=max(previous,min(1.0,(len(contrasts)-rank)*contrasts[i]['exact_sign_p']))
        contrasts[i]['holm_adjusted_p']=previous
    train=df[(df.year==2012)&df.lai_max.notna()&df.yield_dry_kg_ha.notna()]
    test=df[(df.year==2013)&df.lai_max.notna()&df.yield_dry_kg_ha.notna()]
    y=train.yield_dry_kg_ha.to_numpy()
    ridge=make_pipeline(StandardScaler(),Ridge(alpha=1.)).fit(train[['lai_max']],y)
    pred=test[['year','plot','block','treatment','lai_max','yield_dry_kg_ha']].copy()
    pred['training_mean']=y.mean();pred['ridge_lai']=ridge.predict(test[['lai_max']])
    pred.to_csv(OUT/'conditional_state_predictions.csv',index=False)
    summary={'protocol':PROTOCOL,'protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),
             'source_sha256':source['sha256'],'n_plot_years':len(df),'n_sites':1,'independent_years':2,
             'missing_values':{'grain_yield':int(df.yield_15_5pct_kg_ha.isna().sum()),'biomass_2013':int(df.loc[df.year==2013,'biomass_dry_kg_ha'].isna().sum())},
             'contrast_results':contrasts,
             'conditional_state_results':{name:score(pred.yield_dry_kg_ha,pred[name]) for name in ['training_mean','ridge_lai']},
             'process_model_evaluated':False,'national_checkpoint_evaluated':False,'deployed_management_calibrated':False}
    (OUT/'results.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'contrasts':contrasts,'conditional_state':summary['conditional_state_results']},indent=2,ensure_ascii=False))


if __name__=='__main__':main()
