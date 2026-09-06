# ML Lab Extension Guide

This guide explains how to extend ML Lab with new models, data sources, metrics, and statistical tests.

## Adding New Models

### Step 1: Define Model Metadata

Add your model to the `ModelCatalog` in `core/model_catalog.py`:

```python
from core.model_catalog import ModelCategory, ModelMetadata

# Add to the model registry
MODEL_REGISTRY = {
    # ... existing models
    "my_custom_model": ModelMetadata(
        name="my_custom_model",
        category=ModelCategory.TREE_BASED,
        description="My custom model description",
        supported_problem_types=[ProblemType.REGRESSION, ProblemType.BINARY_CLASSIFICATION],
        supported_data_types=[DataType.TABULAR],
        requires_scaling=True,
        handles_missing=False,
        handles_categorical=False,
        interpretable=True,
        fast_training=True,
        fast_inference=True,
        memory_efficient=True,
        dependencies=["scikit-learn"],
        default_hyperparameters={
            "n_estimators": 100,
            "max_depth": 5,
        },
        hyperparameter_search_space={
            "n_estimators": [50, 100, 200],
            "max_depth": [3, 5, 7],
        },
    ),
}
```

### Step 2: Implement Model Class

Create a model class that inherits from `BaseModel`:

```python
from core.model_catalog import BaseModel
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

class MyCustomModel(BaseModel):
    """Custom model implementation."""
    
    def __init__(self, hyperparameters: Dict[str, Any]):
        self.hyperparameters = hyperparameters
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the underlying model."""
        # Determine if classification or regression
        if self.hyperparameters.get("problem_type") == "classification":
            self.model = RandomForestClassifier(
                n_estimators=self.hyperparameters.get("n_estimators", 100),
                max_depth=self.hyperparameters.get("max_depth", 5),
                random_state=self.hyperparameters.get("random_state", 42),
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=self.hyperparameters.get("n_estimators", 100),
                max_depth=self.hyperparameters.get("max_depth", 5),
                random_state=self.hyperparameters.get("random_state", 42),
            )
    
    def fit(self, X, y, X_val=None, y_val=None, early_stopping=False, early_stopping_patience=10):
        """Train the model."""
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        """Make predictions."""
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Return prediction probabilities."""
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        raise NotImplementedError("This model does not support predict_proba")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance."""
        if hasattr(self.model, "feature_importances_"):
            return dict(zip(self.hyperparameters.get("feature_names", []), 
                            self.model.feature_importances_))
        return {}
```

### Step 3: Register Model in Catalog

Add the model creation function to `ModelCatalog`:

```python
def create_model(self, model_name: str, hyperparameters: Dict[str, Any] = None) -> BaseModel:
    """Create a model instance."""
    if model_name == "my_custom_model":
        return MyCustomModel(hyperparameters or {})
    # ... existing models
```

## Adding New Data Sources

### Step 1: Define Data Source Type

Add to `DataSourceType` enum in `core/project.py`:

```python
class DataSourceType(Enum):
    UPLOAD = "upload"
    URL = "url"
    DATABASE = "database"
    PROVIDER = "provider"
    API = "api"  # New data source
    STREAM = "stream"  # New data source
```

### Step 2: Implement Data Extractor

Create a data extractor following the adapter pattern:

```python
from abc import ABC, abstractmethod
import pandas as pd

class DataExtractor(ABC):
    """Base class for data extractors."""
    
    @abstractmethod
    def extract(self, source: str, **kwargs) -> pd.DataFrame:
        """Extract data from source."""
        pass

class APIExtractor(DataExtractor):
    """Extract data from API."""
    
    def extract(self, source: str, **kwargs) -> pd.DataFrame:
        """Extract data from API endpoint."""
        import requests
        
        response = requests.get(source, params=kwargs)
        response.raise_for_status()
        
        data = response.json()
        return pd.DataFrame(data)

class StreamExtractor(DataExtractor):
    """Extract data from streaming source."""
    
    def extract(self, source: str, **kwargs) -> pd.DataFrame:
        """Extract data from streaming source."""
        # Implementation depends on streaming protocol
        pass
```

### Step 3: Register Extractor

Add to `DataSourceRegistry`:

```python
class DataSourceRegistry:
    """Registry for data extractors."""
    
    _extractors = {
        "upload": FileExtractor(),
        "url": URLExtractor(),
        "database": DatabaseExtractor(),
        "api": APIExtractor(),
        "stream": StreamExtractor(),
    }
    
    @classmethod
    def get_extractor(cls, source_type: str) -> DataExtractor:
        """Get extractor for source type."""
        return cls._extractors.get(source_type)
```

## Adding New Metrics

### Step 1: Implement Metric Function

Add metric function to `core/metrics_engine.py`:

```python
def calculate_custom_metric(y_true, y_pred, y_proba=None) -> float:
    """Calculate custom metric."""
    # Implement your metric calculation
    error = np.abs(y_true - y_pred)
    return np.mean(error)
```

### Step 2: Register Metric

Add to the metrics registry:

```python
METRICS_REGISTRY = {
    # ... existing metrics
    "custom_metric": {
        "function": calculate_custom_metric,
        "direction": "minimize",  # or "maximize"
        "problem_types": ["regression"],
        "requires_proba": False,
    },
}
```

### Step 3: Update Problem Type Mapping

Add to `get_metrics_for_problem_type()`:

```python
def get_metrics_for_problem_type(self, problem_type: str) -> List[str]:
    """Get metrics for a problem type."""
    if problem_type == "regression":
        return ["mse", "mae", "r2", "rmse", "custom_metric"]
    # ... other problem types
```

## Adding New Statistical Tests

### Step 1: Define Test Metadata

Add to `engines/statistical_engine.py`:

```python
from engines.statistical_engine import StatisticalTest

CUSTOM_TEST = StatisticalTest(
    name="custom_test",
    description="Custom statistical test description",
    requires_observations=True,
    requires_projections=False,
)
```

### Step 2: Implement Test Function

```python
def run_custom_test(sample1, sample2, alpha=0.05) -> Dict[str, Any]:
    """Run custom statistical test."""
    from scipy import stats
    
    # Implement your test
    statistic, p_value = stats.ttest_ind(sample1, sample2)
    
    return {
        "test": "custom_test",
        "statistic": statistic,
        "p_value": p_value,
        "significant": p_value < alpha,
        "alpha": alpha,
    }
```

### Step 3: Register Test

Add to the test registry:

```python
TEST_REGISTRY = {
    # ... existing tests
    "custom_test": {
        "metadata": CUSTOM_TEST,
        "function": run_custom_test,
    },
}
```

### Step 4: Update Problem Type Mapping

Add to `get_tests_for_problem_type()`:

```python
def get_tests_for_problem_type(self, problem_type: str) -> List[StatisticalTest]:
    """Get tests for a problem type."""
    if problem_type == "regression":
        return [KS_TEST, PAIRED_T_TEST, BOOTSTRAP_CI, CUSTOM_TEST]
    # ... other problem types
```

## Adding New Validation Strategies

### Step 1: Define Strategy

Add to `ValidationStrategy` enum in `core/project.py`:

```python
class ValidationStrategy(Enum):
    TRAIN_TEST_SPLIT = "train_test_split"
    K_FOLD = "k_fold"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    TIME_SERIES_SPLIT = "time_series_split"
    GROUP_K_FOLD = "group_k_fold"
    REPEATED_K_FOLD = "repeated_k_fold"
    LEAVE_ONE_OUT = "leave_one_out"
    NESTED_CV = "nested_cv"  # New strategy
```

### Step 2: Implement Strategy

Add to `engines/validation_engine.py`:

```python
def _split_data(self, X, y, validation_strategy: str, **kwargs):
    """Split data into train and test sets."""
    if validation_strategy == "nested_cv":
        return self._nested_cv_split(X, y, **kwargs)
    # ... existing strategies

def _nested_cv_split(self, X, y, n_splits=5, inner_n_splits=3, random_state=42):
    """Implement nested cross-validation."""
    from sklearn.model_selection import KFold, cross_val_score
    
    outer_cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    inner_cv = KFold(n_splits=inner_n_splits, shuffle=True, random_state=random_state)
    
    # Implementation for nested CV
    return X_train, X_test, y_train, y_test
```

## Adding New UI Components

### Step 1: Create UI Module

Create a new file in `ui/` directory:

```python
# ui/my_component.py
"""My custom UI component."""
from __future__ import annotations

import streamlit as st

def render_my_component(data: Any) -> None:
    """Render my custom component."""
    st.subheader("My Component")
    
    # Your UI logic here
    st.write(data)
```

### Step 2: Export from `__init__.py`

Add to `ui/__init__.py`:

```python
from .my_component import render_my_component

__all__ = [
    # ... existing exports
    "render_my_component",
]
```

### Step 3: Add to App

Add to `app.py`:

```python
from ui import render_my_component

def render_my_component_page():
    """Render my component page."""
    st.title("My Component")
    render_my_component(st.session_state.current_project)
```

## Adding New Report Formats

### Step 1: Implement Format Function

Add to `core/report_generator.py`:

```python
def generate_pdf_report(self, report: Dict[str, Any]) -> str:
    """Generate PDF report."""
    # Use weasyprint or similar library
    from weasyprint import HTML
    
    html_content = self.generate_html_report(report)
    pdf = HTML(string=html_content).write_pdf()
    return pdf
```

### Step 2: Add to Save Method

Update `save_report()`:

```python
def save_report(self, report, project_id, format="json"):
    """Save report to artifacts."""
    if format == "pdf":
        pdf = self.generate_pdf_report(report)
        # Save PDF
```

## Testing Your Extensions

### Unit Tests

Create tests in `tests/` directory:

```python
# tests/test_my_extension.py
import pytest
from my_extension import MyCustomModel

def test_custom_model():
    """Test custom model."""
    model = MyCustomModel({"n_estimators": 10})
    assert model is not None
```

### Integration Tests

Add to `tests/test_integration.py`:

```python
def test_custom_model_integration():
    """Test custom model in full workflow."""
    # Test with actual data
    pass
```

## Best Practices

1. **Follow existing patterns**: Use the same patterns as existing code
2. **Add documentation**: Document your extension with docstrings
3. **Write tests**: Add unit tests for your extension
4. **Handle errors**: Add proper error handling
5. **Use type hints**: Add type hints for better IDE support
6. **Keep it modular**: Make your extension independent and reusable
7. **Version control**: Track changes with git
8. **Code review**: Get your code reviewed before merging

## Examples

### Example: Adding a Gradient Boosting Model

```python
# 1. Add to MODEL_REGISTRY
"gradient_boosting": ModelMetadata(
    name="gradient_boosting",
    category=ModelCategory.TREE_BASED,
    description="Gradient Boosting Machine",
    supported_problem_types=[ProblemType.REGRESSION, ProblemType.BINARY_CLASSIFICATION],
    # ... other metadata
),

# 2. Implement model class
class GradientBoostingModel(BaseModel):
    def __init__(self, hyperparameters):
        from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
        # Implementation

# 3. Add to create_model
if model_name == "gradient_boosting":
    return GradientBoostingModel(hyperparameters or {})
```

### Example: Adding a Custom Metric

```python
# 1. Implement metric
def calculate_mean_absolute_percentage_error(y_true, y_pred, y_proba=None):
    """Calculate MAPE."""
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

# 2. Register
"mape": {
    "function": calculate_mean_absolute_percentage_error,
    "direction": "minimize",
    "problem_types": ["regression"],
    "requires_proba": False,
}
```

## Contributing

When contributing extensions to ML Lab:

1. Fork the repository
2. Create a feature branch
3. Implement your extension
4. Add tests
5. Update documentation
6. Submit a pull request

Include in your PR:
- Description of the extension
- Use cases
- Examples
- Test results
