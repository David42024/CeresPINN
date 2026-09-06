"""Training Engine - Generic training engine for ML Lab.

This module implements a generic training engine that can train any model
from the model catalog. It handles data preprocessing, model training,
validation, and artifact persistence. This is a generalized version adapted
from CeresPINN's train.py for use in ML Lab.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler

from ..core.artifact_manager import ArtifactManager
from ..core.metrics_engine import MetricsEngine
from ..core.model_catalog import BaseModel, get_catalog
from ..core.model_registry import save_experiment, save_model
from ..core.project import ProjectSpecification, ValidationStrategy


class TrainingConfig:
    """Configuration for training engine."""
    
    def __init__(
        self,
        random_state: int = 42,
        test_size: float = 0.2,
        validation_strategy: str = "train_test_split",
        n_splits: int = 5,
        scale_features: bool = True,
        scaling_method: str = "standard",  # "standard", "minmax"
        encode_categorical: bool = True,
        encoding_method: str = "onehot",  # "onehot", "label"
        early_stopping: bool = False,
        early_stopping_patience: int = 10,
        save_best_model: bool = True,
        save_training_history: bool = True,
    ):
        self.random_state = random_state
        self.test_size = test_size
        self.validation_strategy = validation_strategy
        self.n_splits = n_splits
        self.scale_features = scale_features
        self.scaling_method = scaling_method
        self.encode_categorical = encode_categorical
        self.encoding_method = encoding_method
        self.early_stopping = early_stopping
        self.early_stopping_patience = early_stopping_patience
        self.save_best_model = save_best_model
        self.save_training_history = save_training_history


class TrainingResult:
    """Result of training a model."""
    
    def __init__(
        self,
        model: BaseModel,
        metrics: Dict[str, float],
        training_history: Optional[Dict[str, List[float]]] = None,
        model_path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.model = model
        self.metrics = metrics
        self.training_history = training_history or {}
        self.model_path = model_path
        self.metadata = metadata or {}
        self.trained_at = datetime.utcnow()


class TrainingEngine:
    """Generic training engine for ML Lab.
    
    This engine can train any model from the model catalog with configurable
    preprocessing, validation, and artifact persistence.
    """
    
    def __init__(
        self,
        config: Optional[TrainingConfig] = None,
        artifact_manager: Optional[ArtifactManager] = None,
    ):
        """Initialize the training engine.
        
        Args:
            config: Training configuration
            artifact_manager: Artifact manager for saving results
        """
        self.config = config or TrainingConfig()
        self.artifact_manager = artifact_manager
        self.metrics_engine = MetricsEngine()
        self.catalog = get_catalog()
        
        # Preprocessing artifacts
        self.scaler = None
        self.label_encoder = None
        self.feature_names: List[str] = []
        self.target_name: str = ""
    
    def train_model(
        self,
        model_name: str,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        target_name: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> TrainingResult:
        """Train a single model from the catalog.
        
        Args:
            model_name: Name of model to train
            X: Training features
            y: Training targets
            feature_names: Names of features
            target_name: Name of target
            hyperparameters: Hyperparameters for the model
            project_id: Project ID for artifact management
            experiment_id: Experiment ID for tracking
        
        Returns:
            TrainingResult with trained model and metrics
        """
        # Store feature/target names
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        self.target_name = target_name or "target"
        
        # Get model from catalog
        model_metadata = self.catalog.get_model_metadata(model_name)
        if model_metadata is None:
            raise ValueError(f"Model {model_name} not found in catalog")
        
        # Create model instance
        model = self.catalog.create_model(model_name, hyperparameters or {})
        
        # Preprocess data
        X_processed, y_processed = self._preprocess_data(X, y, model_metadata)
        
        # Split data
        X_train, X_test, y_train, y_test = self._split_data(
            X_processed, y_processed, self.config.validation_strategy
        )
        
        # Train model
        trained_model = self._train_single_model(
            model, X_train, y_train, X_test, y_test, model_metadata
        )
        
        # Evaluate model
        metrics = self._evaluate_model(
            trained_model, X_test, y_test, model_metadata
        )
        
        # Save model
        model_path = None
        if project_id:
            model_path = self._save_model(
                trained_model, project_id, model_name, metrics
            )
            
            # Save model to database
            try:
                model_db_data = {
                    "id": f"{project_id}_{model_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "project_id": project_id,
                    "experiment_id": experiment_id,
                    "name": model_name,
                    "type": model_metadata.category.value,
                    "category": model_metadata.category.value,
                    "version": "1.0.0",
                    "architecture": model_metadata.description,
                    "framework": "sklearn",
                    "parameters": hyperparameters or {},
                    "training_config": {
                        "random_state": self.config.random_state,
                        "validation_strategy": self.config.validation_strategy,
                    },
                    "metrics_global": metrics,
                    "metrics_cv": {},
                    "model_path": str(model_path) if model_path else None,
                    "model_size_bytes": 0,
                    "is_active": True,
                    "is_production": False,
                    "status": "trained",
                    "trained_at": datetime.utcnow().isoformat(),
                    "registered_at": datetime.utcnow().isoformat(),
                    "description": model_metadata.description,
                    "tags": [],
                }
                save_model(model_db_data)
            except Exception:
                # Database save is optional, don't fail if it errors
                pass
        
        # Create result
        result = TrainingResult(
            model=trained_model,
            metrics=metrics,
            model_path=model_path,
            metadata={
                "model_name": model_name,
                "feature_names": feature_names,
                "target_name": target_name,
                "hyperparameters": hyperparameters or {},
                "model_metadata": {
                    "category": model_metadata.category.value,
                    "requires_scaling": model_metadata.requires_scaling,
                    "handles_missing": model_metadata.handles_missing,
                },
            },
        )
        
        return result
    
    def _preprocess_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_metadata: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess features and targets.
        
        Args:
            X: Raw features
            y: Raw targets
            model_metadata: Model metadata for preprocessing requirements
        
        Returns:
            Tuple of (processed X, processed y)
        """
        X_processed = X.copy()
        y_processed = y.copy()
        
        # Scale features if required
        if self.config.scale_features and model_metadata.requires_scaling:
            if self.config.scaling_method == "standard":
                self.scaler = StandardScaler()
            else:
                self.scaler = MinMaxScaler()
            X_processed = self.scaler.fit_transform(X_processed)
        
        # Encode categorical targets
        if self.config.encode_categorical and y_processed.dtype == object:
            if self.config.encoding_method == "label":
                self.label_encoder = LabelEncoder()
                y_processed = self.label_encoder.fit_transform(y_processed)
            else:
                # One-hot encoding would require more complex handling
                pass
        
        return X_processed, y_processed
    
    def _split_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_strategy: str,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into train and test sets.
        
        Args:
            X: Features
            y: Targets
            validation_strategy: Validation strategy
        
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        if validation_strategy == "train_test_split":
            return train_test_split(
                X, y,
                test_size=self.config.test_size,
                random_state=self.config.random_state,
                stratify=y if len(np.unique(y)) > 1 and len(y) > 10 else None,
            )
        else:
            # For now, default to train_test_split
            # TODO: Implement other validation strategies
            return train_test_split(
                X, y,
                test_size=self.config.test_size,
                random_state=self.config.random_state,
            )
    
    def _train_single_model(
        self,
        model: BaseModel,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_metadata: Any,
    ) -> BaseModel:
        """Train a single model.
        
        Args:
            model: Model to train
            X_train: Training features
            y_train: Training targets
            X_test: Test features
            y_test: Test targets
            model_metadata: Model metadata
        
        Returns:
            Trained model
        """
        # Check if model has custom fit method with additional parameters
        try:
            # Try to fit with validation data for early stopping
            model.fit(
                X_train, y_train,
                X_val=X_test,
                y_val=y_test,
                early_stopping=self.config.early_stopping,
                early_stopping_patience=self.config.early_stopping_patience,
            )
        except TypeError:
            # Fall back to standard fit
            model.fit(X_train, y_train)
        
        return model
    
    def _evaluate_model(
        self,
        model: BaseModel,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_metadata: Any,
    ) -> Dict[str, float]:
        """Evaluate a trained model.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test targets
            model_metadata: Model metadata
        
        Returns:
            Dictionary of metrics
        """
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Get probabilities if available
        y_proba = None
        try:
            y_proba = model.predict_proba(X_test)
        except (AttributeError, NotImplementedError):
            pass
        
        # Determine problem type from model metadata
        problem_type = model_metadata.supported_problem_types[0] if model_metadata.supported_problem_types else "regression"
        
        # Get appropriate metrics
        if "classification" in problem_type:
            metric_names = self.metrics_engine.get_metrics_for_problem_type(problem_type)
        else:
            metric_names = self.metrics_engine.get_metrics_for_problem_type("regression")
        
        # Calculate metrics
        metrics = self.metrics_engine.calculate_metrics(
            metric_names, y_test, y_pred, y_proba
        )
        
        return metrics
    
    def _save_model(
        self,
        model: BaseModel,
        project_id: str,
        model_name: str,
        metrics: Dict[str, float],
    ) -> Path:
        """Save a trained model and its metadata.
        
        Args:
            model: Trained model
            project_id: Project ID
            model_name: Name of the model
            metrics: Model metrics
        
        Returns:
            Path to saved model
        """
        if self.artifact_manager is None:
            return None
        
        # Save model
        model_filename = f"{model_name}_model.pkl"
        model_path = self.artifact_manager.save_artifact(
            project_id,
            "models",
            model_filename,
            model,
            metadata=metrics,
        )
        
        # Save preprocessing artifacts
        if self.scaler is not None:
            scaler_filename = f"{model_name}_scaler.pkl"
            self.artifact_manager.save_artifact(
                project_id,
                "preprocessing",
                scaler_filename,
                self.scaler,
            )
        
        if self.label_encoder is not None:
            encoder_filename = f"{model_name}_encoder.pkl"
            self.artifact_manager.save_artifact(
                project_id,
                "preprocessing",
                encoder_filename,
                self.label_encoder,
            )
        
        return model_path
    
    def train_multiple_models(
        self,
        model_names: List[str],
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        target_name: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Dict[str, Any]]] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, TrainingResult]:
        """Train multiple models from the catalog.
        
        Args:
            model_names: Names of models to train
            X: Training features
            y: Training targets
            feature_names: Names of features
            target_name: Name of target
            hyperparameters: Dictionary of hyperparameters per model
            project_id: Project ID for artifact management
        
        Returns:
            Dictionary mapping model names to TrainingResults
        """
        results = {}
        hyperparameters = hyperparameters or {}
        
        for model_name in model_names:
            try:
                result = self.train_model(
                    model_name=model_name,
                    X=X,
                    y=y,
                    feature_names=feature_names,
                    target_name=target_name,
                    hyperparameters=hyperparameters.get(model_name),
                    project_id=project_id,
                )
                results[model_name] = result
            except Exception as e:
                print(f"Failed to train {model_name}: {e}")
                results[model_name] = None
        
        return results
    
    def load_model(
        self,
        project_id: str,
        model_name: str,
        load_preprocessing: bool = True,
    ) -> BaseModel:
        """Load a trained model from artifacts.
        
        Args:
            project_id: Project ID
            model_name: Name of the model
            load_preprocessing: Whether to load preprocessing artifacts
        
        Returns:
            Loaded model
        """
        if self.artifact_manager is None:
            raise ValueError("Artifact manager not configured")
        
        # Load model
        model_filename = f"{model_name}_model.pkl"
        model = self.artifact_manager.load_artifact(project_id, "models", model_filename)
        
        # Load preprocessing artifacts
        if load_preprocessing:
            try:
                scaler_filename = f"{model_name}_scaler.pkl"
                self.scaler = self.artifact_manager.load_artifact(
                    project_id, "preprocessing", scaler_filename
                )
            except Exception:
                pass
            
            try:
                encoder_filename = f"{model_name}_encoder.pkl"
                self.label_encoder = self.artifact_manager.load_artifact(
                    project_id, "preprocessing", encoder_filename
                )
            except Exception:
                pass
        
        return model
    
    def predict_with_model(
        self,
        model: BaseModel,
        X: np.ndarray,
        apply_preprocessing: bool = True,
    ) -> np.ndarray:
        """Make predictions with a trained model.
        
        Args:
            model: Trained model
            X: Features to predict
            apply_preprocessing: Whether to apply preprocessing
        
        Returns:
            Predictions
        """
        X_processed = X.copy()
        
        if apply_preprocessing:
            if self.scaler is not None:
                X_processed = self.scaler.transform(X_processed)
        
        return model.predict(X_processed)
