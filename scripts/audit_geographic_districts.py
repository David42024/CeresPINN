"""Leave-one-USDA-agricultural-district-out future-year benchmark.

Fixed protocol saved before fitting. Administrative groups are drawn from the
preserved original NASS export, not optimized using yields or model scores.
"""
from pathlib import Path
import hashlib,json,sys
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.verify_reacquired_county import main as verify_sources
from scripts.revision_scientific_audit import metrics,county_interval
OUT=ROOT/'docs/q1_artifacts/reacquired_20261026'
PROTOCOL={'version':1,'design':'leave one official USDA Iowa agricultural statistics district out; train other districts through 2017, evaluate excluded district during 2018-2025',
          'groups':'All nine official agricultural district codes, 10 through 90, as recorded in the original USDA CSV',
          'models':{'trend_only':['year'],'climate_only':['season_temp_mean_c','season_precip_mm'],
                    'trend_and_climate':['year','season_temp_mean_c','season_precip_mm']},
          'ridge_alpha':1.,'scaling':'training rows only; StandardScaler',
          'selection':'No hyperparameter, district, boundary or buffer chosen from evaluation scores',
          'uncertainty':'descriptive complete-year moving-block bootstrap; block length 3, 20000 draws',
          'independence':'Nine spatial groups share eight weather years; districts are not nine independent temporal replicates',
          'limits':'One state; no spatial buffer; retrospective additional audit; original national neural checkpoint not fitted or validated here',
          'official_definition_url':'https://www.nass.usda.gov/Data_and_Statistics/County_Data_Files/Frequently_Asked_Questions/index.php',
          'official_map_url':'https://www.nass.usda.gov/Statistics_by_State/Iowa/Publications/Crop_Report/IA_Ag_Districts_Map.pdf'}


def main():
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'district_protocol.json'
    if path.exists() and json.loads(path.read_text())!=PROTOCOL:raise ValueError('District protocol changed; do not overwrite an evaluated protocol')
    if not path.exists():path.write_text(json.dumps(PROTOCOL,indent=2))
    verify_sources(allow_source_drift=True,verbose=False)
    meta=json.loads((ROOT/'data/reacquired/nass/acquisition_manifest.json').read_text())
    raw=pd.read_csv(ROOT/meta['path'],dtype=str,keep_default_na=False)
    raw=raw[raw['County ANSI'].ne('')].copy();raw['fips']=raw['State ANSI'].str.zfill(2)+raw['County ANSI'].str.zfill(3)
    if raw.groupby('fips')['Ag District Code'].nunique().max()!=1:raise ValueError('District membership changes across source years')
    mapping=raw[['fips','Ag District Code','Ag District']].drop_duplicates().rename(columns={'Ag District Code':'district','Ag District':'district_name'})
    if len(mapping)!=99 or sorted(mapping.district.unique())!=[str(i) for i in range(10,100,10)]:raise ValueError('Invalid district grouping')
    mapping.to_csv(ROOT/'data/reacquired/iowa_county_districts.csv',index=False)
    data=pd.read_csv(ROOT/'data/reacquired/cerespinn_county_rebuilt.csv',dtype={'fips':str}).merge(mapping,on='fips',how='left',validate='many_to_one')
    rows=[];splits=[]
    for district in sorted(mapping.district.unique()):
        train=data[(data.year<=2017)&data.district.ne(district)]
        test=data[(data.year>=2018)&data.district.eq(district)]
        assert set(train.fips).isdisjoint(test.fips) and train.year.max()<test.year.min()
        splits.append({'excluded_district':district,'name':test.district_name.iloc[0],
                       'train_rows':len(train),'test_rows':len(test),'excluded_counties':sorted(test.fips.unique())})
        for model,columns in PROTOCOL['models'].items():
            estimator=make_pipeline(StandardScaler(),Ridge(alpha=1.)).fit(train[columns],train.yield_kg_ha)
            for (_,r),p in zip(test.iterrows(),estimator.predict(test[columns])):
                rows.append({'district':district,'district_name':r.district_name,'model':model,'year':r.year,'fips':r.fips,
                             'observed':r.yield_kg_ha,'predicted':float(p)})
    predictions=pd.DataFrame(rows);predictions.to_csv(OUT/'held_district_future_predictions.csv',index=False)
    scores=[];district_errors=[]
    for model,g in predictions.groupby('model'):
        scores.append({'model':model,**metrics(g.observed,g.predicted),'annual_cluster_bootstrap_ci':county_interval(g)})
        for district,h in g.groupby('district'):district_errors.append({'model':model,'district':district,'rows':len(h),**metrics(h.observed,h.predicted)})
    pd.DataFrame(district_errors).to_csv(OUT/'held_district_errors.csv',index=False)
    result={'protocol':PROTOCOL,'protocol_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'input_rows':len(data),'counties':len(mapping),'districts':9,'distinct_test_years':8,
            'test_county_years':len(predictions[predictions.model=='trend_only']),
            'splits':splits,'scores':scores,'national_neural_checkpoint_unchanged':True}
    (OUT/'district_benchmark.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({'districts':9,'test_county_years':result['test_county_years'],'scores':scores},indent=2))


if __name__=='__main__':main()
