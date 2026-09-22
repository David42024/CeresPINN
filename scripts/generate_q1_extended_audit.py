"""Extended, checkpoint-grounded audit artifacts for the CeresPINN manuscript.

This is intentionally separate from the product validation endpoint because
backend/validation.py contains a deterministic demonstration surrogate.  Every
model result here is computed from the tracked checkpoint or from a retraining
run over the exact 84/24 grouped-year matrix reconstructed from the local
processed dataset.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy.stats import qmc
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.inference import get_inference
from backend.training.config import TrainConfig
from backend.training.pinn import CeresPINN, physics_loss


DATASET = ROOT / "data" / "cerespinn_training_iowa.csv"
METADATA = ROOT / "backend" / "models" / "cerespinn_metadata.json"
CHECKPOINT = ROOT / "backend" / "models" / "cerespinn_pinn.pt"
OUTPUT = ROOT / "docs" / "q1_artifacts" / "extended"
BU_TO_KG = 62.77
FEATURES = [
    "year",
    "temp_anomaly_c",
    "precip_anomaly_pct",
    "co2_ppm",
    "heatwave_risk",
    "seasonal_precip_mm",
    "seasonal_cdd",
]
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 42]


def score(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {
        "rmse_bu_acre": float(mean_squared_error(y, pred) ** 0.5),
        "mae_bu_acre": float(mean_absolute_error(y, pred)),
        "r2": float(r2_score(y, pred)),
        "rmse_kg_ha": float(mean_squared_error(y, pred) ** 0.5 * BU_TO_KG),
        "mae_kg_ha": float(mean_absolute_error(y, pred) * BU_TO_KG),
    }


def annualize(years: np.ndarray, observed: np.ndarray, **predictions: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame({"year": years.astype(int), "observed_bu_acre": observed, **predictions})
    return frame.groupby("year", as_index=False).mean(numeric_only=True).sort_values("year")


def load_matrix() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    meta = json.loads(METADATA.read_text(encoding="utf-8"))
    raw = pd.read_csv(DATASET)
    annual = (
        raw.groupby(["scenario", "year"], as_index=False)
        .agg({**{feature: "median" for feature in FEATURES}, "yield_bu_acre": "median"})
        .sort_values(["scenario", "year"])
        .reset_index(drop=True)
    )
    train = annual[annual.year.isin(meta["evaluation"]["split"]["train_years"])].copy()
    test = annual[annual.year.isin(meta["evaluation"]["split"]["test_years"])].copy()
    assert len(train) == 84 and len(test) == 24
    assert np.allclose(train[FEATURES].to_numpy().mean(axis=0), meta["normalization"]["mean"], atol=1e-6)
    return train, test, meta


def fit_neural(
    train: pd.DataFrame,
    test: pd.DataFrame,
    seed: int,
    physics_weight: float,
    features: list[str] = FEATURES,
) -> tuple[np.ndarray, float]:
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
        loss_physics_weight=physics_weight,
        loss_reg_weight=1e-4,
        seed=seed,
        device="cpu",
        feature_names=features,
    )
    torch.manual_seed(seed)
    np.random.seed(seed)
    x_train = train[features].to_numpy(float)
    x_test = test[features].to_numpy(float)
    y_train = train.yield_bu_acre.to_numpy(float)
    mean, std = x_train.mean(axis=0), x_train.std(axis=0) + 1e-8
    x_train_n, x_test_n = (x_train - mean) / std, (x_test - mean) / std
    ymin, ymax = float(y_train.min()), float(y_train.max()) + 1e-8
    y_train_n = (y_train - ymin) / (ymax - ymin)

    model = CeresPINN(cfg, input_dim=len(features))
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    mse = nn.MSELoss()
    loader = DataLoader(
        TensorDataset(torch.tensor(x_train_n, dtype=torch.float32), torch.tensor(y_train_n, dtype=torch.float32)),
        batch_size=cfg.batch_size,
        shuffle=True,
    )
    started = time.perf_counter()
    for _ in range(cfg.epochs):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            pred, _ = model(xb)
            data_loss = mse(pred, yb)
            physical = physics_loss(model, xb, cfg)
            l2_manual = sum(parameter.pow(2).sum() for parameter in model.parameters())
            loss = data_loss + physical + cfg.loss_reg_weight * l2_manual
            loss.backward()
            optimizer.step()
    elapsed = time.perf_counter() - started
    model.eval()
    with torch.no_grad():
        pred, _ = model(torch.tensor(x_test_n, dtype=torch.float32))
    return pred.numpy() * (ymax - ymin) + ymin, elapsed


def load_tracked_model(meta: dict) -> CeresPINN:
    cfg = TrainConfig()
    model = CeresPINN(cfg, input_dim=7)
    model.load_state_dict(torch.load(CHECKPOINT, map_location="cpu", weights_only=True))
    model.eval()
    return model


def checkpoint_predict_matrix(model: CeresPINN, x: np.ndarray, meta: dict) -> np.ndarray:
    mean = np.asarray(meta["normalization"]["mean"], dtype=float)
    std = np.asarray(meta["normalization"]["std"], dtype=float)
    xn = (x - mean) / std
    with torch.no_grad():
        pred, _ = model(torch.tensor(xn, dtype=torch.float32))
    return pred.numpy() * (meta["normalization"]["y_max"] - meta["normalization"]["y_min"]) + meta["normalization"]["y_min"]


def bootstrap_model_differences(annual: pd.DataFrame, n_boot: int = 20_000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    y = annual.observed_bu_acre.to_numpy()
    base = annual.CeresPINN.to_numpy()
    competitors = [column for column in annual.columns if column not in {"year", "observed_bu_acre", "CeresPINN"}]
    rows = []
    for competitor in competitors:
        other = annual[competitor].to_numpy()
        rmse_delta, mae_delta = [], []
        for _ in range(n_boot):
            idx = rng.integers(0, len(y), len(y))
            rmse_delta.append((mean_squared_error(y[idx], base[idx]) ** 0.5 - mean_squared_error(y[idx], other[idx]) ** 0.5) * BU_TO_KG)
            mae_delta.append((mean_absolute_error(y[idx], base[idx]) - mean_absolute_error(y[idx], other[idx])) * BU_TO_KG)
        rows.append(
            {
                "comparison": f"CeresPINN - {competitor}",
                "delta_rmse_kg_ha": float(np.mean(rmse_delta)),
                "delta_rmse_ci95_low": float(np.percentile(rmse_delta, 2.5)),
                "delta_rmse_ci95_high": float(np.percentile(rmse_delta, 97.5)),
                "delta_mae_kg_ha": float(np.mean(mae_delta)),
                "delta_mae_ci95_low": float(np.percentile(mae_delta, 2.5)),
                "delta_mae_ci95_high": float(np.percentile(mae_delta, 97.5)),
                "n_independent_years": len(y),
                "n_bootstrap": n_boot,
                "seed": 42,
            }
        )
    return pd.DataFrame(rows)


def checkpoint_sobol(model: CeresPINN, meta: dict, n: int = 32_768, n_boot: int = 500) -> pd.DataFrame:
    """Saltelli/Jansen estimates over three checkpoint inputs at 2050."""
    sampler = qmc.Sobol(d=6, scramble=True, seed=42)
    sample = sampler.random_base2(m=int(math.log2(n)))
    a, b = sample[:, :3], sample[:, 3:]
    bounds = np.asarray([[2.2, 3.4], [-0.28, -0.15], [500.0, 600.0]], dtype=float)
    a = qmc.scale(a, bounds[:, 0], bounds[:, 1])
    b = qmc.scale(b, bounds[:, 0], bounds[:, 1])

    def evaluate(values: np.ndarray) -> np.ndarray:
        temp, precip, co2 = values[:, 0], values[:, 1], values[:, 2]
        x = np.column_stack(
            [
                np.full(len(values), 2050.0),
                temp,
                precip,
                co2,
                np.full(len(values), 0.78),
                480.0 + precip * 480.0,
                np.full(len(values), 20.0),
            ]
        )
        return checkpoint_predict_matrix(model, x, meta)

    ya, yb = evaluate(a), evaluate(b)
    y_ab = []
    for idx in range(3):
        ab = a.copy()
        ab[:, idx] = b[:, idx]
        y_ab.append(evaluate(ab))
    variance = float(np.var(np.concatenate([ya, yb]), ddof=1))

    def estimate(indexes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        aa, bb = ya[indexes], yb[indexes]
        var = float(np.var(np.concatenate([aa, bb]), ddof=1))
        s1, st = [], []
        for values in y_ab:
            cc = values[indexes]
            # Jansen first-order estimator. AB_i contains B_i and A_-i, so
            # (B - AB_i) removes X_i and estimates the complementary variance.
            s1.append(float(1.0 - np.mean((bb - cc) ** 2) / (2.0 * var)))
            st.append(float(np.mean((aa - cc) ** 2) / (2.0 * var)))
        return np.asarray(s1), np.asarray(st)

    indexes = np.arange(n)
    s1, st = estimate(indexes)
    rng = np.random.default_rng(42)
    s1_boot, st_boot = [], []
    for _ in range(n_boot):
        draw = rng.integers(0, n, n)
        first, total = estimate(draw)
        s1_boot.append(first)
        st_boot.append(total)
    s1_boot, st_boot = np.asarray(s1_boot), np.asarray(st_boot)
    rows = []
    for idx, variable in enumerate(["temp_anomaly_c", "precip_anomaly_pct", "co2_ppm"]):
        rows.append(
            {
                "variable": variable,
                "S1": float(s1[idx]),
                "S1_ci95_low": float(np.percentile(s1_boot[:, idx], 2.5)),
                "S1_ci95_high": float(np.percentile(s1_boot[:, idx], 97.5)),
                "S1_conf_half_width": float((np.percentile(s1_boot[:, idx], 97.5) - np.percentile(s1_boot[:, idx], 2.5)) / 2),
                "ST": float(st[idx]),
                "ST_ci95_low": float(np.percentile(st_boot[:, idx], 2.5)),
                "ST_ci95_high": float(np.percentile(st_boot[:, idx], 97.5)),
                "ST_conf_half_width": float((np.percentile(st_boot[:, idx], 97.5) - np.percentile(st_boot[:, idx], 2.5)) / 2),
                "base_N": n,
                "total_model_evaluations": int(n * 5),
                "bootstrap_repetitions": n_boot,
                "seed": 42,
            }
        )
    return pd.DataFrame(rows)


def management_artifacts() -> tuple[pd.DataFrame, dict]:
    inference = get_inference()
    common = {
        "field_id": "field-iowa-01",
        "scenario": "SSP5-8.5",
        "target_year": 2050,
        "planting_date": "2026-05-15",
        "maize_variety": "medium_cycle",
        "irrigation_strategy": "deficit_50",
        "soil_moisture_initial_percent": 60.0,
        "nitrogen_application_kg_ha": 180.0,
        "carbon_dioxide_ppm": 520.0,
        "temperature_anomaly_c": 2.7,
        "precipitation_anomaly_percent": -24.0,
    }
    configs = {
        "baseline": {},
        "early_planting_minus_14d": {"planting_date": "2026-05-01"},
        "short_cycle": {"maize_variety": "short_cycle"},
        "irrigation_75": {"irrigation_strategy": "deficit_75"},
        "combined": {
            "planting_date": "2026-05-01",
            "maize_variety": "short_cycle",
            "irrigation_strategy": "deficit_75",
        },
    }
    raw_bu = inference.predict_yield_bu_acre(common)
    results = {}
    rows = []
    baseline_yield = None
    for name, override in configs.items():
        payload = {**common, **override}
        result = inference.run_full_simulation(payload)
        results[name] = result
        if baseline_yield is None:
            baseline_yield = result["projected_yield_kg_ha"]
        rows.append(
            {
                "scenario": name,
                "yield_kg_ha": result["projected_yield_kg_ha"],
                "delta_pct": (result["projected_yield_kg_ha"] / baseline_yield - 1.0) * 100.0,
                "water_use_mm": result["total_water_consumed_mm"],
                "irrigation_mm": result["total_irrigation_applied_mm"],
                "CWSI_max": result["peak_water_stress_index"],
                "critical_days": result["critical_drought_days_count"],
                "days_to_maturity": result["days_to_maturity"],
                "economic_return_usd_ha": result["economic_return_usd_ha"],
                "raw_checkpoint_bu_acre": raw_bu,
            }
        )

    # Approximate whole-profile water accounting from rounded exported records.
    baseline = results["baseline"]
    fc, wp = 0.32, 0.16
    initial = wp + (fc - wp) * 0.60
    storage_previous = initial * 300.0 + initial * 1.04 * 300.0 + initial * 1.08 * 400.0
    residuals = []
    for record in baseline["daily_records"]:
        storage = (
            record["soil_moisture_top"] * 300.0
            + record["soil_moisture_mid"] * 300.0
            + record["soil_moisture_deep"] * 400.0
        )
        inflow = record["precipitation_mm"] + record["irrigation_mm"]
        outflow = record["transpiration_mm"] + record["evaporation_mm"] + record["deep_drainage_mm"]
        residuals.append(inflow - outflow - (storage - storage_previous))
        storage_previous = storage
    water_audit = {
        "basis": "rounded API daily_records; not internal full-precision states",
        "sum_residual_mm": float(np.sum(residuals)),
        "mean_abs_daily_residual_mm": float(np.mean(np.abs(residuals))),
        "max_abs_daily_residual_mm": float(np.max(np.abs(residuals))),
        "n_days": len(residuals),
    }
    return pd.DataFrame(rows), water_audit


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, test, meta = load_matrix()
    x_train, x_test = train[FEATURES].to_numpy(float), test[FEATURES].to_numpy(float)
    y_train, y_test = train.yield_bu_acre.to_numpy(float), test.yield_bu_acre.to_numpy(float)
    years_test = test.year.to_numpy()
    tracked = load_tracked_model(meta)
    checkpoint_pred = checkpoint_predict_matrix(tracked, x_test, meta)

    # Conventional baselines.
    predictions: dict[str, np.ndarray] = {"CeresPINN": checkpoint_pred}
    baseline_models = {
        "LinearRegression": make_pipeline(StandardScaler(), LinearRegression()),
        "Ridge_alpha1": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "RandomForest": RandomForestRegressor(n_estimators=500, min_samples_leaf=2, random_state=42, n_jobs=-1),
    }
    for name, estimator in baseline_models.items():
        estimator.fit(x_train, y_train)
        predictions[name] = estimator.predict(x_test)

    # Ten paired neural seeds plus one repeated seed-42 fit for determinism.
    multiseed_rows = []
    seed42_predictions: dict[str, np.ndarray] = {}
    for seed in SEEDS:
        for label, weight in [("CeresPINN_retrained", 0.5), ("MLP_no_monotonicity", 0.0)]:
            pred, elapsed = fit_neural(train, test, seed=seed, physics_weight=weight)
            annual = annualize(years_test, y_test, prediction=pred)
            values = score(annual.observed_bu_acre.to_numpy(), annual.prediction.to_numpy())
            multiseed_rows.append({"model": label, "seed": seed, "train_seconds": elapsed, **values})
            if seed == 42:
                seed42_predictions[label] = pred
                if label == "MLP_no_monotonicity":
                    predictions["MLP_no_monotonicity"] = pred
    repeated, repeat_seconds = fit_neural(train, test, seed=42, physics_weight=0.5)
    determinism = {
        "seed": 42,
        "max_abs_prediction_difference_bu_acre": float(np.max(np.abs(repeated - seed42_predictions["CeresPINN_retrained"]))),
        "mean_abs_prediction_difference_bu_acre": float(np.mean(np.abs(repeated - seed42_predictions["CeresPINN_retrained"]))),
        "repeat_train_seconds": repeat_seconds,
        "torch_deterministic_algorithms_enabled": bool(torch.are_deterministic_algorithms_enabled()),
    }

    multiseed = pd.DataFrame(multiseed_rows)
    multiseed.to_csv(OUTPUT / "multiseed_neural_results.csv", index=False)
    summary_rows = []
    for model_name, group in multiseed.groupby("model"):
        for metric in ["rmse_kg_ha", "mae_kg_ha", "r2"]:
            values = group[metric].to_numpy()
            half = 1.96 * values.std(ddof=1) / math.sqrt(len(values))
            summary_rows.append(
                {
                    "model": model_name,
                    "metric": metric,
                    "n_seeds": len(values),
                    "mean": float(values.mean()),
                    "std": float(values.std(ddof=1)),
                    "ci95_low_normal": float(values.mean() - half),
                    "ci95_high_normal": float(values.mean() + half),
                }
            )
    pd.DataFrame(summary_rows).to_csv(OUTPUT / "multiseed_neural_summary.csv", index=False)

    # CO2 ablation, seed 42.
    no_co2 = [feature for feature in FEATURES if feature != "co2_ppm"]
    co2_pred, co2_seconds = fit_neural(train, test, seed=42, physics_weight=0.5, features=no_co2)
    co2_annual = annualize(years_test, y_test, prediction=co2_pred)
    co2_result = {"features": no_co2, "seed": 42, "train_seconds": co2_seconds, **score(co2_annual.observed_bu_acre.to_numpy(), co2_annual.prediction.to_numpy())}

    annual_predictions = annualize(years_test, y_test, **predictions)
    for column in annual_predictions.columns:
        if column != "year":
            annual_predictions[f"{column}_kg_ha"] = annual_predictions[column] * BU_TO_KG
    annual_predictions.to_csv(OUTPUT / "hindcast_all_models.csv", index=False)
    bootstrap_model_differences(annual_predictions[["year", "observed_bu_acre", *predictions.keys()]]) \
        .to_csv(OUTPUT / "model_difference_bootstrap.csv", index=False)

    # Exact final model table from independent annual units.
    comparison = []
    for name in predictions:
        comparison.append({"model": name, "n_independent_years": 8, "seed": 42, **score(annual_predictions.observed_bu_acre.to_numpy(), annual_predictions[name].to_numpy())})
    pd.DataFrame(comparison).to_csv(OUTPUT / "baseline_metrics_full_precision.csv", index=False)

    # Correlation structure and temporal coverage.
    annual_all = pd.concat([train, test]).sort_values(["scenario", "year"])
    annual_all = annual_all.assign(scenario_forcing=annual_all.scenario.map({"SSP1-2.6": 2.6, "SSP3-7.0": 7.0, "SSP5-8.5": 8.5}))
    annual_all[["year", "co2_ppm", "scenario_forcing", "temp_anomaly_c", "heatwave_risk", "seasonal_precip_mm", "seasonal_cdd"]] \
        .corr().to_csv(OUTPUT / "training_feature_correlations.csv")
    raw = pd.read_csv(DATASET)
    temporal = raw.groupby("year").agg(expanded_rows=("yield_bu_acre", "size"), median_yield_bu_acre=("yield_bu_acre", "median")).reset_index()
    temporal["original_nass_records_reconstructed"] = temporal.expanded_rows / 3
    temporal.to_csv(OUTPUT / "temporal_coverage.csv", index=False)
    pd.DataFrame(
        {
            "feature": FEATURES,
            "train_mean": meta["normalization"]["mean"],
            "train_std": meta["normalization"]["std"],
            "constant_or_near_constant": [value < 1e-6 for value in meta["normalization"]["std"]],
        }
    ).to_csv(OUTPUT / "normalization_stats.csv", index=False)
    pd.DataFrame(
        [
            {"stage": "USDA NASS county-year records", "rows": 22160, "independent_years": 36, "transformation": "numeric cleaning"},
            {"stage": "annual median targets", "rows": 36, "independent_years": 36, "transformation": "median yield by year"},
            {"stage": "year-scenario matrix", "rows": 108, "independent_years": 36, "transformation": "replicate each target across 3 SSP templates"},
            {"stage": "training partition", "rows": 84, "independent_years": 28, "transformation": "grouped random-year split"},
            {"stage": "test partition", "rows": 24, "independent_years": 8, "transformation": "grouped random-year split"},
        ]
    ).to_csv(OUTPUT / "data_lineage_counts.csv", index=False)
    pd.DataFrame(
        [
            {"parameter": "input_features", "value": 7},
            {"parameter": "hidden_layers", "value": 4},
            {"parameter": "hidden_units_each", "value": 128},
            {"parameter": "hidden_activation", "value": "tanh"},
            {"parameter": "dropout", "value": 0.05},
            {"parameter": "yield_head", "value": "128->64(ReLU)->1"},
            {"parameter": "physics_head", "value": "128->32(ReLU)->1(Sigmoid)"},
            {"parameter": "optimizer", "value": "Adam"},
            {"parameter": "learning_rate", "value": 0.001},
            {"parameter": "adam_weight_decay", "value": 1e-5},
            {"parameter": "manual_l2_lambda", "value": 1e-4},
            {"parameter": "lambda_monotonicity", "value": 0.5},
            {"parameter": "batch_size", "value": 64},
            {"parameter": "epochs", "value": 300},
            {"parameter": "seed", "value": 42},
            {"parameter": "early_stopping", "value": False},
            {"parameter": "normalization", "value": "feature z-score and target min-max, train only"},
        ]
    ).to_csv(OUTPUT / "hyperparameters.csv", index=False)

    # Sobol, management, and model structure diagnostics.
    sobol = checkpoint_sobol(tracked, meta)
    sobol.to_csv(OUTPUT / "sobol_checkpoint.csv", index=False)
    management, water_audit = management_artifacts()
    management.to_csv(OUTPUT / "management_scenarios.csv", index=False)
    pd.DataFrame(
        [
            {"field_id": "field-bajio-02", "fc": 0.38, "wp": 0.22, "sat": 0.52, "ks_mm_day": 35.0, "origin": "hard-coded demonstration constant"},
            {"field_id": "field-iowa-01", "fc": 0.32, "wp": 0.16, "sat": 0.48, "ks_mm_day": 85.0, "origin": "hard-coded demonstration constant"},
            {"field_id": "field-pampas-03", "fc": 0.28, "wp": 0.13, "sat": 0.46, "ks_mm_day": 120.0, "origin": "hard-coded demonstration constant"},
            {"field_id": "field-ebro-04", "fc": 0.22, "wp": 0.09, "sat": 0.41, "ks_mm_day": 240.0, "origin": "hard-coded demonstration constant"},
        ]
    ).to_csv(OUTPUT / "field_soil_constants.csv", index=False)

    # Effective range loss and parameter counts.
    mean, std = np.asarray(meta["normalization"]["mean"]), np.asarray(meta["normalization"]["std"])
    train_n = (x_train - mean) / std
    with torch.no_grad():
        _, physical_head = tracked(torch.tensor(train_n, dtype=torch.float32))
        range_penalty = torch.relu(physical_head - 1.0).mean() + torch.relu(-physical_head).mean()
    structure = {
        "total_parameters": int(sum(p.numel() for p in tracked.parameters())),
        "trainable_parameters": int(sum(p.numel() for p in tracked.parameters() if p.requires_grad)),
        "physics_head_min_train": float(physical_head.min()),
        "physics_head_max_train": float(physical_head.max()),
        "effective_range_penalty_train": float(range_penalty),
        "physics_head_has_observed_target": False,
    }

    report = {
        "determinism_same_seed_repeat": determinism,
        "co2_ablation_seed42": co2_result,
        "structure": structure,
        "water_balance_from_rounded_output": water_audit,
        "sobol_method": {
            "estimator": "Jansen first-order and total-order",
            "sampler": "scipy.stats.qmc.Sobol(scramble=True)",
            "scipy_version": __import__("scipy").__version__,
            "base_N": 32768,
            "bounds": {"temp_anomaly_c": [2.2, 3.4], "precip_anomaly_pct": [-0.28, -0.15], "co2_ppm": [500, 600]},
            "fixed": {"year": 2050, "heatwave_risk": 0.78, "seasonal_cdd": 20.0, "seasonal_precip_mm": "480*(1+precip_anomaly_pct)"},
            "seed": 42,
        },
    }
    (OUTPUT / "extended_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
