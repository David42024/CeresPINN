"""End-to-end API tests for the CeresPINN FastAPI backend."""
from __future__ import annotations

import json
from pathlib import Path
import re


MODELS = Path(__file__).resolve().parent.parent / "models"


# ---------------------------------------------------------------------------
# /api/simulate
# ---------------------------------------------------------------------------
def test_simulate_returns_valid_contract(test_client, simulation_payload):
    resp = test_client.post("/api/simulate", json=simulation_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["inference_mode"] in ("pinn", "pinn-calibrated-surrogate")
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


def test_simulate_endpoint_invokes_real_trained_checkpoint(test_client, simulation_payload, monkeypatch):
    """Regression guard for every frontend run button: /api/simulate must execute the checkpoint."""
    import backend.inference as inf_mod

    inv = inf_mod.get_inference()
    assert inv.load_model() is not None
    assert inv.uses_real_data is True
    original_predict = inv.predict_yield_bu_acre
    calls = 0

    def traced_predict(payload):
        nonlocal calls
        calls += 1
        return original_predict(payload)

    monkeypatch.setattr(inv, "predict_yield_bu_acre", traced_predict)
    resp = test_client.post("/api/simulate", json=simulation_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert calls == 1
    assert data["inference_mode"] == "pinn"
    assert data["model_uses_real_data"] is True
    assert data["model_data_source"] == "nass+nex-gddp"


def test_simulate_omits_legacy_equation_metrics(test_client, simulation_payload):
    """The simulation contract must not expose fabricated scientific metrics."""
    response = test_client.post("/api/simulate", json=simulation_payload)
    assert response.status_code == 200
    data = response.json()
    assert "pinn_validation_metrics" not in data
    serialized = response.text.lower()
    for forbidden in (
        "pde_residual_richards_loss",
        "boundary_condition_loss",
        "physics_conservation_error_percent",
    ):
        assert forbidden not in serialized


def test_simulation_declares_exploratory_decision_scope(test_client, simulation_payload):
    response = test_client.post("/api/simulate", json=simulation_payload)
    assert response.status_code == 200
    scope = response.json()["scientific_scope"]
    assert scope["use_classification"] == "exploratory_research_only"
    assert scope["spatial_calibration"] is False
    assert scope["county_level_validation"] is False
    assert scope["soil_affects_yield_network"] is False
    assert scope["territorial_prioritization_supported"] is False
    assert "public_policy" in scope["prohibited_decision_uses"]
    assert "water_allocation" in scope["prohibited_decision_uses"]
    assert "transparent_uncertainty_quantification" in scope["required_before_decision_use"]


def test_model_status_matches_checkpoint_metadata(test_client):
    import backend.inference as inf_mod

    meta = inf_mod.get_inference().metadata
    resp = test_client.get("/api/model/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["real_data"] is True
    assert data["data_source"] == "nass+nex-gddp"
    assert data["r2_score"] == meta["test_metrics"]["r2"]
    assert data["epochs"] == meta["epochs"]


def test_model_registry_contains_only_deployed_checkpoint_metadata(test_client):
    response = test_client.get("/api/model-registry")
    assert response.status_code == 200
    models = response.json()
    assert len(models) == 1
    assert models[0]["active"] is True
    assert models[0]["epochs"] == 300
    assert models[0]["monotonicityWeight"] == 0.5
    assert "richardsWeightLambda" not in models[0]


def test_simulate_fallback_without_model(test_client, simulation_payload, monkeypatch, tmp_path):
    """Simulate absence of a trained model by monkeypatching the loader."""
    import backend.inference as inf_mod

    no_model = inf_mod.PinnInference(
        checkpoint=tmp_path / "missing.pt",
        metadata=tmp_path / "missing.json",
    )
    monkeypatch.setattr(inf_mod, "get_inference", lambda: no_model)
    resp = test_client.post("/api/simulate", json=simulation_payload)
    assert resp.status_code == 200
    assert resp.json()["inference_mode"] == "pinn-calibrated-surrogate"


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
# /api/chatbot
# ---------------------------------------------------------------------------
def test_chatbot_requires_backend_key(test_client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resp = test_client.post("/api/chatbot", json={"message": "Hola"})
    assert resp.status_code == 503
    assert "configurado" in resp.json()["detail"]


def test_chatbot_calls_openai_with_compact_context(test_client, monkeypatch):
    import backend.app as app_mod

    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Respuesta de prueba"

    monkeypatch.setenv("OPENAI_API_KEY", "test-only-secret")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-nano")
    monkeypatch.setattr(app_mod, "_generate_llm_reply", fake_generate)
    resp = test_client.post(
        "/api/chatbot",
        json={"message": "¿Cuál es el rendimiento?", "context": {"projectedYieldKgHa": 8778}},
    )
    assert resp.status_code == 200
    assert resp.json()["reply"] == "Respuesta de prueba"
    assert captured["api_key"] == "test-only-secret"
    assert captured["model"] == "gpt-5-nano"
    assert '"projectedYieldKgHa": 8778' in captured["contents"]


def test_chatbot_provider_failure_is_sanitized(test_client, monkeypatch):
    import backend.app as app_mod

    def fail_generate(**_kwargs):
        raise RuntimeError("provider failed with do-not-leak-this")

    monkeypatch.setenv("OPENAI_API_KEY", "do-not-leak-this")
    monkeypatch.setattr(app_mod, "_generate_llm_reply", fail_generate)
    resp = test_client.post("/api/chatbot", json={"message": "Hola"})
    assert resp.status_code == 502
    assert "do-not-leak-this" not in resp.text


def test_chatbot_status_never_exposes_key(test_client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "top-secret")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-nano")
    resp = test_client.get("/api/chatbot/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
    assert resp.json()["model"] == "gpt-5-nano"
    assert "top-secret" not in resp.text


def test_render_vercel_origin_regex_is_project_scoped():
    import backend.app as app_mod

    render_config = (Path(__file__).resolve().parents[2] / "render.yaml").read_text(encoding="utf-8")
    match = re.search(r"FRONTEND_ORIGIN_REGEX[\s\S]*?value: '([^']+)'", render_config)
    assert match is not None
    pattern = match.group(1).replace("\\\\", "\\")
    assert re.fullmatch(pattern, "https://ceres-pinn.vercel.app")
    assert re.fullmatch(
        pattern,
        "https://ceres-pinn-qsuo9pjvz-daln486279513-gmailcoms-projects.vercel.app",
    )
    assert not re.fullmatch(pattern, "https://unrelated-project.vercel.app")
    assert re.fullmatch(app_mod._frontend_origin_regex, "https://ceres-pinn.vercel.app")
    assert not re.fullmatch(app_mod._frontend_origin_regex, "https://unrelated-project.vercel.app")


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
