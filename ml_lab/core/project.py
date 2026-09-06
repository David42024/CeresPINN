"""Project Specification - Central data structure for ML Lab projects.

This module defines the ProjectSpecification dataclass which serves as the
single source of truth for pipeline generation. It contains all information
needed to determine the appropriate ML pipeline based on context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class DataType(Enum):
    """Type of data the project works with."""
    TABULAR = "tabular"
    IMAGE = "image"
    TEXT = "text"
    TIME_SERIES = "time_series"
    MULTIMODAL = "multimodal"
    GEOSPATIAL = "geospatial"


class ProblemType(Enum):
    """Type of ML problem."""
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES_FORECASTING = "time_series_forecasting"
    OBJECT_DETECTION = "object_detection"
    SEMANTIC_SEGMENTATION = "semantic_segmentation"


class Objective(Enum):
    """Business/research objective."""
    PREDICTION = "prediction"
    INFERENCE = "inference"
    EXPLANATION = "explanation"
    GENERATION = "generation"
    OPTIMIZATION = "optimization"


class ValidationStrategy(Enum):
    """Validation strategy based on problem type."""
    TRAIN_TEST_SPLIT = "train_test_split"
    K_FOLD = "k_fold"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    TIME_SERIES_SPLIT = "time_series_split"
    GROUP_K_FOLD = "group_k_fold"
    REPEATED_K_FOLD = "repeated_k_fold"
    LEAVE_ONE_OUT = "leave_one_out"


@dataclass
class PreprocessingConfig:
    """Preprocessing configuration."""
    handle_missing: bool = True
    handle_duplicates: bool = True
    handle_outliers: bool = False
    scaling: Optional[str] = None  # "standard", "minmax", "robust"
    encoding: Optional[str] = None  # "onehot", "label", "target"
    feature_selection: bool = False
    feature_engineering: bool = False
    custom_transformations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationConfig:
    """Validation configuration."""
    strategy: ValidationStrategy = ValidationStrategy.TRAIN_TEST_SPLIT
    test_size: float = 0.2
    n_splits: int = 5
    random_state: int = 42
    group_column: Optional[str] = None
    time_column: Optional[str] = None


@dataclass
class ModelConfig:
    """Model configuration."""
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class MetricConfig:
    """Metric configuration."""
    primary: str
    secondary: List[str] = field(default_factory=list)
    direction: str = "maximize"  # "maximize" or "minimize"


@dataclass
class ExplainabilityConfig:
    """Explainability configuration."""
    enabled: bool = True
    methods: List[str] = field(default_factory=list)  # "shap", "feature_importance", "permutation"


@dataclass
class HyperparameterConfig:
    """Hyperparameter tuning configuration."""
    enabled: bool = False
    method: str = "grid_search"  # "grid_search", "random_search", "bayesian"
    n_iter: int = 10
    cv: int = 5
    search_space: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatisticalTestConfig:
    """Statistical test configuration."""
    enabled: bool = True
    tests: List[str] = field(default_factory=list)  # "ks_test", "t_test", "mcnemar", etc.
    alpha: float = 0.05


@dataclass
class ProjectSpecification:
    """Central specification for an ML Lab project.
    
    This dataclass contains all information needed to generate an appropriate
    ML pipeline based on the project context. It is populated by the
    ProjectAnalyzer and consumed by the PipelineEngine.
    """
    # Project Metadata
    project_id: str
    project_name: str
    description: str
    domain: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Problem Definition
    problem_type: ProblemType
    data_type: DataType
    objective: Objective
    target_variable: Optional[str] = None
    business_objective: str = ""
    constraints: List[str] = field(default_factory=list)
    
    # Dataset Information
    dataset_path: Optional[Path] = None
    dataset_source: str = "upload"  # "upload", "url", "database", "provider"
    dataset_version: str = "v1"
    
    # Features
    features: List[str] = field(default_factory=list)
    feature_types: Dict[str, str] = field(default_factory=dict)  # feature -> type
    categorical_features: List[str] = field(default_factory=list)
    numerical_features: List[str] = field(default_factory=list)
    temporal_features: List[str] = field(default_factory=list)
    
    # Class Information (for classification)
    classes: Optional[List[str]] = None
    class_balance: Optional[str] = None  # "balanced", "imbalanced", "unknown"
    
    # Pipeline Configuration
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    models: List[ModelConfig] = field(default_factory=list)
    metrics: MetricConfig = field(default_factory=lambda: MetricConfig(primary="accuracy"))
    hyperparameter_tuning: HyperparameterConfig = field(default_factory=HyperparameterConfig)
    explainability: ExplainabilityConfig = field(default_factory=ExplainabilityConfig)
    statistical_tests: StatisticalTestConfig = field(default_factory=StatisticalTestConfig)
    
    # Reproducibility
    random_seed: int = 42
    python_version: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)
    
    # Artifact Paths
    project_dir: Optional[Path] = None
    artifacts_dir: Optional[Path] = None
    models_dir: Optional[Path] = None
    reports_dir: Optional[Path] = None
    
    # Status
    status: str = "created"  # "created", "analyzing", "analyzed", "training", "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert specification to dictionary."""
        from dataclasses import asdict
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectSpecification":
        """Create specification from dictionary."""
        # Handle enum conversions
        if "problem_type" in data and isinstance(data["problem_type"], str):
            data["problem_type"] = ProblemType(data["problem_type"])
        if "data_type" in data and isinstance(data["data_type"], str):
            data["data_type"] = DataType(data["data_type"])
        if "objective" in data and isinstance(data["objective"], str):
            data["objective"] = Objective(data["objective"])
        if "validation" in data and "strategy" in data["validation"]:
            if isinstance(data["validation"]["strategy"], str):
                data["validation"]["strategy"] = ValidationStrategy(data["validation"]["strategy"])
        
        # Handle datetime
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        # Handle Path objects
        if "dataset_path" in data and isinstance(data["dataset_path"], str):
            data["dataset_path"] = Path(data["dataset_path"])
        if "project_dir" in data and isinstance(data["project_dir"], str):
            data["project_dir"] = Path(data["project_dir"])
        if "artifacts_dir" in data and isinstance(data["artifacts_dir"], str):
            data["artifacts_dir"] = Path(data["artifacts_dir"])
        if "models_dir" in data and isinstance(data["models_dir"], str):
            data["models_dir"] = Path(data["models_dir"])
        if "reports_dir" in data and isinstance(data["reports_dir"], str):
            data["reports_dir"] = Path(data["reports_dir"])
        
        return cls(**data)
    
    def save(self, path: Path) -> None:
        """Save specification to JSON file."""
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: Path) -> "ProjectSpecification":
        """Load specification from JSON file."""
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
