# ML Lab Architecture

## Overview

ML Lab is a modular, extensible machine learning platform designed for building, training, and validating ML models. The architecture follows a layered design with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer (Streamlit)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Projects │ │ Dataset  │ │ Training │ │ Experiments│     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Project      │ │ Dataset      │ │ Model        │        │
│  │ Analyzer     │ │ Analyzer     │ │ Catalog      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Artifact      │ │ Model        │ │ Report       │        │
│  │ Manager      │ │ Registry     │ │ Generator    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Engine Layer                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Training     │ │ Validation   │ │ Statistical  │        │
│  │ Engine       │ │ Engine       │ │ Engine       │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ PostgreSQL   │ │ File System  │ │ Model Files  │        │
│  │ (Shared)     │ │ (Artifacts)  │ │ (Pickles)    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Project Analyzer

**Purpose**: Analyzes natural language context to infer ML problem characteristics.

**Key Functions**:
- `analyze_context()`: Infers problem type, data type, objective from text
- `create_project()`: Creates ProjectSpecification from analysis
- `list_projects()`: Lists all projects
- `get_project()`: Retrieves a specific project
- `update_project()`: Updates project metadata
- `delete_project()`: Deletes a project

**Design Pattern**: Strategy pattern for context analysis with keyword-based inference.

### 2. Dataset Analyzer

**Purpose**: Analyzes datasets to generate profiles and detect issues.

**Key Functions**:
- `analyze_tabular()`: Analyzes tabular data
- `analyze_image()`: Analyzes image data (future)
- `analyze_text()`: Analyzes text data (future)

**Design Pattern**: Template method pattern for different data types.

### 3. Model Catalog

**Purpose**: Central registry of available ML models with metadata.

**Key Functions**:
- `get_all_models()`: Lists all available models
- `get_models_by_problem_type()`: Filters models by problem type
- `get_recommended_models()`: Returns recommended models
- `get_model_metadata()`: Gets detailed model metadata
- `create_model()`: Instantiates a model

**Design Pattern**: Registry pattern with metadata-driven model creation.

### 4. Artifact Manager

**Purpose**: Manages storage of models, preprocessing artifacts, and results.

**Key Functions**:
- `save_artifact()`: Saves an artifact
- `load_artifact()`: Loads an artifact
- `list_artifacts()`: Lists artifacts by type
- `get_artifact_metadata()`: Gets artifact metadata

**Design Pattern**: Abstract factory pattern for artifact storage.

### 5. Training Engine

**Purpose**: Trains models with configurable preprocessing and validation.

**Key Functions**:
- `train_model()`: Trains a single model
- `train_multiple_models()`: Trains multiple models
- `load_model()`: Loads a trained model

**Design Pattern**: Strategy pattern for different model types.

### 6. Validation Engine

**Purpose**: Validates models using various cross-validation strategies.

**Key Functions**:
- `validate_model()`: Validates a single model
- `validate_multiple_models()`: Validates multiple models
- `compare_models()`: Compares model performance

**Design Pattern**: Strategy pattern for validation strategies.

### 7. Statistical Engine

**Purpose**: Runs statistical tests to compare model performance.

**Key Functions**:
- `run_test()`: Runs a single statistical test
- `run_tests()`: Runs multiple tests
- `get_tests_for_problem_type()`: Gets applicable tests

**Design Pattern**: Strategy pattern for statistical tests.

### 8. Model Registry

**Purpose**: Database-backed registry for projects, experiments, and models.

**Key Functions**:
- `save_project()`: Saves project to database
- `list_projects()`: Lists projects from database
- `save_experiment()`: Saves experiment to database
- `save_model()`: Saves model to database
- `set_production_model()`: Promotes model to production

**Design Pattern**: Repository pattern with database abstraction.

## Data Flow

### Project Creation Flow

```
User Input (Context) → Project Analyzer → ProjectSpecification
                                                    ↓
                                            Model Registry (DB)
```

### Training Flow

```
Dataset → Dataset Analyzer → Profile
                                    ↓
ProjectSpecification → Training Engine → Model
                                    ↓
                            Artifact Manager → Saved Model
                                    ↓
                            Model Registry (DB)
```

### Validation Flow

```
Model + Data → Validation Engine → ValidationResult
                                    ↓
                            Artifact Manager → Saved Results
                                    ↓
                            Model Registry (DB)
```

### Inference Flow

```
New Data → Preprocessing (saved artifacts) → Trained Model → Predictions
```

## Database Schema

### ML Lab Tables

**ml_lab_projects**
- Stores project metadata and specifications
- Foreign key relationships to experiments, models, datasets

**ml_lab_datasets**
- Stores dataset profiles
- Linked to projects

**ml_lab_experiments**
- Stores experiment configurations and results
- Linked to projects

**ml_lab_models**
- Stores trained model metadata
- Linked to projects and experiments

**ml_lab_artifacts**
- Stores artifact metadata
- Linked to projects, experiments, models

**ml_lab_reports**
- Stores generated reports
- Linked to projects

### Integration with CeresPINN

ML Lab shares the PostgreSQL database with CeresPINN using table namespacing:
- CeresPINN tables: `fields`, `soil_profiles`, `scenarios`, `model_registry`, etc.
- ML Lab tables: `ml_lab_projects`, `ml_lab_experiments`, `ml_lab_models`, etc.

This allows:
- Shared authentication and user management
- Shared field and soil profile data
- Independent ML Lab project management

## Extensibility Points

### Adding New Models

1. Add model metadata to `ModelCatalog`
2. Implement model class inheriting from `BaseModel`
3. Add to appropriate category in `ModelCategory`

### Adding New Data Sources

1. Implement data extractor following adapter pattern
2. Add to `DataSourceType` enum
3. Register in `DataSourceRegistry`

### Adding New Metrics

1. Add metric function to `MetricsEngine`
2. Register in `get_metrics_for_problem_type()`
3. Update metric configuration

### Adding New Statistical Tests

1. Add test to `StatisticalEngine`
2. Implement test function
3. Add to `get_tests_for_problem_type()`

### Adding New Validation Strategies

1. Add to `ValidationStrategy` enum
2. Implement in `ValidationEngine`
3. Update `_split_data()` method

## Design Patterns Used

1. **Registry Pattern**: Model catalog, data source registry
2. **Strategy Pattern**: Validation strategies, statistical tests
3. **Template Method Pattern**: Dataset analyzer for different data types
4. **Repository Pattern**: Model registry for database operations
5. **Abstract Factory Pattern**: Artifact manager for storage backends
6. **Builder Pattern**: Project specification builder
7. **Adapter Pattern**: Data source adapters for different formats

## Performance Considerations

1. **Caching**: Streamlit session state for expensive operations
2. **Lazy Loading**: Large datasets loaded on demand
3. **Batch Processing**: Training and validation in batches
4. **Database Indexing**: Indexes on frequently queried columns
5. **Artifact Compression**: Model artifacts compressed before storage

## Security Considerations

1. **Database Access**: Connection pooling, prepared statements
2. **Artifact Storage**: Secure file permissions
3. **User Authentication**: Shared with CeresPINN
4. **API Keys**: Environment variable configuration
5. **Input Validation**: All user inputs validated

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
┌─────────────▼──────┐ ┌──────▼────────┐ ┌──▼──────────────┐
│  Streamlit UI      │ │  FastAPI API   │ │  Worker Process  │
│  (Port 8501)       │ │  (Port 8000)   │ │  (Background)    │
└────────────────────┘ └────────────────┘ └─────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│              (CeresPINN + ML Lab Tables)                     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    File Storage (S3/Local)                    │
│              (Artifacts, Models, Reports)                    │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **UI**: Streamlit
- **Backend**: Python 3.9+
- **ML**: scikit-learn, PyTorch (for PINN)
- **Database**: PostgreSQL with SQLAlchemy
- **Storage**: Local filesystem / S3
- **Testing**: pytest
- **Deployment**: Docker, Render

## Module Dependencies

```
ml_lab/
├── core/
│   ├── project_analyzer (independent)
│   ├── dataset_analyzer (independent)
│   ├── model_catalog (independent)
│   ├── artifact_manager (independent)
│   ├── model_registry (depends on db.py)
│   ├── metrics_engine (independent)
│   └── report_generator (depends on artifact_manager)
├── engines/
│   ├── training_engine (depends on core, model_catalog)
│   ├── validation_engine (depends on core, metrics_engine)
│   └── statistical_engine (independent)
└── ui/
    ├── (all UI components depend on core and engines)
```

## Future Enhancements

1. **Distributed Training**: Support for multi-GPU training
2. **AutoML**: Automated hyperparameter optimization
3. **Model Serving**: REST API for model inference
4. **Real-time Monitoring**: Model performance monitoring
5. **A/B Testing**: Automated model comparison in production
6. **Explainability**: SHAP, LIME integration
7. **Federated Learning**: Privacy-preserving training
