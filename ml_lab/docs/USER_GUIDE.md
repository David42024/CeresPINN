# ML Lab User Guide

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/cerespinn---climate-adaptive-maize-digital-twin.git
cd cerespinn---climate-adaptive-maize-digital-twin/ml_lab

# Install dependencies
pip install -r requirements.txt
```

### Running ML Lab

```bash
# Set up environment variables
export DATABASE_URL="postgresql://user:password@host:port/database"

# Run Streamlit app
streamlit run app.py
```

The UI will be available at `http://localhost:8501`

## Creating a Project

### Step 1: Navigate to Projects

Click on "New Project" in the sidebar.

### Step 2: Provide Project Information

- **Project Name**: A descriptive name for your project
- **Description**: Brief description of the project
- **Domain**: The domain (e.g., agriculture, healthcare, finance)
- **Context Description**: Describe your ML problem in natural language

Example context:
```
I want to predict crop yield based on weather data, soil properties, 
and management practices. The data includes temperature, precipitation, 
soil moisture, nitrogen levels, and historical yields.
```

### Step 3: Review Generated Configuration

ML Lab will automatically infer:
- Problem type (regression, classification, etc.)
- Data type (tabular, image, text, etc.)
- Objective (prediction, inference, explanation, etc.)

Review and adjust if needed.

### Step 4: Create Project

Click "Create Project" to save your project.

## Analyzing a Dataset

### Step 1: Navigate to Dataset Analysis

Click on "Dataset Analysis" in the sidebar.

### Step 2: Upload Your Dataset

- Click "Upload Dataset"
- Select a CSV file
- Or provide a file path

### Step 3: Review Dataset Profile

ML Lab will automatically analyze:
- Number of rows and columns
- Numerical and categorical features
- Missing values
- Duplicates
- Outliers
- Target column suggestion

### Step 4: Exploratory Data Analysis

Navigate to "EDA" to view:
- Data overview
- Univariate analysis
- Bivariate analysis
- Correlation matrix
- Missing values heatmap
- Outlier detection
- Target variable analysis

## Training Models

### Step 1: Navigate to Model Training

Click on "Model Training" in the sidebar.

### Step 2: Select Models

Browse the model catalog and select models to train:
- Filter by interpretable, fast training, or memory efficient
- View model descriptions and requirements
- Select multiple models for comparison

### Step 3: Configure Hyperparameters

- Use default hyperparameters or customize per model
- Configure validation strategy (train-test split, k-fold, etc.)
- Set random state for reproducibility

### Step 4: Start Training

Click "Start Training" to begin model training.

### Step 5: View Results

Training results will show:
- Metrics for each model
- Training history (if available)
- Feature importance (if applicable)

## Validating Models

### Step 1: Navigate to Validation

Click on "Validation" in the sidebar.

### Step 2: View Validation Configuration

- Validation strategy
- Number of folds
- Test size

### Step 3: Run Validation

Click "Run Validation" to perform cross-validation.

### Step 4: Review Results

Validation results include:
- Cross-validation metrics
- Model rankings
- Statistical comparisons
- Training history

## Comparing Models

### Step 1: Navigate to Model Comparison

Click on "Model Comparison" in the sidebar.

### Step 2: Select Models to Compare

Select models from the dropdown.

### Step 3: View Comparison

- Metric comparison table
- Metric comparison plots
- Radar chart for multi-metric comparison
- Statistical significance tests

## Hyperparameter Tuning

### Step 1: Navigate to Hyperparameter Tuning

Click on "Hyperparameter Tuning" in the sidebar.

### Step 2: Select Tuning Strategy

Choose from:
- Grid Search
- Random Search
- Bayesian Optimization
- Optuna

### Step 3: Configure Search Space

Define hyperparameter ranges for each model.

### Step 4: Start Tuning

Click "Start Tuning" to begin optimization.

### Step 5: Review Results

- Best hyperparameters
- Optimization history
- Performance comparison

## Model Explainability

### Step 1: Navigate to Explainability

Click on "Explainability" in the sidebar.

### Step 2: Configure Explainability

Select explainability methods:
- Feature Importance
- Permutation Importance
- SHAP Values
- LIME

### Step 3: View Explanations

- Feature importance plots
- SHAP summary plots
- Permutation importance
- Local explanations for individual predictions

## Model Registry

### Step 1: Navigate to Model Registry

Click on "Model Registry" in the sidebar.

### Step 2: Register a Model

- Provide model name, type, version
- Upload model file
- Add performance metrics
- Set tags

### Step 3: Model Versioning

- View all model versions
- Compare versions
- Promote to production

### Step 4: Deploy Model

- Select deployment environment (staging, production)
- Configure resource limits
- Deploy model

## Inference

### Step 1: Navigate to Inference

Click on "Inference" in the sidebar.

### Step 2: Select Model

Choose a registered model from the dropdown.

### Step 3: Provide Input Data

- Upload CSV file for batch inference
- Or provide manual input for single prediction

### Step 4: Run Inference

Click "Run Inference" to generate predictions.

### Step 5: View Results

- Prediction results
- Prediction probabilities (if applicable)
- Download results

## Generating Reports

### Step 1: Navigate to Reports

Click on "Reports" in the sidebar.

### Step 2: Configure Report

- Select report sections
- Choose output format (Markdown, HTML, PDF, JSON)
- Set report style and theme

### Step 3: Generate Report

Click "Generate Report" to create the report.

### Step 4: View and Export

- Preview the report
- Download in selected format
- View report history

## Statistical Tests

### Step 1: Navigate to Statistical Tests

Click on "Statistical Tests" in the sidebar.

### Step 2: Select Tests

Choose statistical tests based on your problem type:
- KS Test
- Paired t-test
- McNemar's test
- Bootstrap CI
- Cochran's Q test

### Step 3: Configure Parameters

Set significance level (alpha) and test-specific parameters.

### Step 4: Run Tests

Click "Run Statistical Tests" to execute.

### Step 5: Review Results

- Test statistics
- P-values
- Significance indicators
- Interpretation

## Best Practices

### Project Organization

1. **Use descriptive project names**: "Crop Yield Prediction 2024"
2. **Provide detailed context descriptions**: Include data sources, objectives, constraints
3. **Organize experiments**: Use clear experiment names for tracking

### Data Preparation

1. **Clean data before upload**: Handle obvious issues manually
2. **Use appropriate data types**: Ensure numerical columns are numeric
3. **Document data sources**: Note where data came from and any preprocessing

### Model Selection

1. **Start with simple models**: Begin with linear regression or decision trees
2. **Compare multiple models**: Always train and compare multiple models
3. **Consider interpretability**: Choose interpretable models for production

### Validation

1. **Use appropriate validation strategy**: Stratified k-fold for classification
2. **Set random seeds**: Ensure reproducibility
3. **Cross-validate**: Always use cross-validation for reliable estimates

### Hyperparameter Tuning

1. **Start with defaults**: Use default hyperparameters first
2. **Tune systematically**: Tune one parameter at a time
3. **Use appropriate strategies**: Grid search for small spaces, random for large

### Deployment

1. **Test thoroughly**: Validate on held-out test set
2. **Monitor performance**: Track model performance in production
3. **Version control**: Keep track of model versions

## Troubleshooting

### Common Issues

**Issue**: "No models available for training"
- **Solution**: Ensure you have analyzed a dataset first

**Issue**: "Training failed with error"
- **Solution**: Check the error message in the UI logs, ensure data is properly formatted

**Issue**: "Database connection failed"
- **Solution**: Verify DATABASE_URL environment variable is set correctly

**Issue**: "Memory error during training"
- **Solution**: Reduce batch size or use a smaller subset of data

**Issue**: "Model not saving"
- **Solution**: Check artifact manager configuration and disk space

### Getting Help

1. Check the documentation in the `docs/` directory
2. Review error messages in the UI
3. Check logs for detailed error information
4. Open an issue on GitHub with:
   - Project context
   - Dataset information
   - Error messages
   - Steps to reproduce

## Keyboard Shortcuts

- `Ctrl/Cmd + Enter`: Run the current cell (in notebooks)
- `Ctrl/Cmd + S`: Save current state
- `Ctrl/Cmd + R`: Refresh the page

## Tips and Tricks

1. **Use session state**: ML Lab saves your progress in session state
2. **Export projects**: Export projects for backup or sharing
3. **Use the dashboard**: The dashboard provides a quick overview of all projects
4. **Batch operations**: Train multiple models at once for comparison
5. **Use explainability**: Understand why models make predictions
