# ML Lab API Documentation

## Overview

ML Lab provides a comprehensive API for building, training, and validating machine learning models. The API is organized into several core modules:

- `core.project_analyzer` - Project creation and management
- `core.dataset_analyzer` - Dataset analysis and profiling
- `core.model_catalog` - Model catalog and model metadata
- `core.artifact_manager` - Artifact storage and retrieval
- `core.model_registry` - Database-backed model registry
- `engines.training_engine` - Model training
- `engines.validation_engine` - Model validation
- `engines.statistical_engine` - Statistical testing
- `ui.*` - Streamlit UI components

## Core Modules

### Project Analyzer

```python
from core.project_analyzer import ProjectAnalyzer

analyzer = ProjectAnalyzer()

# Analyze context to infer problem type
context_result = analyzer.analyze_context(
    "Predict crop yield based on weather data"
)

# Create a project
project = analyzer.create_project(
    project_name="Crop Yield Prediction",
    description="Predict crop yield using ML",
    domain="agriculture",
    context_analysis=context_result,
)

# List projects
projects = analyzer.list_projects()

# Get a specific project
project = analyzer.get_project(project_id)

# Update a project
analyzer.update_project(project)

# Delete a project
analyzer.delete_project(project_id)
```

### Dataset Analyzer

```python
from core.dataset_analyzer import DatasetAnalyzer
import pandas as pd

analyzer = DatasetAnalyzer()

# Analyze tabular data
df = pd.read_csv("data.csv")
profile = analyzer.analyze_tabular(df)

# Profile properties:
# - profile.rows: Number of rows
# - profile.columns: Number of columns
# - profile.numerical_features: List of numerical feature names
# - profile.categorical_features: List of categorical feature names
# - profile.total_missing_percentage: Percentage of missing values
# - profile.has_duplicates: Boolean indicating duplicates
# - profile.has_outliers: Boolean indicating outliers
# - profile.target_column: Suggested target column
```

### Model Catalog

```python
from core.model_catalog import get_catalog

catalog = get_catalog()

# Get all models
all_models = catalog.get_all_models()

# Get models for a problem type
models = catalog.get_models_by_problem_type("regression")

# Get recommended models
recommended = catalog.get_recommended_models(
    problem_type="regression",
    data_type="tabular"
)

# Get model metadata
metadata = catalog.get_model_metadata("random_forest")

# Create a model instance
model = catalog.create_model("random_forest", hyperparameters={"n_estimators": 100})
```

### Training Engine

```python
from engines.training_engine import TrainingEngine, TrainingConfig

config = TrainingConfig(
    random_state=42,
    test_size=0.2,
    validation_strategy="k_fold",
    n_splits=5,
    scale_features=True,
)

engine = TrainingEngine(config=config)

# Train a single model
result = engine.train_model(
    model_name="random_forest",
    X=X_train,
    y=y_train,
    feature_names=feature_names,
    target_name="target",
    hyperparameters={"n_estimators": 100},
    project_id="project_id",
)

# Train multiple models
results = engine.train_multiple_models(
    model_names=["random_forest", "linear_regression"],
    X=X_train,
    y=y_train,
    feature_names=feature_names,
    target_name="target",
)

# Result properties:
# - result.model: Trained model
# - result.metrics: Dictionary of metrics
# - result.training_history: Training history (if available)
# - result.model_path: Path to saved model
```

### Validation Engine

```python
from engines.validation_engine import ValidationEngine, ValidationConfig

config = ValidationConfig(
    strategy="k_fold",
    n_splits=5,
    random_state=42,
)

engine = ValidationEngine(config=config)

# Validate a single model
result = engine.validate_model(
    model=model,
    X=X,
    y=y,
    problem_type="regression",
)

# Validate multiple models
results = engine.validate_multiple_models(
    models={"model1": model1, "model2": model2},
    X=X,
    y=y,
    problem_type="regression",
)

# Result properties:
# - result.metrics: Dictionary of metrics with mean, std, min, max
# - result.fold_metrics: List of per-fold metrics
# - result.metadata: Additional metadata
```

### Statistical Engine

```python
from engines.statistical_engine import StatisticalEngine

engine = StatisticalEngine()

# Get available tests
tests = engine.get_tests_for_problem_type("binary_classification")

# Run a single test
result = engine.run_test(
    test_name="ks_test",
    sample1=sample1,
    sample2=sample2,
)

# Run multiple tests
results = engine.run_tests(
    test_names=["ks_test", "paired_t_test"],
    sample1=sample1,
    sample2=sample2,
)

# Result properties:
# - result.statistic: Test statistic
# - result.p_value: P-value
# - result.significant: Boolean indicating significance
```

### Model Registry (Database)

```python
from core.model_registry import (
    save_project,
    list_projects,
    get_project,
    delete_project,
    save_experiment,
    list_experiments,
    save_model,
    list_models,
    set_production_model,
    export_project,
    import_project,
)

# Save a project to database
save_project(project_dict)

# List projects from database
projects = list_projects()

# Get a specific project
project = get_project(project_id)

# Save an experiment
save_experiment(experiment_dict)

# List experiments for a project
experiments = list_experiments(project_id)

# Save a model
save_model(model_dict)

# List models for a project
models = list_models(project_id)

# Set a model as production
set_production_model(model_id)

# Export a project
export_data = export_project(project_id)

# Import a project
import_project(export_data)
```

## Data Structures

### ProjectSpecification

```python
from core.project import ProjectSpecification, ProblemType, DataType, Objective

project = ProjectSpecification(
    project_id="unique_id",
    project_name="My Project",
    description="Project description",
    domain="agriculture",
    problem_type=ProblemType.REGRESSION,
    data_type=DataType.TABULAR,
    objective=Objective.PREDICTION,
    target_variable="yield",
    business_objective="Maximize crop yield",
    constraints=["privacy", "real-time"],
    dataset_path=Path("data.csv"),
    # ... additional fields
)
```

### TrainingResult

```python
from engines.training_engine import TrainingResult

result = TrainingResult(
    model=trained_model,
    metrics={"accuracy": 0.95, "f1": 0.93},
    training_history={"loss": [0.5, 0.3, 0.1]},
    model_path=Path("model.pkl"),
    metadata={"hyperparameters": {...}},
)
```

### ValidationResult

```python
from engines.validation_engine import ValidationResult

result = ValidationResult(
    metrics={"accuracy": {"mean": 0.95, "std": 0.02}},
    fold_metrics=[{"accuracy": 0.94}, {"accuracy": 0.96}],
    metadata={"strategy": "k_fold"},
)
```

## UI Components

### Streamlit UI

```python
from ui import (
    render_project_form,
    render_dataset_analyzer_ui,
    render_model_training_ui,
    render_experiment_tracking,
    # ... other UI components
)

# Render project creation form
spec = render_project_form(project_analyzer)

# Render dataset analysis UI
render_dataset_analyzer_ui(dataset_analyzer)

# Render model training UI
render_model_training_ui(spec, catalog, training_engine)
```

## Examples

### Complete Workflow

```python
from core.project_analyzer import ProjectAnalyzer
from core.dataset_analyzer import DatasetAnalyzer
from engines.training_engine import TrainingEngine, TrainingConfig
from engines.validation_engine import ValidationEngine, ValidationConfig
import pandas as pd

# 1. Analyze context
analyzer = ProjectAnalyzer()
context_result = analyzer.analyze_context("Predict crop yield")

# 2. Create project
project = analyzer.create_project(
    project_name="Crop Yield",
    description="Predict crop yield",
    domain="agriculture",
    context_analysis=context_result,
)

# 3. Load and analyze dataset
df = pd.read_csv("crop_data.csv")
dataset_analyzer = DatasetAnalyzer()
profile = dataset_analyzer.analyze_tabular(df)

# 4. Train model
config = TrainingConfig(random_state=42)
training_engine = TrainingEngine(config=config)

X = df.drop("yield", axis=1).values
y = df["yield"].values

result = training_engine.train_model(
    model_name="random_forest",
    X=X,
    y=y,
    feature_names=profile.numerical_features,
    target_name="yield",
)

# 5. Validate model
validation_config = ValidationConfig(n_splits=5)
validation_engine = ValidationEngine(config=validation_config)

validation_result = validation_engine.validate_model(
    model=result.model,
    X=X,
    y=y,
    problem_type="regression",
)

print(f"Validation R2: {validation_result.metrics['r2']['mean']:.4f}")
```

## Error Handling

All API functions follow a consistent error handling pattern:

```python
try:
    result = analyzer.analyze_context(context)
except ValueError as e:
    print(f"Invalid context: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

Database operations return `None` on failure:

```python
from core.model_registry import list_projects

projects = list_projects()
if projects is None:
    print("Database unavailable or error occurred")
```
