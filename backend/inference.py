"""PINN inference service for the CeresPINN FastAPI backend.

Loads the trained CeresPINN weights (`cerespinn_pinn.pt` + `cerespinn_metadata.json`)
and serves real yield predictions for `/api/simulate`.

Fallback contract (rigorous, never silent)
  - If no trained model is present, or torch is unavailable, inference degrades to the
    deterministic mock. The response flags exactly which path was used via
    `"inference_mode": "pinn" | "mock"` so callers can surface it.
  - Loading is lazy and cached; a failed load marks the cache as unavailable so we do
    not retry a broken file on every request.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .training.config import TrainConfig

_MODEL_DIR = Path(__file__).resolve().parent / "models"
_CHECKPOINT = _MODEL_DIR / "cerespinn_pinn.pt"
_METADATA = _MODEL_DIR / "cerespinn_metadata.json"


class PinnInference:
    """Thin wrapper around the trained PINN with graceful degradation."""

    def __init__(self, checkpoint: Path = _CHECKPOINT, metadata: Path = _METADATA) -> None:
        self.checkpoint = checkpoint
        self.metadata_path = metadata
        self._model = None
        self._meta: Optional[Dict[str, Any]] = None
        self._torch = None
        self._cached_error: Optional[str] = None

    # -- Availability --------------------------------------------------------
    @property
    def available(self) -> bool:
        if self._cached_error is not None:
            return False
        return self.checkpoint.exists() and self.metadata_path.exists()

    @property
    def error_message(self) -> Optional[str]:
        return self._cached_error

    def _load_torch(self):
        if self._torch is None:
            try:
                import torch  # type: ignore

                self._torch = torch
            except ImportError as exc:  # pragma: no cover - env dependent
                self._cached_error = f"PyTorch no disponible: {exc}"
                return None
        return self._torch

    # -- Model loading (lazy + cached) ---------------------------------------
    def load_model(self):
        if self._model is not None:
            return self._model
        if not self.available:
            self._cached_error = "Modelo entrenado no encontrado (entrena con backend.training.train)."
            return None

        torch = self._load_torch()
        if torch is None:
            return None

        import json

        try:
            meta = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            from .training.pinn import CeresPINN

            model = CeresPINN(TrainConfig(), input_dim=int(meta["input_dim"]))
            model.load_state_dict(torch.load(self.checkpoint, map_location="cpu", weights_only=True))
            model.eval()
            self._model = model
            self._meta = meta
            return model
        except Exception as exc:  # noqa: BLE001
            self._cached_error = f"Fallo al cargar el PINN: {exc}"
            return None

    # -- Features ------------------------------------------------------------
    @staticmethod
    def build_features(payload: Dict[str, Any], meta: Dict[str, Any]) -> Optional[np.ndarray]:
        """Build the exact feature vector used at training time from a simulation payload."""
        try:
            mean = np.array(meta["normalization"]["mean"], dtype=float)
            std = np.array(meta["normalization"]["std"], dtype=float) + 1e-8
        except (KeyError, TypeError):
            return None

        scenario = str(payload.get("scenario", ""))
        template = _scenario_template(scenario)
        year = int(payload.get("target_year", 2030))
        years_from_base = max(0, year - 2026)

        precip_anomaly_pct = float(payload.get("precipitation_anomaly_percent", template["precip_anomaly_pct"])) / 100.0
        temp_anomaly = float(payload.get("temperature_anomaly_c", template["temp_anomaly_c"]))
        co2 = float(payload.get("carbon_dioxide_ppm", template["co2_ppm"]))

        features = {
            "year": float(year),
            "temp_anomaly_c": temp_anomaly,
            "precip_anomaly_pct": precip_anomaly_pct,
            "co2_ppm": co2,
            "heatwave_risk": float(template["heatwave_risk"]),
            "seasonal_precip_mm": 480.0 + precip_anomaly_pct * 480.0,
            "seasonal_cdd": 20.0 + years_from_base * 0.6,
        }

        feature_names = meta.get("feature_names", TrainConfig().feature_names)
        try:
            x = np.array([features[name] for name in feature_names], dtype=float)
        except KeyError as exc:
            return None  # pragma: no cover
        x_n = (x - mean) / std
        return x_n.reshape(1, -1)

    # -- Predict -------------------------------------------------------------
    def predict_yield_bu_acre(self, payload: Dict[str, Any]) -> Optional[float]:
        model = self.load_model()
        if model is None or self._meta is None:
            return None

        torch = self._torch
        x = self.build_features(payload, self._meta)
        if x is None:
            return None

        with torch.no_grad():
            yield_norm, _ = model(torch.tensor(x, dtype=torch.float32))
        y_min = float(self._meta["normalization"]["y_min"])
        y_max = float(self._meta["normalization"]["y_max"])
        bu = float(yield_norm.cpu().numpy().ravel()[0] * (y_max - y_min) + y_min)
        return bu


def _scenario_template(scenario: str) -> Dict[str, float]:
    return {
        "SSP1-2.6": {"precip_anomaly_pct": -0.02, "temp_anomaly_c": 0.9, "co2_ppm": 445.0, "heatwave_risk": 0.15},
        "SSP3-7.0": {"precip_anomaly_pct": -0.12, "temp_anomaly_c": 1.8, "co2_ppm": 480.0, "heatwave_risk": 0.42},
        "SSP5-8.5": {"precip_anomaly_pct": -0.24, "temp_anomaly_c": 2.7, "co2_ppm": 520.0, "heatwave_risk": 0.78},
    }.get(scenario, {"precip_anomaly_pct": -0.02, "temp_anomaly_c": 0.9, "co2_ppm": 445.0, "heatwave_risk": 0.15})


# Module-level cached inference service.
_inference = PinnInference()


def get_inference() -> PinnInference:
    return _inference
