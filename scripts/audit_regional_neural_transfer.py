"""Retrospective geographic and future-year audit of new regional MLP models.

The original national checkpoint is not evaluated or replaced. Districts,
years, feature sets and hyperparameters are fixed before this experiment.
The previously inspected Iowa outcomes mean this is not a pristine holdout.
"""
from pathlib import Path
import hashlib
import json
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.revision_scientific_audit import county_interval, metrics

OUT = ROOT / 'docs/q1_artifacts/regional_neural_20261026'
CLIMATE = ['season_temp_mean_c', 'season_precip_mm']
FULL = ['year', *CLIMATE]
SEEDS = (0, 1, 42)
PROTOCOL = {
    'version': 1,
    'design': 'nine leave-one-district-out folds; train other districts through 2017; test excluded district 2018-2025',
    'source': 'previously reacquired USDA NASS yields and NOAA Climate at a Glance county seasonal data',
    'models': ['ridge_trend', 'ridge_trend_climate', 'ridge_climate', 'mlp_trend_climate', 'mlp_climate', 'mlp_detrended_climate'],
    'features': {'trend': ['year'], 'climate': CLIMATE, 'trend_climate': FULL},
    'excluded': ['co2_ppm', 'heatwave_risk', 'scenario', 'precip_anomaly_pct', 'seasonal_cdd'],
    'detrending': 'OLS year trend fitted on each fold training rows only; MLP sees only climate and learns training residuals',
    'training': {'hidden_layers': [16, 8], 'activation': 'tanh', 'alpha': 0.0001, 'max_iter': 300, 'seeds': list(SEEDS), 'scaling': 'fit feature and target scalers on training rows only'},
    'uncertainty': 'descriptive 95% moving-block bootstrap of complete test years, block length 3',
    'limitations': 'Iowa only; eight shared weather years; no spatial buffer; retrospective after earlier outcome inspection; regional MLP is distinct from the national checkpoint',
    'model_selection': 'None based on evaluation outcomes; no algorithm or hyperparameter selection',
}


def split_district(data, district):
    train = data[(data.year <= 2017) & (data.district != district)]
    test = data[(data.year.between(2018, 2025)) & (data.district == district)]
    if train.empty or test.empty or not set(train.fips).isdisjoint(test.fips):
        raise ValueError('Invalid geographic or temporal split')
    if train.year.max() >= test.year.min():
        raise ValueError('Future data leakage')
    return train, test


def mlp(seed):
    reg = MLPRegressor(hidden_layer_sizes=(16, 8), activation='tanh', alpha=0.0001,
                       max_iter=300, random_state=seed, early_stopping=False)
    return TransformedTargetRegressor(regressor=make_pipeline(StandardScaler(), reg),
                                      transformer=StandardScaler())


def predict_fold(train, test):
    y = train.yield_kg_ha.to_numpy()
    trend = LinearRegression().fit(train[['year']], y)
    predictions = {}
    for name, cols in [('ridge_trend', ['year']), ('ridge_trend_climate', FULL), ('ridge_climate', CLIMATE)]:
        predictions[name] = make_pipeline(StandardScaler(), Ridge(alpha=1)).fit(train[cols], y).predict(test[cols])
    convergence = {}
    for name, cols, residual in [('mlp_trend_climate', FULL, False), ('mlp_climate', CLIMATE, False),
                                 ('mlp_detrended_climate', CLIMATE, True)]:
        target = y - trend.predict(train[['year']]) if residual else y
        seeds, convergence[name] = [], []
        for seed in SEEDS:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always', ConvergenceWarning)
                estimator = mlp(seed).fit(train[cols], target)
            pred = estimator.predict(test[cols])
            if residual:
                pred += trend.predict(test[['year']])
            seeds.append(pred)
            convergence[name].append({'seed': seed, 'iterations': int(estimator.regressor_.named_steps['mlpregressor'].n_iter_),
                                      'convergence_warning': any(isinstance(w.message, ConvergenceWarning) for w in caught)})
        predictions[name] = np.mean(seeds, axis=0)
    return predictions, convergence


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol_path = OUT / 'protocol.json'
    if protocol_path.exists() and json.loads(protocol_path.read_text(encoding='utf-8')) != PROTOCOL:
        raise ValueError('Existing protocol differs; do not overwrite it')
    if not protocol_path.exists():
        protocol_path.write_text(json.dumps(PROTOCOL, indent=2) + '\n', encoding='utf-8')
    panel_path = ROOT / 'data/reacquired/cerespinn_county_rebuilt.csv'
    map_path = ROOT / 'data/reacquired/iowa_county_districts.csv'
    df = pd.read_csv(panel_path, dtype={'fips': str}).merge(
        pd.read_csv(map_path, dtype={'fips': str, 'district': str}), on='fips', validate='many_to_one')
    if df.duplicated(['year', 'fips']).any() or df[FULL + ['yield_kg_ha', 'district']].isna().any().any():
        raise ValueError('Duplicate county-years or missing data')
    districts = sorted(df.district.unique())
    if districts != [str(i) for i in range(10, 100, 10)]:
        raise ValueError('Unexpected district codes')
    results, folds = [], []
    for district in districts:
        train, test = split_district(df, district)
        preds, convergence = predict_fold(train, test)
        folds.append({'district': district, 'training_rows': len(train), 'test_rows': len(test), 'convergence': convergence})
        for model, values in preds.items():
            frame = test[['year', 'fips', 'district', 'yield_kg_ha']].copy()
            frame = frame.rename(columns={'yield_kg_ha': 'observed'})
            frame['model'], frame['predicted'] = model, values
            results.append(frame)
        print('District', district, 'completed', flush=True)
    predictions = pd.concat(results, ignore_index=True)
    expected = df[df.year.between(2018, 2025)]
    sizes = predictions.groupby('model').size()
    if not sizes.eq(len(expected)).all() or predictions.duplicated(['model', 'year', 'fips']).any():
        raise ValueError('Each available future county-year must occur once per model')
    predictions.to_csv(OUT/'predictions.csv', index=False)
    scores = []
    for name, group in predictions.groupby('model'):
        scores.append({'model': name, **metrics(group.observed, group.predicted),
                       'annual_cluster_bootstrap_ci': county_interval(group)})
    result = {'protocol': PROTOCOL, 'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
              'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [panel_path, map_path]},
              'folds': folds, 'test_county_years_per_model': len(expected), 'distinct_test_years': int(expected.year.nunique()),
              'national_checkpoint_evaluated': False, 'national_checkpoint_replaced': False, 'scores': scores}
    (OUT/'metrics.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(scores, indent=2))


if __name__ == '__main__':
    main()
