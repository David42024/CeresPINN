"""USDA NASS QuickStats extraction for maize harvest yield observations.

The QuickStats API returns CSV/JSON for county-level crop yield histories. These
observations are the empirical ground truth used as the NASS loss term during PINN
training (see README: "45,200 County-Year Yield Observations").

Documentation:
    - API reference: https://quickstats.nass.usda.gov/api
    - Requires an API key: https://quickstats.nass.usda.gov/api#param_requirements

Example request:
    GET https://quickstats.nass.usda.gov/api/api_GET/?key=KEY&commodity_desc=CORN
        &statisticcat_desc=YIELD&agg_level_desc=COUNTY&format=JSON&year__GE=1990
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from .config import Settings
from .provider_base import BaseProvider, ExtractionError


_NASS_API = "https://quickstats.nass.usda.gov/api/api_GET/"


class NASSProvider(BaseProvider):
    """Fetches county-level maize yield observations from USDA NASS QuickStats."""

    name = "usda-nass"

    def __init__(self, config: Settings, progress: Any = None) -> None:
        super().__init__(config, progress)
        self.out_dir = config.paths.nass
        self.cfg = config.nass

    def _build_params(self, year_ge: int, year_le: int) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "key": self.cfg.api_key,
            "source_desc": self.cfg.source_desc,
            "sector_desc": self.cfg.sector_desc,
            "commodity_desc": self.cfg.commodity_desc,
            "reference_period_desc": self.cfg.reference_period_desc,
            "statisticcat_desc": self.cfg.statisticcat_desc,
            "agg_level_desc": self.cfg.agg_level_desc,
            "unit_desc": self.cfg.unit_desc,
            "format": "JSON",
            "year__GE": year_ge,
            "year__LE": year_le,
        }
        # Optional state filter (e.g. "IA" for Iowa) via environment.
        if self.cfg.state_alpha:
            params["state_alpha"] = self.cfg.state_alpha
        return params

    def extract(self) -> Dict[str, Any]:
        dry_run = self.config.extraction.dry_run
        timeout = self.config.extraction.timeout_seconds
        year_ge = self.config.time.historical_start
        year_le = self.config.time.historical_end

        if dry_run:
            self.log_step(
                "[dry-run] would query NASS QuickStats for "
                f"CORN COUNTY YIELD {year_ge}-{year_le}"
            )
            self._emit_empty_scenario(year_ge, year_le)
            return {"fetched": 0, "note": "Dry run; no network call performed."}

        if not self.cfg.api_key:
            raise ExtractionError(
                "NASS_API_KEY not set. Register at "
                "https://quickstats.nass.usda.gov/api and export the key."
            )

        params = self._build_params(year_ge, year_le)
        resp = requests.get(_NASS_API, params=params, timeout=timeout)
        if not resp.ok:
            raise ExtractionError(f"NASS API HTTP {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        rows = data.get("data", [])
        self.log_step(f"NASS returned {len(rows)} county-year observations")

        records = self._rows_to_frame(rows)
        csv_path = self.out_dir / "maize_county_yield_usda.csv"
        self.write_snapshot(csv_path, records)

        manifest_extra = {
            "source": _NASS_API,
            "commodity": self.cfg.commodity_desc,
            "statisticcat": self.cfg.statisticcat_desc,
            "agg_level": self.cfg.agg_level_desc,
            "period": f"{year_ge}-{year_le}",
        }
        self.write_manifest(self.out_dir, records=len(records), extra=manifest_extra)

        summary = {
            "fetched": len(records),
            "years": sorted(records["year"].unique().tolist()) if len(records) else [],
            "csv_path": str(csv_path),
        }
        self.log_step(f"Wrote {len(records)} rows to {csv_path.name}")
        self.set_progress(1, 1, "nass::complete")
        return summary

    @staticmethod
    def _rows_to_frame(rows: List[Dict[str, Any]]) -> pd.DataFrame:
        keep = [
            "year",
            "state_name",
            "state_alpha",
            "county_name",
            "county_ansi",
            "Value",
            "unit_desc",
            "statisticcat_desc",
        ]
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=keep)
        # Normalize numeric value strings like "12,345" -> float
        if "Value" in df.columns:
            df["Value"] = (
                df["Value"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("(", "", regex=False)
                .str.replace(")", "", regex=False)
                .astype(float, errors="ignore")
            )
        missing = [c for c in keep if c not in df.columns]
        for c in missing:
            df[c] = None
        return df[keep]

    def _emit_empty_scenario(self, year_ge: int, year_le: int) -> None:
        empty = pd.DataFrame(
            columns=[
                "year", "state_name", "state_alpha", "county_name",
                "county_ansi", "Value", "unit_desc", "statisticcat_desc",
            ]
        )
        self.write_snapshot(self.out_dir / "maize_county_yield_usda.csv", empty)
        self.write_manifest(
            self.out_dir,
            records=0,
            extra={"source": _NASS_API, "period": f"{year_ge}-{year_le}", "dry_run": True},
        )


def run_nass(config: Settings) -> Dict[str, Any]:
    return NASSProvider(config).run()
