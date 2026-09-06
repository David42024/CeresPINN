"""CHIRPS precipitation data provider for ML Lab.

This module provides a generalized CHIRPS data provider adapted from
CeresPINN for use in ML Lab. It downloads CHIRPS daily precipitation
GeoTIFFs for a specified study area and time window.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from .base import BaseProvider, DataProviderError


_CHIRPS_BASE = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05"


class CHIRPSProvider(BaseProvider):
    """Downloads CHIRPS daily precipitation GeoTIFFs for the study window.
    
    This provider is generalized from CeresPINN's chirps.py to work with
    ML Lab's provider architecture. It downloads precipitation data for
    a configurable time window and geographic area.
    """
    
    name = "chirps"
    
    def __init__(self, config: Any, progress: Optional[Any] = None) -> None:
        """Initialize the CHIRPS provider.
        
        Args:
            config: Configuration with study area and time window
            progress: Optional callback for progress reporting
        """
        super().__init__(config, progress)
        
        # Configuration attributes
        self.out_dir = getattr(config, "output_dir", Path.cwd() / "data" / "chirps")
        self.days_back = getattr(config, "days_back", 5)
        self.start_date = getattr(config, "start_date", None)
        self.end_date = getattr(config, "end_date", None)
        
        # Study area (bounding box)
        self.lat_min = getattr(config, "lat_min", None)
        self.lat_max = getattr(config, "lat_max", None)
        self.lon_min = getattr(config, "lon_min", None)
        self.lon_max = getattr(config, "lon_max", None)
    
    def _file_name(self, day: dt.date) -> str:
        """Generate CHIRPS file name for a given date.
        
        Args:
            day: Date to generate file name for
        
        Returns:
            CHIRPS file name
        """
        return f"chirps-v2.0.{day.year}.{day.month:02d}.{day.day:02d}.tif"
    
    def _url(self, day: dt.date) -> str:
        """Generate CHIRPS download URL for a given date.
        
        Args:
            day: Date to generate URL for
        
        Returns:
            CHIRPS download URL
        """
        return f"{_CHIRPS_BASE}/{day.year}/{self._file_name(day)}"
    
    def _get_date_range(self) -> List[dt.date]:
        """Get the date range for data extraction.
        
        Returns:
            List of dates to download
        """
        if self.start_date and self.end_date:
            start = pd.to_datetime(self.start_date).date()
            end = pd.to_datetime(self.end_date).date()
            return [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
        else:
            # Default to recent window
            end_date = dt.date.today()
            start_date = end_date - dt.timedelta(days=self.days_back)
            return [start_date + dt.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    
    def extract(self) -> Dict[str, Any]:
        """Extract CHIRPS data for the configured date range.
        
        Returns:
            Dictionary with extraction results
        """
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        dates = self._get_date_range()
        downloaded = 0
        failed = 0
        
        self.log_step(f"Downloading CHIRPS data for {len(dates)} days")
        
        for i, day in enumerate(dates):
            self.set_progress(i + 1, len(dates), f"Downloading {day}")
            
            file_name = self._file_name(day)
            file_path = self.out_dir / file_name
            
            if file_path.exists():
                self.log_step(f"File already exists: {file_name}")
                downloaded += 1
                continue
            
            try:
                url = self._url(day)
                self.log_step(f"Downloading {url}")
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                downloaded += 1
                self.throttled()  # Be polite to the API
                
            except Exception as e:
                self.log_step(f"Failed to download {file_name}: {e}")
                failed += 1
        
        # Write manifest
        manifest = self.write_manifest(
            self.out_dir,
            downloaded,
            extra={
                "date_range": f"{dates[0]} to {dates[-1]}",
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
        """Load CHIRPS data as a pandas DataFrame.
        
        For CHIRPS, this loads the manifest and returns metadata.
        Actual GeoTIFF processing would require xarray/rasterio.
        
        Returns:
            DataFrame with CHIRPS metadata
        """
        manifest_path = self.out_dir / f"{self.name}_manifest.json"
        
        if not manifest_path.exists():
            raise DataProviderError(f"Manifest not found: {manifest_path}")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        # Return manifest as a single-row DataFrame
        return pd.DataFrame([manifest])
