"""Reviewer corrections with frozen, leakage-safe internal validation.

Does not replace the deployed checkpoint or select a model using the test set.
County inputs are preserved processed observations, not independently verified raw data.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
import torch
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.generate_q1_extended_audit import FEATURES, fit_neural

OUT = ROOT / 'docs/q1_artifacts/revision_20261026'
SEEDS = [0, 1, 42]
CLIMATE = ['temp_anomaly_c', 'seasonal_precip_mm']


def metrics(y, p):
    y, p = np.asarray(y), np.asarray(p)
    return {'rmse_kg_ha': float(np.mean((p-y)**2)**0.5),
            'mae_kg_ha': float(np.abs(p-y).mean()),
            'r2': float(1-np.sum((p-y)**2)/np.sum((y-y.mean())**2)),
            'bias_kg_ha': float((p-y).mean())}


def interval(y, p, block=3, draws=20000):
    rng = np.random.default_rng(42)
    y,p=np.asarray(y),np.asarray(p)
    starts=rng.integers(0,len(y),size=(draws,int(np.ceil(len(y)/block))))
    idx=((starts[:,:,None]+np.arange(block))%len(y)).reshape(draws,-1)[:,:len(y)]
    errors=p[idx]-y[idx]
    return {k: np.quantile(v,[.025,.975]).tolist() for k,v in {
        'rmse_kg_ha':np.sqrt(np.mean(errors**2,axis=1)),
        'mae_kg_ha':np.mean(abs(errors),axis=1)}.items()}


def county_interval(frame, draws=20000):
    """Resample complete year clusters and recompute pooled county-year errors."""
    e=frame.assign(squared=(frame.predicted-frame.observed)**2,
                   absolute=abs(frame.predicted-frame.observed))
    groups=e.groupby('year').agg(squared=('squared','sum'),absolute=('absolute','sum'),n=('year','size'))
    rng=np.random.default_rng(42);n=len(groups)
    starts=rng.integers(0,n,size=(draws,int(np.ceil(n/3))))
    idx=((starts[:,:,None]+np.arange(3))%n).reshape(draws,-1)[:,:n]
    denom=groups.n.to_numpy()[idx].sum(axis=1)
    rmse=np.sqrt(groups.squared.to_numpy()[idx].sum(axis=1)/denom)
    mae=groups.absolute.to_numpy()[idx].sum(axis=1)/denom
    return {'rmse_kg_ha':np.quantile(rmse,[.025,.975]).tolist(),
            'mae_kg_ha':np.quantile(mae,[.025,.975]).tolist()}


def vif_table(frame):
    active=[c for c in frame if frame[c].std()>1e-9]
    rows=[]
    for c in frame:
        if c not in active:
            rows.append({'feature':c,'vif':None,'status':'constant excluded'});continue
        others=[x for x in active if x!=c]
        r2=LinearRegression().fit(frame[others],frame[c]).score(frame[others],frame[c])
        rows.append({'feature':c,'vif':float(1/(1-r2)) if r2<1-1e-12 else None,
                     'status':'rank deficient infinite VIF' if r2>=1-1e-12 else 'finite'})
    return pd.DataFrame(rows)


def national():
    raw=pd.read_csv(ROOT/'data/cerespinn_training_iowa.csv')
    a=raw.groupby(['scenario','year'],as_index=False)[FEATURES+['yield_bu_acre']].median()
    train0=a[a.year<=2005]
    train0[FEATURES].corr().to_csv(OUT/'correlations_initial_training_only.csv')
    vif_table(train0[FEATURES]).to_csv(OUT/'vif_initial_training_only.csv',index=False)
    vif_table(train0[CLIMATE]).to_csv(OUT/'vif_reduced_initial_training_only.csv',index=False)
    allrows=[]
    for start in range(2006,2026,4):
        tr=a[a.year<start].copy(); te=a[a.year.between(start,start+3)].copy()
        trend=LinearRegression().fit(tr[['year']],tr.yield_bu_acre)
        preds={'year_trend':trend.predict(te[['year']])}
        for name, cols, reg in [('linear_all',FEATURES,LinearRegression()),
                                 ('ridge_all',FEATURES,Ridge(alpha=1.0)),
                                 ('ridge_climate_only',CLIMATE,Ridge(alpha=1.0))]:
            est=make_pipeline(StandardScaler(),reg).fit(tr[cols],tr.yield_bu_acre)
            preds[name]=est.predict(te[cols])
        for name,cols,weight,detrend in [
            ('mlp_all',FEATURES,0.,False), ('monotonic_all',FEATURES,.5,False),
            ('monotonic_climate_only',CLIMATE,.5,False),
            ('detrended_monotonic_climate',CLIMATE,.5,True)]:
            train=tr.copy()
            if detrend: train['yield_bu_acre']=tr.yield_bu_acre-trend.predict(tr[['year']])
            pp=[]
            for seed in SEEDS:
                prediction,_=fit_neural(train,te,seed,weight,cols)
                if detrend: prediction=prediction+trend.predict(te[['year']])
                pp.append(prediction)
            preds[name]=np.mean(pp,axis=0)
        frame=pd.DataFrame({'year':te.year,'observed':te.yield_bu_acre,**preds})
        annual=frame.groupby('year',as_index=False).mean(numeric_only=True)
        annual['fold']=start
        for col in annual:
            if col not in ['year','fold']: annual[col]*=62.77
        allrows.append(annual)
        print(f'National fold {start}-{start+3} complete',flush=True)
    oof=pd.concat(allrows).sort_values('year')
    oof.to_csv(OUT/'rolling_origin_predictions.csv',index=False)
    scores=[]
    for name in preds:
        scores.append({'model':name,**metrics(oof.observed,oof[name]),
                       'block_bootstrap_95_ci':interval(oof.observed,oof[name])})
    comparisons=[]
    for comp in ['year_trend','linear_all','ridge_all','mlp_all']:
        delta=abs(oof.monotonic_all-oof.observed)-abs(oof[comp]-oof.observed)
        d=pd.DataFrame({'fold':oof.fold,'delta':delta}).groupby('fold').delta.mean().to_numpy()
        permutations=np.asarray(list(itertools.product([-1,1],repeat=len(d))))
        p=float((abs((permutations*d).mean(axis=1))>=abs(d.mean())-1e-10).mean())
        comparisons.append({'comparison':f'monotonic_all minus {comp}',
                            'mean_absolute_error_difference_kg_ha':float(delta.mean()),
                            'fold_sign_randomization_p':p,'independent_blocks':len(d)})
    order=np.argsort([c['fold_sign_randomization_p'] for c in comparisons]); previous=0
    for rank,i in enumerate(order):
        previous=max(previous,min(1.,(len(order)-rank)*comparisons[i]['fold_sign_randomization_p']))
        comparisons[i]['holm_adjusted_p']=previous
    return {'design':'five expanding-window four-year test blocks 2006-2025; no future training',
            'n_unique_test_years':20,'initial_train_years':list(range(1990,2006)),
            'seeds':SEEDS,'epochs':300,'hyperparameters':'fixed before new evaluation; no test tuning',
            'climate_only_features':CLIMATE,'trend':'OLS on training years only; residual network has no year input',
            'uncertainty':'circular moving-block bootstrap, block length 3 years, 20000 draws; descriptive intervals',
            'caveat':'retrospective additional internal audit; earlier manuscript results already known; not a pristine external holdout',
            'scores':scores,'paired_comparisons':comparisons}


def county(input_path=None,output_dir=None,provenance=None):
    frozen=Path(input_path) if input_path is not None else ROOT/'data/cerespinn_county_audit.csv'
    destination=Path(output_dir) if output_dir is not None else OUT
    destination.mkdir(parents=True,exist_ok=True)
    if not frozen.exists():
        if input_path is not None:raise FileNotFoundError(frozen)
        source=ROOT/'backend/data/processed/canonical_panel.parquet'
        df=pd.read_parquet(source)
        cols=['year','fips','county_name','yield_kg_ha','season_temp_mean_c','season_tmax_mean_c','season_precip_mm']
        df[cols].sort_values(['year','fips']).to_csv(frozen,index=False,float_format='%.12g')
    df=pd.read_csv(frozen,dtype={'fips':str})
    if df.duplicated(['year','fips']).any(): raise ValueError('Duplicate county-years')
    if df.isna().any().any(): raise ValueError('Missing county values')
    if not df.fips.str.fullmatch('19[0-9]{3}').all(): raise ValueError('Non-Iowa county')
    if (df.fips.str[-3:]=='000').any(): raise ValueError('State aggregates are not counties')
    counties=sorted(df.fips.unique());rng=np.random.default_rng(42);rng.shuffle(counties)
    groups=np.array_split(counties,5);rows=[]
    for fold,held in enumerate(groups):
        tr=df[(df.year<=2017)&~df.fips.isin(held)]
        te=df[(df.year>=2018)&df.fips.isin(held)]
        for name,cols in [('trend_only',['year']),('climate_only',['season_temp_mean_c','season_precip_mm']),
                          ('trend_and_climate',['year','season_temp_mean_c','season_precip_mm'])]:
            est=make_pipeline(StandardScaler(),Ridge(alpha=1.)).fit(tr[cols],tr.yield_kg_ha)
            for (_,r),pred in zip(te.iterrows(),est.predict(te[cols])):
                rows.append({'fold':fold,'model':name,'year':r.year,'fips':r.fips,
                             'observed':r.yield_kg_ha,'predicted':float(pred)})
    pred=pd.DataFrame(rows);pred.to_csv(destination/'held_county_future_predictions.csv',index=False)
    scores=[]
    for name,g in pred.groupby('model'):
        annual=g.groupby('year')[['observed','predicted']].mean()
        county_scores=[metrics(h.observed,h.predicted)['rmse_kg_ha'] for _,h in g.groupby('fips')]
        scores.append({'model':name,**metrics(g.observed,g.predicted),
                       'county_rmse_median_kg_ha':float(np.median(county_scores)),
                       'annual_cluster_bootstrap_ci':county_interval(g)})
    return {'design':'five disjoint county groups; train other counties <=2017, test held counties 2018-2025',
            'input_rows':len(df),'counties':len(counties),'test_county_years':int((df.year>=2018).sum()),
            'independent_test_years':8,'spatial_scope':'internal Iowa county transfer; not independent field validation',
            'features_removed':{'cdd':'NOAA cooling degree days; NOT consecutive dry days',
                'gdd':'seasonal mean approximation, not daily accumulated GDD',
                'heat_days_30c/35c':'heuristic from seasonal mean maxima, not observed daily counts',
                'vpd_mean_kpa':'heuristic temperature formula, not measured vapor pressure deficit'},
            'season':'April-September, six months ending September; historical column names retained',
            'input_path':frozen.relative_to(ROOT).as_posix(),
            'provenance':provenance or 'preserved processed panel; current-source fidelity and reacquired baseline are documented separately in docs/q1_artifacts/reacquired_20261026',
            'scores':scores}


def base_revision():
    # An extracted archive must not accidentally inherit a parent checkout's
    # Git identity, or require Git just to reproduce numerical experiments.
    if (ROOT/'.git').exists():
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for name in ['MANIFIESTO_PUBLICO.json','MANIFIESTO_REVISION.json']:
        path=ROOT/name
        if path.exists():return json.loads(path.read_text())['base_commit']
    raise FileNotFoundError('No repository metadata or frozen archive manifest records the base revision')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    revision=base_revision()
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    result={'national':national(),'county':county(),
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
                           'scipy':scipy.__version__,'sklearn':sklearn.__version__,'torch':torch.__version__},
            'base_commit':revision}
    inputs=['data/cerespinn_training_iowa.csv','data/cerespinn_county_audit.csv','scripts/revision_scientific_audit.py']
    result['inputs']=[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()} for p in inputs]
    (OUT/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print('Scientific audit complete',flush=True)


if __name__=='__main__':main()
