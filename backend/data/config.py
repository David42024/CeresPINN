"""Centralized configuration for CeresPINN data extraction pipelines.

Coordinates, time windows and dataset-specific parameters are consolidated here so
each provider (CHIRPS, USDA NASS, NASA NEX-GDDP) reads from a single source of truth.
Everything can be overridden via environment variables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
@dataclass
class Paths:
    """Filesystem layout for raw and processed data artifacts."""

    base_dir: Path

    @property
    def raw(self) -> Path:
        path = Path(os.getenv("CERESPINN_RAW_DIR", self.base_dir / "raw"))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def processed(self) -> Path:
        path = Path(os.getenv("CERESPINN_PROCESSED_DIR", self.base_dir / "processed"))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chirps(self) -> Path:
        path = self.raw / "chirps"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def nass(self) -> Path:
        path = self.raw / "nass"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def nex(self) -> Path:
        path = self.raw / "nex-gddp"
        path.mkdir(parents=True, exist_ok=True)
        return path


def default_paths() -> Paths:
    """Create Paths rooted at the backend directory."""
    base = Path(os.getenv("CERESPINN_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
    return Paths(base_dir=base)


# ---------------------------------------------------------------------------
# Study area (default: Bajío region, Mexico — Celaya, Guanajuato)
# ---------------------------------------------------------------------------
@dataclass
class StudyArea:
    """Bounding box and reference point of the simulation area."""

    name: str = "Bajio-Mexico"
    min_lat: float = 19.5
    max_lat: float = 21.5
    min_lon: float = -102.0
    max_lon: float = -99.5
    # Reference point used for point-sample extractions (CMIP6, CHIRPS)
    ref_lat: float = 20.5222   # Celaya, Guanajuato
    ref_lon: float = -100.8123

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        return (self.min_lon, self.min_lat, self.max_lon, self.max_lat)


# ---------------------------------------------------------------------------
# Temporal / scenario configuration
# ---------------------------------------------------------------------------
@dataclass
class TimeConfig:
    """Historical and projection windows plus the CMIP6 scenarios of interest."""

    historical_start: int = 1990
    historical_end: int = 2025
    projection_start: int = 2015
    projection_end: int = 2050
    # CMIP6 SSP scenarios surfaced in the UI
    scenarios: List[str] = field(
        default_factory=lambda: ["ssp126", "ssp370", "ssp585"]
    )
    # Subset of CMIP6 ensemble members (NASA NEX-GDDP) to avoid downloading 32 models.
    # Keyed by SSP -> list of model ids.
    ensemble_members: dict = field(
        default_factory=lambda: {
            "ssp126": ["ACCESS-ESM1-5", "CanESM5", "CESM2", "EC-Earth3", "MIROC6", "MPI-ESM1-2-LR", "MRI-ESM2-0"],
            "ssp370": ["ACCESS-ESM1-5", "CanESM5", "CESM2", "EC-Earth3", "MIROC6", "MPI-ESM1-2-LR", "MRI-ESM2-0"],
            "ssp585": ["ACCESS-ESM1-5", "CanESM5", "CESM2", "EC-Earth3", "MIROC6", "MPI-ESM1-2-LR", "MRI-ESM2-0"],
        }
    )
    # CMIP6 variables to extract per projection day
    cmip6_variables: List[str] = field(
        default_factory=lambda: ["pr", "tasmax", "tasmin", "rsds", "huss"]
    )


# ---------------------------------------------------------------------------
# USDA NASS
# ---------------------------------------------------------------------------
@dataclass
class NASSConfig:
    """USDA NASS QuickStats query parameters (maize harvest yield)."""

    api_key: str = field(
        default_factory=lambda: os.getenv("NASS_API_KEY", "")
    )
    source_desc: str = "SURVEY"
    sector_desc: str = "CROPS"
    commodity_desc: str = "CORN"
    class_desc: str = "ALL CLASSES"
    reference_period_desc: str = "YEAR"
    statisticcat_desc: str = "YIELD"
    agg_level_desc: str = "COUNTY"
    unit_desc: str = "BU / ACRE"
    year: str = ""
    state_alpha: str = field(
        default_factory=lambda: os.getenv("NASS_STATE_ALPHA", "")
    )


# ---------------------------------------------------------------------------
# Runtime switch: dry-run (no network) vs real extraction
# ---------------------------------------------------------------------------
@dataclass
class ExtractionConfig:
    """Global switches shared by every provider."""

    dry_run: bool = os.getenv("CERESPINN_DRY_RUN", "1") == "1"
    max_points: int = int(os.getenv("CERESPINN_MAX_POINTS", "5"))
    timeout_seconds: int = int(os.getenv("CERESPINN_TIMEOUT", "60"))


# ---------------------------------------------------------------------------
# Aggregate access
# ---------------------------------------------------------------------------
class Settings:
    """Thin facade bundling all configuration objects."""

    def __init__(self) -> None:
        self.paths = default_paths()
        self.area = StudyArea()
        self.time = TimeConfig()
        self.nass = NASSConfig()
        self.extraction = ExtractionConfig()


settings = Settings()
