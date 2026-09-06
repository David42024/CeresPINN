"""Tests for Training Engine.

This module contains tests for the TrainingEngine component.
"""
from __future__ import annotations

import pytest
import numpy as np
from sklearn.datasets import make_classification, make_regression

from engines.training_engine import TrainingEngine, TrainingConfig


@pytest.fixture
def training_config():
    """Create a TrainingConfig instance for testing."""
    return TrainingConfig(
        random_state=42,
        test_size=0.2,
        validation_strategy="train_test_split",
        scale_features=True,
        save_best_model=False,
        save_training_history=False,
    )


@pytest.fixture
def training_engine(training_config):
    """Create a TrainingEngine instance for testing."""
    return TrainingEngine(config=training_config)


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


def test_train_model_regression(training_engine, regression_data):
    """Test training a regression model."""
    X, y = regression_data
    
    result = training_engine.train_model(
        model_name="random_forest",
        X=X,
        y=y,
        feature_names=["f1", "f2", "f3", "f4", "f5"],
        target_name="target",
    )
    
    assert result is not None
    assert result.model is not None
    assert result.metrics is not None
    assert len(result.metrics) > 0


def test_train_model_classification(training_engine, classification_data):
    """Test training a classification model."""
    X, y = classification_data
    
    result = training_engine.train_model(
        model_name="random_forest",
        X=X,
        y=y,
        feature_names=["f1", "f2", "f3", "f4", "f5"],
        target_name="target",
    )
    
    assert result is not None
    assert result.model is not None
    assert result.metrics is not None


def test_train_multiple_models(training_engine, regression_data):
    """Test training multiple models."""
    X, y = regression_data
    
    results = training_engine.train_multiple_models(
        model_names=["random_forest", "linear_regression"],
        X=X,
        y=y,
        feature_names=["f1", "f2", "f3", "f4", "f5"],
        target_name="target",
    )
    
    assert results is not None
    assert len(results) == 2
    assert "random_forest" in results
    assert "linear_regression" in results


def test_preprocessing_scaling(training_engine, regression_data):
    """Test feature scaling during preprocessing."""
    X, y = regression_data
    
    training_engine.config.scale_features = True
    training_engine.config.scaling_method = "standard"
    
    result = training_engine.train_model(
        model_name="linear_regression",
        X=X,
        y=y,
    )
    
    assert result is not None
    assert training_engine.scaler is not None


def test_hyperparameters(training_engine, regression_data):
    """Test training with custom hyperparameters."""
    X, y = regression_data
    
    hyperparameters = {"n_estimators": 10, "max_depth": 3}
    
    result = training_engine.train_model(
        model_name="random_forest",
        X=X,
        y=y,
        hyperparameters=hyperparameters,
    )
    
    assert result is not None
    assert result.metadata["hyperparameters"] == hyperparameters


def test_invalid_model(training_engine, regression_data):
    """Test training with invalid model name."""
    X, y = regression_data
    
    with pytest.raises(ValueError):
        training_engine.train_model(
            model_name="invalid_model_name",
            X=X,
            y=y,
        )


def test_training_config_defaults():
    """Test TrainingConfig default values."""
    config = TrainingConfig()
    
    assert config.random_state == 42
    assert config.test_size == 0.2
    assert config.validation_strategy == "train_test_split"
    assert config.scale_features is True
    assert config.scaling_method == "standard"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
