"""End-to-end API tests for the CeresPINN FastAPI backend."""
from __future__ import annotations

import json
from pathlib import Path


MODELS = Path(__file__).resolve().parent.parent / "models"


# ---------------------------------------------------------------------------
# /api/simulate
# ---------------------------------------------------------------------------
def test_simulate_returns_valid_contract(test_client, simulation_payload):
    resp = test_client.post("/api/simulate", json=simulation_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["inference_mode"] in ("pinn", "mock", "mock-unavailable")
    assert isinstance(data["projected_yield_kg_ha"], (int, float))
    assert data["projected_yield_kg_ha"] > 0
    assert isinstance(data["daily_records"], list)
    assert len(data["daily_records"]) > 0
    # Required KPIs consumed by the frontend.
    for key in (
        "potential_yield_kg_ha",
        "yield_loss_due_to_drought_percent",
        "total_biomass_kg_ha",
        "drought_resilience_score",
        "economic_return_usd_ha",
    ):
        assert key in data, f"missing KPI {key}"


def test_simulate_uses_pinn_when_model_present(test_client, simulation_payload):
    if not (MODELS / "cerespinn_pinn.pt").exists():
        import pytest

        pytest.skip("No trained model; PINN path not exercised.")
    resp = test_client.post("/api/simulate", json=simulation_payload)
    assert resp.status_code == 200
    assert resp.json()["inference_mode"] == "pinn"


def test_simulate_fallback_without_model(test_client, simulation_payload, monkeypatch):
    """Simulate absence of a trained model by monkeypatching the loader."""
    import backend.inference as inf_mod

    class _NoModel:
        available = False
        error_message = "no model"

        def predict_yield_bu_acre(self, payload):
            return None

    monkeypatch.setattr(inf_mod, "get_inference", lambda: _NoModel())
    resp = test_client.post("/api/simulate", json=simulation_payload)
    assert resp.status_code == 200
    assert resp.json()["inference_mode"] == "mock"


def test_simulate_rejects_bad_payload(test_client):
    resp = test_client.post("/api/simulate", json={"field_id": "x"})
    assert resp.status_code == 422  # pydantic validation


def test_more_extreme_scenario_yields_less_or_equal_mock(test_client):
    """Mock fallback must be monotone: more severe SSP never strictly increases yield."""
    base = {
        "field_id": "f",
        "target_year": 2040,
        "planting_date": "2026-05-01",
        "maize_variety": "medium_cycle",
        "irrigation_strategy": "full",
        "soil_moisture_initial_percent": 75.0,
        "nitrogen_application_kg_ha": 180.0,
        "carbon_dioxide_ppm": 520.0,
        "temperature_anomaly_c": 2.7,
        "precipitation_anomaly_percent": -24.0,
    }
    mild = {**base, "scenario": "SSP1-2.6"}
    severe = {**base, "scenario": "SSP5-8.5"}
    y_mild = test_client.post("/api/simulate", json=mild).json()["projected_yield_kg_ha"]
    y_severe = test_client.post("/api/simulate", json=severe).json()["projected_yield_kg_ha"]
    if not (MODELS / "cerespinn_pinn.pt").exists():
        assert y_severe <= y_mild


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------
def test_health(test_client):
    resp = test_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /api/pipelines
# ---------------------------------------------------------------------------
def test_list_pipelines(test_client):
    resp = test_client.get("/api/pipelines")
    assert resp.status_code == 200
    pipes = resp.json()["pipelines"]
    ids = {p["id"] for p in pipes}
    assert ids == {"pipe-chirps", "pipe-nasa-nex", "pipe-usda-nass"}
    for p in pipes:
        assert p["status"] in ("healthy", "empty", "error", "never")


def test_sync_pipeline_and_poll_job(test_client):
    resp = test_client.post("/api/pipelines/pipe-chirps/sync")
    assert resp.status_code in (200, 202)
    job_id = resp.json()["job_id"]

    # Poll until the background job settles (dry-run is fast).
    status = None
    for _ in range(50):
        poll = test_client.get(f"/api/pipelines/jobs/{job_id}")
        assert poll.status_code == 200
        status = poll.json()
        if status["status"] in ("done", "error"):
            break
        import time

        time.sleep(0.1)
    assert status["status"] in ("done", "error")
    assert "percent" in status


def test_sync_unknown_pipeline_404(test_client):
    resp = test_client.post("/api/pipelines/nonexistent/sync")
    assert resp.status_code == 404


def test_job_unknown_404(test_client):
    resp = test_client.get("/api/pipelines/jobs/does-not-exist")
    assert resp.status_code == 404


def test_pipelines_sync_all(test_client):
    resp = test_client.post("/api/pipelines/sync-all")
    assert resp.status_code in (200, 202)
    assert resp.json()["pipeline_id"] == "*"
    assert resp.json()["job_id"]
