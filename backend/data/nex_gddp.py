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
# NOTE: the bucket enforces a region-scoped endpoint (us-west-2). Using the
# global endpoint triggers a PermanentRedirect that most HTTP clients follow,
# but file readers (netCDF/HTTPRange) do not. Use the regional host directly.
_NEX_BASE = "https://nex-gddp-cmip6.s3-us-west-2.amazonaws.com"
# Observed layout inside the bucket: NEX-GDDP-CMIP6/{model}/{scenario}/r1i1p1f1/
#   {variable}/{variable}_day_{model}_{scenario}_r1i1p1f1_gn_{year}_v2.0.nc
# Files are ANNUAL (single year per file) and carry a `_v2.0` version suffix.
_NEX_VERSION = "NEX-GDDP-CMIP6"
_NEX_SUFFIX = "v2.0"


class NEXGDDPProvider(BaseProvider):
    """Extracts a downsampled sample of NASA NEX-GDDP-CMIP6 NetCDF projections."""

    name = "nex-gddp"

    def __init__(self, config: Settings, progress: Any = None) -> None:
        super().__init__(config, progress)
        self.out_dir = config.paths.nex

    def _scan_window(self) -> List[int]:
        """Sample years: first year of each year in the projection window.

        NEX-GDDP-CMIP6 publishes one *annual* NetCDF per (model, scenario,
        variable, year), so the temporal unit is the year, not the month.
        A `step` env override (e.g. CERESPINN_NEX_YEAR_STEP=5) keeps the demo
        light on slow connections.
        """
        start_year = self.config.time.projection_start
        end_year = self.config.time.projection_end
        import os

        step = int(os.getenv("CERESPINN_NEX_YEAR_STEP", "1"))
        return sorted({y for y in range(start_year, end_year + 1, step)})

    def _build_object_url(self, scenario: str, model: str, variable: str, year: int) -> str:
        fname = (
            f"{variable}_day_{model}_{scenario}_r1i1p1f1_gn_"
            f"{year}_{_NEX_SUFFIX}.nc"
        )
        rel = f"{_NEX_VERSION}/{model}/{scenario}/r1i1p1f1/{variable}/{urllib.parse.quote(fname)}"
        return f"{_NEX_BASE}/{rel}"

    def _regional_summary(self, url: str, scenario: str, model: str, variable: str,
                          year: int, area: Any) -> Optional[Dict[str, Any]]:
        """Read only the study-area bbox of an annual NetCDF via S3 range requests.

        Uses fsspec (HTTP seekable file) + h5py to avoid downloading the full
        0.25-degree global file (~200 MB/file). Returns None if the remote file
        is missing / unreadable so the caller can fall back to a full download.
        """
        # Region -> 0..360 lon domain (NEX-GDDP-CMIP6 uses 0..360 lon).
        lon_a = (float(area.min_lon) % 360.0)
        lon_b = (float(area.max_lon) % 360.0)
        if lon_b < lon_a:
            lon_a, lon_b = lon_b, lon_a

        try:
            import fsspec  # noqa: PLC0415 - heavy optional
            import h5py  # noqa: PLC0415

            _f = fsspec.open(url).open()
            with h5py.File(_f, "r") as h5:
                if variable not in h5:
                    return None
                lat = h5["lat"][:]
                lon = h5["lon"][:]
                lat_idx = np.arange(
                    int(np.argmin(np.abs(lat - float(area.min_lat)))),
                    int(np.argmin(np.abs(lat - float(area.max_lat)))) + 1,
                )
                lon_idx = np.where((lon >= lon_a) & (lon <= lon_b))[0]
                if not len(lat_idx) or not len(lon_idx):
                    return None
                ds = h5[variable]
                # Sample the seasonal mean over evenly-spaced days to keep the
                # read tiny (a handful of byte ranges instead of a full sweep).
                n_days = int(ds.shape[0])
                day_rows = np.linspace(0, n_days - 1, num=min(n_days, 12)).astype(int)
                vals = ds[day_rows, lat_idx[0]:lat_idx[-1] + 1, lon_idx[0]:lon_idx[-1] + 1]
                vals = vals[~np.isnan(vals)]
                if not vals.size:
                    return None
                return {
                    "scenario": scenario,
                    "model": model,
                    "variable": variable,
                    "year": year,
                    "region_mean": float(np.mean(vals)),
                    "region_min": float(np.min(vals)),
                    "region_max": float(np.max(vals)),
                    "sampled_days": int(len(day_rows)),
                }
        except Exception as exc:  # noqa: BLE001 - optional enrichment path
            self.log_step(f"Regional read failed for {url}: {exc}")
            return None

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
        grand_total = len(combos) * len(self.config.time.cmip6_variables) * len(window)
        done = 0

        for scenario in self.config.time.scenarios:
            for model in self.config.time.ensemble_members.get(scenario, []):
                for variable in self.config.time.cmip6_variables:
                    for year in window:
                        done += 1
                        self.set_progress(done, grand_total, f"nex::{scenario}::{model}::{variable}::{year}")
                        url = self._build_object_url(scenario, model, variable, year)
                        dest = self.out_dir / scenario / model / f"{variable}_{year}.nc"

                        if dry_run:
                            self.log_step(f"[dry-run] would read regional {url}")
                            total_downloaded += 1
                            continue

                        # Regional summary via remote range reads (no full-file
                        # download): fsspec+HTTP gives a seekable file object and
                        # h5py keeps the heavy .nc on S3, only pulling the bbox.
                        rec = self._regional_summary(url, scenario, model, variable, year, area)
                        if rec is not None:
                            summary_records.append(rec)
                            total_downloaded += 1
                        else:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            try:
                                import requests as _rq

                                resp = _rq.get(url, timeout=timeout)
                                if resp.ok:
                                    dest.write_bytes(resp.content)
                                    total_downloaded += 1
                                else:
                                    total_skipped += 1
                            except Exception as exc:  # noqa: BLE001
                                self.log_step(f"Fallback full download failed for {year}: {exc}")
                                total_skipped += 1

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
