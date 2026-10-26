"""Regression checks for scientific data meaning and audit fallback rejection."""
import pandas as pd
import pytest

from backend.data.noaa_cag import normalize_seasonal_climate


def test_noaa_degree_days_never_become_drought_days_or_daily_observations():
    source = pd.DataFrame([{'year': 2020, 'fips': '19169',
        'season_temp_mean_f': 68., 'season_tmax_mean_f': 86.,
        'season_precip_in': 10., 'cdd_f': 900.}])
    converted = normalize_seasonal_climate(source)
    assert converted.iloc[0].cooling_degree_days_c == pytest.approx(500.)
    assert converted.iloc[0].season_precip_mm == pytest.approx(254.)
    assert converted.iloc[0].season_start_month == 4
    assert converted.iloc[0].season_end_month == 9
    assert not {'cdd','gdd','heat_days_30c','heat_days_35c','vpd_mean_kpa'} & set(converted.columns)


def test_scientific_management_audit_rejects_surrogate(monkeypatch):
    from scripts import generate_q1_extended_audit as audit
    class MissingAdapter:
        def predict_yield_bu_acre(self, payload):
            return None
    class MissingInference:
        adapter = MissingAdapter()
        def run_full_simulation(self, payload):
            pytest.fail('Surrogate results must never enter scientific audit artifacts')
    monkeypatch.setattr(audit, 'get_inference', lambda: MissingInference())
    with pytest.raises(RuntimeError, match='fallback is not evidence'):
        audit.management_artifacts()
