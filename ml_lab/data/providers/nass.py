"""USDA NASS data provider for ML Lab.

This module provides a generalized USDA NASS QuickStats data provider adapted from
CeresPINN for use in ML Lab. It fetches agricultural data from the USDA NASS API.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from .base import BaseProvider, DataProviderError


_NASS_API = "https://quickstats.nass.usda.gov/api/api_GET/"


class NASSProvider(BaseProvider):
    """Fetches agricultural data from USDA NASS QuickStats.
    
    This provider is generalized from CeresPINN's nass.py to work with
    ML Lab's provider architecture. It fetches data based on configurable
    parameters for commodity, statistic category, geographic level, etc.
    """
    
    name = "usda-nass"
    
    def __init__(self, config: Any, progress: Optional[Any] = None) -> None:
        """Initialize the NASS provider.
        
        Args:
            config: Configuration with API key and query parameters
            progress: Optional callback for progress reporting
        """
        super().__init__(config, progress)
        
        self.out_dir = getattr(config, "output_dir", Path.cwd() / "data" / "nass")
        self.api_key = getattr(config, "api_key", None)
        
        # Query parameters
        self.source_desc = getattr(config, "source_desc", "SURVEY")
        self.sector_desc = getattr(config, "sector_desc", "CROPS")
        self.commodity_desc = getattr(config, "commodity_desc", "CORN")
        self.statisticcat_desc = getattr(config, "statisticcat_desc", "YIELD")
        self.agg_level_desc = getattr(config, "agg_level_desc", "COUNTY")
        self.unit_desc = getattr(config, "unit_desc", "BU / ACRE")
        self.year_ge = getattr(config, "year_ge", 1990)
        self.year_le = getattr(config, "year_le", 2024)
        self.state_fips = getattr(config, "state_fips", None)
    
    def _build_params(self) -> Dict[str, Any]:
        """Build API request parameters.
        
        Returns:
            Dictionary of API parameters
        """
        params: Dict[str, Any] = {
            "key": self.api_key,
            "source_desc": self.source_desc,
            "sector_desc": self.sector_desc,
            "commodity_desc": self.commodity_desc,
            "statisticcat_desc": self.statisticcat_desc,
            "agg_level_desc": self.agg_level_desc,
            "unit_desc": self.unit_desc,
            "format": "JSON",
            "year__GE": self.year_ge,
            "year__LE": self.year_le,
        }
        
        if self.state_fips:
            params["state_fips"] = self.state_fips
        
        return params
    
    def extract(self) -> Dict[str, Any]:
        """Extract data from USDA NASS API.
        
        Returns:
            Dictionary with extraction results
        """
        if self.api_key is None:
            raise DataProviderError("API key not provided")
        
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_step("Fetching data from USDA NASS QuickStats")
        
        try:
            params = self._build_params()
            self.log_step(f"Request parameters: {params}")
            
            response = requests.get(_NASS_API, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                raise DataProviderError("No data returned from API")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Save to file
            output_path = self.out_dir / "nass_data.csv"
            df.to_csv(output_path, index=False)
            
            self.log_step(f"Saved {len(df)} records to {output_path}")
            
            # Write manifest
            manifest = self.write_manifest(
                self.out_dir,
                len(df),
                extra={
                    "commodity": self.commodity_desc,
                    "statistic": self.statisticcat_desc,
                    "year_range": f"{self.year_ge}-{self.year_le}",
                    "columns": list(df.columns),
                },
            )
            
            return {
                "records": len(df),
                "columns": len(df.columns),
                "output_path": str(output_path),
                "manifest": str(manifest),
            }
            
        except requests.exceptions.RequestException as e:
            raise DataProviderError(f"API request failed: {e}")
        except Exception as e:
            raise DataProviderError(f"Data extraction failed: {e}")
    
    def load(self) -> pd.DataFrame:
        """Load NASS data from disk.
        
        Returns:
            DataFrame with NASS data
        """
        data_path = self.out_dir / "nass_data.csv"
        
        if not data_path.exists():
            raise DataProviderError(f"Data file not found: {data_path}")
        
        return pd.read_csv(data_path)
