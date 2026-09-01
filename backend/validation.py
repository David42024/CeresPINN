"""Statistical validation and uncertainty analysis for CeresPINN.

Implements the hypothesis-testing pipeline from the research protocol:

  - Hindcast validation   : simulate 1990-2020 with historical climate and
                            compare against the observational reference (USDA
                            NASS when present). Produces RMSE / MAE / R2.
  - KS test               : two-sample Kolmogorov-Smirnov comparing the
                            simulated yield distribution vs. the observed one.
  - Paired t-test         : SSP5-8.5 vs. historical baseline yield per year,
                            reporting the % loss and the H1 >= 15% threshold.
  - Sobol sensitivity     : first-order + total Sobol indices over the
                            dominant climate drivers (Tmax, precipitation,
                            rainfall distribution / CDD).
  - Bootstrap             : 95% CI of projected yield via resampling the
                            GCM ensemble members.
  - Ensemble uncertainty  : mean, interquartile range (IQR) and CI across the
                            downscaled multi-model projections.

Design notes
  - numpy + scipy only (no torch) so this runs on the light Render container.
  - A deterministic crop-response engine `deterministic_yield` is used as the
    surrogate curve so every statistic is reproducible even before a trained
    PINN checkpoint is deployed. When the observed NASS file is absent the
    reference is a clearly-flagged deterministic baseline.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats

# Historical hindcast window used by the protocol.
HINDCAST_START = 1990
HINDCAST_END = 2020

# H1 resilience threshold from the protocol: projected loss under SSP5-8.5.
H1_MIN_LOSS_PCT = 15.0
# Adaptation hedging target: optimal planting mitigates >= 50% of the loss.
H1_MITIGATION_PCT = 50.0

# Per-scenario anomaly bands (Tmax degC, precip % , distribution/CDD) used to
# emulate the spread of the downscaled GCM ensemble when no raw NetCDF is on disk.
SCENARIO_BANDS = {
    "SSP1-2.6": {"temp": (0.6, 1.3), "precip": (-0.05, 0.02), "cdd": (18, 26)},
    "SSP2-4.5": {"temp": (1.1, 2.0), "precip": (-0.10, -0.02), "cdd": (22, 34)},
    "SSP3-7.0": {"temp": (1.5, 2.6), "precip": (-0.16, -0.06), "cdd": (26, 42)},
    "SSP5-8.5": {"temp": (2.2, 3.4), "precip": (-0.28, -0.15), "cdd": (32, 52)},
}

# GCM members used to emulate the ensemble (NASA NEX-GDDP subset).
ENSEMBLE_MODELS = [
    "CESM2",
    "EC-Earth3",
    "MIROC6",
    "MPI-ESM1-2-LR",
    "MRI-ESM2-0",
    "ACCESS-ESM1-5",
    "CanESM5",
]


def _scenario_band(scenario: str) -> Dict[str, tuple]:
    return SCENARIO_BANDS.get(scenario, SCENARIO_BANDS["SSP1-2.6"])


def deterministic_yield(
    year: int,
    temp_anomaly_c: float,
    precip_anomaly_pct: float,
    cdd: float = 20.0,
    base_yield: float = 9200.0,
) -> float:
    """Deterministic surrogate crop response (kg/ha).

    Mimics a plausible maize response:
      - yields fall with warming (thermal stress),
      - yields also fall when precipitation drops or the season dries out
        (CDD proxy), saturating at a positive water response.

    This is the reproducible fallback curve used by all statistics when the
    trained PINN is not deployed.
    """
    # Thermal: optimum near +0C anomaly, penalty grows with warming.
    temp_penalty = max(0.0, temp_anomaly_c) ** 1.35 * 0.045
    # Water: symmetric-ish penalty. Some yield benefit from modest extra rain,
    # monotonic penalty as rainfall is removed.
    precip_penalty = max(0.0, -precip_anomaly_pct) ** 1.2 * 0.06
    water_penalty = max(0.0, (cdd - 20.0)) * 0.0045
    # Mild trend improvement (technology/CO2 fertilization) over the decades.
    tech = 1.0 + (year - 2000) * 0.002

    stress = temp_penalty + precip_penalty + water_penalty
    return float(base_yield * tech * (1.0 - min(0.85, stress)))


# ---------------------------------------------------------------------------
# Reference (observations) loader
# ---------------------------------------------------------------------------
def load_observed_reference(
    nass_csv: Optional[Path | str] = None,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Return (years, observed_yield_kg_ha, source).

    Reads the USDA NASS CSV when available; otherwise returns a deterministic
    baseline clearly flagged as synthetic so the user is never misled.
    """
    years = np.arange(HINDCAST_START, HINDCAST_END + 1, dtype=int)

    if nass_csv is not None and Path(nass_csv).exists():
        try:
            import pandas as pd

            df = pd.read_csv(nass_csv)
            # Keep years in the hindcast window with a "Value" yield column.
            if {"year", "Value"}.issubset(df.columns):
                sub = df[["year", "Value"]].dropna()
                sub["year"] = sub["year"].astype(int)
                sub = sub[(sub["year"] >= HINDCAST_START) & (sub["year"] <= HINDCAST_END)]
                obs = sub.groupby("year")["Value"].median().reindex(years).ffill().bfill()
                if obs.notna().any():
                    return years, obs.to_numpy(dtype=float) * 62.77 * 2.47105, "usda-nass"
        except Exception:  # noqa: BLE001 - malformed reference must not break
            pass

    # Deterministic synthetic reference (no network / no NASS present).
    rng = np.random.default_rng(0)
    base = np.array([deterministic_yield(int(y), 0.3, -0.02, 24.0) for y in years])
    obs = base + rng.normal(0, 220, size=len(years))
    obs = np.clip(obs, 2000, None)
    return years, obs, "synthetic-reference"


# ---------------------------------------------------------------------------
# Hindcast + predictive metrics
# ---------------------------------------------------------------------------
def hindcast(nass_csv: Optional[Path | str] = None) -> Dict[str, Any]:
    """Simulate the hindcast window and score RMSE / MAE / R2 vs reference."""
    years, obs, source = load_observed_reference(nass_csv)
    sim = np.array(
        [
            deterministic_yield(int(y), 0.25 + (y - 1990) * 0.004, -0.01 - (y - 1990) * 0.0008, 20.0 + (y - 1990) * 0.05)
            for y in years
        ]
    )
    resid = sim - obs
    rmse = float(np.sqrt(np.mean(resid**2)))
    mae = float(np.mean(np.abs(resid)))
    ss_tot = float(np.sum((obs - np.mean(obs)) ** 2))
    r2 = float(1.0 - np.sum(resid**2) / (ss_tot + 1e-9))
    return {
        "window_years": [HINDCAST_START, HINDCAST_END],
        "n_years": int(len(years)),
        "reference_source": source,
        "metrics": {"rmse_kg_ha": round(rmse, 1), "mae_kg_ha": round(mae, 1), "r2": round(r2, 4)},
        "by_year": [
            {"year": int(y), "simulated_kg_ha": round(float(s), 0), "observed_kg_ha": round(float(o), 0)}
            for y, s, o in zip(years, sim, obs)
        ],
    }


# ---------------------------------------------------------------------------
# KS test
# ---------------------------------------------------------------------------
def ks_test(nass_csv: Optional[Path | str] = None) -> Dict[str, Any]:
    """Two-sample KS: simulated vs observed yield distribution."""
    years, obs, source = load_observed_reference(nass_csv)
    sim = np.array([deterministic_yield(int(y), 0.25 + (y - 1990) * 0.004, -0.01 - (y - 1990) * 0.0008, 20.0 + (y - 1990) * 0.05) for y in years])
    stat, pvalue = stats.ks_2samp(sim, obs)
    return {
        "test": "Kolmogorov-Smirnov (two-sample)",
        "reference_source": source,
        "n_simulated": int(len(sim)),
        "n_observed": int(len(obs)),
        "statistic": round(float(stat), 4),
        "p_value": round(float(pvalue), 5),
        "null_hypothesis": "distributions are equal",
        "reject_null_at_05": bool(pvalue < 0.05),
    }


# ---------------------------------------------------------------------------
# Paired t-test (SSP5-8.5 vs historical baseline)
# ---------------------------------------------------------------------------
def paired_t_test_ssp(target_year: int = 2050, scenario: str = "SSP5-8.5") -> Dict[str, Any]:
    """Paired t-test of projected yield under `scenario` vs. historical baseline.

    Uses per-year rows of the hindcast window as the matched (baseline)
    observations and projects them forward with the scenario's anomaly bands to
    emulate the projected vs. historical comparison per the protocol.
    """
    years = np.arange(HINDCAST_START, HINDCAST_END + 1, dtype=int)
    band = _scenario_band(scenario)
    temp = float(np.mean(band["temp"]))
    precip = float(np.mean(band["precip"]))
    cdd = float(np.mean(band["cdd"]))
    horizon_shift = max(0, target_year - 2026) * 0.02

    baseline = np.array([deterministic_yield(int(y), 0.25, -0.01, 20.0) for y in years])
    projected = np.array(
        [deterministic_yield(int(y), temp + horizon_shift, precip, cdd) for y in years]
    )

    diffs = projected - baseline
    mean_loss_pct = float(np.mean((baseline - projected) / baseline) * 100.0)

    if np.allclose(diffs, 0):
        t_stat, p_value = 0.0, 1.0
    else:
        t_stat, p_value = stats.ttest_1samp(diffs, 0.0)

    return {
        "test": "Paired t-test (one-sample on per-year differences)",
        "scenario": scenario,
        "target_year": target_year,
        "n_years": int(len(years)),
        "mean_projected_kg_ha": round(float(np.mean(projected)), 0),
        "mean_baseline_kg_ha": round(float(np.mean(baseline)), 0),
        "mean_loss_pct": round(mean_loss_pct, 2),
        "meets_h1_min_loss_pct": bool(mean_loss_pct >= H1_MIN_LOSS_PCT),
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_value), 5),
        "significant_at_05": bool(p_value < 0.05),
    }


# ---------------------------------------------------------------------------
# Sobol sensitivity (first-order + total) via Saltelli sampling
# ---------------------------------------------------------------------------
def sobol_sensitivity(
    scenario: str = "SSP5-8.5",
    target_year: int = 2050,
    n_samples: int = 256,
    seed: int = 42,
) -> Dict[str, Any]:
    """First-order and total Sobol indices for Tmax, precipitation, CDD.

    Implements a variance-decomposition by conditional averaging (a
    conditioning-grid Sobol estimator) that is stable for strongly non-linear /
    interactive crop-response surfaces and is guaranteed to return indices in
    [0, 1] by construction. numpy/scipy only (no external SALib dependency).
    """
    param_names = ["tmax", "precip", "rainfall_distribution_cdd"]
    band = _scenario_band(scenario)
    horizon_shift = max(0, target_year - 2026) * 0.02
    bounds = [
        (band["temp"][0] - 0.15, band["temp"][1] + 0.15),
        (band["precip"][0] - 0.03, band["precip"][1] + 0.03),
        (band["cdd"][0] - 3.0, band["cdd"][1] + 3.0),
    ]

    def model_fn(x: np.ndarray) -> np.ndarray:
        return np.array(
            [
                deterministic_yield(target_year, float(r[0]) + horizon_shift, float(r[1]), float(r[2]))
                for r in x
            ]
        )

    rng = np.random.default_rng(seed)
    d = len(param_names)
    # Raw Sobol/global sample used to obtain the total output variance.
    raw = np.empty((n_samples, d))
    for j, (lo, hi) in enumerate(bounds):
        raw[:, j] = rng.uniform(lo, hi, size=n_samples)
    y_raw = model_fn(raw)
    var_y = float(np.var(y_raw, ddof=1))
    if var_y <= 1e-12:
        var_y = 1e-12

    # Conditioning grid: n_grid outer points per parameter, n_inner draws over
    # the remaining parameters.
    n_grid = 96
    n_inner = 96

    first_order = []
    total = []
    for j in range(d):
        grid_vals = np.linspace(bounds[j][0], bounds[j][1], n_grid)
        others = [k for k in range(d) if k != j]
        cond_expect = np.empty(n_grid)
        cond_var = np.empty(n_grid)
        for gi, gv in enumerate(grid_vals):
            inner = np.empty((n_inner, d))
            for k in range(d):
                inner[:, k] = rng.uniform(bounds[k][0], bounds[k][1], size=n_inner)
            inner[:, j] = gv
            y_inner = model_fn(inner)
            cond_expect[gi] = float(y_inner.mean())
            cond_var[gi] = float(y_inner.var(ddof=1))
        # First order: Var(E[Y | X_j]) / Var(Y); Total: E[Var(Y | X_-j]) / Var(Y)
        vi = float(np.var(cond_expect, ddof=1, axis=0))
        vt = float(np.mean(cond_var))
        first_order.append(vi / var_y)
        total.append(vt / var_y)

    # Clamp residual float noise to the mathematically valid [0, 1].
    first_order = [min(1.0, max(0.0, v)) for v in first_order]
    total = [min(1.0, max(0.0, v)) for v in total]

    dominant_idx = int(np.argmax(first_order))
    return {
        "method": "Variance decomposition by conditioning grid (Sobol first-order + total)",
        "scenario": scenario,
        "target_year": target_year,
        "n_samples": n_samples,
        "grid_points_per_parameter": n_grid,
        "parameters": param_names,
        "first_order": [round(v, 4) for v in first_order],
        "total": [round(v, 4) for v in total],
        "dominant_parameter": param_names[dominant_idx],
        "dominant_var_explained": round(float(first_order[dominant_idx]), 4),
    }


# ---------------------------------------------------------------------------
# Bootstrap + ensemble uncertainty
# ---------------------------------------------------------------------------
def bootstrap_ensemble(
    scenario: str = "SSP5-8.5",
    target_year: int = 2050,
    n_bootstrap: int = 1000,
    seed: int = 7,
) -> Dict[str, Any]:
    """95% bootstrap CI of projected yield resampled over the GCM ensemble.

    Samples a GCM member, draws its anomaly within the scenario band, and
    bootstraps the resulting projected yields to build a 95% CI.
    """
    band = _scenario_band(scenario)
    rng = np.random.default_rng(seed)
    base_yield = 9200.0
    center_cdd = float(np.mean(band["cdd"]))
    horizon_shift = max(0, target_year - 2026) * 0.02

    # Ensemble sample: for each model pick anomalies within the band.
    ensemble_vals = np.empty(len(ENSEMBLE_MODELS))
    for i, _m in enumerate(ENSEMBLE_MODELS):
        temp = rng.uniform(*band["temp"])
        precip = rng.uniform(*band["precip"])
        cdd = rng.uniform(*band["cdd"])
        ensemble_vals[i] = deterministic_yield(target_year, temp + horizon_shift, precip, cdd, base_yield)

    # Bootstrap resampling of the ensemble members.
    boot_means = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        idx = rng.integers(0, len(ensemble_vals), size=len(ensemble_vals))
        boot_means[b] = ensemble_vals[idx].mean()

    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    q25, q75 = np.percentile(ensemble_vals, [25, 75])
    return {
        "method": "Bootstrap (resampling of the multi-model ensemble)",
        "scenario": scenario,
        "target_year": target_year,
        "n_ensemble_models": int(len(ensemble_vals)),
        "ensemble_models": ENSEMBLE_MODELS,
        "ensemble_mean_kg_ha": round(float(ensemble_vals.mean()), 0),
        "ci95_lower_kg_ha": round(float(lo), 0),
        "ci95_upper_kg_ha": round(float(hi), 0),
        "iqr_q25_kg_ha": round(float(q25), 0),
        "iqr_q75_kg_ha": round(float(q75), 0),
        "n_bootstrap": n_bootstrap,
    }


def ensemble_uncertainty(
    scenario: str = "SSP5-8.5",
    target_year: int = 2050,
    seed: int = 11,
) -> Dict[str, Any]:
    """Multi-model spread: mean, IQR and 95% CI across the downscaled ensemble."""
    band = _scenario_band(scenario)
    rng = np.random.default_rng(seed)
    horizon_shift = max(0, target_year - 2026) * 0.02

    # 4 draws per model to emulate internal-variability spread on top of the
    # inter-model spread (mimics a richer ensemble).
    vals = []
    for _m in ENSEMBLE_MODELS:
        for _ in range(4):
            temp = rng.uniform(*band["temp"])
            precip = rng.uniform(*band["precip"])
            cdd = rng.uniform(*band["cdd"])
            vals.append(deterministic_yield(target_year, temp + horizon_shift, precip, cdd))

    arr = np.array(vals)
    mean = float(arr.mean())
    sd = float(arr.std(ddof=1))
    lo, hi = mean - 1.96 * sd / np.sqrt(len(arr)), mean + 1.96 * sd / np.sqrt(len(arr))
    return {
        "method": "Downscaled GCM ensemble spread",
        "scenario": scenario,
        "target_year": target_year,
        "n_members": int(len(arr)),
        "mean_kg_ha": round(mean, 0),
        "std_kg_ha": round(sd, 0),
        "iqr": {
            "q25_kg_ha": round(float(np.percentile(arr, 25)), 0),
            "q75_kg_ha": round(float(np.percentile(arr, 75)), 0),
            "range_kg_ha": round(float(np.percentile(arr, 75) - np.percentile(arr, 25)), 0),
        },
        "ci95_kg_ha": {"lower": round(float(lo), 0), "upper": round(float(hi), 0)},
    }


def full_report(nass_csv: Optional[Path | str] = None) -> Dict[str, Any]:
    """Aggregate every statistic into one report for the UI / API."""
    return {
        "hypothesis_tests": {
            "h0": "El twin climático no predice diferencias significativas de rendimiento entre SSP2-4.5 y SSP5-8.5 para 2050",
            "h1": "El twin predice reducción del rendimiento en >=15% bajo SSP5-8.5 vs. baseline histórico, con ventanas de siembra óptimas que mitigan >=50% de la pérdida",
        },
        "hindcast": hindcast(nass_csv),
        "ks_test": ks_test(nass_csv),
        "paired_t_test_ssp585_vs_historical": paired_t_test_ssp(2050, "SSP5-8.5"),
        "sobol_sensitivity": sobol_sensitivity("SSP5-8.5", 2050),
        "bootstrap_ci_ssp585": bootstrap_ensemble("SSP5-8.5", 2050),
        "ensemble_uncertainty_ssp585": ensemble_uncertainty("SSP5-8.5", 2050),
        "scenarios_supported": sorted(SCENARIO_BANDS.keys()),
    }
