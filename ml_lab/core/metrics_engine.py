"""Metrics Engine - Dynamic metric selection and calculation.

This module implements the MetricsEngine which dynamically selects and calculates
metrics based on the problem type and objective. The engine supports multiple
metric categories for different ML problems.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    f1_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    precision_score,
    recall_score,
    r2_score,
    silhouette_score,
)
from sklearn.metrics import roc_auc_score, average_precision_score


class MetricCategory(Enum):
    """Categories of metrics."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    FORECASTING = "forecasting"


class MetricDirection(Enum):
    """Direction of metric optimization."""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


@dataclass
class MetricDefinition:
    """Definition of a metric."""
    name: str
    category: MetricCategory
    description: str
    direction: MetricDirection
    requires_proba: bool = False
    requires_y_true: bool = True


class MetricsEngine:
    """Dynamic metric selection and calculation.
    
    The MetricsEngine selects appropriate metrics based on the problem type
    and objective, then calculates them for model evaluation.
    """
    
    def __init__(self):
        """Initialize the metrics engine."""
        self._metric_definitions = self._get_builtin_metrics()
    
    def get_metric_definition(self, name: str) -> Optional[MetricDefinition]:
        """Get the definition of a metric by name."""
        return self._metric_definitions.get(name)
    
    def get_metrics_for_problem_type(
        self, problem_type: str, objective: str = "prediction"
    ) -> List[str]:
        """Get recommended metrics for a problem type.
        
        Args:
            problem_type: Type of ML problem
            objective: Business/research objective
        
        Returns:
            List of recommended metric names
        """
        if problem_type in ["binary_classification", "multiclass_classification"]:
            if objective == "explanation":
                return ["accuracy", "f1", "precision", "recall"]
            return ["accuracy", "f1", "precision", "recall", "roc_auc", "pr_auc"]
        elif problem_type == "regression":
            return ["mae", "rmse", "r2", "mape"]
        elif problem_type == "clustering":
            return ["silhouette", "calinski_harabasz", "davies_bouldin"]
        elif problem_type == "time_series_forecasting":
            return ["mae", "rmse", "mape", "smape"]
        else:
            return ["accuracy"]
    
    def get_primary_metric(
        self, problem_type: str, objective: str = "prediction"
    ) -> str:
        """Get the primary metric for a problem type.
        
        Args:
            problem_type: Type of ML problem
            objective: Business/research objective
        
        Returns:
            Name of the primary metric
        """
        if problem_type == "binary_classification":
            return "f1"
        elif problem_type == "multiclass_classification":
            return "f1_weighted"
        elif problem_type == "regression":
            return "rmse"
        elif problem_type == "clustering":
            return "silhouette"
        elif problem_type == "time_series_forecasting":
            return "mae"
        else:
            return "accuracy"
    
    def calculate_metric(
        self,
        metric_name: str,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        **kwargs,
    ) -> float:
        """Calculate a specific metric.
        
        Args:
            metric_name: Name of the metric to calculate
            y_true: True labels/values
            y_pred: Predicted labels/values
            y_proba: Predicted probabilities (for some metrics)
            **kwargs: Additional metric-specific parameters
        
        Returns:
            Calculated metric value
        """
        definition = self.get_metric_definition(metric_name)
        if definition is None:
            raise ValueError(f"Unknown metric: {metric_name}")
        
        if definition.requires_proba and y_proba is None:
            raise ValueError(f"Metric {metric_name} requires probability predictions")
        
        try:
            if metric_name == "accuracy":
                return accuracy_score(y_true, y_pred)
            elif metric_name == "precision":
                average = kwargs.get("average", "weighted")
                return precision_score(y_true, y_pred, average=average, zero_division=0)
            elif metric_name == "recall":
                average = kwargs.get("average", "weighted")
                return recall_score(y_true, y_pred, average=average, zero_division=0)
            elif metric_name == "f1":
                average = kwargs.get("average", "weighted")
                return f1_score(y_true, y_pred, average=average, zero_division=0)
            elif metric_name == "f1_weighted":
                return f1_score(y_true, y_pred, average="weighted", zero_division=0)
            elif metric_name == "f1_macro":
                return f1_score(y_true, y_pred, average="macro", zero_division=0)
            elif metric_name == "f1_micro":
                return f1_score(y_true, y_pred, average="micro", zero_division=0)
            elif metric_name == "roc_auc":
                if y_proba is None:
                    return 0.0
                # Handle binary vs multiclass
                if len(y_proba.shape) == 1:
                    return roc_auc_score(y_true, y_proba)
                else:
                    return roc_auc_score(y_true, y_proba, multi_class="ovr", average="weighted")
            elif metric_name == "pr_auc":
                if y_proba is None:
                    return 0.0
                return average_precision_score(y_true, y_proba)
            elif metric_name == "mae":
                return mean_absolute_error(y_true, y_pred)
            elif metric_name == "mse":
                return mean_squared_error(y_true, y_pred)
            elif metric_name == "rmse":
                return np.sqrt(mean_squared_error(y_true, y_pred))
            elif metric_name == "r2":
                return r2_score(y_true, y_pred)
            elif metric_name == "mape":
                # Handle division by zero
                y_true_safe = np.where(y_true == 0, 1e-10, y_true)
                return mean_absolute_percentage_error(y_true_safe, y_pred)
            elif metric_name == "smape":
                return self._calculate_smape(y_true, y_pred)
            elif metric_name == "silhouette":
                return silhouette_score(y_true, y_pred)
            elif metric_name == "calinski_harabasz":
                return calinski_harabasz_score(y_true, y_pred)
            elif metric_name == "davies_bouldin":
                return davies_bouldin_score(y_true, y_pred)
            else:
                raise ValueError(f"Metric calculation not implemented: {metric_name}")
        except Exception as e:
            # Return NaN on error to avoid breaking the pipeline
            print(f"Error calculating metric {metric_name}: {e}")
            return np.nan
    
    def calculate_metrics(
        self,
        metric_names: List[str],
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Dict[str, float]:
        """Calculate multiple metrics.
        
        Args:
            metric_names: List of metric names to calculate
            y_true: True labels/values
            y_pred: Predicted labels/values
            y_proba: Predicted probabilities (optional)
            **kwargs: Additional metric-specific parameters
        
        Returns:
            Dictionary mapping metric names to calculated values
        """
        results = {}
        for metric_name in metric_names:
            try:
                results[metric_name] = self.calculate_metric(
                    metric_name, y_true, y_pred, y_proba, **kwargs
                )
            except Exception as e:
                print(f"Error calculating {metric_name}: {e}")
                results[metric_name] = np.nan
        return results
    
    def get_metric_direction(self, metric_name: str) -> MetricDirection:
        """Get the optimization direction for a metric.
        
        Args:
            metric_name: Name of the metric
        
        Returns:
            MetricDirection (MAXIMIZE or MINIMIZE)
        """
        definition = self.get_metric_definition(metric_name)
        if definition:
            return definition.direction
        
        # Default to maximize for most metrics
        if metric_name in ["mae", "mse", "rmse", "mape", "smape", "davies_bouldin"]:
            return MetricDirection.MINIMIZE
        return MetricDirection.MAXIMIZE
    
    def compare_metrics(
        self, metric_name: str, value1: float, value2: float
    ) -> bool:
        """Compare two metric values according to the metric's direction.
        
        Args:
            metric_name: Name of the metric
            value1: First value
            value2: Second value
        
        Returns:
            True if value1 is better than value2 according to the metric direction
        """
        direction = self.get_metric_direction(metric_name)
        if direction == MetricDirection.MAXIMIZE:
            return value1 > value2
        else:
            return value1 < value2
    
    def _calculate_smape(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Symmetric Mean Absolute Percentage Error."""
        numerator = np.abs(y_true - y_pred)
        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
        denominator = np.where(denominator == 0, 1e-10, denominator)
        return np.mean(numerator / denominator) * 100
    
    def _get_builtin_metrics(self) -> Dict[str, MetricDefinition]:
        """Get built-in metric definitions."""
        return {
            # Classification metrics
            "accuracy": MetricDefinition(
                name="accuracy",
                category=MetricCategory.CLASSIFICATION,
                description="Ratio of correctly predicted observations",
                direction=MetricDirection.MAXIMIZE,
            ),
            "precision": MetricDefinition(
                name="precision",
                category=MetricCategory.CLASSIFICATION,
                description="Ratio of correctly predicted positive observations",
                direction=MetricDirection.MAXIMIZE,
            ),
            "recall": MetricDefinition(
                name="recall",
                category=MetricCategory.CLASSIFICATION,
                description="Ratio of correctly predicted actual positives",
                direction=MetricDirection.MAXIMIZE,
            ),
            "f1": MetricDefinition(
                name="f1",
                category=MetricCategory.CLASSIFICATION,
                description="Weighted average of precision and recall",
                direction=MetricDirection.MAXIMIZE,
            ),
            "f1_weighted": MetricDefinition(
                name="f1_weighted",
                category=MetricCategory.CLASSIFICATION,
                description="F1 score with weighted average",
                direction=MetricDirection.MAXIMIZE,
            ),
            "f1_macro": MetricDefinition(
                name="f1_macro",
                category=MetricCategory.CLASSIFICATION,
                description="F1 score with macro average",
                direction=MetricDirection.MAXIMIZE,
            ),
            "f1_micro": MetricDefinition(
                name="f1_micro",
                category=MetricCategory.CLASSIFICATION,
                description="F1 score with micro average",
                direction=MetricDirection.MAXIMIZE,
            ),
            "roc_auc": MetricDefinition(
                name="roc_auc",
                category=MetricCategory.CLASSIFICATION,
                description="Area under the ROC curve",
                direction=MetricDirection.MAXIMIZE,
                requires_proba=True,
            ),
            "pr_auc": MetricDefinition(
                name="pr_auc",
                category=MetricCategory.CLASSIFICATION,
                description="Area under the Precision-Recall curve",
                direction=MetricDirection.MAXIMIZE,
                requires_proba=True,
            ),
            # Regression metrics
            "mae": MetricDefinition(
                name="mae",
                category=MetricCategory.REGRESSION,
                description="Mean Absolute Error",
                direction=MetricDirection.MINIMIZE,
            ),
            "mse": MetricDefinition(
                name="mse",
                category=MetricCategory.REGRESSION,
                description="Mean Squared Error",
                direction=MetricDirection.MINIMIZE,
            ),
            "rmse": MetricDefinition(
                name="rmse",
                category=MetricCategory.REGRESSION,
                description="Root Mean Squared Error",
                direction=MetricDirection.MINIMIZE,
            ),
            "r2": MetricDefinition(
                name="r2",
                category=MetricCategory.REGRESSION,
                description="R-squared score",
                direction=MetricDirection.MAXIMIZE,
            ),
            "mape": MetricDefinition(
                name="mape",
                category=MetricCategory.REGRESSION,
                description="Mean Absolute Percentage Error",
                direction=MetricDirection.MINIMIZE,
            ),
            "smape": MetricDefinition(
                name="smape",
                category=MetricCategory.REGRESSION,
                description="Symmetric Mean Absolute Percentage Error",
                direction=MetricDirection.MINIMIZE,
            ),
            # Clustering metrics
            "silhouette": MetricDefinition(
                name="silhouette",
                category=MetricCategory.CLUSTERING,
                description="Silhouette coefficient",
                direction=MetricDirection.MAXIMIZE,
            ),
            "calinski_harabasz": MetricDefinition(
                name="calinski_harabasz",
                category=MetricCategory.CLUSTERING,
                description="Calinski-Harabasz index",
                direction=MetricDirection.MAXIMIZE,
            ),
            "davies_bouldin": MetricDefinition(
                name="davies_bouldin",
                category=MetricCategory.CLUSTERING,
                description="Davies-Bouldin index",
                direction=MetricDirection.MINIMIZE,
            ),
        }


# Global metrics engine instance
_engine = MetricsEngine()


def get_metrics_engine() -> MetricsEngine:
    """Get the global metrics engine instance."""
    return _engine
