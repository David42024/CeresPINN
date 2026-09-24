"""Run a leakage-safe prospective temporal validation for CeresPINN.

Protocol
--------
* Training years: 1990-2017 (inclusive).
* Test years: 2018-2025 (inclusive).
* Every scenario copy of a year remains in the same partition.
* Normalization and target scaling are fitted on the training period only.
* Headline metrics are calculated over eight independent annual observations,
  after averaging the three scenario-conditioned predictions for each year.
* Ten deterministic neural seeds are reported individually and as an ensemble.

This experiment evaluates temporal extrapolation. It does not constitute an
external spatial or field validation.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.training.config import TrainConfig
from backend.training.pinn import CeresPINN, physics_loss


DATASET = ROOT / "data" / "cerespinn_training_iowa.csv"
OUTPUT = ROOT / "docs" / "q1_artifacts" / "temporal"
TRAIN_END = 2017
TEST_START = 2018
TEST_END = 2025
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 42]
BU_ACRE_TO_KG_HA = 62.77
FEATURES = [
    "year",
    "temp_anomaly_c",
    "precip_anomaly_pct",
    "co2_ppm",
    "heatwave_risk",
    "seasonal_precip_mm",
    "seasonal_cdd",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    # Canonicalize line endings so the provenance digest is identical on
    # Windows (CRLF checkout) and Linux CI (LF checkout).
    digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def score(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    rmse = float(mean_squared_error(observed, predicted) ** 0.5)
    mae = float(mean_absolute_error(observed, predicted))
    return {
        "rmse_bu_acre": rmse,
        "mae_bu_acre": mae,
        "r2": float(r2_score(observed, predicted)),
        "rmse_kg_ha": rmse * BU_ACRE_TO_KG_HA,
        "mae_kg_ha": mae * BU_ACRE_TO_KG_HA,
    }


def annualize(
    years: np.ndarray,
    observed: np.ndarray,
    **predictions: np.ndarray,
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {"year": years.astype(int), "observed_bu_acre": observed, **predictions}
    )
    return (
        frame.groupby("year", as_index=False)
        .mean(numeric_only=True)
        .sort_values("year")
        .reset_index(drop=True)
    )


def load_temporal_split() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not DATASET.exists():
        raise FileNotFoundError(
            f"Missing tracked processed dataset: {DATASET.relative_to(ROOT)}"
        )
    raw = pd.read_csv(DATASET)
    required = {"scenario", "yield_bu_acre", *FEATURES}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {sorted(missing)}")

    # The stored file retains county-level duplicates. The production training
    # matrix uses one median row per scenario and year, so the same deterministic
    # aggregation is applied here before splitting by time.
    annual = (
        raw.groupby(["scenario", "year"], as_index=False)
        .agg({**{feature: "median" for feature in FEATURES}, "yield_bu_acre": "median"})
        .sort_values(["scenario", "year"])
        .reset_index(drop=True)
    )
    train = annual[annual["year"] <= TRAIN_END].copy()
    test = annual[
        (annual["year"] >= TEST_START) & (annual["year"] <= TEST_END)
    ].copy()

    expected_train_years = list(range(1990, TRAIN_END + 1))
    expected_test_years = list(range(TEST_START, TEST_END + 1))
    if sorted(train["year"].unique().tolist()) != expected_train_years:
        raise RuntimeError("Training period is incomplete")
    if sorted(test["year"].unique().tolist()) != expected_test_years:
        raise RuntimeError("Test period is incomplete")
    if set(train["year"]).intersection(set(test["year"])):
        raise RuntimeError("Temporal leakage detected: a year occurs in both partitions")
    return train, test


def fit_seed(
    train: pd.DataFrame,
    test: pd.DataFrame,
    seed: int,
) -> np.ndarray:
    cfg = TrainConfig(
        hidden_layers=4,
        hidden_units=128,
        activation="tanh",
        dropout=0.05,
        learning_rate=1e-3,
        epochs=300,
        batch_size=64,
        weight_decay=1e-5,
        loss_data_weight=1.0,
        loss_physics_weight=0.5,
        loss_reg_weight=1e-4,
        seed=seed,
        device="cpu",
        feature_names=FEATURES,
    )
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.use_deterministic_algorithms(True)

    x_train = train[FEATURES].to_numpy(float)
    x_test = test[FEATURES].to_numpy(float)
    y_train = train["yield_bu_acre"].to_numpy(float)
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-8
    x_train_n = (x_train - mean) / std
    x_test_n = (x_test - mean) / std
    y_min = float(y_train.min())
    y_max = float(y_train.max()) + 1e-8
    y_train_n = (y_train - y_min) / (y_max - y_min)

    model = CeresPINN(cfg, input_dim=len(FEATURES))
    optimizer = torch.optim.Adam(
        model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay
    )
    criterion = nn.MSELoss()
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        TensorDataset(
            torch.tensor(x_train_n, dtype=torch.float32),
            torch.tensor(y_train_n, dtype=torch.float32),
        ),
        batch_size=cfg.batch_size,
        shuffle=True,
        generator=generator,
    )

    for _ in range(cfg.epochs):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            prediction, _ = model(xb)
            monotonicity_penalty = physics_loss(model, xb, cfg)
            weight_penalty = sum(parameter.pow(2).sum() for parameter in model.parameters())
            loss = (
                criterion(prediction, yb)
                + monotonicity_penalty
                + cfg.loss_reg_weight * weight_penalty
            )
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        prediction, _ = model(torch.tensor(x_test_n, dtype=torch.float32))
    return prediction.numpy() * (y_max - y_min) + y_min


def bootstrap_intervals(
    observed: np.ndarray,
    predicted: np.ndarray,
    draws: int = 20_000,
) -> dict[str, list[float]]:
    rng = np.random.default_rng(42)
    values: dict[str, list[float]] = {
        "rmse_kg_ha": [],
        "mae_kg_ha": [],
        "r2": [],
    }
    for _ in range(draws):
        index = rng.integers(0, len(observed), len(observed))
        sampled_observed = observed[index]
        sampled_predicted = predicted[index]
        sampled = score(sampled_observed, sampled_predicted)
        values["rmse_kg_ha"].append(sampled["rmse_kg_ha"])
        values["mae_kg_ha"].append(sampled["mae_kg_ha"])
        if np.unique(sampled_observed).size > 1:
            values["r2"].append(sampled["r2"])
    return {
        metric: [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]
        for metric, samples in values.items()
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, test = load_temporal_split()
    x_train = train[FEATURES].to_numpy(float)
    x_test = test[FEATURES].to_numpy(float)
    y_train = train["yield_bu_acre"].to_numpy(float)
    y_test = test["yield_bu_acre"].to_numpy(float)

    seed_predictions: dict[int, np.ndarray] = {}
    seed_rows: list[dict[str, float | int]] = []
    for seed in SEEDS:
        prediction = fit_seed(train, test, seed)
        seed_predictions[seed] = prediction
        annual = annualize(test["year"].to_numpy(), y_test, predicted=prediction)
        seed_rows.append(
            {
                "seed": seed,
                "n_independent_test_years": len(annual),
                **score(
                    annual["observed_bu_acre"].to_numpy(),
                    annual["predicted"].to_numpy(),
                ),
            }
        )

    ensemble_prediction = np.mean(list(seed_predictions.values()), axis=0)
    baselines = {
        "linear_regression": make_pipeline(StandardScaler(), LinearRegression()),
        "ridge_alpha_1": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": RandomForestRegressor(
            n_estimators=500,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=1,
        ),
    }
    baseline_predictions: dict[str, np.ndarray] = {}
    for name, estimator in baselines.items():
        estimator.fit(x_train, y_train)
        baseline_predictions[name] = estimator.predict(x_test)

    annual = annualize(
        test["year"].to_numpy(),
        y_test,
        cerespinn_ensemble_bu_acre=ensemble_prediction,
        **{f"{name}_bu_acre": pred for name, pred in baseline_predictions.items()},
    )
    annual["observed_kg_ha"] = annual["observed_bu_acre"] * BU_ACRE_TO_KG_HA
    annual["cerespinn_ensemble_kg_ha"] = (
        annual["cerespinn_ensemble_bu_acre"] * BU_ACRE_TO_KG_HA
    )
    annual.to_csv(OUTPUT / "temporal_predictions_2018_2025.csv", index=False)
    pd.DataFrame(seed_rows).to_csv(OUTPUT / "temporal_seed_metrics.csv", index=False)

    observed = annual["observed_bu_acre"].to_numpy()
    ensemble = annual["cerespinn_ensemble_bu_acre"].to_numpy()
    baseline_metrics = {
        name: score(observed, annual[f"{name}_bu_acre"].to_numpy())
        for name in baselines
    }
    result = {
        "protocol": {
            "design": "prospective temporal holdout",
            "aggregation": "median by scenario-year before split; metrics averaged to independent years",
            "train_years": list(range(1990, TRAIN_END + 1)),
            "test_years": list(range(TEST_START, TEST_END + 1)),
            "train_rows_after_aggregation": int(len(train)),
            "test_rows_after_aggregation": int(len(test)),
            "independent_train_years": int(train["year"].nunique()),
            "independent_test_years": int(test["year"].nunique()),
            "normalization": "fit on 1990-2017 only",
            "seeds": SEEDS,
            "epochs_per_seed": 300,
            "leakage_check": "passed",
            "scope": "internal temporal validation; not external spatial/field validation",
        },
        "data": {
            "path": str(DATASET.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(DATASET),
        },
        "cerespinn_ensemble_metrics": score(observed, ensemble),
        "cerespinn_ensemble_bootstrap_95_ci": bootstrap_intervals(observed, ensemble),
        "cerespinn_seed_summary": {
            metric: {
                "mean": float(pd.DataFrame(seed_rows)[metric].mean()),
                "std": float(pd.DataFrame(seed_rows)[metric].std(ddof=1)),
            }
            for metric in ["rmse_kg_ha", "mae_kg_ha", "r2"]
        },
        "baseline_metrics": baseline_metrics,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "torch": torch.__version__,
            "device": "cpu",
        },
    }
    output_json = OUTPUT / "temporal_validation_1990_2017_to_2018_2025.json"
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
