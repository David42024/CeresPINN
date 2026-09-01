"""Hyperparameters and dataset configuration for CeresPINN training.

All knobs are dataclass-backed and overridable via environment variables so run
scripts stay reproducible without editing code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class DataConfig:
    """Paths to the artifacts produced by backend.data extractors."""

    base_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("CERESPINN_DATA_DIR", Path(__file__).resolve().parent.parent / "data")
        )
    )
    nass_csv: str = "raw/nass/maize_county_yield_usda.csv"
    chirps_dir: str = "raw/chirps"
    nex_dir: str = "raw/nex-gddp"

    @property
    def nass_path(self) -> Path:
        return self.base_dir / self.nass_csv

    @property
    def chirps_path(self) -> Path:
        return self.base_dir / self.chirps_dir

    @property
    def nex_path(self) -> Path:
        return self.base_dir / self.nex_dir


@dataclass
class TrainConfig:
    """Model architecture and training loop settings."""

    # Architecture
    hidden_layers: int = int(os.getenv("CERESPINN_HIDDEN_LAYERS", "4"))
    hidden_units: int = int(os.getenv("CERESPINN_HIDDEN_UNITS", "128"))
    activation: str = os.getenv("CERESPINN_ACTIVATION", "tanh")  # tanh | gelu | relu
    dropout: float = float(os.getenv("CERESPINN_DROPOUT", "0.05"))

    # Optimization
    learning_rate: float = float(os.getenv("CERESPINN_LR", "1e-3"))
    epochs: int = int(os.getenv("CERESPINN_EPOCHS", "300"))
    batch_size: int = int(os.getenv("CERESPINN_BATCH_SIZE", "64"))
    weight_decay: float = float(os.getenv("CERESPINN_WEIGHT_DECAY", "1e-5"))

    # Physics-informed loss weights
    loss_data_weight: float = float(os.getenv("CERESPINN_LOSS_DATA", "1.0"))
    loss_physics_weight: float = float(os.getenv("CERESPINN_LOSS_PHYSICS", "0.5"))
    loss_reg_weight: float = float(os.getenv("CERESPINN_LOSS_REG", "1e-4"))

    # Data
    train_frac: float = float(os.getenv("CERESPINN_TRAIN_FRAC", "0.8"))
    seed: int = int(os.getenv("CERESPINN_SEED", "42"))

    # Outputs
    output_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("CERESPINN_MODEL_DIR", Path(__file__).resolve().parent.parent / "models")
        )
    )
    device: str = field(default_factory=lambda: os.getenv("CERESPINN_DEVICE", "auto"))

    # Features used by the model, matching the data contract (see dataset.py)
    feature_names: List[str] = field(
        default_factory=lambda: [
            "year",
            "temp_anomaly_c",
            "precip_anomaly_pct",
            "co2_ppm",
            "heatwave_risk",
            "seasonal_precip_mm",
            "seasonal_cdd",  # consecutive dry days proxy
        ]
    )
    target_name: str = "yield_bu_acre"
