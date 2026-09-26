"""Tests for the PINN inference service (backend.inference)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.inference import PinnAdapter, get_inference
from backend.training.config import TrainConfig

MODELS = Path(__file__).resolve().parent.parent / "models"


@pytest.fixture
def trained_model_present():
    """Skip test unless a trained checkpoint + metadata exist."""
    if not (MODELS / "cerespinn_pinn.pt").exists() or not (MODELS / "cerespinn_metadata.json").exists():
        pytest.skip("Entrena primero con `python -m backend.training.train`.")
    return True


def test_inference_available_when_model_exists(trained_model_present):
    inv = PinnAdapter(
        checkpoint=MODELS / "cerespinn_pinn.pt",
        metadata=MODELS / "cerespinn_metadata.json",
    )
    assert inv.available is True
    # load must succeed.
    assert inv.load() is True
    assert inv.metadata["data_source"] == "nass+nex-gddp"


def test_inference_unavailable_without_model(tmp_path):
    inv = PinnAdapter(
        checkpoint=tmp_path / "missing.pt",
        metadata=tmp_path / "missing.json",
    )
    assert inv.available is False
    assert inv.load() is False


def test_predict_yield_returns_plausible_bu(trained_model_present):
    inv = PinnAdapter(
        checkpoint=MODELS / "cerespinn_pinn.pt",
        metadata=MODELS / "cerespinn_metadata.json",
    )
    assert inv.load() is True

    payload = {
        "scenario": "SSP3-7.0",
        "target_year": 2040,
        "precipitation_anomaly_percent": -5.0,
        "temperature_anomaly_c": 1.5,
        "carbon_dioxide_ppm": 480.0,
    }

    bu = inv.predict_yield_bu_acre(payload)
    # Average US corn yield is 150-180 bu/acre, model should be in ballpark.
    assert 10.0 < bu < 350.0


def test_missing_model_predict_is_none(tmp_path):
    inv = PinnAdapter(
        checkpoint=tmp_path / "missing.pt",
        metadata=tmp_path / "missing.json",
    )
    assert inv.predict_yield_bu_acre({"scenario": "SSP3"}) is None
