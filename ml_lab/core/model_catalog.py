"""Model Catalog - Extensible registry of ML models.

This module implements the ModelCatalog which serves as a registry of available
ML models organized by category. The catalog is extensible and allows adding
new models without modifying the core system.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from dataclasses import dataclass as dataclass_decorator
from enum import Enum
from typing import Any, Dict, List, Optional, Type


class ModelCategory(Enum):
    """Categories of ML models."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"
    COMPUTER_VISION = "computer_vision"
    NLP = "nlp"
    SPECIALIZED = "specialized"


@dataclass
class ModelMetadata:
    """Metadata for a model in the catalog."""
    name: str
    category: ModelCategory
    description: str
    supported_problem_types: List[str]
    supported_data_types: List[str]
    requires_scaling: bool = True
    handles_missing: bool = False
    handles_categorical: bool = False
    interpretable: bool = False
    fast_training: bool = False
    fast_inference: bool = False
    memory_efficient: bool = False
    default_hyperparameters: Dict[str, Any] = field(default_factory=dict)
    hyperparameter_search_space: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


class BaseModel(ABC):
    """Abstract base class for all models in the catalog."""
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        """Initialize the model.
        
        Args:
            hyperparameters: Model hyperparameters
        """
        self.hyperparameters = hyperparameters or {}
        self.model = None
        self.is_fitted = False
    
    @abstractmethod
    def fit(self, X, y):
        """Fit the model to training data."""
        pass
    
    @abstractmethod
    def predict(self, X):
        """Make predictions."""
        pass
    
    @abstractmethod
    def predict_proba(self, X):
        """Predict class probabilities (for classification)."""
        pass
    
    @abstractmethod
    def get_feature_importance(self):
        """Get feature importance (if available)."""
        pass


class ModelCatalog:
    """Extensible catalog of ML models.
    
    The catalog organizes models by category and provides methods to:
    - Register new models
    - Query models by category/problem type/data type
    - Get model metadata
    - Instantiate models with hyperparameters
    """
    
    def __init__(self):
        """Initialize the model catalog."""
        self._models: Dict[str, ModelMetadata] = {}
        self._model_classes: Dict[str, Type[BaseModel]] = {}
        self._register_builtin_models()
    
    def register_model(
        self,
        metadata: ModelMetadata,
        model_class: Optional[Type[BaseModel]] = None,
    ) -> None:
        """Register a model in the catalog.
        
        Args:
            metadata: Model metadata
            model_class: Optional model class for instantiation
        """
        self._models[metadata.name] = metadata
        if model_class:
            self._model_classes[metadata.name] = model_class
    
    def get_model_metadata(self, name: str) -> Optional[ModelMetadata]:
        """Get metadata for a model by name."""
        return self._models.get(name)
    
    def get_models_by_category(self, category: ModelCategory) -> List[ModelMetadata]:
        """Get all models in a category."""
        return [
            metadata for metadata in self._models.values()
            if metadata.category == category
        ]
    
    def get_models_by_problem_type(self, problem_type: str) -> List[ModelMetadata]:
        """Get models that support a specific problem type."""
        return [
            metadata for metadata in self._models.values()
            if problem_type in metadata.supported_problem_types
        ]
    
    def get_models_by_data_type(self, data_type: str) -> List[ModelMetadata]:
        """Get models that support a specific data type."""
        return [
            metadata for metadata in self._models.values()
            if data_type in metadata.supported_data_types
        ]
    
    def get_recommended_models(
        self, problem_type: str, data_type: str, constraints: Optional[List[str]] = None
    ) -> List[str]:
        """Get recommended models based on problem type and data type.
        
        Args:
            problem_type: Type of ML problem
            data_type: Type of data
            constraints: Optional constraints (e.g., "fast_training", "interpretable")
        
        Returns:
            List of recommended model names
        """
        candidates = self.get_models_by_problem_type(problem_type)
        candidates = [m for m in candidates if data_type in m.supported_data_types]
        
        # Apply constraints
        if constraints:
            for constraint in constraints:
                if constraint == "fast_training":
                    candidates = [m for m in candidates if m.fast_training]
                elif constraint == "interpretable":
                    candidates = [m for m in candidates if m.interpretable]
                elif constraint == "memory_efficient":
                    candidates = [m for m in candidates if m.memory_efficient]
        
        return [m.name for m in candidates]
    
    def instantiate_model(self, name: str, hyperparameters: Optional[Dict[str, Any]] = None) -> Optional[BaseModel]:
        """Instantiate a model by name.
        
        Args:
            name: Model name
            hyperparameters: Optional hyperparameters
        
        Returns:
            Instantiated model or None if not found
        """
        if name not in self._model_classes:
            return None
        
        model_class = self._model_classes[name]
        return model_class(hyperparameters=hyperparameters)
    
    def list_all_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())
    
    def _register_builtin_models(self) -> None:
        """Register built-in models."""
        # Import model classes
        try:
            from ..models.catalog.tabular import (
                GradientBoostingClassifierModel,
                GradientBoostingRegressorModel,
                LassoModel,
                LinearRegressionModel,
                LogisticRegressionModel,
                RandomForestClassifierModel,
                RandomForestRegressorModel,
                RidgeModel,
                SVMClassifierModel,
                SVMRegressorModel,
                XGBoostClassifierModel,
                XGBoostRegressorModel,
            )
            from ..models.catalog.neural import MLPClassifier, MLPRegressor
            from ..models.catalog.specialized import CeresPINNModel, GenericPINNModel
            
            # Register model classes
            self._model_classes["logistic_regression"] = LogisticRegressionModel
            self._model_classes["linear_regression"] = LinearRegressionModel
            self._model_classes["ridge"] = RidgeModel
            self._model_classes["lasso"] = LassoModel
            self._model_classes["random_forest"] = RandomForestClassifierModel
            self._model_classes["random_forest_regression"] = RandomForestRegressorModel
            self._model_classes["gradient_boosting"] = GradientBoostingClassifierModel
            self._model_classes["gradient_boosting_regression"] = GradientBoostingRegressorModel
            self._model_classes["svm"] = SVMClassifierModel
            self._model_classes["svm_regression"] = SVMRegressorModel
            self._model_classes["xgboost"] = XGBoostClassifierModel
            self._model_classes["xgboost_regression"] = XGBoostRegressorModel
            self._model_classes["mlp_classifier"] = MLPClassifier
            self._model_classes["mlp_regressor"] = MLPRegressor
            self._model_classes["cerespinn"] = CeresPINNModel
            self._model_classes["generic_pinn"] = GenericPINNModel
        except ImportError:
            # Models not available yet
            pass
        
        # Classification models
        self.register_model(ModelMetadata(
            name="logistic_regression",
            category=ModelCategory.CLASSIFICATION,
            description="Linear model for binary and multiclass classification",
            supported_problem_types=["binary_classification", "multiclass_classification"],
            supported_data_types=["tabular"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=True,
            fast_inference=True,
            memory_efficient=True,
            default_hyperparameters={"C": 1.0, "penalty": "l2"},
            hyperparameter_search_space={"C": [0.01, 0.1, 1.0, 10.0, 100.0], "penalty": ["l1", "l2"]},
            dependencies=["scikit-learn"],
        ))
        
        self.register_model(ModelMetadata(
            name="random_forest",
            category=ModelCategory.CLASSIFICATION,
            description="Ensemble of decision trees for classification and regression",
            supported_problem_types=["binary_classification", "multiclass_classification", "regression"],
            supported_data_types=["tabular"],
            requires_scaling=False,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=False,
            fast_inference=True,
            memory_efficient=False,
            default_hyperparameters={"n_estimators": 100, "max_depth": None},
            hyperparameter_search_space={"n_estimators": [50, 100, 200], "max_depth": [None, 10, 20, 30]},
            dependencies=["scikit-learn"],
        ))
        
        self.register_model(ModelMetadata(
            name="xgboost",
            category=ModelCategory.CLASSIFICATION,
            description="Gradient boosting trees for classification and regression",
            supported_problem_types=["binary_classification", "multiclass_classification", "regression"],
            supported_data_types=["tabular"],
            requires_scaling=False,
            handles_missing=True,
            handles_categorical=False,
            interpretable=True,
            fast_training=False,
            fast_inference=True,
            memory_efficient=False,
            default_hyperparameters={"n_estimators": 100, "learning_rate": 0.1},
            hyperparameter_search_space={"n_estimators": [50, 100, 200], "learning_rate": [0.01, 0.1, 0.3]},
            dependencies=["xgboost"],
        ))
        
        self.register_model(ModelMetadata(
            name="svm",
            category=ModelCategory.CLASSIFICATION,
            description="Support Vector Machine for classification and regression",
            supported_problem_types=["binary_classification", "multiclass_classification", "regression"],
            supported_data_types=["tabular"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=False,
            fast_training=False,
            fast_inference=True,
            memory_efficient=False,
            default_hyperparameters={"C": 1.0, "kernel": "rbf"},
            hyperparameter_search_space={"C": [0.1, 1.0, 10.0], "kernel": ["linear", "rbf", "poly"]},
            dependencies=["scikit-learn"],
        ))
        
        self.register_model(ModelMetadata(
            name="gradient_boosting",
            category=ModelCategory.CLASSIFICATION,
            description="Gradient boosting machines for classification and regression",
            supported_problem_types=["binary_classification", "multiclass_classification", "regression"],
            supported_data_types=["tabular"],
            requires_scaling=False,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=False,
            fast_inference=True,
            memory_efficient=False,
            default_hyperparameters={"n_estimators": 100, "learning_rate": 0.1},
            hyperparameter_search_space={"n_estimators": [50, 100, 200], "learning_rate": [0.01, 0.1, 0.3]},
            dependencies=["scikit-learn"],
        ))
        
        # Regression models
        self.register_model(ModelMetadata(
            name="linear_regression",
            category=ModelCategory.REGRESSION,
            description="Linear regression model",
            supported_problem_types=["regression"],
            supported_data_types=["tabular"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=True,
            fast_inference=True,
            memory_efficient=True,
            default_hyperparameters={},
            hyperparameter_search_space={},
            dependencies=["scikit-learn"],
        ))
        
        # Clustering models
        self.register_model(ModelMetadata(
            name="kmeans",
            category=ModelCategory.CLUSTERING,
            description="K-Means clustering algorithm",
            supported_problem_types=["clustering"],
            supported_data_types=["tabular"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=True,
            fast_inference=True,
            memory_efficient=True,
            default_hyperparameters={"n_clusters": 3},
            hyperparameter_search_space={"n_clusters": [2, 3, 4, 5, 6, 7, 8]},
            dependencies=["scikit-learn"],
        ))
        
        self.register_model(ModelMetadata(
            name="dbscan",
            category=ModelCategory.CLUSTERING,
            description="DBSCAN density-based clustering",
            supported_problem_types=["clustering"],
            supported_data_types=["tabular"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=True,
            fast_inference=True,
            memory_efficient=True,
            default_hyperparameters={"eps": 0.5, "min_samples": 5},
            hyperparameter_search_space={"eps": [0.3, 0.5, 0.7], "min_samples": [3, 5, 10]},
            dependencies=["scikit-learn"],
        ))
        
        # Time series models
        self.register_model(ModelMetadata(
            name="arima",
            category=ModelCategory.TIME_SERIES,
            description="ARIMA time series forecasting",
            supported_problem_types=["time_series_forecasting"],
            supported_data_types=["time_series"],
            requires_scaling=False,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=False,
            fast_inference=True,
            memory_efficient=True,
            default_hyperparameters={"order": (1, 1, 1)},
            hyperparameter_search_space={"p": [0, 1, 2], "d": [0, 1], "q": [0, 1, 2]},
            dependencies=["statsmodels"],
        ))
        
        # Computer vision models
        self.register_model(ModelMetadata(
            name="cnn",
            category=ModelCategory.COMPUTER_VISION,
            description="Convolutional Neural Network for image classification",
            supported_problem_types=["binary_classification", "multiclass_classification"],
            supported_data_types=["image"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=False,
            fast_training=False,
            fast_inference=True,
            memory_efficient=False,
            default_hyperparameters={"layers": [32, 64], "kernel_size": 3},
            hyperparameter_search_space={"layers": [[16, 32], [32, 64], [64, 128]], "kernel_size": [3, 5]},
            dependencies=["torch", "torchvision"],
        ))
        
        self.register_model(ModelMetadata(
            name="resnet",
            category=ModelCategory.COMPUTER_VISION,
            description="ResNet transfer learning for image classification",
            supported_problem_types=["binary_classification", "multiclass_classification"],
            supported_data_types=["image"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=False,
            fast_training=False,
            fast_inference=True,
            memory_efficient=False,
            default_hyperparameters={"pretrained": True, "num_classes": 2},
            hyperparameter_search_space={"pretrained": [True, False]},
            dependencies=["torch", "torchvision"],
        ))
        
        # NLP models
        self.register_model(ModelMetadata(
            name="logistic_regression_tfidf",
            category=ModelCategory.NLP,
            description="Logistic regression with TF-IDF features for text classification",
            supported_problem_types=["binary_classification", "multiclass_classification"],
            supported_data_types=["text"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=True,
            fast_training=True,
            fast_inference=True,
            memory_efficient=True,
            default_hyperparameters={"C": 1.0},
            hyperparameter_search_space={"C": [0.1, 1.0, 10.0]},
            dependencies=["scikit-learn"],
        ))
        
        # Specialized models (e.g., CeresPINN)
        self.register_model(ModelMetadata(
            name="cerespinn",
            category=ModelCategory.SPECIALIZED,
            description="Physics-Informed Neural Network for climate-adaptive maize yield prediction",
            supported_problem_types=["regression"],
            supported_data_types=["tabular"],
            requires_scaling=True,
            handles_missing=False,
            handles_categorical=False,
            interpretable=False,
            fast_training=False,
            fast_inference=True,
            memory_efficient=False,
            default_hyperparameters={"hidden_dim": 64, "num_layers": 3},
            hyperparameter_search_space={"hidden_dim": [32, 64, 128], "num_layers": [2, 3, 4]},
            dependencies=["torch"],
        ))


# Global catalog instance
_catalog = ModelCatalog()


def get_catalog() -> ModelCatalog:
    """Get the global model catalog instance."""
    return _catalog
