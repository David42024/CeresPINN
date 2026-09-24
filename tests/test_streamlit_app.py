"""Behavioral tests for the public Streamlit client.

The suite runs the real ``streamlit_app.py`` with Streamlit's AppTest harness
and replaces only HTTP transport. This verifies the user-visible behavior and
the exact request sent to FastAPI without requiring a live deployment.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


@dataclass
class FakeResponse:
    payload: Any
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> Any:
        return self.payload


@pytest.fixture(autouse=True)
def clear_streamlit_state() -> None:
    """Prevent cached HTTP results from leaking between AppTest executions."""
    st.cache_data.clear()
    yield
    st.cache_data.clear()


@pytest.fixture
def api_payloads() -> dict[str, Any]:
    return {
        "/api/health/database": {
            "status": "connected",
            "database": "postgresql",
            "postgis": "3.4",
        },
        "/api/model-registry": [
            {
                "version": "v2.5",
                "name": "CeresPINN checkpoint",
                "architecture": "PyTorch MLP + monotonicity",
                "trainedDate": "2026-09-21",
                "epochs": 300,
                "testR2": 0.8225,
                "testRmseKgHa": 717.1,
                "active": True,
                "status": "production",
            }
        ],
        "/api/validation": {
            "hindcast": {
                "metrics": {
                    "rmse_kg_ha": 712.12,
                    "mae_kg_ha": 604.19,
                    "r2": 0.825085,
                },
                "by_year": [
                    {"year": 2023, "observed_kg_ha": 10_000},
                    {"year": 2024, "observed_kg_ha": 12_000},
                ],
            },
            "sobol_sensitivity": {
                "parameters": ["temperature", "precipitation"],
                "first_order": [0.40, 0.30],
                "total": [0.55, 0.42],
            },
        },
        "/api/scenarios": [{"id": "SSP3-7.0", "label": "SSP3-7.0"}],
        "/api/soil-profiles": [{"id": "clay_loam", "label": "Franco Arcilloso"}],
        "/api/fields": [{"id": "field-iowa-01", "name": "Ames Norte"}],
    }


def install_get_mock(monkeypatch: pytest.MonkeyPatch, payloads: dict[str, Any]) -> None:
    def fake_get(url: str, timeout: int) -> FakeResponse:
        del timeout
        for suffix, payload in payloads.items():
            if url.endswith(suffix):
                return FakeResponse(payload)
        raise AssertionError(f"Unexpected GET request: {url}")

    monkeypatch.setattr(requests, "get", fake_get)


def metric_values(app: AppTest) -> dict[str, str]:
    return {metric.label: metric.value for metric in app.metric}


def run_button(app: AppTest):
    return next(button for button in app.button if button.label == "🚀 Ejecutar Simulación")


def test_offline_mode_renders_controls_without_fabricated_results(monkeypatch: pytest.MonkeyPatch) -> None:
    def offline(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise requests.ConnectionError("backend intentionally offline")

    monkeypatch.setattr(requests, "get", offline)
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()

    assert not app.exception
    values = metric_values(app)
    assert values["Checkpoint"] == "No disponible"
    assert values["Rendimiento calculado"] == "—"
    assert values["Biomasa total"] == "—"
    assert values["Estrés hídrico pico"] == "—"
    assert values["Productividad del agua"] == "—"
    assert any("no se muestran métricas sustitutas" in item.value for item in app.warning)
    assert any(box.label == "Campo" for box in app.selectbox)
    assert len(app.button) == 1


def test_online_mode_uses_backend_validation_and_registry(
    monkeypatch: pytest.MonkeyPatch,
    api_payloads: dict[str, Any],
) -> None:
    install_get_mock(monkeypatch, api_payloads)
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()

    assert not app.exception
    values = metric_values(app)
    assert values["Checkpoint"] == "Disponible"
    assert values["RMSE"] == "712.12 kg/ha"
    assert values["MAE"] == "604.19 kg/ha"
    assert values["R² Score"] == "0.825"
    assert values["NRMSE"] == "6.5%"
    assert len(app.dataframe) == 1
    assert len(app.get("plotly_chart")) == 1
    assert not any("métricas sustitutas" in item.value for item in app.warning)


def test_execute_button_posts_full_payload_and_displays_checkpoint_result(
    monkeypatch: pytest.MonkeyPatch,
    api_payloads: dict[str, Any],
) -> None:
    install_get_mock(monkeypatch, api_payloads)
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any], timeout: int) -> FakeResponse:
        captured.update({"url": url, "payload": json, "timeout": timeout})
        return FakeResponse(
            {
                "inference_mode": "pinn",
                "model_uses_real_data": True,
                "scientific_scope": {
                    "use_classification": "exploratory_research_only",
                    "territorial_prioritization_supported": False,
                },
                "projected_yield_kg_ha": 8321,
                "total_biomass_kg_ha": 11150,
                "peak_water_stress_index": 0.42,
                "water_productivity_kg_m3": 1.73,
                "daily_records": [
                    {"dap": 1, "lai": 0.10, "soil_moisture_avg": 0.28},
                    {"dap": 30, "lai": 2.40, "soil_moisture_avg": 0.24},
                ],
            }
        )

    monkeypatch.setattr(requests, "post", fake_post)
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()
    app = run_button(app).click().run()

    assert not app.exception
    assert captured["url"].endswith("/api/simulate")
    assert captured["timeout"] == 30
    assert captured["payload"] == {
        "field_id": "field-iowa-01",
        "scenario": "SSP3-7.0",
        "target_year": 2035,
        "planting_date": "2026-05-01",
        "maize_variety": "short_cycle",
        "irrigation_strategy": "rainfed",
        "soil_moisture_initial_percent": 28.0,
        "nitrogen_application_kg_ha": 180.0,
        "carbon_dioxide_ppm": 540.0,
        "temperature_anomaly_c": 1.8,
        "precipitation_anomaly_percent": -12.0,
    }
    values = metric_values(app)
    assert values["Rendimiento calculado"] == "8,321 kg/ha"
    assert values["Biomasa total"] == "11,150 kg/ha"
    assert values["Estrés hídrico pico"] == "0.42"
    assert values["Productividad del agua"] == "1.73 kg/m³"
    assert len(app.get("plotly_chart")) == 3
    assert any("checkpoint desplegado" in item.value for item in app.success)


def test_decision_scope_notice_is_always_visible(
    monkeypatch: pytest.MonkeyPatch,
    api_payloads: dict[str, Any],
) -> None:
    install_get_mock(monkeypatch, api_payloads)
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()

    assert not app.exception
    assert any(
        "No usar para política pública" in item.value
        and "priorización territorial" in item.value
        for item in app.warning
    )


@pytest.mark.parametrize(
    ("invalid_result", "expected_message"),
    [
        (
            {
                "inference_mode": "pinn-calibrated-surrogate",
                "model_uses_real_data": False,
                "projected_yield_kg_ha": 9000,
            },
            "no confirmó inferencia mediante el checkpoint",
        ),
        (
            {
                "inference_mode": "pinn",
                "model_uses_real_data": False,
                "projected_yield_kg_ha": 9000,
            },
            "no confirmó procedencia de datos reales",
        ),
    ],
)
def test_execute_button_rejects_non_checkpoint_or_non_real_data_results(
    monkeypatch: pytest.MonkeyPatch,
    api_payloads: dict[str, Any],
    invalid_result: dict[str, Any],
    expected_message: str,
) -> None:
    install_get_mock(monkeypatch, api_payloads)
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(invalid_result),
    )

    app = AppTest.from_file(APP_PATH, default_timeout=20).run()
    app = run_button(app).click().run()

    assert not app.exception
    assert any(expected_message in item.value for item in app.error)
    values = metric_values(app)
    assert values["Rendimiento calculado"] == "—"
    assert not app.success
