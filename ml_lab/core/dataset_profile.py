"""Dataset Profile - Structured analysis of dataset characteristics.

This module defines the DatasetProfile dataclass which contains comprehensive
information about a dataset's characteristics. This profile is used by the
PipelineEngine to make decisions about preprocessing, model selection, and
validation strategies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class DataType(Enum):
    """Data type of a column."""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class MissingValueStrategy(Enum):
    """Strategy for handling missing values."""
    DROP = "drop"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    CONSTANT = "constant"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    INTERPOLATE = "interpolate"


@dataclass
class ColumnProfile:
    """Profile of a single column."""
    name: str
    data_type: DataType
    dtype: str  # pandas dtype
    missing_count: int = 0
    missing_percentage: float = 0.0
    unique_count: int = 0
    cardinality: str = "low"  # "low", "medium", "high"
    is_constant: bool = False
    is_identifier: bool = False
    
    # Numerical statistics
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None
    
    # Categorical statistics
    categories: Optional[List[str]] = None
    category_distribution: Optional[Dict[str, int]] = None
    
    # Temporal statistics
    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None
    
    # Text statistics
    avg_length: Optional[float] = None
    max_length: Optional[int] = None
    
    # Outliers
    outlier_count: int = 0
    outlier_percentage: float = 0.0


@dataclass
class CorrelationInfo:
    """Correlation information between columns."""
    column1: str
    column2: str
    correlation: float
    method: str = "pearson"  # "pearson", "spearman", "kendall"


@dataclass
class DatasetProfile:
    """Comprehensive profile of a dataset.
    
    This profile contains all information needed to make informed decisions
    about preprocessing, model selection, and validation strategies.
    """
    # Basic Information
    dataset_path: Optional[Path] = None
    dataset_name: str = ""
    rows: int = 0
    columns: int = 0
    memory_mb: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    
    # Column Information
    column_profiles: List[ColumnProfile] = field(default_factory=list)
    numerical_features: List[str] = field(default_factory=list)
    categorical_features: List[str] = field(default_factory=list)
    temporal_features: List[str] = field(default_factory=list)
    text_features: List[str] = field(default_factory=list)
    boolean_features: List[str] = field(default_factory=list)
    
    # Data Quality
    has_missing_values: bool = False
    total_missing_count: int = 0
    total_missing_percentage: float = 0.0
    has_duplicates: bool = False
    duplicate_count: int = 0
    duplicate_percentage: float = 0.0
    has_constant_features: bool = False
    constant_features: List[str] = field(default_factory=list)
    has_identifiers: bool = False
    identifier_features: List[str] = field(default_factory=list)
    
    # Target Information
    target_column: Optional[str] = None
    target_type: Optional[DataType] = None
    target_classes: Optional[List[str]] = None
    target_distribution: Optional[Dict[str, int]] = None
    is_imbalanced: bool = False
    imbalance_ratio: Optional[float] = None  # minority_class / majority_class
    
    # Correlations
    correlations: List[CorrelationInfo] = field(default_factory=list)
    high_correlation_pairs: List[tuple] = field(default_factory=list)  # (col1, col2, corr)
    
    # Outliers
    has_outliers: bool = False
    outlier_columns: List[str] = field(default_factory=list)
    
    # Data Type Detection
    detected_data_type: str = "tabular"  # "tabular", "image", "text", "time_series"
    
    # Recommendations
    recommended_preprocessing: List[str] = field(default_factory=list)
    recommended_validation: str = "train_test_split"
    recommended_models: List[str] = field(default_factory=list)
    recommended_metrics: List[str] = field(default_factory=list)
    
    # Potential Issues
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_column_profile(self, column_name: str) -> Optional[ColumnProfile]:
        """Get profile for a specific column."""
        for col in self.column_profiles:
            if col.name == column_name:
                return col
        return None
    
    def get_missing_value_strategy(self, column_name: str) -> MissingValueStrategy:
        """Recommend missing value strategy for a column."""
        profile = self.get_column_profile(column_name)
        if profile is None:
            return MissingValueStrategy.DROP
        
        if profile.missing_percentage > 0.5:
            return MissingValueStrategy.DROP
        elif profile.data_type == DataType.NUMERICAL:
            return MissingValueStrategy.MEAN
        elif profile.data_type == DataType.CATEGORICAL:
            return MissingValueStrategy.MODE
        elif profile.data_type == DataType.TEMPORAL:
            return MissingValueStrategy.FORWARD_FILL
        else:
            return MissingValueStrategy.DROP
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        from dataclasses import asdict
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetProfile":
        """Create profile from dictionary."""
        # Handle datetime
        if "analyzed_at" in data and isinstance(data["analyzed_at"], str):
            data["analyzed_at"] = datetime.fromisoformat(data["analyzed_at"])
        
        # Handle Path
        if "dataset_path" in data and isinstance(data["dataset_path"], str):
            data["dataset_path"] = Path(data["dataset_path"])
        
        # Handle enums in column profiles
        if "column_profiles" in data:
            for col in data["column_profiles"]:
                if "data_type" in col and isinstance(col["data_type"], str):
                    col["data_type"] = DataType(col["data_type"])
        
        return cls(**data)
    
    def save(self, path: Path) -> None:
        """Save profile to JSON file."""
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: Path) -> "DatasetProfile":
        """Load profile from JSON file."""
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
