"""NASA NEX-GDDP CMIP6 climate projection extraction.

NASA NEX-GDDP-CMIP6 provides downscaled, bias-corrected daily climate projections at
0.25 deg (~25 km) for 1950-2100, for the CMIP6 SSP scenarios. Files are published as
NetCDF in a public S3 bucket:

    s3://nex-gddp-cmip6/

For example day files (one per day per model per scenario per variable):
    nex-gddp-cmip6/{ssp}/{model}/pr/pr_{model}_{ssp}_r1i1p1f1_gn_20150101-20150131.nc

Because the full archive is enormous, this module downloads a *subset*: the chosen
scenarios, a curated list of ensemble members, the configured variables, and only for
a bounded projection window, clipped to the study area. NetCDF files are opened with
xarray/netCDF4 and resampled/aggregated to a monthly mean per grid point.

This is intentionally a lightweight sampling extractor. Increase the window / members
in config.py for a fuller dataset.
"""
from __future__ import annotations

import datetime as dt
import urllib.parse
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import requests

from .config import Settings
from .provider_base import BaseProvider, ExtractionError

# Public NEX-GDDP-CMIP6 bucket (anonymous read via HTTPS, no signing needed).
# The documented pattern uses a signed S3 URL; we build a direct https endpoint here.
_NEX_BASE = "https://nex-gddp-cmip6.s3.amazonaws.com"
_NEX_VERSION = "CMIP6"


class NEXGDDPProvider(BaseProvider):
    """Extracts a downsampled sample of NASA NEX-GDDP-CMIP6 NetCDF projections."""

    name = "nex-gddp"

    def __init__(self, config: Settings, progress: Any = None) -> None:
        super().__init__(config, progress)
        self.out_dir = config.paths.nex

    def _scan_window(self) -> List[dt.date]:
        """Monthly grid: first day of each month within the projection window."""
        start_year = self.config.time.projection_start
        end_year = self.config.time.projection_end
        months: List[dt.date] = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                months.append(dt.date(year, month, 1))
        # Sample to keep the demo light: first month of each year.
        return months[::12]

    def _build_object_url(self, scenario: str, model: str, variable: str, first: dt.date) -> str:
        fname = (
            f"{variable}_{model}_{scenario}_r1i1p1f1_gn_"
            f"{first.year}{first.month:02d}{first.day:02d}.nc"
        )
        rel = f"{_NEX_VERSION}/{scenario}/{model}/{variable}/{urllib.parse.quote(fname)}"
        return f"{_NEX_BASE}/{rel}"

    def extract(self) -> Dict[str, Any]:
        dry_run = self.config.extraction.dry_run
        timeout = self.config.extraction.timeout_seconds
        area = self.config.area
        window = self._scan_window()

        total_downloaded = 0
        total_skipped = 0
        summary_records: List[Dict[str, Any]] = []

        combos = [
            (sc, model) for sc in self.config.time.scenarios
            for model in self.config.time.ensemble_members.get(sc, [])
        ]
        grand_total = len(combos) * len(self.config.time.cmip6_variables)
        done = 0

        for scenario in self.config.time.scenarios:
            for model in self.config.time.ensemble_members.get(scenario, []):
                for variable in self.config.time.cmip6_variables:
                    done += 1
                    self.set_progress(done, grand_total, f"nex::{scenario}::{model}::{variable}")
                    first = window[0]
                    url = self._build_object_url(scenario, model, variable, first)
                    dest = self.out_dir / scenario / model / f"{variable}_{first.year}.nc"
                    dest.parent.mkdir(parents=True, exist_ok=True)

                    if dest.exists():
                        total_skipped += 1
                        continue

                    if dry_run:
                        self.log_step(f"[dry-run] would download {url}")
                        total_downloaded += 1
                        continue

                    session = requests.Session()
                    resp = session.get(url, timeout=timeout)
                    if resp.status_code == 404:
                        self.log_step(f"404: {url}")
                        continue
                    if not resp.ok:
                        self.log_step(f"HTTP {resp.status_code}: {url}")
                        continue
                    dest.write_bytes(resp.content)
                    total_downloaded += 1
                    self.log_step(f"Downloaded {dest.name} ({len(resp.content)/1024/1024:.1f} MB)")
                    self.throttled()

                    # Light statistical summary of the clipped region.
                    try:
                        import xarray as xr  # heavy import kept local
                        ds = xr.open_dataset(dest, engine="netcdf4")
                        clipped = ds[variable]
                        lon_attr = "lon"
                        if lon_attr in clipped.coords:
                            clipped = clipped.sel(
                                lon=slice(area.min_lon, area.max_lon),
                                lat=slice(area.min_lat, area.max_lat),
                            )
                        vals = clipped.values
                        vals = vals[~np.isnan(vals)]
                        summary_records.append(
                            {
                                "scenario": scenario,
                                "model": model,
                                "variable": variable,
                                "year": first.year,
                                "region_mean": float(np.mean(vals)) if vals.size else None,
                                "region_min": float(np.min(vals)) if vals.size else None,
                                "region_max": float(np.max(vals)) if vals.size else None,
                            }
                        )
                        ds.close()
                    except Exception as exc:  # pragma: no cover - optional enrichment
                        self.log_step(f"Could not summarize {dest.name}: {exc}")

        if total_downloaded == 0 and total_skipped == 0 and not summary_records and not dry_run:
            raise ExtractionError("No NEX-GDDP files fetched.")

        summary_df = pd.DataFrame(summary_records)
        csv_path = self.out_dir / "nex_gddp_region_summary.csv"
        self.write_snapshot(csv_path, summary_df)

        manifest_extra = {
            "source": _NEX_BASE,
            "version": _NEX_VERSION,
            "scenarios": self.config.time.scenarios,
            "variables": self.config.time.cmip6_variables,
            "window": f"{self.config.time.projection_start}-{self.config.time.projection_end}",
            "bbox": area.bbox,
            "ensemble_members": self.config.time.ensemble_members,
        }
        self.write_manifest(self.out_dir, records=len(summary_df), extra=manifest_extra)

        return {
            "downloads": total_downloaded,
            "already_present": total_skipped,
            "region_stats_rows": len(summary_records),
            "csv_path": str(csv_path),
        }


def run_nex(config: Settings) -> Dict[str, Any]:
    return NEXGDDPProvider(config).run()
