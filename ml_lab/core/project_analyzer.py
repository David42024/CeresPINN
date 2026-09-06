"""Project Analyzer - Analyzes project context and generates specification.

This module analyzes the project context provided by the user (natural language
description, domain, objective, etc.) and generates a ProjectSpecification.
It uses rule-based analysis with optional LLM integration for context interpretation.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .project import (
    DataType,
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
from .dataset_profile import DatasetProfile


class ProjectAnalyzer:
    """Analyzes project context and generates ProjectSpecification.
    
    This analyzer uses rule-based pattern matching to determine problem type,
    data type, objective, and recommended configurations based on the user's
    natural language description and domain.
    """
    
    # Keywords for problem type detection
    CLASSIFICATION_KEYWORDS = [
        "classify", "classification", "predict class", "categorize", "category",
        "churn", "fraud", "spam", "default", "detect", "diagnose", "identify",
        "binary", "multiclass", "class", "label"
    ]
    
    REGRESSION_KEYWORDS = [
        "predict", "forecast", "estimate", "regression", "price", "value",
        "amount", "quantity", "yield", "output", "continuous", "numeric",
        "score", "rate", "temperature", "sales", "revenue"
    ]
    
    CLUSTERING_KEYWORDS = [
        "cluster", "group", "segment", "unsupervised", "discover patterns",
        "grouping", "similar", "anomaly", "outlier"
    ]
    
    TIME_SERIES_KEYWORDS = [
        "time series", "forecast", "temporal", "sequence", "trend", "seasonal",
        "over time", "historical", "future", "prediction over time"
    ]
    
    IMAGE_KEYWORDS = [
        "image", "photo", "picture", "visual", "object detection", "segmentation",
        "cnn", "convolutional", "pixel"
    ]
    
    TEXT_KEYWORDS = [
        "text", "nlp", "language", "sentiment", "document", "word", "token",
        "semantic", "translation", "summarization"
    ]
    
    # Keywords for objective detection
    PREDICTION_KEYWORDS = ["predict", "forecast", "estimate"]
    EXPLANATION_KEYWORDS = ["explain", "interpret", "understand", "why"]
    OPTIMIZATION_KEYWORDS = ["optimize", "maximize", "minimize", "best"]
    
    # Domain-specific patterns
    AGRICULTURE_KEYWORDS = ["crop", "yield", "soil", "weather", "agriculture", "farm"]
    FINANCE_KEYWORDS = ["stock", "price", "financial", "trading", "investment"]
    HEALTH_KEYWORDS = ["medical", "health", "disease", "patient", "diagnosis"]
    RETAIL_KEYWORDS = ["customer", "product", "sales", "retail", "e-commerce"]
    
    def __init__(self, use_llm: bool = False):
        """Initialize the project analyzer.
        
        Args:
            use_llm: Whether to use LLM for context interpretation (future feature).
        """
        self.use_llm = use_llm
    
    def analyze(
        self,
        project_name: str,
        description: str,
        domain: str,
        business_objective: str,
        constraints: List[str],
        dataset_path: Optional[Path] = None,
        target_variable: Optional[str] = None,
    ) -> ProjectSpecification:
        """Analyze project context and generate specification.
        
        Args:
            project_name: Name of the project
            description: Natural language description of the problem
            domain: Domain of the project (e.g., "agriculture", "finance")
            business_objective: Business/research objective
            constraints: List of constraints
            dataset_path: Path to dataset (optional)
            target_variable: Name of target variable (optional)
        
        Returns:
            ProjectSpecification with analyzed configuration
        """
        # Generate project ID
        project_id = self._generate_project_id(project_name)
        
        # Detect problem type
        problem_type = self._detect_problem_type(description, business_objective)
        
        # Detect data type
        data_type = self._detect_data_type(description, domain)
        
        # Detect objective
        objective = self._detect_objective(business_objective)
        
        # Generate recommended configurations
        validation_config = self._recommend_validation(problem_type, data_type)
        metrics_config = self._recommend_metrics(problem_type, objective)
        models_config = self._recommend_models(problem_type, data_type)
        preprocessing_config = self._recommend_preprocessing(problem_type, data_type)
        explainability_config = self._recommend_explainability(problem_type, objective)
        statistical_config = self._recommend_statistical_tests(problem_type)
        
        # Create specification
        spec = ProjectSpecification(
            project_id=project_id,
            project_name=project_name,
            description=description,
            domain=domain,
            problem_type=problem_type,
            data_type=data_type,
            objective=objective,
            target_variable=target_variable,
            business_objective=business_objective,
            constraints=constraints,
            dataset_path=dataset_path,
            validation=validation_config,
            metrics=metrics_config,
            models=models_config,
            preprocessing=preprocessing_config,
            explainability=explainability_config,
            statistical_tests=statistical_config,
        )
        
        return spec
    
    def _generate_project_id(self, project_name: str) -> str:
        """Generate a unique project ID."""
        import uuid
        # Create a slug from project name
        slug = re.sub(r"[^a-zA-Z0-9-]", "-", project_name.lower())
        slug = re.sub(r"-+", "-", slug).strip("-")
        return f"{slug}-{uuid.uuid4().hex[:8]}"
    
    def _detect_problem_type(self, description: str, objective: str) -> ProblemType:
        """Detect problem type from description and objective."""
        text = (description + " " + objective).lower()
        
        # Check for time series first (can overlap with regression)
        if any(keyword in text for keyword in self.TIME_SERIES_KEYWORDS):
            return ProblemType.TIME_SERIES_FORECASTING
        
        # Check for clustering
        if any(keyword in text for keyword in self.CLUSTERING_KEYWORDS):
            return ProblemType.CLUSTERING
        
        # Check for classification
        if any(keyword in text for keyword in self.CLASSIFICATION_KEYWORDS):
            # Check if binary or multiclass
            if "binary" in text or "two" in text or "2" in text:
                return ProblemType.BINARY_CLASSIFICATION
            return ProblemType.MULTICLASS_CLASSIFICATION
        
        # Check for regression
        if any(keyword in text for keyword in self.REGRESSION_KEYWORDS):
            return ProblemType.REGRESSION
        
        # Default to binary classification
        return ProblemType.BINARY_CLASSIFICATION
    
    def _detect_data_type(self, description: str, domain: str) -> DataType:
        """Detect data type from description and domain."""
        text = (description + " " + domain).lower()
        
        if any(keyword in text for keyword in self.IMAGE_KEYWORDS):
            return DataType.IMAGE
        if any(keyword in text for keyword in self.TEXT_KEYWORDS):
            return DataType.TEXT
        if any(keyword in text for keyword in self.TIME_SERIES_KEYWORDS):
            return DataType.TIME_SERIES
        
        # Default to tabular
        return DataType.TABULAR
    
    def _detect_objective(self, business_objective: str) -> Objective:
        """Detect objective from business objective."""
        text = business_objective.lower()
        
        if any(keyword in text for keyword in self.EXPLANATION_KEYWORDS):
            return Objective.EXPLANATION
        if any(keyword in text for keyword in self.OPTIMIZATION_KEYWORDS):
            return Objective.OPTIMIZATION
        
        return Objective.PREDICTION
    
    def _recommend_validation(
        self, problem_type: ProblemType, data_type: DataType
    ) -> ValidationConfig:
        """Recommend validation strategy based on problem type."""
        if problem_type == ProblemType.TIME_SERIES_FORECASTING:
            return ValidationConfig(strategy=ValidationStrategy.TIME_SERIES_SPLIT)
        elif problem_type in (ProblemType.BINARY_CLASSIFICATION, ProblemType.MULTICLASS_CLASSIFICATION):
            return ValidationConfig(strategy=ValidationStrategy.STRATIFIED_K_FOLD, n_splits=5)
        elif problem_type == ProblemType.REGRESSION:
            return ValidationConfig(strategy=ValidationStrategy.K_FOLD, n_splits=5)
        else:
            return ValidationConfig(strategy=ValidationStrategy.TRAIN_TEST_SPLIT)
    
    def _recommend_metrics(self, problem_type: ProblemType, objective: Objective) -> MetricConfig:
        """Recommend metrics based on problem type and objective."""
        if problem_type == ProblemType.BINARY_CLASSIFICATION:
            return MetricConfig(
                primary="f1",
                secondary=["accuracy", "precision", "recall", "roc_auc", "pr_auc"],
                direction="maximize"
            )
        elif problem_type == ProblemType.MULTICLASS_CLASSIFICATION:
            return MetricConfig(
                primary="f1_weighted",
                secondary=["accuracy", "f1_macro", "precision_weighted", "recall_weighted"],
                direction="maximize"
            )
        elif problem_type == ProblemType.REGRESSION:
            return MetricConfig(
                primary="rmse",
                secondary=["mae", "r2", "mape"],
                direction="minimize"
            )
        elif problem_type == ProblemType.TIME_SERIES_FORECASTING:
            return MetricConfig(
                primary="mae",
                secondary=["rmse", "mape", "smape"],
                direction="minimize"
            )
        elif problem_type == ProblemType.CLUSTERING:
            return MetricConfig(
                primary="silhouette",
                secondary=["calinski_harabasz", "davies_bouldin"],
                direction="maximize"
            )
        else:
            return MetricConfig(primary="accuracy")
    
    def _recommend_models(
        self, problem_type: ProblemType, data_type: DataType
    ) -> List[ModelConfig]:
        """Recommend models based on problem type and data type."""
        models = []
        
        if data_type == DataType.TABULAR:
            if problem_type == ProblemType.BINARY_CLASSIFICATION:
                models.extend([
                    ModelConfig(name="logistic_regression", enabled=True),
                    ModelConfig(name="random_forest", enabled=True),
                    ModelConfig(name="xgboost", enabled=True),
                    ModelConfig(name="svm", enabled=True),
                    ModelConfig(name="gradient_boosting", enabled=True),
                ])
            elif problem_type == ProblemType.MULTICLASS_CLASSIFICATION:
                models.extend([
                    ModelConfig(name="random_forest", enabled=True),
                    ModelConfig(name="xgboost", enabled=True),
                    ModelConfig(name="gradient_boosting", enabled=True),
                    ModelConfig(name="svm", enabled=True),
                ])
            elif problem_type == ProblemType.REGRESSION:
                models.extend([
                    ModelConfig(name="linear_regression", enabled=True),
                    ModelConfig(name="random_forest", enabled=True),
                    ModelConfig(name="xgboost", enabled=True),
                    ModelConfig(name="gradient_boosting", enabled=True),
                    ModelConfig(name="svm", enabled=True),
                ])
            elif problem_type == ProblemType.TIME_SERIES_FORECASTING:
                models.extend([
                    ModelConfig(name="arima", enabled=True),
                    ModelConfig(name="prophet", enabled=True),
                    ModelConfig(name="lstm", enabled=True),
                ])
            elif problem_type == ProblemType.CLUSTERING:
                models.extend([
                    ModelConfig(name="kmeans", enabled=True),
                    ModelConfig(name="dbscan", enabled=True),
                    ModelConfig(name="hierarchical", enabled=True),
                ])
        elif data_type == DataType.IMAGE:
            models.extend([
                ModelConfig(name="cnn", enabled=True),
                ModelConfig(name="resnet", enabled=True),
                ModelConfig(name="efficientnet", enabled=True),
            ])
        elif data_type == DataType.TEXT:
            models.extend([
                ModelConfig(name="logistic_regression_tfidf", enabled=True),
                ModelConfig(name="random_forest_tfidf", enabled=True),
                ModelConfig(name="bert", enabled=True),
            ])
        
        return models
    
    def _recommend_preprocessing(
        self, problem_type: ProblemType, data_type: DataType
    ) -> PreprocessingConfig:
        """Recommend preprocessing based on problem type and data type."""
        if data_type == DataType.TABULAR:
            return PreprocessingConfig(
                handle_missing=True,
                handle_duplicates=True,
                handle_outliers=True,
                scaling="standard",
                encoding="onehot",
                feature_selection=False,
                feature_engineering=True,
            )
        elif data_type == DataType.IMAGE:
            return PreprocessingConfig(
                handle_missing=False,
                handle_duplicates=True,
                handle_outliers=False,
                scaling="minmax",
                encoding=None,
                feature_selection=False,
                feature_engineering=False,
            )
        elif data_type == DataType.TEXT:
            return PreprocessingConfig(
                handle_missing=False,
                handle_duplicates=True,
                handle_outliers=False,
                scaling=None,
                encoding=None,
                feature_selection=False,
                feature_engineering=True,
            )
        else:
            return PreprocessingConfig()
    
    def _recommend_explainability(
        self, problem_type: ProblemType, objective: Objective
    ) -> ExplainabilityConfig:
        """Recommend explainability based on problem type and objective."""
        if objective == Objective.EXPLANATION:
            return ExplainabilityConfig(
                enabled=True,
                methods=["shap", "feature_importance", "permutation"]
            )
        elif problem_type in (ProblemType.BINARY_CLASSIFICATION, ProblemType.REGRESSION):
            return ExplainabilityConfig(
                enabled=True,
                methods=["shap", "feature_importance"]
            )
        else:
            return ExplainabilityConfig(enabled=False)
    
    def _recommend_statistical_tests(self, problem_type: ProblemType) -> StatisticalTestConfig:
        """Recommend statistical tests based on problem type."""
        if problem_type in (ProblemType.BINARY_CLASSIFICATION, ProblemType.MULTICLASS_CLASSIFICATION):
            return StatisticalTestConfig(
                enabled=True,
                tests=["mcnemar", "cochran_q", "bootstrap"],
                alpha=0.05
            )
        elif problem_type == ProblemType.REGRESSION:
            return StatisticalTestConfig(
                enabled=True,
                tests=["paired_t_test", "bootstrap"],
                alpha=0.05
            )
        else:
            return StatisticalTestConfig(enabled=False)
    
    def refine_from_dataset(
        self, spec: ProjectSpecification, dataset_profile: DatasetProfile
    ) -> ProjectSpecification:
        """Refine specification based on dataset analysis.
        
        Args:
            spec: Initial project specification
            dataset_profile: Profile of the dataset
        
        Returns:
            Refined project specification
        """
        # Update data type if detected from dataset
        spec.data_type = DataType(dataset_profile.detected_data_type)
        
        # Update feature lists
        spec.features = [col.name for col in dataset_profile.column_profiles]
        spec.numerical_features = dataset_profile.numerical_features
        spec.categorical_features = dataset_profile.categorical_features
        spec.temporal_features = dataset_profile.temporal_features
        
        # Update target information
        if dataset_profile.target_column:
            spec.target_variable = dataset_profile.target_column
            spec.target_type = dataset_profile.target_type
            spec.target_classes = dataset_profile.target_classes
            spec.is_imbalanced = dataset_profile.is_imbalanced
            spec.imbalance_ratio = dataset_profile.imbalance_ratio
        
        # Adjust validation strategy if imbalanced
        if dataset_profile.is_imbalanced and spec.problem_type in (
            ProblemType.BINARY_CLASSIFICATION,
            ProblemType.MULTICLASS_CLASSIFICATION,
        ):
            spec.validation.strategy = ValidationStrategy.STRATIFIED_K_FOLD
        
        # Adjust preprocessing based on data quality
        if dataset_profile.has_missing_values:
            spec.preprocessing.handle_missing = True
        if dataset_profile.has_duplicates:
            spec.preprocessing.handle_duplicates = True
        if dataset_profile.has_outliers:
            spec.preprocessing.handle_outliers = True
        
        # Use dataset recommendations
        spec.models = [
            ModelConfig(name=model, enabled=True)
            for model in dataset_profile.recommended_models
        ]
        spec.metrics.secondary = dataset_profile.recommended_metrics
        spec.validation.strategy = dataset_profile.recommended_validation
        
        spec.updated_at = dataset_profile.analyzed_at
        
        return spec
