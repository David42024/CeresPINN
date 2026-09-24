"""Generate auditable statistics and tables for the CeresPINN Q1 revision.

The script intentionally uses the exact grouped-year split stored alongside the
production checkpoint.  It compares the checkpoint with conventional baselines
on the same independent test years, computes inferential statistics at annual
resolution, and probes checkpoint robustness under input noise and single-feature
missingness.  No network access is required.
"""
from __future__ import annotations

import csv
import json
import math
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy import stats
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
METADATA = ROOT / "backend" / "models" / "cerespinn_metadata.json"
CHECKPOINT = ROOT / "backend" / "models" / "cerespinn_pinn.pt"
OUTPUT = ROOT / "docs" / "q1_artifacts"

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


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "rmse_bu_acre": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "mae_bu_acre": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "rmse_kg_ha": float(mean_squared_error(y_true, y_pred) ** 0.5 * BU_ACRE_TO_KG_HA),
        "mae_kg_ha": float(mean_absolute_error(y_true, y_pred) * BU_ACRE_TO_KG_HA),
    }


def annualize(years: np.ndarray, observed: np.ndarray, predicted: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame({"year": years.astype(int), "observed": observed, "predicted": predicted})
    return frame.groupby("year", as_index=False).mean(numeric_only=True).sort_values("year")


def bootstrap_metrics(y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 20_000) -> dict[str, list[float]]:
    rng = np.random.default_rng(42)
    n = len(y_true)
    draws: dict[str, list[float]] = {"rmse_kg_ha": [], "mae_kg_ha": [], "r2": []}
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt, yp = y_true[idx], y_pred[idx]
        draws["rmse_kg_ha"].append(float(mean_squared_error(yt, yp) ** 0.5 * BU_ACRE_TO_KG_HA))
        draws["mae_kg_ha"].append(float(mean_absolute_error(yt, yp) * BU_ACRE_TO_KG_HA))
        # R2 is undefined for a resample containing a single unique target.
        if np.unique(yt).size > 1:
            draws["r2"].append(float(r2_score(yt, yp)))
    return {
        name: [
            float(np.percentile(values, 2.5)),
            float(np.percentile(values, 97.5)),
        ]
        for name, values in draws.items()
    }


def load_checkpoint(metadata: dict) -> CeresPINN:
    cfg = TrainConfig(
        hidden_layers=4,
        hidden_units=128,
        activation="tanh",
        dropout=0.05,
        learning_rate=float(metadata["training_config"]["learning_rate"]),
        epochs=int(metadata["epochs"]),
        batch_size=int(metadata["training_config"]["batch_size"]),
        loss_physics_weight=float(metadata["training_config"]["loss_physics_weight"]),
        seed=int(metadata["training_config"]["seed"]),
    )
    model = CeresPINN(cfg, input_dim=len(FEATURES))
    state = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model


def checkpoint_predict(model: CeresPINN, x: np.ndarray, metadata: dict) -> np.ndarray:
    norm = metadata["normalization"]
    mean = np.asarray(norm["mean"], dtype=float)
    std = np.asarray(norm["std"], dtype=float)
    xn = (x - mean) / std
    with torch.no_grad():
        pred, _ = model(torch.tensor(xn, dtype=torch.float32))
    return pred.numpy() * (float(norm["y_max"]) - float(norm["y_min"])) + float(norm["y_min"])


def benchmark_latency(model: CeresPINN, x: np.ndarray, metadata: dict) -> dict[str, float]:
    # Warm-up prevents import/dispatch overhead from contaminating the result.
    for _ in range(100):
        checkpoint_predict(model, x[:1], metadata)
    timings = []
    for _ in range(2_000):
        start = time.perf_counter_ns()
        checkpoint_predict(model, x[:1], metadata)
        timings.append((time.perf_counter_ns() - start) / 1_000_000)
    return {
        "n_repetitions": len(timings),
        "batch_size": 1,
        "median_ms": float(np.median(timings)),
        "p95_ms": float(np.percentile(timings, 95)),
        "mean_ms": float(np.mean(timings)),
        "device": "CPU",
    }


def benchmark_training(x_train: np.ndarray, y_train: np.ndarray, metadata: dict) -> dict[str, float | int | str]:
    """Time one exact 300-epoch CPU fit without overwriting the checkpoint."""
    cfg = TrainConfig(
        hidden_layers=4,
        hidden_units=128,
        activation="tanh",
        dropout=0.05,
        learning_rate=float(metadata["training_config"]["learning_rate"]),
        epochs=int(metadata["epochs"]),
        batch_size=int(metadata["training_config"]["batch_size"]),
        loss_physics_weight=float(metadata["training_config"]["loss_physics_weight"]),
        seed=int(metadata["training_config"]["seed"]),
        device="cpu",
    )
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-8
    xn = (x_train - mean) / std
    ymin, ymax = float(y_train.min()), float(y_train.max()) + 1e-8
    yn = (y_train - ymin) / (ymax - ymin)
    network = CeresPINN(cfg, input_dim=xn.shape[1])
    optimizer = torch.optim.Adam(network.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    criterion = nn.MSELoss()
    loader = DataLoader(
        TensorDataset(torch.tensor(xn, dtype=torch.float32), torch.tensor(yn, dtype=torch.float32)),
        batch_size=cfg.batch_size,
        shuffle=True,
    )
    start = time.perf_counter()
    for _ in range(cfg.epochs):
        network.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            prediction, _ = network(xb)
            data_loss = criterion(prediction, yb)
            physical = physics_loss(network, xb, cfg)
            regularization = sum(parameter.pow(2).sum() for parameter in network.parameters())
            loss = cfg.loss_data_weight * data_loss + physical + cfg.loss_reg_weight * regularization
            loss.backward()
            optimizer.step()
    elapsed = time.perf_counter() - start
    return {
        "elapsed_seconds": float(elapsed),
        "epochs": cfg.epochs,
        "train_rows": int(len(x_train)),
        "batch_size": cfg.batch_size,
        "device": "CPU",
        "torch_threads": int(torch.get_num_threads()),
        "platform": platform.platform(),
    }


def fit_unconstrained_mlp(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    metadata: dict,
) -> tuple[np.ndarray, float]:
    """Fit the checkpoint architecture without the monotonicity loss."""
    cfg = TrainConfig(
        hidden_layers=4,
        hidden_units=128,
        activation="tanh",
        dropout=0.05,
        learning_rate=float(metadata["training_config"]["learning_rate"]),
        epochs=int(metadata["epochs"]),
        batch_size=int(metadata["training_config"]["batch_size"]),
        loss_physics_weight=0.0,
        seed=int(metadata["training_config"]["seed"]),
        device="cpu",
    )
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-8
    x_train_n = (x_train - mean) / std
    x_test_n = (x_test - mean) / std
    ymin, ymax = float(y_train.min()), float(y_train.max()) + 1e-8
    y_train_n = (y_train - ymin) / (ymax - ymin)
    network = CeresPINN(cfg, input_dim=x_train_n.shape[1])
    optimizer = torch.optim.Adam(network.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    criterion = nn.MSELoss()
    loader = DataLoader(
        TensorDataset(
            torch.tensor(x_train_n, dtype=torch.float32),
            torch.tensor(y_train_n, dtype=torch.float32),
        ),
        batch_size=cfg.batch_size,
        shuffle=True,
    )
    start = time.perf_counter()
    for _ in range(cfg.epochs):
        network.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            prediction, _ = network(xb)
            # Keep the exact same forward-call schedule as CeresPINN.  With
            # lambda=0 this contributes no gradient, but still consumes the
            # same dropout RNG calls, making the ablation differ only in the
            # monotonicity weight.
            physical = physics_loss(network, xb, cfg)
            regularization = sum(parameter.pow(2).sum() for parameter in network.parameters())
            loss = cfg.loss_data_weight * criterion(prediction, yb) + physical + cfg.loss_reg_weight * regularization
            loss.backward()
            optimizer.step()
    elapsed = time.perf_counter() - start
    network.eval()
    with torch.no_grad():
        prediction, _ = network(torch.tensor(x_test_n, dtype=torch.float32))
    return prediction.numpy() * (ymax - ymin) + ymin, elapsed


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    raw = pd.read_csv(DATASET)

    # Reconstruct the exact 108-row annual-scenario matrix consumed by train.py.
    annual = (
        raw.groupby(["scenario", "year"], as_index=False)
        .agg({**{feature: "median" for feature in FEATURES}, "yield_bu_acre": "median"})
        .sort_values(["scenario", "year"])
        .reset_index(drop=True)
    )
    train_years = set(metadata["evaluation"]["split"]["train_years"])
    test_years = set(metadata["evaluation"]["split"]["test_years"])
    train = annual[annual["year"].isin(train_years)].copy()
    test = annual[annual["year"].isin(test_years)].copy()
    x_train, y_train = train[FEATURES].to_numpy(float), train["yield_bu_acre"].to_numpy(float)
    x_test, y_test = test[FEATURES].to_numpy(float), test["yield_bu_acre"].to_numpy(float)

    expected_mean = np.asarray(metadata["normalization"]["mean"], dtype=float)
    expected_std = np.asarray(metadata["normalization"]["std"], dtype=float)
    if not np.allclose(x_train.mean(axis=0), expected_mean, atol=1e-6):
        raise RuntimeError("Dataset does not reproduce checkpoint training means")
    if not np.allclose(x_train.std(axis=0) + 1e-8, expected_std, atol=1e-6):
        raise RuntimeError("Dataset does not reproduce checkpoint training standard deviations")

    model = load_checkpoint(metadata)
    pinn_pred = checkpoint_predict(model, x_test, metadata)
    saved_pred = np.asarray([row["predicted_bu_acre"] for row in metadata["evaluation"]["samples"]])
    if not np.allclose(pinn_pred, saved_pred, atol=2e-3):
        raise RuntimeError("Live checkpoint predictions differ from persisted evaluation samples")

    estimators = {
        "CeresPINN": None,
        "Linear regression": make_pipeline(StandardScaler(), LinearRegression()),
        "Ridge (alpha=1)": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "Random Forest": RandomForestRegressor(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
    }
    predictions: dict[str, np.ndarray] = {"CeresPINN": pinn_pred}
    for name, estimator in estimators.items():
        if estimator is None:
            continue
        estimator.fit(x_train, y_train)
        predictions[name] = estimator.predict(x_test)
    mlp_pred, mlp_train_seconds = fit_unconstrained_mlp(x_train, y_train, x_test, metadata)
    predictions["MLP (same architecture, no monotonicity regularization)"] = mlp_pred

    comparison_rows = []
    annual_predictions: dict[str, pd.DataFrame] = {}
    for name, pred in predictions.items():
        annual_pred = annualize(test["year"].to_numpy(), y_test, pred)
        annual_predictions[name] = annual_pred
        score = metrics(annual_pred["observed"].to_numpy(), annual_pred["predicted"].to_numpy())
        comparison_rows.append({"model": name, "n_independent_years": len(annual_pred), **score})
    pd.DataFrame(comparison_rows).to_csv(OUTPUT / "same_split_baseline_comparison.csv", index=False)

    hindcast = annual_predictions["CeresPINN"].rename(
        columns={"observed": "observed_bu_acre", "predicted": "predicted_bu_acre"}
    )
    hindcast["observed_kg_ha"] = hindcast["observed_bu_acre"] * BU_ACRE_TO_KG_HA
    hindcast["predicted_kg_ha"] = hindcast["predicted_bu_acre"] * BU_ACRE_TO_KG_HA
    hindcast.to_csv(OUTPUT / "hindcast_independent_years.csv", index=False)

    y_obs = hindcast["observed_bu_acre"].to_numpy()
    y_hat = hindcast["predicted_bu_acre"].to_numpy()
    differences = y_hat - y_obs
    paired_t = stats.ttest_rel(y_hat, y_obs)
    ks = stats.ks_2samp(y_hat, y_obs, alternative="two-sided", method="auto")
    inferential = {
        "n_independent_years": int(len(y_obs)),
        "mean_bias_bu_acre": float(differences.mean()),
        "mean_bias_kg_ha": float(differences.mean() * BU_ACRE_TO_KG_HA),
        "paired_t_statistic": float(paired_t.statistic),
        "paired_t_p_value_two_sided": float(paired_t.pvalue),
        "cohen_dz": float(differences.mean() / differences.std(ddof=1)),
        "ks_d": float(ks.statistic),
        "ks_p_value": float(ks.pvalue),
        "bootstrap_95_ci": bootstrap_metrics(y_obs, y_hat),
    }

    # Robustness: 5% Gaussian noise relative to each training feature SD.
    rng = np.random.default_rng(42)
    base = metrics(y_test, pinn_pred)
    noise_rmse = []
    prediction_mad = []
    feature_scale = x_train.std(axis=0)
    feature_scale[feature_scale < 1e-12] = 0.0
    for _ in range(1_000):
        perturbed = x_test + rng.normal(0.0, 0.05, size=x_test.shape) * feature_scale
        pred = checkpoint_predict(model, perturbed, metadata)
        noise_rmse.append(mean_squared_error(y_test, pred) ** 0.5)
        prediction_mad.append(np.mean(np.abs(pred - pinn_pred)))

    robustness_rows = [
        {
            "condition": "Gaussian noise (sigma=5% train SD)",
            "feature": "all non-constant features",
            "rmse_bu_acre": float(np.mean(noise_rmse)),
            "rmse_change_pct": float((np.mean(noise_rmse) / base["rmse_bu_acre"] - 1.0) * 100.0),
            "mean_abs_prediction_change_bu_acre": float(np.mean(prediction_mad)),
            "repetitions": 1_000,
        }
    ]
    # Missingness: replace one feature at a time by its training mean.
    for idx, feature in enumerate(FEATURES):
        missing = x_test.copy()
        missing[:, idx] = x_train[:, idx].mean()
        pred = checkpoint_predict(model, missing, metadata)
        rmse = mean_squared_error(y_test, pred) ** 0.5
        robustness_rows.append(
            {
                "condition": "single-feature mean imputation",
                "feature": feature,
                "rmse_bu_acre": float(rmse),
                "rmse_change_pct": float((rmse / base["rmse_bu_acre"] - 1.0) * 100.0),
                "mean_abs_prediction_change_bu_acre": float(np.mean(np.abs(pred - pinn_pred))),
                "repetitions": 1,
            }
        )
    pd.DataFrame(robustness_rows).to_csv(OUTPUT / "robustness_results.csv", index=False)

    latency = benchmark_latency(model, x_test, metadata)
    training_benchmark = benchmark_training(x_train, y_train, metadata)
    result = {
        "provenance": {
            "dataset": str(DATASET.relative_to(ROOT)).replace("\\", "/"),
            "checkpoint": str(CHECKPOINT.relative_to(ROOT)).replace("\\", "/"),
            "metadata": str(METADATA.relative_to(ROOT)).replace("\\", "/"),
            "split": metadata["evaluation"]["split"],
            "seed": 42,
            "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        },
        "checkpoint_annual_metrics": metrics(y_obs, y_hat),
        "inferential_statistics": inferential,
        "latency": latency,
        "training_benchmark": training_benchmark,
        "unconstrained_mlp_train_seconds": mlp_train_seconds,
        "baseline_comparison": comparison_rows,
        "robustness": robustness_rows,
    }
    (OUTPUT / "q1_statistics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
