"""Tests for the statistical validation / uncertainty module (backend.validation).

These exercise the protocol's hypothesis-testing pipeline: hindcast metrics,
KS test, paired t-test, Sobol indices, bootstrap CI and ensemble spread.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from backend import validation as v


# ---------------------------------------------------------------------------
# Deterministic engine
# ---------------------------------------------------------------------------
def test_deterministic_yield_decreases_with_heat():
    cool = v.deterministic_yield(2000, temp_anomaly_c=0.0, precip_anomaly_pct=0.0)
    hot = v.deterministic_yield(2000, temp_anomaly_c=3.0, precip_anomaly_pct=0.0)
    assert hot < cool


def test_deterministic_yield_decreases_with_dryness():
    wet = v.deterministic_yield(2000, temp_anomaly_c=1.0, precip_anomaly_pct=0.0)
    dry = v.deterministic_yield(2000, temp_anomaly_c=1.0, precip_anomaly_pct=-0.25)
    assert dry < wet


def test_deterministic_yield_sane_range():
    y = v.deterministic_yield(2050, temp_anomaly_c=3.5, precip_anomaly_pct=-0.3)
    assert 500 <= y <= 12000


# ---------------------------------------------------------------------------
# Hindcast
# ---------------------------------------------------------------------------
def test_hindcast_structure():
    r = v.hindcast()
    assert r["n_years"] >= 20
    assert set(r["metrics"]) == {"rmse_kg_ha", "mae_kg_ha", "r2"}
    assert len(r["by_year"]) == r["n_years"]
    assert r["reference_source"] in {"usda-nass", "synthetic-reference"}


# ---------------------------------------------------------------------------
# KS test
# ---------------------------------------------------------------------------
def test_ks_test_output_contract():
    r = v.ks_test()
    assert {"statistic", "p_value", "n_simulated", "n_observed"} <= set(r)
    assert 0.0 <= r["statistic"] <= 1.0
    assert 0.0 <= r["p_value"] <= 1.0
    assert isinstance(r["reject_null_at_05"], bool)


# ---------------------------------------------------------------------------
# Paired t-test
# ---------------------------------------------------------------------------
def test_paired_ttest_ssp585_h1_met():
    r = v.paired_t_test_ssp(2050, "SSP5-8.5")
    assert r["mean_projected_kg_ha"] < r["mean_baseline_kg_ha"]
    assert r["mean_loss_pct"] > 0
    assert isinstance(r["meets_h1_min_loss_pct"], bool)
    assert 0.0 <= r["p_value"] <= 1.0


def test_paired_ttest_warmer_scenario_more_loss():
    mild = v.paired_t_test_ssp(2050, "SSP1-2.6")["mean_loss_pct"]
    severe = v.paired_t_test_ssp(2050, "SSP5-8.5")["mean_loss_pct"]
    assert severe > mild


# ---------------------------------------------------------------------------
# Sobol sensitivity
# ---------------------------------------------------------------------------
def test_sobol_indices_in_unit_range():
    r = v.sobol_sensitivity("SSP5-8.5", 2050)
    for val in r["first_order"] + r["total"]:
        assert 0.0 <= val <= 1.0
    assert len(r["first_order"]) == 3 and len(r["total"]) == 3
    assert r["dominant_parameter"] in r["parameters"]


def test_sobol_deterministic_across_calls():
    a = v.sobol_sensitivity("SSP1-2.6", 2030)
    b = v.sobol_sensitivity("SSP1-2.6", 2030)
    assert a["first_order"] == b["first_order"]
    assert a["total"] == b["total"]


# ---------------------------------------------------------------------------
# Bootstrap + ensemble
# ---------------------------------------------------------------------------
def test_bootstrap_ci_contains_mean():
    r = v.bootstrap_ensemble("SSP5-8.5", 2050)
    assert r["ci95_lower_kg_ha"] < r["ensemble_mean_kg_ha"] < r["ci95_upper_kg_ha"]
    assert len(r["ensemble_models"]) == len(v.ENSEMBLE_MODELS)


def test_ensemble_uncertainty_contract():
    r = v.ensemble_uncertainty("SSP5-8.5", 2050)
    assert r["n_members"] > 0
    assert r["iqr"]["q25_kg_ha"] <= r["iqr"]["q75_kg_ha"]
    assert r["ci95_kg_ha"]["lower"] < r["ci95_kg_ha"]["upper"]


# ---------------------------------------------------------------------------
# Full report + API
# ---------------------------------------------------------------------------
def test_full_report_aggregates_all_statistics():
    r = v.full_report()
    for key in [
        "hypothesis_tests",
        "hindcast",
        "ks_test",
        "paired_t_test_ssp585_vs_historical",
        "sobol_sensitivity",
        "bootstrap_ci_ssp585",
        "ensemble_uncertainty_ssp585",
    ]:
        assert key in r


def test_scenarios_supported_includes_four_ssp():
    r = v.full_report()
    assert set(r["scenarios_supported"]) == {"SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"}


def test_validation_endpoint(test_client):
    resp = test_client.get("/api/validation")
    assert resp.status_code == 200
    body = resp.json()
    assert "sobol_sensitivity" in body
    assert "paired_t_test_ssp585_vs_historical" in body
    assert body["ks_test"]["p_value"] >= 0.0
