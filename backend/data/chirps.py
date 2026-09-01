"""CHIRPS daily precipitation extraction (UCSB Climate Hazards Center).

CHIRPS is distributed as daily global GeoTIFFs (.tif) via FTP at:
    https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05/
OR via the coinciding HTTP endpoint. We download a bounded recent window for the
configured study area and sample the reference point rather than ingesting the whole
globe (the full archive is ~50 GB).

Real ingestion example (for a production implementation):
    import xarray as xr
    ds = xr.open_dataset("chirps-v2.0.{yyyy}.{mm}.{dd}.tif", engine="rasterio")
    point = ds.sel(x=lon, y=lat, method="nearest")["precip"]

This module focuses on the *fetch/snapshot* stage: downloading the raw GeoTIFF files
and logging a manifest. Geospatial resampling/aggregation is delegated to a separate
processing stage.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List

import requests

from .config import Settings
from .provider_base import BaseProvider, ExtractionError


_CHIRPS_BASE = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05"


class CHIRPSProvider(BaseProvider):
    """Downloads CHIRPS daily precipitation GeoTIFFs for the study window."""

    name = "chirps"

    def __init__(self, config: Settings, progress: Any = None) -> None:
        super().__init__(config, progress)
        self.out_dir = config.paths.chirps
        self.days_back = 5  # recent window to keep the sample light

    def _file_name(self, day: dt.date) -> str:
        return f"chirps-v2.0.{day.year}.{day.month:02d}.{day.day:02d}.tif"

    def _url(self, day: dt.date) -> str:
        return f"{_CHIRPS_BASE}/{day.year}/{self._file_name(day)}"

    def _sample_point(self) -> Dict[str, float]:
        """Return metadata noting the reference point for later resampling."""
        return {
            "ref_lat": self.config.area.ref_lat,
            "ref_lon": self.config.area.ref_lon,
        }

    def extract(self) -> Dict[str, Any]:
        dry_run = self.config.extraction.dry_run
        timeout = self.config.extraction.timeout_seconds
        session = requests.Session()

        today = dt.date.today()
        days = [today - dt.timedelta(days=i) for i in range(self.days_back)]
        total = len(days)

        downloaded: List[str] = []
        existing: List[str] = []

        for idx, day in enumerate(days, start=1):
            self.set_progress(idx, total, f"chirps::{day.isoformat()}")
            name = self._file_name(day)
            dest: Path = self.out_dir / name
            if dest.exists():
                existing.append(name)
                continue

            if dry_run:
                self.log_step(f"[dry-run] would download {self._url(day)}")
                downloaded.append(name)
                continue

            resp = session.get(self._url(day), timeout=timeout)
            if resp.status_code == 404:
                self.log_step(f"Not found (404): {name}")
                continue
            if not resp.ok:
                self.log_step(f"HTTP {resp.status_code} for {name}")
                continue
            dest.write_bytes(resp.content)
            downloaded.append(name)
            self.log_step(f"Downloaded {name} ({len(resp.content) / 1024:.1f} KB)")
            self.throttled()

        if not downloaded and not existing:
            raise ExtractionError("No CHIRPS files fetched or found.")

        manifest = {
            "source": _CHIRPS_BASE,
            "window_days": [d.isoformat() for d in days],
            "downloaded": downloaded,
            "already_present": existing,
            "bbox": self.config.area.bbox,
            "point": self._sample_point(),
            "note": "GeoTIFFs stored raw; convert to xarray/rasterio in processing stage.",
        }
        self.write_manifest(self.out_dir, records=len(downloaded) + len(existing), extra=manifest)
        return {
            "total_files": len(downloaded) + len(existing),
            "downloaded": len(downloaded),
            "already_present": len(existing),
        }


def run_chirps(config: Settings) -> Dict[str, Any]:
    return CHIRPSProvider(config).run()
