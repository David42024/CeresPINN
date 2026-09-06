"""Engines module for ML Lab.

This module provides engine implementations including:
- Training Engine - Generic model training
- Validation Engine - Dynamic cross-validation
- Statistical Engine - Generalized statistical tests
"""
from .statistical_engine import StatisticalEngine, StatisticalTest, get_statistical_engine
from .training_engine import TrainingConfig, TrainingEngine, TrainingResult
from .validation_engine import (
    ValidationConfig,
    ValidationEngine,
    ValidationResult,
)

__all__ = [
    # Training
    "TrainingConfig",
    "TrainingEngine",
    "TrainingResult",
    # Validation
    "ValidationConfig",
    "ValidationEngine",
    "ValidationResult",
    # Statistical
    "StatisticalEngine",
    "StatisticalTest",
    # Helpers
    "get_statistical_engine",
]
