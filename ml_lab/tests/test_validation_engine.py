"""Tests for Validation Engine.

This module contains tests for the ValidationEngine component.
"""
from __future__ import annotations

import pytest
import numpy as np
from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from engines.validation_engine import ValidationEngine, ValidationConfig


@pytest.fixture
def validation_config():
    """Create a ValidationConfig instance for testing."""
    return ValidationConfig(
        strategy="k_fold",
        n_splits=5,
        random_state=42,
    )


@pytest.fixture
def validation_engine(validation_config):
    """Create a ValidationEngine instance for testing."""
    return ValidationEngine(config=validation_config)


@pytest.fixture
def regression_data():
    """Create sample regression data."""
    X, y = make_regression(n_samples=100, n_features=5, noise=0.1, random_state=42)
    return X, y


@pytest.fixture
def classification_data():
    """Create sample classification data."""
    X, y = make_classification(n_samples=100, n_features=5, n_classes=2, random_state=42)
    return X, y


def test_validate_model_regression(validation_engine, regression_data):
    """Test validating a regression model."""
    X, y = regression_data
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    
    result = validation_engine.validate_model(
        model=model,
        X=X,
        y=y,
        problem_type="regression",
    )
    
    assert result is not None
    assert result.metrics is not None
    assert len(result.fold_metrics) == validation_engine.config.n_splits


def test_validate_model_classification(validation_engine, classification_data):
    """Test validating a classification model."""
    X, y = classification_data
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    result = validation_engine.validate_model(
        model=model,
        X=X,
        y=y,
        problem_type="classification",
    )
    
    assert result is not None
    assert result.metrics is not None
    assert len(result.fold_metrics) == validation_engine.config.n_splits


def test_validate_multiple_models(validation_engine, regression_data):
    """Test validating multiple models."""
    X, y = regression_data
    models = {
        "model1": RandomForestRegressor(n_estimators=10, random_state=42),
        "model2": RandomForestRegressor(n_estimators=5, random_state=42),
    }
    
    results = validation_engine.validate_multiple_models(
        models=models,
        X=X,
        y=y,
        problem_type="regression",
    )
    
    assert results is not None
    assert len(results) == 2
    assert "model1" in results
    assert "model2" in results


def test_train_test_split_strategy():
    """Test train_test_split validation strategy."""
    config = ValidationConfig(strategy="train_test_split", test_size=0.2, random_state=42)
    engine = ValidationEngine(config=config)
    
    X, y = make_regression(n_samples=100, n_features=5, random_state=42)
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    
    result = engine.validate_model(model, X, y, "regression")
    
    assert result is not None
    assert result.metrics is not None


def test_stratified_k_fold_strategy():
    """Test stratified k-fold validation strategy."""
    config = ValidationConfig(strategy="stratified_k_fold", n_splits=3, random_state=42)
    engine = ValidationEngine(config=config)
    
    X, y = make_classification(n_samples=100, n_features=5, n_classes=2, random_state=42)
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    result = engine.validate_model(model, X, y, "classification")
    
    assert result is not None
    assert result.metrics is not None


def test_validation_config_defaults():
    """Test ValidationConfig default values."""
    config = ValidationConfig()
    
    assert config.strategy == "k_fold"
    assert config.n_splits == 5
    assert config.random_state == 42


def test_cross_validation_metrics(validation_engine, regression_data):
    """Test that cross-validation metrics are computed correctly."""
    X, y = regression_data
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    
    result = validation_engine.validate_model(model, X, y, "regression")
    
    # Check that fold metrics exist
    assert len(result.fold_metrics) > 0
    
    # Check that mean and std are computed
    for metric_name, metric_values in result.metrics.items():
        assert "mean" in metric_values
        assert "std" in metric_values
        assert "min" in metric_values
        assert "max" in metric_values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
