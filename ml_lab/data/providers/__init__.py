"""Data providers module for ML Lab.

This module provides data providers for various data sources including
generic file formats (CSV, Parquet, JSON, Excel) and specialized sources
like CHIRPS, USDA NASS, and NASA NEX-GDDP.
"""
from .base import BaseProvider, DataProviderError, GenericProvider
from .chirps import CHIRPSProvider
from .config import (
    CHIRPSConfig,
    DataConfig,
    ExtractionConfig,
    GenericConfig,
    NASSConfig,
    NEXGDDPConfig,
)
from .nass import NASSProvider
from .nex_gddp import NEXGDDPProvider

__all__ = [
    # Base classes
    "BaseProvider",
    "DataProviderError",
    "GenericProvider",
    # Configuration
    "DataConfig",
    "ExtractionConfig",
    "CHIRPSConfig",
    "NASSConfig",
    "NEXGDDPConfig",
    "GenericConfig",
    # Providers
    "CHIRPSProvider",
    "NASSProvider",
    "NEXGDDPProvider",
]
