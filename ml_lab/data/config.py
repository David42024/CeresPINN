"""Data configuration for ML Lab data providers.

This module provides configuration classes for data providers, allowing
centralized management of data source settings and parameters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExtractionConfig:
    """Configuration for data extraction operations."""
    dry_run: bool = False
    output_dir: Optional[Path] = None
    overwrite: bool = False


@dataclass
class CHIRPSConfig:
    """Configuration for CHIRPS data provider."""
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "data" / "chirps")
    days_back: int = 5
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None


@dataclass
class NASSConfig:
    """Configuration for USDA NASS data provider."""
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "data" / "nass")
    api_key: Optional[str] = None
    source_desc: str = "SURVEY"
    sector_desc: str = "CROPS"
    commodity_desc: str = "CORN"
    statisticcat_desc: str = "YIELD"
    agg_level_desc: str = "COUNTY"
    unit_desc: str = "BU / ACRE"
    year_ge: int = 1990
    year_le: int = 2024
    state_fips: Optional[str] = None


@dataclass
class NEXGDDPConfig:
    """Configuration for NASA NEX-GDDP data provider."""
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "data" / "nex_gddp")
    scenarios: List[str] = field(default_factory=lambda: ["historical", "ssp245", "ssp585"])
    models: List[str] = field(default_factory=lambda: ["ACCESS-CM2", "CNRM-ESM2-1", "MIROC6"])
    variables: List[str] = field(default_factory=lambda: ["tasmax", "tasmin", "pr"])
    start_year: int = 2015
    end_year: int = 2025
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None


@dataclass
class GenericConfig:
    """Configuration for generic file-based data provider."""
    file_path: Path
    output_dir: Optional[Path] = None


@dataclass
class DataConfig:
    """Main configuration for all data providers."""
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    chirps: CHIRPSConfig = field(default_factory=CHIRPSConfig)
    nass: NASSConfig = field(default_factory=NASSConfig)
    nex_gddp: NEXGDDPConfig = field(default_factory=NEXGDDPConfig)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataConfig":
        """Create configuration from dictionary."""
        extraction = ExtractionConfig(**data.get("extraction", {}))
        chirps = CHIRPSConfig(**data.get("chirps", {}))
        nass = NASSConfig(**data.get("nass", {}))
        nex_gddp = NEXGDDPConfig(**data.get("nex_gddp", {}))
        
        return cls(
            extraction=extraction,
            chirps=chirps,
            nass=nass,
            nex_gddp=nex_gddp,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        from dataclasses import asdict
        return asdict(self)
