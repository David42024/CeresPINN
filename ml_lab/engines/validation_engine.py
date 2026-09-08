"""Validation Engine - Dynamic cross-validation for ML Lab.

This module implements a validation engine that supports dynamic cross-validation
strategies based on the ProjectSpecification. It integrates with the training
engine and metrics engine to provide comprehensive model validation.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.model_selection import (
    KFold,
    StratifiedKFold,
    TimeSeriesSplit,
    cross_val_score,
    cross_validate,
)

from core.artifact_manager import ArtifactManager
from core.metrics_engine import MetricsEngine
from core.model_catalog import BaseModel, get_catalog
from core.project import ProjectSpecification, ValidationStrategy


class ValidationConfig:
    """Configuration for validation engine."""
    
    def __init__(
        self,
        strategy: str = "k_fold",
        n_splits: int = 5,
        random_state: int = 42,
        shuffle: bool = True,
        scoring: Optional[List[str]] = None,
        return_train_score: bool = False,
        n_jobs: int = 1,
        test_size: float = 0.2,
    ):
        self.strategy = strategy
        self.n_splits = n_splits
        self.random_state = random_state
        self.shuffle = shuffle
        self.scoring = scoring
        self.return_train_score = return_train_score
        self.n_jobs = n_jobs
        self.test_size = test_size


class ValidationResult:
    """Result of model validation."""
    
    def __init__(
        self,
        model_name: str,
        metrics: Dict[str, Any],
        fold_metrics: Optional[List[Dict[str, float]]] = None,
        cross_val_scores: Optional[Dict[str, np.ndarray]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.model_name = model_name
        self.metrics = metrics
        self.fold_metrics = fold_metrics or []
        self.cross_val_scores = cross_val_scores or {}
        self.metadata = metadata or {}
        self.validated_at = datetime.utcnow()


class ValidationEngine:
    """Dynamic validation engine for ML Lab.
    
    This engine supports multiple validation strategies including:
    - Train-test split
    - K-fold cross-validation
    - Stratified K-fold (for imbalanced classification)
    - Time series split
    - Leave-one-out (for small datasets)
    """
    
    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        artifact_manager: Optional[ArtifactManager] = None,
    ):
        """Initialize the validation engine.
        
        Args:
            config: Validation configuration
            artifact_manager: Artifact manager for saving results
        """
        self.config = config or ValidationConfig()
        self.artifact_manager = artifact_manager
        self.metrics_engine = MetricsEngine()
        self.catalog = get_catalog()
    
    def get_cv_splitter(self):
        """Get the cross-validation splitter based on strategy.
        
        Returns:
            Scikit-learn CV splitter
        """
        strategy = self.config.strategy
        
        if strategy == "k_fold":
            return KFold(
                n_splits=self.config.n_splits,
                shuffle=self.config.shuffle,
                random_state=self.config.random_state,
            )
        elif strategy == "stratified_k_fold":
            return StratifiedKFold(
                n_splits=self.config.n_splits,
                shuffle=self.config.shuffle,
                random_state=self.config.random_state,
            )
        elif strategy == "time_series_split":
            return TimeSeriesSplit(
                n_splits=self.config.n_splits,
            )
        else:
            # Default to KFold
            return KFold(
                n_splits=self.config.n_splits,
                shuffle=self.config.shuffle,
                random_state=self.config.random_state,
            )
    
    def validate_model(
        self,
        model: BaseModel,
        X: np.ndarray,
        y: np.ndarray,
        model_name: Optional[str] = None,
        problem_type: str = "regression",
        project_id: Optional[str] = None,
    ) -> ValidationResult:
        """Validate a model using the configured strategy.
        
        Args:
            model: Trained model to validate
            X: Features
            y: Targets
            model_name: Name of the model
            problem_type: Type of ML problem
            project_id: Project ID for artifact management
        
        Returns:
            ValidationResult with validation metrics
        """
        if model_name is None:
            model_name = getattr(model, "name", getattr(model, "__class__", type("M", (), {})).__name__)
        # Get CV splitter
        cv = self.get_cv_splitter()
        
        # Get appropriate metrics
        if self.config.scoring:
            scoring_metrics = self.config.scoring
        else:
            scoring_metrics = self.metrics_engine.get_metrics_for_problem_type(problem_type)
        
        # Convert to sklearn-compatible scoring names
        sklearn_scoring = self._convert_to_sklearn_scoring(scoring_metrics, problem_type)
        
        # Unwrap underlying estimator if model is an ML Lab wrapper
        estimator = getattr(model, "model", model)
        if estimator is None:
            estimator = model

        # Perform cross-validation
        cv_results = cross_validate(
            estimator,
            X,
            y,
            cv=cv,
            scoring=sklearn_scoring,
            return_train_score=self.config.return_train_score,
            n_jobs=self.config.n_jobs,
        )
        
        # Aggregate results
        metrics = {}
        fold_metrics = []
        
        for metric_name in sklearn_scoring:
            test_key = f"test_{metric_name}"
            if test_key in cv_results:
                scores = cv_results[test_key]
                metrics[metric_name] = {
                    "mean": float(np.mean(scores)),
                    "std": float(np.std(scores)),
                    "min": float(np.min(scores)),
                    "max": float(np.max(scores)),
                    "values": scores.tolist(),
                }
                
                # Store per-fold metrics
                for i, score in enumerate(scores):
                    if i >= len(fold_metrics):
                        fold_metrics.append({})
                    fold_metrics[i][metric_name] = float(score)
        
        # Create validation result
        result = ValidationResult(
            model_name=model_name,
            metrics=metrics,
            fold_metrics=fold_metrics,
            cross_val_scores=cv_results,
            metadata={
                "strategy": self.config.strategy,
                "n_splits": self.config.n_splits,
                "n_samples": len(X),
                "scoring": sklearn_scoring,
            },
        )
        
        # Save artifacts
        if project_id and self.artifact_manager:
            self._save_validation_result(result, project_id, model_name)
        
        return result
    
    def validate_multiple_models(
        self,
        models: Dict[str, BaseModel],
        X: np.ndarray,
        y: np.ndarray,
        problem_type: str = "regression",
        project_id: Optional[str] = None,
    ) -> Dict[str, ValidationResult]:
        """Validate multiple models.
        
        Args:
            models: Dictionary mapping model names to trained models
            X: Features
            y: Targets
            problem_type: Type of ML problem
            project_id: Project ID for artifact management
        
        Returns:
            Dictionary mapping model names to ValidationResults
        """
        results = {}
        for model_name, model in models.items():
            try:
                result = self.validate_model(
                    model=model,
                    X=X,
                    y=y,
                    model_name=model_name,
                    problem_type=problem_type,
                    project_id=project_id,
                )
                results[model_name] = result
            except Exception as e:
                print(f"Failed to validate {model_name}: {e}")
                results[model_name] = None
        
        return results
    
    def compare_models(
        self,
        validation_results: Dict[str, ValidationResult],
        primary_metric: str = "f1",
    ) -> Dict[str, Any]:
        """Compare multiple models based on validation results.
        
        Args:
            validation_results: Dictionary of ValidationResults
            primary_metric: Primary metric for comparison
        
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "models": [],
            "ranking": [],
            "best_model": None,
        }
        
        for model_name, result in validation_results.items():
            if result is None:
                continue
            
            metric_value = result.metrics.get(primary_metric, {}).get("mean", 0.0)
            comparison["models"].append({
                "name": model_name,
                primary_metric: metric_value,
                "metrics": result.metrics,
            })
        
        # Sort by primary metric (assuming higher is better)
        comparison["models"].sort(key=lambda x: x[primary_metric], reverse=True)
        comparison["ranking"] = [m["name"] for m in comparison["models"]]
        
        if comparison["ranking"]:
            comparison["best_model"] = comparison["ranking"][0]
        
        return comparison
    
    def _convert_to_sklearn_scoring(self, metrics: List[str], problem_type: str) -> List[str]:
        """Convert ML Lab metric names to sklearn scoring names.
        
        Args:
            metrics: List of ML Lab metric names
            problem_type: Type of ML problem
        
        Returns:
            List of sklearn-compatible scoring names
        """
        sklearn_mapping = {
            "accuracy": "accuracy",
            "f1": "f1_weighted",
            "f1_weighted": "f1_weighted",
            "f1_macro": "f1_macro",
            "precision": "precision_weighted",
            "recall": "recall_weighted",
            "roc_auc": "roc_auc_ovr_weighted",
            "mae": "neg_mean_absolute_error",
            "mse": "neg_mean_squared_error",
            "rmse": "neg_root_mean_squared_error",
            "r2": "r2",
            "mape": "neg_mean_absolute_percentage_error",
        }
        
        sklearn_metrics = []
        for metric in metrics:
            if metric in sklearn_mapping:
                sklearn_metrics.append(sklearn_mapping[metric])
            elif metric not in ("crps", "ensemble_iqr", "sobol_total_index", "coverage_95"):
                sklearn_metrics.append(metric)
        
        return sklearn_metrics
    
    def _save_validation_result(
        self,
        result: ValidationResult,
        project_id: str,
        model_name: str,
    ) -> None:
        """Save validation result to artifacts.
        
        Args:
            result: ValidationResult to save
            project_id: Project ID
            model_name: Name of the model
        """
        if self.artifact_manager is None:
            return
        
        # Save validation metrics
        metrics_filename = f"{model_name}_validation_metrics.json"
        self.artifact_manager.save_artifact(
            project_id,
            "validation",
            metrics_filename,
            result.metrics,
            metadata=result.metadata,
        )
        
        # Save fold metrics
        if result.fold_metrics:
            fold_filename = f"{model_name}_fold_metrics.json"
            self.artifact_manager.save_artifact(
                project_id,
                "validation",
                fold_filename,
                result.fold_metrics,
            )
    
    def load_validation_result(
        self,
        project_id: str,
        model_name: str,
    ) -> Optional[ValidationResult]:
        """Load a validation result from artifacts.
        
        Args:
            project_id: Project ID
            model_name: Name of the model
        
        Returns:
            ValidationResult or None if not found
        """
        if self.artifact_manager is None:
            return None
        
        try:
            metrics_filename = f"{model_name}_validation_metrics.json"
            metrics = self.artifact_manager.load_artifact(
                project_id, "validation", metrics_filename
            )
            
            fold_filename = f"{model_name}_fold_metrics.json"
            fold_metrics = self.artifact_manager.load_artifact(
                project_id, "validation", fold_filename
            )
            
            return ValidationResult(
                model_name=model_name,
                metrics=metrics,
                fold_metrics=fold_metrics,
            )
        except Exception:
            return None
    
    def select_validation_strategy(
        self,
        spec: ProjectSpecification,
        dataset_size: int,
        is_time_series: bool = False,
        is_imbalanced: bool = False,
    ) -> str:
        """Select the appropriate validation strategy based on project context.
        
        Args:
            spec: Project specification
            dataset_size: Size of the dataset
            is_time_series: Whether data is time series
            is_imbalanced: Whether target is imbalanced
        
        Returns:
            Validation strategy name
        """
        # Use strategy from spec if specified
        if spec.validation.strategy:
            strategy = spec.validation.strategy.value
            if strategy in ["k_fold", "stratified_k_fold", "time_series_split", "train_test_split"]:
                return strategy
        
        # Auto-select based on dataset characteristics
        if is_time_series:
            return "time_series_split"
        elif is_imbalanced:
            return "stratified_k_fold"
        elif dataset_size < 100:
            return "train_test_split"
        else:
            return "k_fold"
