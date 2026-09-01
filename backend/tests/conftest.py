"""Shared fixtures and path configuration for the CeresPINN test-suite.

Ensures `backend` is importable as a package and that tests run in a deterministic,
isolated mode (dry-run data extraction, no external network).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the project root importable (backend/... is a package).
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch):
    """Pin every toggle so tests are offline and reproducible."""
    monkeypatch.setenv("CERESPINN_DRY_RUN", "1")


@pytest.fixture
def test_client():
    """FastAPI TestClient (requires httpx)."""
    from fastapi.testclient import TestClient
    from backend.app import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def simulation_payload() -> dict:
    return {
        "field_id": "field-bajio-02",
        "scenario": "SSP5-8.5",
        "target_year": 2040,
        "planting_date": "2026-05-01",
        "maize_variety": "medium_cycle",
        "irrigation_strategy": "deficit_50",
        "soil_moisture_initial_percent": 75.0,
        "nitrogen_application_kg_ha": 180.0,
        "carbon_dioxide_ppm": 520.0,
        "temperature_anomaly_c": 2.7,
        "precipitation_anomaly_percent": -24.0,
    }
