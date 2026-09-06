"""Tests for Dataset Analyzer.

This module contains tests for the DatasetAnalyzer component.
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from core.dataset_analyzer import DatasetAnalyzer


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    return pd.DataFrame({
        "feature1": np.random.randn(100),
        "feature2": np.random.randn(100),
        "feature3": np.random.randint(0, 10, 100),
        "category": np.random.choice(["A", "B", "C"], 100),
        "target": np.random.randn(100),
    })


@pytest.fixture
def dataset_analyzer():
    """Create a DatasetAnalyzer instance for testing."""
    return DatasetAnalyzer()


def test_analyze_tabular(dataset_analyzer, sample_dataframe):
    """Test tabular data analysis."""
    profile = dataset_analyzer.analyze_tabular(sample_dataframe)
    
    assert profile is not None
    assert profile.rows == 100
    assert profile.columns == 5
    assert profile.numerical_features == 4
    assert profile.categorical_features == 1
    assert profile.temporal_features == 0


def test_detect_missing_values(dataset_analyzer):
    """Test missing value detection."""
    df = pd.DataFrame({
        "col1": [1, 2, np.nan, 4, 5],
        "col2": [1, 2, 3, 4, 5],
        "col3": [np.nan, np.nan, 3, 4, 5],
    })
    
    profile = dataset_analyzer.analyze_tabular(df)
    
    assert profile.total_missing_count == 3
    assert profile.total_missing_percentage == 20.0


def test_detect_duplicates(dataset_analyzer):
    """Test duplicate detection."""
    df = pd.DataFrame({
        "col1": [1, 2, 2, 3, 4],
        "col2": [1, 2, 2, 3, 4],
    })
    
    profile = dataset_analyzer.analyze_tabular(df)
    
    assert profile.has_duplicates is True


def test_detect_outliers(dataset_analyzer):
    """Test outlier detection."""
    df = pd.DataFrame({
        "col1": [1, 2, 3, 4, 100],  # 100 is an outlier
        "col2": [1, 2, 3, 4, 5],
    })
    
    profile = dataset_analyzer.analyze_tabular(df)
    
    assert profile.has_outliers is True


def test_detect_imbalance(dataset_analyzer):
    """Test class imbalance detection."""
    df = pd.DataFrame({
        "feature": [1, 2, 3, 4, 5],
        "target": ["A", "A", "A", "B", "B"],  # Imbalanced
    })
    
    profile = dataset_analyzer.analyze_tabular(df)
    
    assert profile.is_imbalanced is True


def test_suggest_target_column(dataset_analyzer, sample_dataframe):
    """Test target column suggestion."""
    profile = dataset_analyzer.analyze_tabular(sample_dataframe)
    
    assert profile.target_column is not None
    # Should suggest "target" as it's numeric and at the end


def test_generate_profile(dataset_analyzer, sample_dataframe):
    """Test complete profile generation."""
    profile = dataset_analyzer.analyze_tabular(sample_dataframe)
    
    assert profile.rows == 100
    assert profile.columns == 5
    assert profile.memory_mb > 0
    assert len(profile.numerical_features) > 0
    assert len(profile.categorical_features) > 0


def test_analyze_with_missing_target(dataset_analyzer):
    """Test analysis when target column is missing."""
    df = pd.DataFrame({
        "feature1": [1, 2, 3, 4, 5],
        "feature2": [1, 2, 3, 4, 5],
    })
    
    profile = dataset_analyzer.analyze_tabular(df)
    
    assert profile.target_column is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
