"""Core module for ML Lab.

This module provides the core components for ML Lab including:
- Project Specification
- Dataset Profile
- Pipeline Plan
- Project Analyzer
- Dataset Analyzer
- Pipeline Engine
- Model Catalog
- Metrics Engine
- Artifact Manager
"""
from .artifact_manager import ArtifactManager, get_artifact_manager
from .dataset_analyzer import DatasetAnalyzer
from .dataset_profile import (
    ColumnProfile,
    CorrelationInfo,
    DataType,
    DatasetProfile,
    MissingValueStrategy,
)
from .model_catalog import (
    BaseModel,
    ModelCatalog,
    ModelCategory,
    ModelMetadata,
    get_catalog,
)
from .metrics_engine import (
    MetricCategory,
    MetricDefinition,
    MetricDirection,
    MetricsEngine,
    get_metrics_engine,
)
from .pipeline_engine import PipelineEngine
from .pipeline_plan import (
    PipelinePlan,
    PipelineStep,
    StepDependency,
    StepExecution,
    StepStatus,
)
from .project import (
    DataType as ProjectDataType,
    ExplainabilityConfig,
    HyperparameterConfig,
    MetricConfig,
    ModelConfig,
    Objective,
    PreprocessingConfig,
    ProblemType,
    ProjectSpecification,
    StatisticalTestConfig,
    ValidationConfig,
    ValidationStrategy,
)
from .project_analyzer import ProjectAnalyzer
from .report_generator import ReportGenerator, get_report_generator

__all__ = [
    # Project Specification
    "ProjectSpecification",
    "ProblemType",
    "DataType",
    "Objective",
    "ValidationStrategy",
    "PreprocessingConfig",
    "ValidationConfig",
    "ModelConfig",
    "MetricConfig",
    "ExplainabilityConfig",
    "HyperparameterConfig",
    "StatisticalTestConfig",
    # Dataset Profile
    "DatasetProfile",
    "ColumnProfile",
    "CorrelationInfo",
    "DataType",
    "MissingValueStrategy",
    # Pipeline Plan
    "PipelinePlan",
    "PipelineStep",
    "StepStatus",
    "StepExecution",
    "StepDependency",
    # Analyzers
    "ProjectAnalyzer",
    "DatasetAnalyzer",
    # Engines
    "PipelineEngine",
    "ModelCatalog",
    "MetricsEngine",
    "ArtifactManager",
    # Catalog
    "BaseModel",
    "ModelMetadata",
    "ModelCategory",
    # Helpers
    "get_catalog",
    "get_metrics_engine",
    "get_artifact_manager",
]
