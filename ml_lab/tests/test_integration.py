"""End-to-end integration tests for ML Lab.

This module contains integration tests that test the complete workflow
from project creation to model training and validation.
"""
from __future__ import annotations

import pytest
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification, make_regression

from core.project_analyzer import ProjectAnalyzer
from core.dataset_analyzer import DatasetAnalyzer
from engines.training_engine import TrainingEngine, TrainingConfig
from engines.validation_engine import ValidationEngine, ValidationConfig
from engines.statistical_engine import StatisticalEngine


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for integration testing."""
    X, y = make_regression(n_samples=200, n_features=5, noise=0.1, random_state=42)
    df = pd.DataFrame(X, columns=["feature1", "feature2", "feature3", "feature4", "feature5"])
    df["target"] = y
    return df


def test_full_workflow_regression(sample_dataset):
    """Test complete workflow for regression problem."""
    # Step 1: Analyze context
    project_analyzer = ProjectAnalyzer()
    context = "Predict crop yield based on weather and soil data"
    context_result = project_analyzer.analyze_context(context)
    
    # Step 2: Create project
    project = project_analyzer.create_project(
        project_name="Crop Yield Prediction",
        description="Predict crop yield using ML",
        domain="agriculture",
        context_analysis=context_result,
    )
    
    assert project is not None
    assert project.problem_type.value == "regression"
    
    # Step 3: Analyze dataset
    dataset_analyzer = DatasetAnalyzer()
    profile = dataset_analyzer.analyze_tabular(sample_dataset)
    
    assert profile is not None
    assert profile.rows == 200
    assert profile.columns == 6
    
    # Step 4: Train model
    training_config = TrainingConfig(random_state=42, test_size=0.2)
    training_engine = TrainingEngine(config=training_config)
    
    X = sample_dataset.drop("target", axis=1).values
    y = sample_dataset["target"].values
    
    training_result = training_engine.train_model(
        model_name="random_forest",
        X=X,
        y=y,
        feature_names=profile.numerical_features,
        target_name="target",
    )
    
    assert training_result is not None
    assert training_result.model is not None
    assert len(training_result.metrics) > 0
    
    # Step 5: Validate model
    validation_config = ValidationConfig(strategy="k_fold", n_splits=3, random_state=42)
    validation_engine = ValidationEngine(config=validation_config)
    
    validation_result = validation_engine.validate_model(
        model=training_result.model,
        X=X,
        y=y,
        problem_type="regression",
    )
    
    assert validation_result is not None
    assert len(validation_result.fold_metrics) == 3
    
    # Step 6: Statistical tests
    statistical_engine = StatisticalEngine()
    
    # Compare with baseline
    baseline_predictions = np.random.randn(len(y))
    model_predictions = training_result.model.predict(X)
    
    test_result = statistical_engine.run_test(
        test_name="paired_t_test",
        sample1=y,
        sample2=model_predictions,
    )
    
    assert test_result is not None
    assert "p_value" in test_result


def test_full_workflow_classification():
    """Test complete workflow for classification problem."""
    # Step 1: Analyze context
    project_analyzer = ProjectAnalyzer()
    context = "Classify crops as healthy or diseased based on sensor data"
    context_result = project_analyzer.analyze_context(context)
    
    # Step 2: Create project
    project = project_analyzer.create_project(
        project_name="Crop Disease Classification",
        description="Classify crop health",
        domain="agriculture",
        context_analysis=context_result,
    )
    
    assert project is not None
    assert project.problem_type.value == "binary_classification"
    
    # Step 3: Create dataset
    X, y = make_classification(n_samples=200, n_features=5, n_classes=2, random_state=42)
    df = pd.DataFrame(X, columns=["sensor1", "sensor2", "sensor3", "sensor4", "sensor5"])
    df["target"] = y
    
    # Step 4: Analyze dataset
    dataset_analyzer = DatasetAnalyzer()
    profile = dataset_analyzer.analyze_tabular(df)
    
    assert profile is not None
    
    # Step 5: Train model
    training_config = TrainingConfig(random_state=42, test_size=0.2)
    training_engine = TrainingEngine(config=training_config)
    
    X_data = df.drop("target", axis=1).values
    y_data = df["target"].values
    
    training_result = training_engine.train_model(
        model_name="random_forest",
        X=X_data,
        y=y_data,
        feature_names=profile.numerical_features,
        target_name="target",
    )
    
    assert training_result is not None
    
    # Step 6: Validate model
    validation_config = ValidationConfig(strategy="stratified_k_fold", n_splits=3, random_state=42)
    validation_engine = ValidationEngine(config=validation_config)
    
    validation_result = validation_engine.validate_model(
        model=training_result.model,
        X=X_data,
        y=y_data,
        problem_type="classification",
    )
    
    assert validation_result is not None


def test_multi_model_comparison(sample_dataset):
    """Test training and comparing multiple models."""
    # Setup
    project_analyzer = ProjectAnalyzer()
    context = "Predict crop yield"
    context_result = project_analyzer.analyze_context(context)
    project = project_analyzer.create_project(
        project_name="Model Comparison",
        description="Compare multiple models",
        domain="test",
        context_analysis=context_result,
    )
    
    # Prepare data
    X = sample_dataset.drop("target", axis=1).values
    y = sample_dataset["target"].values
    
    # Train multiple models
    training_config = TrainingConfig(random_state=42)
    training_engine = TrainingEngine(config=training_config)
    
    results = training_engine.train_multiple_models(
        model_names=["random_forest", "linear_regression"],
        X=X,
        y=y,
        feature_names=["f1", "f2", "f3", "f4", "f5"],
        target_name="target",
    )
    
    assert len(results) == 2
    
    # Compare results
    validation_config = ValidationConfig(strategy="k_fold", n_splits=3, random_state=42)
    validation_engine = ValidationEngine(config=validation_config)
    
    models = {
        "random_forest": results["random_forest"].model,
        "linear_regression": results["linear_regression"].model,
    }
    
    validation_results = validation_engine.validate_multiple_models(
        models=models,
        X=X,
        y=y,
        problem_type="regression",
    )
    
    assert len(validation_results) == 2
    
    # Statistical comparison
    statistical_engine = StatisticalEngine()
    
    rf_predictions = results["random_forest"].model.predict(X)
    lr_predictions = results["linear_regression"].model.predict(X)
    
    test_result = statistical_engine.run_test(
        test_name="paired_t_test",
        sample1=rf_predictions,
        sample2=lr_predictions,
    )
    
    assert test_result is not None


def test_project_lifecycle():
    """Test complete project lifecycle."""
    project_analyzer = ProjectAnalyzer()
    
    # Create
    context = "Test project"
    context_result = project_analyzer.analyze_context(context)
    project = project_analyzer.create_project(
        project_name="Lifecycle Test",
        description="Test",
        domain="test",
        context_analysis=context_result,
    )
    
    project_id = project.project_id
    
    # Read
    retrieved = project_analyzer.get_project(project_id)
    assert retrieved is not None
    assert retrieved.project_id == project_id
    
    # Update
    retrieved.description = "Updated description"
    project_analyzer.update_project(retrieved)
    
    updated = project_analyzer.get_project(project_id)
    assert updated.description == "Updated description"
    
    # List
    projects = project_analyzer.list_projects()
    assert len(projects) > 0
    
    # Delete
    result = project_analyzer.delete_project(project_id)
    assert result is True
    
    # Verify deletion
    deleted = project_analyzer.get_project(project_id)
    assert deleted is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
