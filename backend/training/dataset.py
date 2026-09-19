"""Dataset assembly for CeresPINN.

Blends the artifacts produced by the extractors (backend.data) into the feature
matrix the PINN consumes:

  targets  : USDA NASS county-year maize yield (bu/acre)
  features : climatological anomalies synthesized from CHIRPS (precip) and
             NASA NEX-GDDP CMIP6 (temperature/CO2/heatwave), per year+scenario.

The engineering here is intentionally conservative and deterministic. The extractor
artifacts are small samples; this module builds a defensible feature/target frame and
provides a clear path to replace the synthetic climate-blending with the raw NetCDF
resampling when a full harvest is available.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from .config import DataConfig, TrainConfig

# CMIP6 scenario -> representative anomaly template.
# Values are placeholders derived from the CLI forcing in src/services/pinnEngine.ts
# and are overwritten by the NEX-GDDP regional summary when present.
SCENARIO_TEMPLATE = {
    "SSP1-2.6": {"temp_anomaly_c": 0.9, "precip_anomaly_pct": -0.02, "co2_ppm": 445.0, "heatwave_risk": 0.15},
    "SSP3-7.0": {"temp_anomaly_c": 1.8, "precip_anomaly_pct": -0.12, "co2_ppm": 480.0, "heatwave_risk": 0.42},
    "SSP5-8.5": {"temp_anomaly_c": 2.7, "precip_anomaly_pct": -0.24, "co2_ppm": 520.0, "heatwave_risk": 0.78},
}


def load_artifacts(data: DataConfig) -> Dict[str, Any]:
    """Load NASS CSV + optional NEX-GDDP regional summary from disk."""
    artifacts: Dict[str, Any] = {}

    if data.nass_path.exists():
        artifacts["nass"] = pd.read_csv(data.nass_path)
    else:
        artifacts["nass"] = None

    nex_summary = data.nex_path / "nex_gddp_region_summary.csv"
    artifacts["nex_summary"] = _read_csv_if_readable(nex_summary)
    return artifacts


def _read_csv_if_readable(path: Path) -> pd.DataFrame | None:
    """Read a CSV, treating missing/empty files as 'no data available'."""
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if df.empty:
            return None
        return df
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return None
    except Exception:  # noqa: BLE001 - a malformed sidecar must not break training
        return None


def _normalize_nass(df: pd.DataFrame) -> pd.DataFrame:
    """Select and clean NASS county-year yield observations."""
    cols = [c for c in ["year", "state_name", "county_name", "Value"] if c in df.columns]
    out = df[cols].copy()
    out = out.rename(columns={"Value": "yield_bu_acre"})
    out["yield_bu_acre"] = pd.to_numeric(out["yield_bu_acre"], errors="coerce")
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    return out.dropna(subset=["year", "yield_bu_acre"])


# NEX-GDDP scenario ids (summary) -> SCENARIO_TEMPLATE keys (training rows).
_NEX_SCENARIO_MAP = {
    "SSP1-2.6": "ssp126",
    "SSP2-4.5": "ssp245",
    "SSP3-7.0": "ssp370",
    "SSP5-8.5": "ssp585",
}

# Growing season (May-Sep) length used to scale daily precip flux to seasonal mm.
_SEASON_DAYS = 153


def _nex_year_lookup(nex_summary: pd.DataFrame | None) -> Dict[str, Any]:
    """Index live NEX-GDDP regional means as {(scenario, year, variable): value}.

    Units out of the extractor: pr = kg/m2/s flux, tasmax = Kelvin.
    Returns the lookup plus the 1990-2014 historical tasmax baseline (degC)
    used to express temp anomalies.
    """
    empty: Dict[str, Any] = {"tasmax_c": {}, "pr_flux": {}, "baseline_c": None}
    if nex_summary is None or nex_summary.empty:
        return empty
    need = {"scenario", "variable", "year", "region_mean"}
    if not need.issubset(set(nex_summary.columns)):
        return empty
    frame = nex_summary.copy()
    frame["scenario"] = frame["scenario"].astype(str)
    frame["variable"] = frame["variable"].astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")

    lookup = {"tasmax_c": {}, "pr_flux": {}, "baseline_c": None}
    for _, row in frame.iterrows():
        if pd.isna(row["year"]):
            continue
        key = (row["scenario"], int(row["year"]), row["variable"])
        try:
            val = float(row["region_mean"])
        except (TypeError, ValueError):
            continue
        if row["variable"] == "tasmax":
            lookup["tasmax_c"][key] = val - 273.15
        elif row["variable"] == "pr":
            lookup["pr_flux"][key] = val

    hist = [v for (sc, _y, _v), v in lookup["tasmax_c"].items() if sc == "historical"]
    if hist:
        lookup["baseline_c"] = float(np.mean(hist))

    # Years harvested sparsely (even historical years, 5-year SSP steps):
    # linearly interpolate within each scenario so every training year has a
    # real-based value instead of falling back to the flat template.
    try:
        full_years = list(range(1990, 2026))
        for store in ("tasmax_c", "pr_flux"):
            by_sc: Dict[str, Dict[int, float]] = {}
            for (sc, y, _v), val in lookup[store].items():
                by_sc.setdefault(sc, {})[y] = val
            for sc, series in by_sc.items():
                s = pd.Series(series).sort_index()
                s = s.reindex(full_years).interpolate(method="linear", limit_direction="both")
                for y in full_years:
                    if (sc, y, "tasmax" if store == "tasmax_c" else "pr") not in lookup[store]:
                        lookup[store][(sc, y, "tasmax" if store == "tasmax_c" else "pr")] = float(s.loc[y])
    except Exception:
        pass
    return lookup


def _blend_climate(
    years: np.ndarray,
    scenarios: np.ndarray,
    nex_summary: pd.DataFrame | None,
) -> pd.DataFrame:
    """Build the climate feature matrix for (year, scenario) rows.

    When a NEX-GDDP regional summary is available for a matching (variable, scenario)
    it overrides the template; otherwise the template stands, so training never
    breaks on missing projection data.
    """
    rows: list[Dict[str, Any]] = []
    lookup = _nex_year_lookup(nex_summary)
    for year, scenario in zip(years, scenarios):
        feats = dict(SCENARIO_TEMPLATE.get(str(scenario), SCENARIO_TEMPLATE["SSP1-2.6"]))
        # Project forward anomalies with year (mild linear drift, mirrors the frontend).
        years_from_base = max(0, int(year) - 2026)
        feats["temp_anomaly_c"] = feats["temp_anomaly_c"] + years_from_base * 0.02
        feats["co2_ppm"] = feats["co2_ppm"] + years_from_base * 1.5

        # Live NEX-GDDP override, per (scenario, year): historical experiment
        # covers 1990-2014, SSP runs cover 2015+. Falls back to template when
        # a given year/scenario was not harvested.
        nex_sc = _NEX_SCENARIO_MAP.get(str(scenario), str(scenario).lower())
        if int(year) < 2015:
            nex_sc = "historical"
        tas_c = lookup["tasmax_c"].get((nex_sc, int(year), "tasmax"))
        if tas_c is not None:
            if lookup["baseline_c"] is not None:
                feats["temp_anomaly_c"] = float(tas_c - lookup["baseline_c"])
            else:
                feats["temp_anomaly_c"] = float(tas_c - 14.0)
        pr_flux = lookup["pr_flux"].get((nex_sc, int(year), "pr"))
        if pr_flux is not None and pr_flux >= 0:
            feats["seasonal_precip_mm"] = float(pr_flux * 86400.0 * _SEASON_DAYS)

        # Secondary engineered features.
        feats["precip_anomaly_pct"] = feats.get("precip_anomaly_pct", 0.0)
        feats["seasonal_precip_mm"] = feats.get("seasonal_precip_mm", 480.0)
        feats["seasonal_cdd"] = feats.get("seasonal_cdd", 20 + years_from_base * 0.6)
        rows.append({"year": year, "scenario": scenario, **feats})

    return pd.DataFrame(rows)


def build_dataset(
    train_config: TrainConfig,
    data_config: DataConfig,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Assemble features/targets and split into train/test arrays.

    Returns (X_train, y_train, X_test, y_test, info).
    """
    artifacts = load_artifacts(data_config)
    info: Dict[str, Any] = {"artifacts_present": {k: v is not None for k, v in artifacts.items()}}

    nass = artifacts.get("nass")
    if nass is None or nass.empty:
        # Deterministic synthetic fallback so training is runnable before a real
        # (key-gated) NASS harvest. Clearly flagged in `info`.
        synthetic = _synthetic_dataset(train_config)
        info["source"] = "synthetic-fallback"
        return synthetic

    norm = _normalize_nass(nass)
    if norm.empty:
        norm = _synthetic_dataset(train_config)[0]
        info["source"] = "synthetic-fallback-empty"
        return norm  # type: ignore[return-value]

    # Deterministic county-aggregate: median yield per year (keeps frame small/loss calm).
    annual = (
        norm.groupby("year")["yield_bu_acre"]
        .median()
        .reset_index()
    )

    # Scenario expansion: every county-year row is replicated across the SSP scenarios
    # because a projected twin is scenario-conditional.
    scenarios = np.array([s for s in SCENARIO_TEMPLATE for _ in annual.index])
    years = np.tile(annual["year"].to_numpy(), len(SCENARIO_TEMPLATE))
    y = np.tile(annual["yield_bu_acre"].to_numpy(), len(SCENARIO_TEMPLATE))

    climate = _blend_climate(years.astype(int), scenarios, artifacts.get("nex_summary"))
    X = climate[train_config.feature_names].to_numpy(dtype=float)

    # Train/test split (seeded, deterministic).
    rng = np.random.default_rng(train_config.seed)
    idx = rng.permutation(len(X))
    split = int(train_config.train_frac * len(X))
    train_idx, test_idx = idx[:split], idx[split:]

    info["source"] = "nass+nex-gddp"
    info["n_rows"] = len(X)
    info["train_rows"] = len(train_idx)
    info["test_rows"] = len(test_idx)
    return X[train_idx], y[train_idx], X[test_idx], y[test_idx], info


def _synthetic_dataset(train_config: TrainConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Deterministic synthetic data for smoke-training before a real harvest."""
    rng = np.random.default_rng(train_config.seed)
    n_scenarios = len(SCENARIO_TEMPLATE)
    years = np.arange(1990, 2026)
    scenarios = np.array([s for s in SCENARIO_TEMPLATE for _ in years])
    yy = np.tile(years, n_scenarios)
    climate = _blend_climate(yy.astype(int), scenarios, None)
    X = climate[train_config.feature_names].to_numpy(dtype=float)

    # Yield: base + temp penalty + noise (a learnable but simple target).
    base = 165.0
    y = base - climate["temp_anomaly_c"].to_numpy() * 8.0 + rng.normal(0, 4.0, size=len(X))

    idx = rng.permutation(len(X))
    split = int(train_config.train_frac * len(X))
    train_idx, test_idx = idx[:split], idx[split:]
    info = {"source": "synthetic-fallback", "n_rows": len(X)}
    return X[train_idx], y[train_idx], X[test_idx], y[test_idx], info
