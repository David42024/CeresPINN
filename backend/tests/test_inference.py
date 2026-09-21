"""Tests for the PINN inference service (backend.inference)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.inference import PinnInference
from backend.training.config import TrainConfig


MODELS = Path(__file__).resolve().parent.parent / "models"


@pytest.fixture
def trained_model_present():
    """Skip test unless a trained checkpoint + metadata exist."""
    if not (MODELS / "cerespinn_pinn.pt").exists() or not (MODELS / "cerespinn_metadata.json").exists():
        pytest.skip("Entrena primero con `python -m backend.training.train`.")
    return True


def test_inference_available_when_model_exists(trained_model_present):
    inv = PinnInference(
        checkpoint=MODELS / "cerespinn_pinn.pt",
        metadata=MODELS / "cerespinn_metadata.json",
    )
    assert inv.available is True
    # load_model must succeed and cache the model.
    assert inv.load_model() is not None
    assert inv.load_model() is inv._model


def test_inference_unavailable_without_model(tmp_path):
    inv = PinnInference(
        checkpoint=tmp_path / "missing.pt",
        metadata=tmp_path / "missing.json",
    )
    assert inv.available is False
    assert inv.load_model() is None
    assert inv.error_message is not None


def test_build_features_shape_and_normalization():
    meta = {
        "feature_names": TrainConfig().feature_names,
        "normalization": {
            "mean": [0.0] * 7,
            "std": [1.0] * 7,
        },
    }
    payload = {
        "scenario": "SSP1-2.6",
        "target_year": 2030,
        "precipitation_anomaly_percent": -2.0,
        "temperature_anomaly_c": 0.9,
        "carbon_dioxide_ppm": 445.0,
    }
    x = PinnInference.build_features(payload, meta)
    assert x is not None
    assert x.shape == (1, 7)
    # precip_anomaly_pct must be a fraction (percentage / 100).
    assert abs(float(x[0, 2]) - (-0.02)) < 1e-6


def test_build_features_keeps_constant_training_features_at_zero():
    meta = {
        "feature_names": TrainConfig().feature_names,
        "normalization": {
            "mean": [2020.0, 1.0, 0.0, 420.0, 0.2, 480.0, 20.0],
            "std": [10.0, 1.0, 1.0, 20.0, 0.1, 1e-8, 1e-8],
        },
    }
    x = PinnInference.build_features(
        {
            "scenario": "SSP5-8.5",
            "target_year": 2070,
            "precipitation_anomaly_percent": -30.0,
        },
        meta,
    )
    assert x is not None
    assert float(x[0, 5]) == 0.0
    assert float(x[0, 6]) == 0.0


def test_predict_yield_returns_plausible_bu(trained_model_present):
    inv = PinnInference(
        checkpoint=MODELS / "cerespinn_pinn.pt",
        metadata=MODELS / "cerespinn_metadata.json",
    )
    payload = {
        "scenario": "SSP3-7.0",
        "target_year": 2040,
        "precipitation_anomaly_percent": -12.0,
        "temperature_anomaly_c": 1.8,
        "carbon_dioxide_ppm": 480.0,
    }
    bu = inv.predict_yield_bu_acre(payload)
    assert bu is not None
    # Realistic maize yield bounds (bu/acre).
    assert 0 < bu < 400


def test_missing_model_predict_is_none(tmp_path):
    inv = PinnInference(checkpoint=tmp_path / "x.pt", metadata=tmp_path / "y.json")
    assert inv.predict_yield_bu_acre({"scenario": "SSP1-2.6"}) is None
