"""Future evaluation targets must not influence selection or exported fits."""
import json
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge


def test_changing_future_targets_cannot_change_selected_exported_model(tmp_path, monkeypatch):
    from backend.training import train_v4_spatial as training
    processed = tmp_path / 'processed'
    processed.mkdir()
    (processed / 'canonical_panel.parquet').touch()
    frame = pd.DataFrame([
        {'year': year, 'fips': county, 'yield_kg_ha': 7000 + 100*(year-1990) + 20*county,
         'season_temp_mean_c': 18 + (year % 3), 'season_precip_mm': 400 + 2*(year % 7),
         'is_outlier': False}
        for year in range(1990, 2026) for county in [19001, 19003]
    ])
    monkeypatch.setattr(training, 'Settings', lambda: SimpleNamespace(paths=SimpleNamespace(processed=processed)))
    monkeypatch.setattr(training.pd, 'read_parquet', lambda _: frame.copy())
    # Keep the regression fast while exercising selection and export end-to-end.
    for constructor in ['RandomForestRegressor', 'HistGradientBoostingRegressor', 'MLPRegressor']:
        monkeypatch.setattr(training, constructor, lambda **_: Ridge(alpha=2.))
    monkeypatch.setattr(training, '__file__', str(tmp_path / 'backend/training/train_v4_spatial.py'))
    monkeypatch.setattr(training, 'get_git_commit', lambda: 'test-base')
    training.main()
    directory = tmp_path / 'backend/models'
    first = joblib.load(directory / 'cerespinn_spatial_v4.joblib')
    first_meta = json.loads((directory / 'cerespinn_spatial_v4_metadata.json').read_text())
    query = np.array([[2010., 19., 450.]])
    prediction = first.predict(query)
    frame.loc[frame.year >= 2018, 'yield_kg_ha'] *= 100
    training.main()
    second = joblib.load(directory / 'cerespinn_spatial_v4.joblib')
    second_meta = json.loads((directory / 'cerespinn_spatial_v4_metadata.json').read_text())
    assert first_meta['algorithm'] == second_meta['algorithm']
    assert second_meta['algorithm_selection']['uses_final_test_for_selection'] is False
    assert second_meta['artifact_fit_period'] == '1990-2017'
    assert second_meta['model_verified'] is False
    np.testing.assert_allclose(prediction, second.predict(query), rtol=0, atol=0)
