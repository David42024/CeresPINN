"""Tests for Project Analyzer.

This module contains tests for the ProjectAnalyzer component.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from core.project_analyzer import ProjectAnalyzer
from core.project import (
    DataType,
    ProblemType,
    Objective,
    ValidationStrategy,
)


@pytest.fixture
def project_analyzer():
    """Create a ProjectAnalyzer instance for testing."""
    return ProjectAnalyzer()


def test_analyze_context_basic(project_analyzer):
    """Test basic context analysis."""
    context = """
    I want to predict crop yield based on weather data, soil properties, and management practices.
    The data includes temperature, precipitation, soil moisture, nitrogen levels, and historical yields.
    """
    
    result = project_analyzer.analyze_context(context)
    
    assert result is not None
    assert result.problem_type in [ProblemType.REGRESSION, ProblemType.BINARY_CLASSIFICATION]
    assert result.data_type == DataType.TABULAR
    assert result.objective == Objective.PREDICTION


def test_analyze_context_classification(project_analyzer):
    """Test context analysis for classification problem."""
    context = """
    I want to classify crops as healthy or diseased based on satellite imagery and weather data.
    """
    
    result = project_analyzer.analyze_context(context)
    
    assert result is not None
    assert result.problem_type == ProblemType.BINARY_CLASSIFICATION


def test_analyze_context_clustering(project_analyzer):
    """Test context analysis for clustering problem."""
    context = """
    I want to group similar fields based on their soil profiles and climate conditions.
    """
    
    result = project_analyzer.analyze_context(context)
    
    assert result is not None
    assert result.problem_type == ProblemType.CLUSTERING


def test_analyze_context_time_series(project_analyzer):
    """Test context analysis for time series problem."""
    context = """
    I want to forecast crop yields over the next 5 years based on historical data and climate projections.
    """
    
    result = project_analyzer.analyze_context(context)
    
    assert result is not None
    assert result.problem_type == ProblemType.TIME_SERIES_FORECASTING


def test_create_project(project_analyzer):
    """Test project creation."""
    context = "Predict crop yield from weather and soil data"
    result = project_analyzer.analyze_context(context)
    
    project = project_analyzer.create_project(
        project_name="Crop Yield Prediction",
        description="Predict crop yield using ML",
        domain="agriculture",
        context_analysis=result,
    )
    
    assert project is not None
    assert project.project_name == "Crop Yield Prediction"
    assert project.domain == "agriculture"
    assert project.problem_type == result.problem_type
    assert project.data_type == result.data_type
    assert project.created_at is not None


def test_list_projects(project_analyzer):
    """Test listing projects."""
    # Create a test project
    context = "Predict crop yield"
    result = project_analyzer.analyze_context(context)
    project_analyzer.create_project(
        project_name="Test Project",
        description="Test",
        domain="test",
        context_analysis=result,
    )
    
    projects = project_analyzer.list_projects()
    
    assert projects is not None
    assert len(projects) > 0


def test_get_project(project_analyzer):
    """Test getting a specific project."""
    context = "Predict crop yield"
    result = project_analyzer.analyze_context(context)
    project = project_analyzer.create_project(
        project_name="Test Project",
        description="Test",
        domain="test",
        context_analysis=result,
    )
    
    retrieved = project_analyzer.get_project(project.project_id)
    
    assert retrieved is not None
    assert retrieved.project_id == project.project_id
    assert retrieved.project_name == project.project_name


def test_delete_project(project_analyzer):
    """Test deleting a project."""
    context = "Predict crop yield"
    result = project_analyzer.analyze_context(context)
    project = project_analyzer.create_project(
        project_name="Test Project",
        description="Test",
        domain="test",
        context_analysis=result,
    )
    
    project_id = project.project_id
    
    result = project_analyzer.delete_project(project_id)
    
    assert result is True
    
    # Verify project is deleted
    retrieved = project_analyzer.get_project(project_id)
    assert retrieved is None


def test_update_project(project_analyzer):
    """Test updating a project."""
    context = "Predict crop yield"
    result = project_analyzer.analyze_context(context)
    project = project_analyzer.create_project(
        project_name="Test Project",
        description="Test",
        domain="test",
        context_analysis=result,
    )
    
    # Update project
    project.description = "Updated description"
    project.target_variable = "yield"
    
    result = project_analyzer.update_project(project)
    
    assert result is True
    
    # Verify update
    retrieved = project_analyzer.get_project(project.project_id)
    assert retrieved.description == "Updated description"
    assert retrieved.target_variable == "yield"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
