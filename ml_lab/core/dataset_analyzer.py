"""Dataset Analyzer - Analyzes datasets and generates profiles.

This module analyzes datasets (tabular, image, text, time series) and generates
a comprehensive DatasetProfile. The profile contains information about data types,
missing values, duplicates, outliers, distributions, and recommendations for
preprocessing, validation, and model selection.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import stats

from .dataset_profile import (
    ColumnProfile,
    CorrelationInfo,
    DataType,
    DatasetProfile,
    MissingValueStrategy,
)


class DatasetAnalyzer:
    """Analyzes datasets and generates comprehensive profiles.
    
    This analyzer supports multiple data types:
    - Tabular: CSV, Parquet, Excel, JSON
    - Image: Directory of images
    - Text: Text files
    - Time Series: Temporal data
    
    The profile generated is used by the PipelineEngine to make informed decisions
    about preprocessing, model selection, and validation strategies.
    """
    
    def __init__(self, sample_size: int = 10000):
        """Initialize the dataset analyzer.
        
        Args:
            sample_size: Maximum number of rows to sample for analysis (for large datasets).
        """
        self.sample_size = sample_size
    
    def analyze(
        self,
        dataset_path: Path,
        target_column: Optional[str] = None,
        data_type: Optional[str] = None,
    ) -> DatasetProfile:
        """Analyze a dataset and generate a profile.
        
        Args:
            dataset_path: Path to the dataset file or directory
            target_column: Name of the target column (for supervised learning)
            data_type: Type of data (auto-detected if None)
        
        Returns:
            DatasetProfile with comprehensive analysis
        """
        # Detect data type if not provided
        if data_type is None:
            data_type = self._detect_data_type(dataset_path)
        
        # Analyze based on data type
        if data_type == "tabular":
            return self._analyze_tabular(dataset_path, target_column)
        elif data_type == "image":
            return self._analyze_images(dataset_path, target_column)
        elif data_type == "text":
            return self._analyze_text(dataset_path, target_column)
        elif data_type == "time_series":
            return self._analyze_time_series(dataset_path, target_column)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
    
    def _detect_data_type(self, dataset_path: Path) -> str:
        """Detect the data type from the file/directory."""
        if dataset_path.is_file():
            suffix = dataset_path.suffix.lower()
            if suffix in [".csv", ".parquet", ".xlsx", ".xls", ".json"]:
                return "tabular"
            elif suffix in [".txt", ".json"]:
                return "text"
        elif dataset_path.is_dir():
            # Check if it contains images
            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
            for file in dataset_path.iterdir():
                if file.suffix.lower() in image_extensions:
                    return "image"
        return "tabular"  # Default
    
    def analyze_tabular(
        self, dataset: Union[Path, pd.DataFrame], target_column: Optional[str] = None
    ) -> DatasetProfile:
        """Analyze a tabular dataset (DataFrame or Path)."""
        return self._analyze_tabular(dataset, target_column)

    def _analyze_tabular(
        self, dataset_or_path: Union[Path, pd.DataFrame], target_column: Optional[str] = None
    ) -> DatasetProfile:
        """Analyze a tabular dataset."""
        # Load dataset
        if isinstance(dataset_or_path, pd.DataFrame):
            df = dataset_or_path.copy()
            dataset_path = Path("dataset.csv")
            dataset_name = "dataset"
        else:
            dataset_path = dataset_or_path
            dataset_name = dataset_path.stem
            df = self._load_tabular(dataset_path)
        
        # Sample if too large
        if len(df) > self.sample_size:
            df = df.sample(n=self.sample_size, random_state=42)
        
        # Auto-detect or resolve target column
        resolved_target = None
        if target_column and target_column in df.columns:
            resolved_target = target_column
        elif target_column:
            t_clean = target_column.strip().lower()
            for col in df.columns:
                c_clean = col.strip().lower()
                if c_clean == t_clean or t_clean in c_clean or c_clean.startswith(t_clean):
                    resolved_target = col
                    break

        if resolved_target is None:
            candidate_targets = ["yield_bu_acre", "yield", "crop_yield", "target", "label", "outcome", "class"]
            for cand in candidate_targets:
                for col in df.columns:
                    c_clean = col.strip().lower()
                    if c_clean == cand or cand in c_clean:
                        resolved_target = col
                        break
                if resolved_target:
                    break
        target_column = resolved_target

        # Create profile
        profile = DatasetProfile(
            dataset_path=dataset_path,
            dataset_name=dataset_name,
            rows=len(df),
            columns=len(df.columns),
            memory_mb=df.memory_usage(deep=True).sum() / 1024 / 1024,
            target_column=target_column,
        )
        
        # Analyze each column
        for col in df.columns:
            col_profile = self._analyze_column(df[col], col)
            profile.column_profiles.append(col_profile)
            
            # Categorize by type
            if col_profile.data_type == DataType.NUMERICAL:
                profile.numerical_features.append(col)
            elif col_profile.data_type == DataType.CATEGORICAL:
                profile.categorical_features.append(col)
            elif col_profile.data_type == DataType.TEMPORAL:
                profile.temporal_features.append(col)
            elif col_profile.data_type == DataType.BOOLEAN:
                profile.boolean_features.append(col)
            elif col_profile.data_type == DataType.TEXT:
                profile.text_features.append(col)
        
        # Analyze data quality
        profile.has_missing_values = any(
            col.missing_count > 0 for col in profile.column_profiles
        )
        profile.total_missing_count = sum(
            col.missing_count for col in profile.column_profiles
        )
        profile.total_missing_percentage = (
            profile.total_missing_count / (profile.rows * profile.columns) * 100
        )
        
        profile.has_duplicates = bool(df.duplicated().any())
        profile.duplicate_count = int(df.duplicated().sum())
        profile.duplicate_percentage = float((profile.duplicate_count / profile.rows) * 100)
        
        profile.has_constant_features = any(
            col.is_constant for col in profile.column_profiles
        )
        profile.constant_features = [
            col.name for col in profile.column_profiles if col.is_constant
        ]
        
        # Analyze target
        if target_column and target_column in df.columns:
            target_profile = profile.get_column_profile(target_column)
            profile.target_type = target_profile.data_type
            
            if target_profile.data_type in (DataType.CATEGORICAL, DataType.NUMERICAL):
                profile.target_classes = target_profile.categories
                profile.target_distribution = target_profile.category_distribution
                # Check imbalance
                if target_profile.category_distribution and len(target_profile.category_distribution) > 1:
                    counts = list(target_profile.category_distribution.values())
                    if min(counts) > 0:
                        profile.is_imbalanced = bool(max(counts) / min(counts) >= 1.5)
                        profile.imbalance_ratio = float(min(counts) / max(counts))
        
        # Analyze correlations (for numerical features)
        if len(profile.numerical_features) > 1:
            profile.correlations = self._analyze_correlations(
                df[profile.numerical_features]
            )
            profile.high_correlation_pairs = [
                (c.column1, c.column2, c.correlation)
                for c in profile.correlations
                if abs(c.correlation) > 0.8
            ]
        
        # Analyze outliers
        profile.has_outliers = any(
            col.outlier_count > 0 for col in profile.column_profiles
        )
        profile.outlier_columns = [
            col.name for col in profile.column_profiles if col.outlier_count > 0
        ]
        
        # Generate recommendations
        profile.recommended_preprocessing = self._recommend_preprocessing(profile)
        profile.recommended_validation = self._recommend_validation(profile)
        profile.recommended_models = self._recommend_models(profile)
        profile.recommended_metrics = self._recommend_metrics(profile)
        
        # Identify issues and warnings
        profile.issues = self._identify_issues(profile)
        profile.warnings = self._identify_warnings(profile)
        
        return profile
    
    def _load_tabular(self, dataset_path: Path) -> pd.DataFrame:
        """Load tabular dataset from file."""
        suffix = dataset_path.suffix.lower()
        
        if suffix == ".csv":
            return pd.read_csv(dataset_path)
        elif suffix == ".parquet":
            return pd.read_parquet(dataset_path)
        elif suffix in [".xlsx", ".xls"]:
            return pd.read_excel(dataset_path)
        elif suffix == ".json":
            return pd.read_json(dataset_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def _analyze_column(self, series: pd.Series, column_name: str) -> ColumnProfile:
        """Analyze a single column."""
        profile = ColumnProfile(
            name=column_name,
            data_type=DataType.UNKNOWN,
            dtype=str(series.dtype),
        )
        
        # Missing values
        profile.missing_count = series.isna().sum()
        profile.missing_percentage = (profile.missing_count / len(series)) * 100
        
        # Unique values
        profile.unique_count = series.nunique()
        
        # Determine data type
        col_lower = column_name.strip().lower()
        is_temporal_name = col_lower in ("year", "date", "time", "timestamp", "datetime", "yr") or col_lower.endswith(("_year", "_date"))
        
        if is_temporal_name:
            profile.data_type = DataType.TEMPORAL
            if pd.api.types.is_numeric_dtype(series):
                profile.min_value = series.min()
                profile.max_value = series.max()
                profile.mean_value = series.mean()
                profile.median_value = series.median()
                profile.std_value = series.std()
            elif pd.api.types.is_datetime64_any_dtype(series):
                profile.min_date = series.min()
                profile.max_date = series.max()
            profile.is_constant = profile.unique_count == 1
        elif pd.api.types.is_numeric_dtype(series):
            profile.data_type = DataType.NUMERICAL
            profile.min_value = series.min()
            profile.max_value = series.max()
            profile.mean_value = series.mean()
            profile.median_value = series.median()
            profile.std_value = series.std()
            
            # Check if constant
            profile.is_constant = profile.unique_count == 1
            
            # Detect outliers using IQR
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = (series < lower_bound) | (series > upper_bound)
            profile.outlier_count = outliers.sum()
            profile.outlier_percentage = (profile.outlier_count / len(series)) * 100
            
            # Cardinality
            if profile.unique_count / len(series) < 0.05:
                profile.cardinality = "low"
            elif profile.unique_count / len(series) < 0.5:
                profile.cardinality = "medium"
            else:
                profile.cardinality = "high"
                
        elif pd.api.types.is_datetime64_any_dtype(series):
            profile.data_type = DataType.TEMPORAL
            profile.min_date = series.min()
            profile.max_date = series.max()
            profile.is_constant = profile.unique_count == 1
            
        elif pd.api.types.is_bool_dtype(series):
            profile.data_type = DataType.BOOLEAN
            profile.is_constant = profile.unique_count == 1
            
        elif pd.api.types.is_string_dtype(series) or series.dtype == object:
            # Check if it's categorical or text
            if profile.unique_count <= 50 or (profile.unique_count / len(series) < 0.5):
                profile.data_type = DataType.CATEGORICAL
                profile.categories = series.dropna().unique().tolist()
                profile.category_distribution = series.value_counts().to_dict()
                profile.is_constant = profile.unique_count == 1
                profile.cardinality = "low" if profile.unique_count < 10 else "medium"
            else:
                profile.data_type = DataType.TEXT
                profile.avg_length = series.str.len().mean()
                profile.max_length = series.str.len().max()
                profile.cardinality = "high"
        else:
            profile.data_type = DataType.UNKNOWN
        
        # Check if it's an identifier (high cardinality, likely unique)
        if profile.unique_count == len(series) and profile.unique_count > 100:
            profile.is_identifier = True
        
        return profile
    
    def _analyze_correlations(self, df: pd.DataFrame) -> List[CorrelationInfo]:
        """Analyze correlations between numerical columns."""
        correlations = []
        corr_matrix = df.corr()
        
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Avoid duplicates and self-correlation
                    corr_value = corr_matrix.iloc[i, j]
                    correlations.append(
                        CorrelationInfo(
                            column1=col1,
                            column2=col2,
                            correlation=corr_value,
                            method="pearson",
                        )
                    )
        
        return correlations
    
    def _recommend_preprocessing(self, profile: DatasetProfile) -> List[str]:
        """Recommend preprocessing steps."""
        recommendations = []
        
        if profile.has_missing_values:
            recommendations.append("handle_missing_values")
        if profile.has_duplicates:
            recommendations.append("remove_duplicates")
        if profile.has_outliers:
            recommendations.append("handle_outliers")
        if profile.categorical_features:
            recommendations.append("encode_categorical")
        if profile.numerical_features:
            recommendations.append("scale_features")
        if profile.constant_features:
            recommendations.append("remove_constant_features")
        if profile.identifier_features:
            recommendations.append("remove_identifiers")
        
        return recommendations
    
    def _recommend_validation(self, profile: DatasetProfile) -> str:
        """Recommend validation strategy."""
        if profile.temporal_features:
            return "time_series_split"
        elif profile.is_imbalanced:
            return "stratified_k_fold"
        else:
            return "k_fold"
    
    def _recommend_models(self, profile: DatasetProfile) -> List[str]:
        """Recommended models based on dataset characteristics."""
        target_name = (profile.target_column or "").lower()
        is_yield_or_physics = "yield" in target_name or any(
            "yield" in c.name.lower() for c in profile.column_profiles
        )
        
        if profile.target_type == DataType.NUMERICAL or is_yield_or_physics:
            if is_yield_or_physics:
                return ["cerespinn", "xgboost", "random_forest", "gradient_boosting", "linear_regression"]
            return ["xgboost", "random_forest", "gradient_boosting", "linear_regression"]
        elif profile.target_type == DataType.CATEGORICAL:
            return ["xgboost", "random_forest", "gradient_boosting", "logistic_regression"]
        else:
            if is_yield_or_physics:
                return ["cerespinn", "xgboost", "random_forest", "gradient_boosting", "linear_regression"]
            return ["random_forest", "xgboost", "linear_regression"]
    
    def _recommend_metrics(self, profile: DatasetProfile) -> List[str]:
        """Recommended metrics based on dataset characteristics."""
        target_name = (profile.target_column or "").lower()
        is_yield_or_physics = "yield" in target_name or any(
            "yield" in c.name.lower() for c in profile.column_profiles
        )
        
        if profile.target_type == DataType.NUMERICAL or is_yield_or_physics:
            if is_yield_or_physics:
                return ["rmse", "mae", "r2", "crps", "ensemble_iqr"]
            return ["rmse", "mae", "r2"]
        elif profile.target_type == DataType.CATEGORICAL:
            if profile.is_imbalanced:
                return ["f1", "precision", "recall", "roc_auc"]
            else:
                return ["accuracy", "f1", "precision", "recall"]
        else:
            return ["rmse", "mae", "r2"]
    
    def _identify_issues(self, profile: DatasetProfile) -> List[str]:
        """Identify critical issues in the dataset."""
        issues = []
        
        if profile.total_missing_percentage > 30:
            issues.append(f"High missing value rate: {profile.total_missing_percentage:.1f}%")
        if profile.duplicate_percentage > 10:
            issues.append(f"High duplicate rate: {profile.duplicate_percentage:.1f}%")
        if profile.rows < 100:
            issues.append(f"Very small dataset: only {profile.rows} rows")
        if profile.columns < 2:
            issues.append("Dataset has less than 2 columns")
        
        return issues
    
    def _identify_warnings(self, profile: DatasetProfile) -> List[str]:
        """Identify warnings in the dataset."""
        warnings = []
        
        if profile.is_imbalanced:
            warnings.append("Target variable is imbalanced")
        if profile.has_constant_features:
            warnings.append(f"Constant features found: {', '.join(profile.constant_features)}")
        if profile.high_correlation_pairs:
            warnings.append(
                f"Highly correlated features found: {len(profile.high_correlation_pairs)} pairs"
            )
        if profile.has_outliers:
            warnings.append(f"Outliers detected in {len(profile.outlier_columns)} columns")
        
        return warnings
    
    def _analyze_images(
        self, dataset_path: Path, target_column: Optional[str]
    ) -> DatasetProfile:
        """Analyze image dataset (placeholder for future implementation)."""
        # TODO: Implement image analysis
        profile = DatasetProfile(
            dataset_path=dataset_path,
            dataset_name=dataset_path.stem,
            detected_data_type="image",
        )
        profile.issues.append("Image analysis not yet implemented")
        return profile
    
    def _analyze_text(
        self, dataset_path: Path, target_column: Optional[str]
    ) -> DatasetProfile:
        """Analyze text dataset (placeholder for future implementation)."""
        # TODO: Implement text analysis
        profile = DatasetProfile(
            dataset_path=dataset_path,
            dataset_name=dataset_path.stem,
            detected_data_type="text",
        )
        profile.issues.append("Text analysis not yet implemented")
        return profile
    
    def _analyze_time_series(
        self, dataset_path: Path, target_column: Optional[str]
    ) -> DatasetProfile:
        """Analyze time series dataset (placeholder for future implementation)."""
        # TODO: Implement time series analysis
        profile = DatasetProfile(
            dataset_path=dataset_path,
            dataset_name=dataset_path.stem,
            detected_data_type="time_series",
        )
        profile.issues.append("Time series analysis not yet implemented")
        return profile
