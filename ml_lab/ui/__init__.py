"""UI module for ML Lab.

This module provides Streamlit UI components for ML Lab including:
- Dashboard components
- Project management
- Context analyzer
- Dataset analysis
- EDA visualization
- Preprocessing
- Experiments
- Model training
- Validation results visualization
- Statistical test results
- Hyperparameter tuning
- Model comparison
- Training history
- Feature importance
- Confusion matrix
- ROC curves
"""
from .context import (
    render_analysis_results,
    render_configuration_editor,
    render_context_analyzer,
    render_context_tips,
)
from .dashboard import (
    render_artifact_summary,
    render_dataset_statistics,
    render_model_comparison,
    render_pipeline_status,
    render_project_overview,
    render_quick_actions,
    render_recent_experiments,
)
from .dataset import (
    render_correlation_heatmap,
    render_dataset_analyzer_ui,
    render_dataset_analysis,
    render_dataset_preview,
    render_dataset_statistics as render_dataset_stats,
    render_dataset_upload,
    render_distribution_plots,
    render_missing_values_analysis,
)
from .eda import (
    render_bivariate_analysis,
    render_correlation_matrix as render_corr_matrix,
    render_eda_overview,
    render_eda_report,
    render_feature_target_correlation,
    render_missing_values_heatmap,
    render_outlier_detection,
    render_target_analysis,
    render_univariate_analysis,
)
from .experiments import (
    render_experiment_comparison,
    render_experiment_details,
    render_experiment_form,
    render_experiment_list,
    render_experiment_tracking,
)
from .models import (
    render_model_catalog,
    render_model_hyperparameters,
    render_model_training_ui,
    render_training_config,
)
from .preprocessing import (
    render_encoding_config,
    render_missing_value_strategy,
    render_outlier_config,
    render_preprocessing_config,
    render_preprocessing_pipeline,
    render_scaling_config,
)
from .projects import (
    render_project_form,
    render_project_list,
    render_project_settings,
)
from .comparison import (
    render_metric_comparison_plot,
    render_model_comparison_table,
    render_model_comparison_ui,
    render_radar_comparison,
    render_ranking_comparison,
    render_statistical_comparison,
)
from .explainability import (
    render_explainability_config,
    render_explainability_ui,
    render_feature_importance_plot,
    render_local_explanation,
    render_permutation_importance_plot,
    render_shap_summary_plot,
)
from .inference import (
    render_batch_inference_config,
    render_inference_input,
    render_inference_results,
    render_inference_ui,
    render_model_selector,
    render_single_prediction_ui,
)
from .registry import (
    render_model_deployment,
    render_model_registration,
    render_model_registry,
    render_model_registry_ui,
    render_model_versioning,
)
from .reports import (
    render_report_config,
    render_report_export,
    render_report_generator_ui,
    render_report_history,
    render_report_preview,
)
from .statistics import (
    render_statistical_test_selector,
    render_statistical_test_results,
    render_statistical_test_ui,
)
from .tuning import (
    render_hyperparameter_space,
    render_tuning_config,
    render_tuning_results,
    render_tuning_strategy_selection,
    render_tuning_ui,
)
from .validation import (
    display_confusion_matrix,
    display_feature_importance,
    display_model_comparison,
    display_roc_curve,
    display_statistical_test_results,
    display_statistical_test_summary,
    display_training_history,
    display_validation_result,
)

__all__ = [
    # Dashboard
    "render_project_overview",
    "render_pipeline_status",
    "render_model_comparison",
    "render_dataset_statistics",
    "render_quick_actions",
    "render_recent_experiments",
    "render_artifact_summary",
    # Projects
    "render_project_form",
    "render_project_list",
    "render_project_settings",
    # Context
    "render_context_analyzer",
    "render_analysis_results",
    "render_configuration_editor",
    "render_context_tips",
    # Dataset
    "render_dataset_upload",
    "render_dataset_preview",
    "render_dataset_stats",
    "render_dataset_analysis",
    "render_dataset_analyzer_ui",
    "render_missing_values_analysis",
    "render_correlation_heatmap",
    "render_distribution_plots",
    # EDA
    "render_eda_overview",
    "render_eda_report",
    "render_univariate_analysis",
    "render_bivariate_analysis",
    "render_corr_matrix",
    "render_missing_values_heatmap",
    "render_outlier_detection",
    "render_target_analysis",
    "render_feature_target_correlation",
    # Preprocessing
    "render_preprocessing_config",
    "render_preprocessing_pipeline",
    "render_missing_value_strategy",
    "render_scaling_config",
    "render_encoding_config",
    "render_outlier_config",
    # Experiments
    "render_experiment_tracking",
    "render_experiment_list",
    "render_experiment_form",
    "render_experiment_details",
    "render_experiment_comparison",
    # Models
    "render_model_training_ui",
    "render_model_catalog",
    "render_model_hyperparameters",
    "render_training_config",
    # Comparison
    "render_model_comparison_ui",
    "render_model_comparison_table",
    "render_metric_comparison_plot",
    "render_radar_comparison",
    "render_ranking_comparison",
    "render_statistical_comparison",
    # Explainability
    "render_explainability_ui",
    "render_explainability_config",
    "render_feature_importance_plot",
    "render_permutation_importance_plot",
    "render_shap_summary_plot",
    "render_local_explanation",
    # Registry
    "render_model_registry_ui",
    "render_model_registry",
    "render_model_registration",
    "render_model_versioning",
    "render_model_deployment",
    # Reports
    "render_report_generator_ui",
    "render_report_config",
    "render_report_preview",
    "render_report_export",
    "render_report_history",
    # Inference
    "render_inference_ui",
    "render_model_selector",
    "render_inference_input",
    "render_batch_inference_config",
    "render_inference_results",
    "render_single_prediction_ui",
    # Statistics
    "render_statistical_test_ui",
    "render_statistical_test_selector",
    "render_statistical_test_results",
    # Validation
    "display_validation_result",
    "display_model_comparison",
    "display_statistical_test_results",
    "display_statistical_test_summary",
    "display_training_history",
    "display_feature_importance",
    "display_confusion_matrix",
    "display_roc_curve",
]
