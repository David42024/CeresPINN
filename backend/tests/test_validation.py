"""Tests for the statistical validation / uncertainty module (backend.validation)."""
from __future__ import annotations

import pytest
from backend import validation as v

def test_full_report_aggregates_all_statistics():
    r = v.full_report()
    for key in [
        "hindcast_metrics",
        "spatial_metrics",
        "t_test_results",
        "sobol_indices",
        "ensemble_uncertainty"
    ]:
        assert key in r

def test_validation_endpoint(test_client):
    resp = test_client.get("/api/validation")
    assert resp.status_code == 200
    body = resp.json()
    assert "sobol_indices" in body
    assert body["sobol_indices"]["status"] == "not_computed"
    assert body["t_test_results"]["status"] == "not_computed"
