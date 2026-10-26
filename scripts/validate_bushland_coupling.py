"""Retrospective external-source experiment; see the frozen protocol.json.

Run after prepare_bushland_data.py. The six fitted parameters use only
1989/1990/1994/2013. No choice depends on the 2016/2018 evaluation scores.
This is a separate process extension, not validation of the national checkpoint.
"""
from pathlib import Path
import sys,json,hashlib
from dataclasses import asdict
import numpy as np
import pandas as pd
import openpyxl
from scipy.optimize import least_squares
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.coupled_crop import SoilLayer,CropParameters,simulate_crop,fao56_reference_et
DATA=ROOT/'data/bushland_processed';OUT=ROOT/'docs/q1_artifacts/bushland'
TRAIN=[1989,1990,1994,2013];TEST=[2016,2018]


def soil_layers():
    path=ROOT/'data/external/bushland/25316362/Bushland_TX_soil_properties.xlsx'
    w=openpyxl.load_workbook(path,read_only=True,data_only=True)
    rows=list(w['Bushland soil properties'].values)[1:14];layers=[]
    for a,b in [(0,30),(30,60),(60,150)]:
        weights=np.array([max(0,min(b,float(r[2]))-max(a,float(r[1]))) for r in rows])
        if abs(weights.sum()-(b-a))>1e-8:raise ValueError('Incomplete soil profile')
        avg=lambda col:float(np.dot(weights,[float(r[col]) for r in rows])/weights.sum())
        layers.append(SoilLayer((b-a)*10,avg(6),avg(7),avg(17),avg(16),avg(20)))
    w.close();return layers


def metrics(obs,pred):
    a=np.asarray(obs);p=np.asarray(pred);d=p-a
    return {'n':len(a),'rmse':float(np.sqrt(np.mean(d*d))),'mae':float(np.mean(abs(d))),
            'bias':float(d.mean()),'r2':float(1-(d*d).sum()/((a-a.mean())**2).sum()) if len(a)>1 and np.std(a)>0 else None}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    protocol=json.loads((OUT/'protocol.json').read_text())
    assert protocol['calibration_years']==TRAIN and protocol['evaluation_years']==TEST
    input_files=sorted(p for p in DATA.iterdir() if p.suffix=='.csv' and p.name!='model_forcing.csv')
    input_manifest=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
                     'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in input_files]
    (OUT/'processed_input_manifest.json').write_text(json.dumps(input_manifest,indent=2))
    soil=soil_layers()
    (DATA/'soil_layers.json').write_text(json.dumps([asdict(s) for s in soil],indent=2))
    weather=pd.read_csv(DATA/'daily_weather.csv');water=pd.read_csv(DATA/'daily_water_observed.csv')
    growth=pd.read_csv(DATA/'growth_observed.csv');theta=pd.read_csv(DATA/'soil_water_observed.csv')
    harvest=pd.read_csv(DATA/'grain_yield_observed.csv');calendar=pd.read_csv(DATA/'calendars.csv')
    events=pd.concat([pd.read_csv(p) for p in DATA.glob('irrigation_events_*.csv')],ignore_index=True)
    summaries=[];seasons=[];forcing=[];observations=[]
    for c in calendar.to_dict('records'):
        y,f,plant=int(c['year']),c['field'],int(c['planting_doy'])
        met=weather[(weather.year==y)&weather.doy.between(plant,320)].copy()
        if len(met)!=321-plant or not met.quality_complete.all():raise ValueError(f'Incomplete weather: {y} {f}')
        wat=water[(water.year==y)&(water.field==f)].set_index('doy')
        eve=events[(events.year==y)&(events.field==f)].groupby('doy').irrigation_mm.sum()
        initial=theta[(theta.year==y)&(theta.field==f)&(theta.doy<plant)&(~theta.is_lysimeter)]
        initial_theta=None;initial_doy=None
        # Initialize on planting day from the latest pre-plant profile only.
        # A stale snapshot is not advanced with unobserved fluxes; age is reported.
        if len(initial):
            initial_doy=int(initial.doy.max());prof=initial[initial.doy==initial_doy]
            vals=[]
            for a,b in [(0,30),(30,60),(60,150)]:
                values=prof[prof.depth_cm.between(a,b,inclusive='right')].theta_m3_m3
                vals.append(float(values.mean()) if len(values) else np.nan)
            if np.isfinite(vals).all():initial_theta=[float(np.clip(v,s.residual,s.saturation)) for v,s in zip(vals,soil)]
        days=[]
        for r in met.to_dict('records'):
            d=int(r['doy']);wr=wat.loc[d] if d in wat.index else {}
            rain=wr.get('rain_mm',np.nan);irrig=wr.get('irrigation_mm',np.nan);dew=wr.get('dew_mm',np.nan)
            r['rain_source']='lysimeter';r['irrigation_source']='daily_record';r['dew_source']='daily_record'
            if not np.isfinite(rain):rain=r['rain_gauge_mm'];r['rain_source']='station_gauge'
            if not np.isfinite(irrig):
                irrig=float(eve.get(d,0.));r['irrigation_source']='event_log' if d in eve.index else 'no_event_assumed_zero'
            if not np.isfinite(dew):dew=0.;r['dew_source']='missing_assumed_zero'
            pressure=r['pressure_kpa'] if r['pressure_measured'] else None
            et0=fao56_reference_et(r['tmin_c'],r['tmax_c'],r['tmean_c'],r['rh_mean_pct'],r['wind_m_s'],r['solar_mj_m2'],d,pressure_kpa=pressure)
            r.update(field=f,rain_mm=rain,irrigation_mm=irrig,dew_mm=dew,et0_mm=et0)
            days.append(r);forcing.append(r)
        g=growth[(growth.year==y)&(growth.field==f)].groupby('doy')[['lai_observed','biomass_kg_ha']].mean()
        h=harvest[(harvest.year==y)&(harvest.field==f)]
        if len(h):
            weights=h.harvested_area_m2.to_numpy();weights=np.where(np.isfinite(weights)&(weights>0),weights,1.)
            target=float(np.average(h.dry_grain_kg_ha,weights=weights))
        else:target=np.nan
        season={'year':y,'field':f,'days':days,'plant':plant,'initial':initial_theta,
                'irrigation_layer':1 if y>=2013 and f in ['NE','SE'] else 0,'growth':g,'water':wat,
                'soil_obs':theta[(theta.year==y)&(theta.field==f)&(~theta.is_lysimeter)&theta.depth_cm.between(0,150,inclusive='right')],
                'yield':target}
        seasons.append(season)
        summaries.append({'year':y,'field':f,'split':'calibration' if y in TRAIN else 'evaluation',
                          'planting_doy':plant,'dry_grain_observed':target,'harvest_subsamples':len(h),
                          'initialization':'preplant_profile' if initial_theta else 'field_capacity',
                          'initial_profile_doy':initial_doy,'initial_profile_age_days':plant-initial_doy if initial_doy else None,
                          'rain_mm':sum(d['rain_mm'] for d in days),'irrigation_mm':sum(d['irrigation_mm'] for d in days),
                          'et0_mm':sum(d['et0_mm'] for d in days),'gdd':sum(max(0,min(30,d['tmean_c'])-10) for d in days),
                          'solar_mj_m2':sum(d['solar_mj_m2'] for d in days)})
    pd.DataFrame(forcing).to_csv(DATA/'model_forcing.csv',index=False)
    def simulate(s,p):return simulate_crop(s['days'],soil,p,s['plant'],s['initial'],s['irrigation_layer'])
    def unpack(x):return CropParameters(x[0],x[1],x[1]+x[2],x[3],x[4],x[5])
    # Each target family has equal total weight within a field-season.
    # Scales declared before fitting: LAI 2; biomass 10000 kg/ha;
    # ET 3 mm/day; soil water .05 m3/m3; dry grain 3000 kg/ha.
    def residual(x):
        p=unpack(x);out=[]
        for s in seasons:
            if s['year'] not in TRAIN:continue
            result=simulate(s,p);d=pd.DataFrame(result['daily_records']).set_index('doy');families=[]
            for name,model,scale in [('lai_observed','lai',2.),('biomass_kg_ha','biomass_kg_ha',10000.)]:
                joined=s['growth'][[name]].join(d[[model]],how='inner',lsuffix='_obs').dropna()
                if name==model:obscol=name+'_obs'
                else:obscol=name
                if len(joined):families.append((joined[model]-joined[obscol]).to_numpy()/scale)
            joined=s['water'][['et_mm']].join(d[['et_mm']],how='inner',lsuffix='_obs').dropna()
            if len(joined):families.append((joined.et_mm-joined.et_mm_obs).to_numpy()/3.)
            t=s['soil_obs'].copy();t['layer']=np.select([t.depth_cm<=30,t.depth_cm<=60],[1,2],default=3)
            tj=t.groupby(['doy','layer']).theta_m3_m3.mean().reset_index();tr=[]
            for r in tj.to_dict('records'):
                if r['doy'] in d.index:tr.append((d.loc[r['doy'],f'theta_layer_{int(r["layer"])}']-r['theta_m3_m3'])/.05)
            if tr:families.append(np.asarray(tr))
            if np.isfinite(s['yield']):families.append(np.array([(result['dry_grain_kg_ha']-s['yield'])/3000.]))
            for arr in families:out.extend(arr/np.sqrt(len(arr)))
        return np.asarray(out)
    fit=least_squares(residual,[6,900,1000,1.2,3,.45],bounds=([2,400,300,.6,1,.2],[9,1400,1600,1.6,5,.65]),max_nfev=100,ftol=1e-7,xtol=1e-7,gtol=1e-7)
    params=unpack(fit.x)
    (OUT/'calibration_parameters.json').write_text(json.dumps({'parameters':asdict(params),'calibration_years':TRAIN,
        'evaluation_years':TEST,'success':bool(fit.success),'nfev':fit.nfev,'cost':fit.cost,
        'jacobian_rank':int(np.linalg.matrix_rank(fit.jac)),'active_bounds':fit.active_mask.tolist(),
        'target_scales':{'lai':2,'biomass_kg_ha':10000,'et_mm':3,'theta':.05,'dry_grain_kg_ha':3000},
        'soil_layers':[asdict(s) for s in soil],'protocol_sha256':hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest()},indent=2))
    frame=pd.DataFrame(summaries);train=frame.year.isin(TRAIN)&frame.dry_grain_observed.notna()
    features=['rain_mm','irrigation_mm','et0_mm','gdd','solar_mj_m2','planting_doy']
    ridge=make_pipeline(StandardScaler(),Ridge(alpha=10.))
    ridge.fit(frame.loc[train,features],frame.loc[train,'dry_grain_observed'])
    frame['training_mean_yield']=frame.loc[train,'dry_grain_observed'].mean()
    frame['weather_irrigation_ridge']=ridge.predict(frame[features])
    mass=[];states=[]
    for i,s in enumerate(seasons):
        for model,p in [('uncalibrated_process',CropParameters()),('calibrated_coupled_process',params)]:
            res=simulate(s,p);frame.loc[i,model]=res['dry_grain_kg_ha']
            for r in res['daily_records']:
                mass.append({'year':s['year'],'field':s['field'],'model':model,'doy':r['doy'],'mass_residual_mm':r['mass_residual_mm']})
                if model=='calibrated_coupled_process':states.append({'year':s['year'],'field':s['field'],**r})
    frame.to_csv(OUT/'field_season_predictions.csv',index=False)
    pd.DataFrame(mass).to_csv(OUT/'mass_balance_residuals.csv',index=False)
    states=pd.DataFrame(states);states.to_csv(OUT/'daily_predictions.csv',index=False)
    result={'design':'Retrospective external-source evaluation of separate coupled process extension',
            'calibration_years':TRAIN,'evaluation_years':TEST,'evaluation_field_seasons':8,'independent_evaluation_years':2,
            'models':{},'daily_states':{},'limitations':['One station; fields and spans are not independent regions',
             'Source endpoints were previewed during extraction; no preregistration claim','No evaluation-score-driven model selection',
             'No external evaluation of the archived national neural checkpoint','Irrigation treatment is confounded with field',
             'Stale preplant profiles used as planting-day approximation with age reported; no subsequent assimilation']}
    for model in ['training_mean_yield','weather_irrigation_ridge','uncalibrated_process','calibrated_coupled_process']:
        result['models'][model]={}
        for split,yrs in [('calibration',TRAIN),('evaluation',TEST)]:
            d=frame[frame.year.isin(yrs)&frame.dry_grain_observed.notna()]
            result['models'][model][split]=metrics(d.dry_grain_observed,d[model])
    # State errors use field-day means, never count plant subsamples as seasons.
    g=growth.groupby(['year','field','doy'])[['lai_observed','biomass_kg_ha']].mean().reset_index()
    for label,obs,name in [('LAI',g,'lai_observed'),('biomass_kg_ha',g,'biomass_kg_ha'),('ET_mm',water,'et_mm')]:
        predname={'LAI':'lai','biomass_kg_ha':'biomass_kg_ha','ET_mm':'et_mm'}[label]
        d=obs[['year','field','doy',name]].merge(states[['year','field','doy',predname]],on=['year','field','doy'],suffixes=('_obs','_pred')).dropna()
        oc=name+'_obs' if name==predname else name;pc=predname+'_pred' if name==predname else predname
        result['daily_states'][label]={sp:metrics((sub:=d[d.year.isin(yrs)])[oc],sub[pc]) for sp,yrs in [('calibration',TRAIN),('evaluation',TEST)]}
        d['endpoint']=label;d.rename(columns={oc:'observed',pc:'predicted'},inplace=True);observations.append(d)
    t=theta[(~theta.is_lysimeter)&theta.depth_cm.between(0,150,inclusive='right')].copy()
    t['layer']=np.select([t.depth_cm<=30,t.depth_cm<=60],[1,2],default=3)
    t=t.groupby(['year','field','doy','layer']).theta_m3_m3.mean().reset_index()
    long=states.melt(id_vars=['year','field','doy'],value_vars=['theta_layer_1','theta_layer_2','theta_layer_3'],value_name='predicted')
    long['layer']=long.variable.str[-1].astype(int)
    t=t.merge(long,on=['year','field','doy','layer']).rename(columns={'theta_m3_m3':'observed'})
    result['daily_states']['theta_m3_m3']={sp:metrics((sub:=t[t.year.isin(yrs)]).observed,sub.predicted) for sp,yrs in [('calibration',TRAIN),('evaluation',TEST)]}
    t['endpoint']='theta_m3_m3';observations.append(t)
    pd.concat(observations,ignore_index=True).to_csv(OUT/'state_observation_pairs.csv',index=False)
    result['maximum_absolute_water_residual_mm']=float(pd.DataFrame(mass).mass_residual_mm.abs().max())
    result['forcing_source_counts']={c:pd.DataFrame(forcing)[c].value_counts().to_dict() for c in ['rain_source','irrigation_source','dew_source']}
    (OUT/'external_metrics.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
