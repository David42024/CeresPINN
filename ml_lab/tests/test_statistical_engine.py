"""Tests for Statistical Engine.

This module contains tests for the StatisticalEngine component.
"""
from __future__ import annotations

import pytest
import numpy as np
from scipy import stats

from engines.statistical_engine import StatisticalEngine, StatisticalTest


@pytest.fixture
def statistical_engine():
    """Create a StatisticalEngine instance for testing."""
    return StatisticalEngine()


@pytest.fixture
def sample_data():
    """Create sample data for statistical tests."""
    np.random.seed(42)
    return {
        "sample1": np.random.normal(0, 1, 100),
        "sample2": np.random.normal(0.5, 1, 100),
    }


def test_get_tests_for_problem_type(statistical_engine):
    """Test getting tests for different problem types."""
    classification_tests = statistical_engine.get_tests_for_problem_type("binary_classification")
    regression_tests = statistical_engine.get_tests_for_problem_type("regression")
    
    assert classification_tests is not None
    assert regression_tests is not None


def test_ks_test(statistical_engine, sample_data):
    """Test Kolmogorov-Smirnov test."""
    result = statistical_engine.run_test(
        test_name="ks_test",
        sample1=sample_data["sample1"],
        sample2=sample_data["sample2"],
    )
    
    assert result is not None
    assert "statistic" in result
    assert "p_value" in result


def test_paired_t_test(statistical_engine, sample_data):
    """Test paired t-test."""
    result = statistical_engine.run_test(
        test_name="paired_t_test",
        sample1=sample_data["sample1"],
        sample2=sample_data["sample2"],
    )
    
    assert result is not None
    assert "statistic" in result
    assert "p_value" in result


def test_bootstrap_ci(statistical_engine, sample_data):
    """Test bootstrap confidence interval."""
    result = statistical_engine.run_test(
        test_name="bootstrap_ci",
        sample=sample_data["sample1"],
        n_bootstrap=100,
        alpha=0.05,
    )
    
    assert result is not None
    assert "ci_lower" in result
    assert "ci_upper" in result


def test_mcnemar_test(statistical_engine):
    """Test McNemar's test."""
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_pred1 = np.array([0, 0, 0, 1, 1, 1, 1, 1])
    y_pred2 = np.array([0, 0, 1, 1, 1, 1, 1, 1])
    
    result = statistical_engine.run_test(
        test_name="mcnemar_test",
        y_true=y_true,
        y_pred1=y_pred1,
        y_pred2=y_pred2,
    )
    
    assert result is not None
    assert "statistic" in result
    assert "p_value" in result


def test_run_multiple_tests(statistical_engine, sample_data):
    """Test running multiple statistical tests."""
    test_names = ["ks_test", "paired_t_test"]
    
    results = statistical_engine.run_tests(
        test_names=test_names,
        sample1=sample_data["sample1"],
        sample2=sample_data["sample2"],
    )
    
    assert results is not None
    assert len(results) == 2
    assert "ks_test" in results
    assert "paired_t_test" in results


def test_test_metadata(statistical_engine):
    """Test getting test metadata."""
    test_metadata = statistical_engine.get_test_metadata("ks_test")
    
    assert test_metadata is not None
    assert test_metadata.name == "ks_test"
    assert test_metadata.description is not None


def test_invalid_test(statistical_engine, sample_data):
    """Test running an invalid test."""
    with pytest.raises(ValueError):
        statistical_engine.run_test(
            test_name="invalid_test",
            sample1=sample_data["sample1"],
            sample2=sample_data["sample2"],
        )


def test_statistical_test_dataclass():
    """Test StatisticalTest dataclass."""
    test = StatisticalTest(
        name="test",
        description="Test description",
        requires_observations=True,
        requires_projections=False,
    )
    
    assert test.name == "test"
    assert test.description == "Test description"
    assert test.requires_observations is True
    assert test.requires_projections is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
