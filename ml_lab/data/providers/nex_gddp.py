"""NASA NEX-GDDP CMIP6 climate projection data provider for ML Lab.

This module provides a generalized NEX-GDDP data provider adapted from
CeresPINN for use in ML Lab. It downloads climate projection data from
the NASA NEX-GDDP-CMIP6 S3 bucket.
"""
from __future__ import annotations

import datetime as dt
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from .base import BaseProvider, DataProviderError


# Public NEX-GDDP-CMIP6 bucket (anonymous read via HTTPS)
_NEX_BASE = "https://nex-gddp-cmip6.s3-us-west-2.amazonaws.com"
_NEX_VERSION = "NEX-GDDP-CMIP6"
_NEX_SUFFIX = "v2.0"


class NEXGDDPProvider(BaseProvider):
    """Extracts NASA NEX-GDDP-CMIP6 climate projection data.
    
    This provider is generalized from CeresPINN's nex_gddp.py to work with
    ML Lab's provider architecture. It downloads climate projections for
    configurable scenarios, models, variables, and time windows.
    """
    
    name = "nex-gddp"
    
    def __init__(self, config: Any, progress: Optional[Any] = None) -> None:
        """Initialize the NEX-GDDP provider.
        
        Args:
            config: Configuration with scenarios, models, variables, and time window
            progress: Optional callback for progress reporting
        """
        super().__init__(config, progress)
        
        self.out_dir = getattr(config, "output_dir", Path.cwd() / "data" / "nex_gddp")
        
        # Configuration
        self.scenarios = getattr(config, "scenarios", ["historical", "ssp245", "ssp585"])
        self.models = getattr(config, "models", ["ACCESS-CM2", "CNRM-ESM2-1", "MIROC6"])
        self.variables = getattr(config, "variables", ["tasmax", "tasmin", "pr"])
        self.start_year = getattr(config, "start_year", 2015)
        self.end_year = getattr(config, "end_year", 2025)
        
        # Study area
        self.lat_min = getattr(config, "lat_min", None)
        self.lat_max = getattr(config, "lat_max", None)
        self.lon_min = getattr(config, "lon_min", None)
        self.lon_max = getattr(config, "lon_max", None)
    
    def _build_url(
        self, model: str, scenario: str, variable: str, year: int
    ) -> str:
        """Build the download URL for a specific file.
        
        Args:
            model: GCM model name
            scenario: SSP scenario
            variable: Climate variable (tasmax, tasmin, pr)
            year: Year
        
        Returns:
            Download URL
        """
        # NEX-GDDP file naming convention:
        # {variable}_day_{model}_{scenario}_r1i1p1f1_gn_{year}_v2.0.nc
        filename = f"{variable}_day_{model}_{scenario}_r1i1p1f1_gn_{year}_{_NEX_SUFFIX}.nc"
        return f"{_NEX_BASE}/{_NEX_VERSION}/{model}/{scenario}/r1i1p1f1/{variable}/{filename}"
    
    def extract(self) -> Dict[str, Any]:
        """Extract NEX-GDDP data for the configured parameters.
        
        Returns:
            Dictionary with extraction results
        """
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = 0
        failed = 0
        total_files = len(self.scenarios) * len(self.models) * len(self.variables) * (self.end_year - self.start_year + 1)
        
        self.log_step(f"Downloading {total_files} NEX-GDDP files")
        
        file_num = 0
        for scenario in self.scenarios:
            for model in self.models:
                for variable in self.variables:
                    for year in range(self.start_year, self.end_year + 1):
                        file_num += 1
                        self.set_progress(file_num, total_files, f"Downloading {scenario}/{model}/{variable}/{year}")
                        
                        # Create subdirectory structure
                        scenario_dir = self.out_dir / scenario / model / variable
                        scenario_dir.mkdir(parents=True, exist_ok=True)
                        
                        filename = f"{variable}_day_{model}_{scenario}_r1i1p1f1_gn_{year}_{_NEX_SUFFIX}.nc"
                        file_path = scenario_dir / filename
                        
                        if file_path.exists():
                            self.log_step(f"File already exists: {filename}")
                            downloaded += 1
                            continue
                        
                        try:
                            url = self._build_url(model, scenario, variable, year)
                            self.log_step(f"Downloading {url}")
                            
                            response = requests.get(url, timeout=60)
                            response.raise_for_status()
                            
                            with open(file_path, "wb") as f:
                                f.write(response.content)
                            
                            downloaded += 1
                            self.throttled()  # Be polite to the API
                            
                        except Exception as e:
                            self.log_step(f"Failed to download {filename}: {e}")
                            failed += 1
        
        # Write manifest
        manifest = self.write_manifest(
            self.out_dir,
            downloaded,
            extra={
                "scenarios": self.scenarios,
                "models": self.models,
                "variables": self.variables,
                "year_range": f"{self.start_year}-{self.end_year}",
                "failed": failed,
                "study_area": {
                    "lat_min": self.lat_min,
                    "lat_max": self.lat_max,
                    "lon_min": self.lon_min,
                    "lon_max": self.lon_max,
                },
            },
        )
        
        return {
            "downloaded": downloaded,
            "failed": failed,
            "output_dir": str(self.out_dir),
            "manifest": str(manifest),
        }
    
    def load(self) -> pd.DataFrame:
        """Load NEX-GDDP metadata as a pandas DataFrame.
        
        For NEX-GDDP, this loads the manifest and returns metadata.
        Actual NetCDF processing would require xarray/netCDF4.
        
        Returns:
            DataFrame with NEX-GDDP metadata
        """
        manifest_path = self.out_dir / f"{self.name}_manifest.json"
        
        if not manifest_path.exists():
            raise DataProviderError(f"Manifest not found: {manifest_path}")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        # Return manifest as a single-row DataFrame
        return pd.DataFrame([manifest])
