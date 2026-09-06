"""Models module for ML Lab.

This module provides model implementations including:
- PINN (Physics-Informed Neural Network)
- Tabular models (linear, tree-based, ensemble)
- Neural networks (MLP)
- Specialized models (CeresPINN wrapper)
"""
from .catalog.neural import MLPClassifier, MLPRegressor
from .catalog.specialized import CeresPINNModel, GenericPINNModel
from .catalog.tabular import (
    GradientBoostingClassifierModel,
    GradientBoostingRegressorModel,
    LassoModel,
    LinearRegressionModel,
    LogisticRegressionModel,
    RandomForestClassifierModel,
    RandomForestRegressorModel,
    RidgeModel,
    SVMClassifierModel,
    SVMRegressorModel,
    XGBoostClassifierModel,
    XGBoostRegressorModel,
)
from .pinn import CeresPINN, GenericPINN, PINNConfig, cerespinn_physics_loss, generic_physics_loss

__all__ = [
    # PINN
    "CeresPINN",
    "GenericPINN",
    "PINNConfig",
    "cerespinn_physics_loss",
    "generic_physics_loss",
    # Tabular models
    "LogisticRegressionModel",
    "LinearRegressionModel",
    "RidgeModel",
    "LassoModel",
    "RandomForestClassifierModel",
    "RandomForestRegressorModel",
    "GradientBoostingClassifierModel",
    "GradientBoostingRegressorModel",
    "SVMClassifierModel",
    "SVMRegressorModel",
    "XGBoostClassifierModel",
    "XGBoostRegressorModel",
    # Neural networks
    "MLPClassifier",
    "MLPRegressor",
    # Specialized
    "CeresPINNModel",
    "GenericPINNModel",
]
