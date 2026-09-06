"""Tabular models for ML Lab.

This module provides implementations of common tabular ML models including
linear models, tree-based models, and ensemble methods.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR

from core.model_catalog import BaseModel


class LogisticRegressionModel(BaseModel):
    """Logistic Regression model for classification."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = LogisticRegression(**self.hyperparameters, max_iter=1000)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self):
        """Get feature importance (coefficients)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return np.abs(self.model.coef_[0])


class LinearRegressionModel(BaseModel):
    """Linear Regression model for regression."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = LinearRegression(**self.hyperparameters)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance (coefficients)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return np.abs(self.model.coef_)


class RidgeModel(BaseModel):
    """Ridge Regression model for regression."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = Ridge(**self.hyperparameters)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance (coefficients)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return np.abs(self.model.coef_)


class LassoModel(BaseModel):
    """Lasso Regression model for regression."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = Lasso(**self.hyperparameters, max_iter=1000)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance (coefficients)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return np.abs(self.model.coef_)


class RandomForestClassifierModel(BaseModel):
    """Random Forest model for classification."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = RandomForestClassifier(**self.hyperparameters, random_state=42)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self):
        """Get feature importance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return self.model.feature_importances_


class RandomForestRegressorModel(BaseModel):
    """Random Forest model for regression."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = RandomForestRegressor(**self.hyperparameters, random_state=42)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return self.model.feature_importances_


class GradientBoostingClassifierModel(BaseModel):
    """Gradient Boosting model for classification."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = GradientBoostingClassifier(**self.hyperparameters, random_state=42)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self):
        """Get feature importance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return self.model.feature_importances_


class GradientBoostingRegressorModel(BaseModel):
    """Gradient Boosting model for regression."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = GradientBoostingRegressor(**self.hyperparameters, random_state=42)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return self.model.feature_importances_


class SVMClassifierModel(BaseModel):
    """Support Vector Machine model for classification."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = SVC(**self.hyperparameters, probability=True, random_state=42)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self):
        """Get feature importance (not available for SVM)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        # SVM doesn't have direct feature importance
        return None


class SVMRegressorModel(BaseModel):
    """Support Vector Machine model for regression."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        self.model = SVR(**self.hyperparameters)
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance (not available for SVM)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return None


class XGBoostClassifierModel(BaseModel):
    """XGBoost model for classification."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        try:
            import xgboost as xgb
            self.model = xgb.XGBClassifier(**self.hyperparameters, random_state=42)
        except ImportError:
            raise ImportError("XGBoost is not installed. Install with: pip install xgboost")
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self):
        """Get feature importance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return self.model.feature_importances_


class XGBoostRegressorModel(BaseModel):
    """XGBoost model for regression."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(hyperparameters)
        try:
            import xgboost as xgb
            self.model = xgb.XGBRegressor(**self.hyperparameters, random_state=42)
        except ImportError:
            raise ImportError("XGBoost is not installed. Install with: pip install xgboost")
    
    def fit(self, X, y):
        """Fit the model to training data."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities (not applicable for regression)."""
        return None
    
    def get_feature_importance(self):
        """Get feature importance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        return self.model.feature_importances_
