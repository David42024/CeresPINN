import pandas as pd
import pytest
import json
import numpy as np
from scripts.audit_regional_neural_transfer import CLIMATE, FULL, OUT, PROTOCOL, split_district


def test_district_and_future_years_are_both_excluded_from_training():
    panel = pd.DataFrame([
        {'year': 2017, 'fips': '19001', 'district': '10'},
        {'year': 2018, 'fips': '19001', 'district': '10'},
        {'year': 2017, 'fips': '19003', 'district': '20'},
        {'year': 2018, 'fips': '19003', 'district': '20'},
        {'year': 2026, 'fips': '19001', 'district': '10'},
    ])
    train, test = split_district(panel, '10')
    assert train[['year', 'fips']].to_records(index=False).tolist() == [(2017, '19003')]
    assert test[['year', 'fips']].to_records(index=False).tolist() == [(2018, '19001')]
    assert set(train.fips).isdisjoint(test.fips)


def test_reduced_neural_inputs_remove_confounded_scenario_proxies():
    assert CLIMATE == ['season_temp_mean_c', 'season_precip_mm']
    assert set(PROTOCOL['excluded']).isdisjoint(FULL)
    assert 'year' not in CLIMATE


def test_split_rejects_missing_held_out_district():
    panel = pd.DataFrame([{'year': 2017, 'fips': '19003', 'district': '20'}])
    with pytest.raises(ValueError):
        split_district(panel, '10')


def test_saved_results_match_each_prediction_and_future_year_coverage():
    metrics = json.loads((OUT / 'metrics.json').read_text(encoding='utf-8'))
    predictions = pd.read_csv(OUT / 'predictions.csv', dtype={'fips': str, 'district': str})
    assert not metrics['national_checkpoint_evaluated']
    assert not predictions.duplicated(['model', 'year', 'fips']).any()
    assert set(predictions.year) == set(range(2018, 2026))
    assert set(predictions.district) == {str(i) for i in range(10, 100, 10)}
    for entry in metrics['scores']:
        rows = predictions[predictions.model == entry['model']]
        assert len(rows) == metrics['test_county_years_per_model'] == 696
        rmse = float(np.sqrt(np.mean((rows.predicted - rows.observed) ** 2)))
        assert rmse == pytest.approx(entry['rmse_kg_ha'], abs=1e-9)
