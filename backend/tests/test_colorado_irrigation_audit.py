import json
import numpy as np
import pandas as pd
import pytest
from scripts.audit_colorado_irrigation import OUT, PROTOCOL, extract, paired_contrast


def test_source_blocks_and_missing_observations_are_not_invented():
    df, _ = extract()
    assert len(df) == 96
    assert set(df.block) == {'1', '2', '3', '4'}
    assert df.loc[df.year == 2013, 'biomass_dry_kg_ha'].isna().sum() == 48
    assert df.yield_15_5pct_kg_ha.isna().sum() == 2
    assert set(df.loc[df.yield_15_5pct_kg_ha.isna(), 'plot']) == {'D31', 'C46'}


def test_missing_control_drops_pair_instead_of_imputation():
    df, _ = extract()
    result = paired_contrast(df, 2013, '100/50')
    assert result['n_blocks'] == 3
    assert result['missing_blocks'] == ['3']
    assert result['difference_kg_ha'] == pytest.approx(np.mean(result['paired_differences_kg_ha']))


def test_saved_conditional_state_results_use_only_held_year_and_observed_lai():
    result = json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    predictions = pd.read_csv(OUT/'conditional_state_predictions.csv')
    assert set(predictions.year) == {2013}
    assert len(predictions) == 46
    assert 'biomass_dry_kg_ha' not in predictions
    assert PROTOCOL['split'] == {'fit_year': 2012, 'evaluation_year': 2013}
    assert not result['process_model_evaluated']
    assert not result['deployed_management_calibrated']
    for model in ('training_mean', 'ridge_lai'):
        rmse = np.sqrt(np.mean((predictions[model] - predictions.yield_dry_kg_ha) ** 2))
        assert rmse == pytest.approx(result['conditional_state_results'][model]['rmse_kg_ha'])
