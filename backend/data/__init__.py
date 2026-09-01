"""CeresPINN data extraction pipelines.

Modular providers for the three scientific datasets:
  - CHIRPS        (UCSB precipitation, GeoTIFF)
  - USDA NASS     (maize county-level yields, QuickStats API)
  - NASA NEX-GDDP (CMIP6 climate projections, NetCDF)
"""
from .config import Settings, settings
from .provider_base import BaseProvider, ExtractionError
from .chirps import CHIRPSProvider
from .nass import NASSProvider
from .nex_gddp import NEXGDDPProvider

__all__ = [
    "Settings",
    "settings",
    "BaseProvider",
    "ExtractionError",
    "CHIRPSProvider",
    "NASSProvider",
    "NEXGDDPProvider",
]
