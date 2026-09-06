"""Pipeline Engine - Generates dynamic pipeline plans based on context.

This module implements the PipelineEngine which generates a PipelinePlan
based on the ProjectSpecification and DatasetProfile. The engine determines
which pipeline steps are necessary, their order, and dependencies.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .dataset_profile import DatasetProfile
from .pipeline_plan import (
    PipelinePlan,
    PipelineStep,
    StepDependency,
    StepStatus,
)
from .project import ProjectSpecification


class PipelineEngine:
    """Generates dynamic pipeline plans based on project context.
    
    The PipelineEngine analyzes the ProjectSpecification and DatasetProfile
    to determine which pipeline steps are necessary, in what order, and what
    dependencies exist between steps. This ensures that the pipeline adapts
    to the specific problem type, data type, and constraints.
    """
    
    def __init__(self):
        """Initialize the pipeline engine."""
        pass
    
    def generate_plan(
        self,
        spec: ProjectSpecification,
        dataset_profile: Optional[DatasetProfile] = None,
    ) -> PipelinePlan:
        """Generate a pipeline plan based on specification and dataset profile.
        
        Args:
            spec: Project specification
            dataset_profile: Dataset profile (optional if not yet analyzed)
        
        Returns:
            PipelinePlan with steps, dependencies, and configuration
        """
        plan = PipelinePlan(project_id=spec.project_id)
        
        # Always start with dataset analysis
        plan.add_step(PipelineStep.DATASET_ANALYSIS)
        
        # Add EDA if enabled
        if spec.preprocessing.handle_missing or spec.preprocessing.handle_duplicates:
            plan.add_step(PipelineStep.EDA)
            plan.add_dependency(PipelineStep.EDA, [PipelineStep.DATASET_ANALYSIS])
        
        # Add preprocessing if enabled
        if spec.preprocessing.handle_missing or spec.preprocessing.handle_duplicates or spec.preprocessing.scaling:
            plan.add_step(PipelineStep.PREPROCESSING)
            plan.add_dependency(PipelineStep.PREPROCESSING, [PipelineStep.EDA])
        
        # Add feature engineering if enabled
        if spec.preprocessing.feature_engineering:
            plan.add_step(PipelineStep.FEATURE_ENGINEERING)
            plan.add_dependency(PipelineStep.FEATURE_ENGINEERING, [PipelineStep.PREPROCESSING])
        
        # Add model training
        plan.add_step(PipelineStep.MODEL_TRAINING)
        deps = [PipelineStep.PREPROCESSING]
        if spec.preprocessing.feature_engineering:
            deps.append(PipelineStep.FEATURE_ENGINEERING)
        plan.add_dependency(PipelineStep.MODEL_TRAINING, deps)
        
        # Add validation if enabled
        if spec.validation.strategy:
            plan.add_step(PipelineStep.VALIDATION)
            plan.add_dependency(PipelineStep.VALIDATION, [PipelineStep.MODEL_TRAINING])
        
        # Add hyperparameter tuning if enabled
        if spec.hyperparameter_tuning.enabled:
            plan.add_step(PipelineStep.HYPERPARAMETER_TUNING)
            plan.add_dependency(PipelineStep.HYPERPARAMETER_TUNING, [PipelineStep.VALIDATION])
        
        # Add model evaluation
        plan.add_step(PipelineStep.MODEL_EVALUATION)
        eval_deps = [PipelineStep.MODEL_TRAINING]
        if spec.hyperparameter_tuning.enabled:
            eval_deps.append(PipelineStep.HYPERPARAMETER_TUNING)
        plan.add_dependency(PipelineStep.MODEL_EVALUATION, eval_deps)
        
        # Add statistical tests if enabled
        if spec.statistical_tests.enabled and spec.statistical_tests.tests:
            plan.add_step(PipelineStep.STATISTICAL_TESTS)
            plan.add_dependency(PipelineStep.STATISTICAL_TESTS, [PipelineStep.MODEL_EVALUATION])
        
        # Add model comparison if multiple models
        if len(spec.models) > 1:
            plan.add_step(PipelineStep.MODEL_COMPARISON)
            comp_deps = [PipelineStep.MODEL_EVALUATION]
            if spec.statistical_tests.enabled:
                comp_deps.append(PipelineStep.STATISTICAL_TESTS)
            plan.add_dependency(PipelineStep.MODEL_COMPARISON, comp_deps)
        
        # Add best model selection
        plan.add_step(PipelineStep.BEST_MODEL_SELECTION)
        best_deps = [PipelineStep.MODEL_EVALUATION]
        if len(spec.models) > 1:
            best_deps.append(PipelineStep.MODEL_COMPARISON)
        plan.add_dependency(PipelineStep.BEST_MODEL_SELECTION, best_deps)
        
        # Add explainability if enabled
        if spec.explainability.enabled and spec.explainability.methods:
            plan.add_step(PipelineStep.EXPLAINABILITY)
            plan.add_dependency(PipelineStep.EXPLAINABILITY, [PipelineStep.BEST_MODEL_SELECTION])
        
        # Add model registry
        plan.add_step(PipelineStep.MODEL_REGISTRY)
        plan.add_dependency(PipelineStep.MODEL_REGISTRY, [PipelineStep.BEST_MODEL_SELECTION])
        
        # Add report generation if enabled
        if True:  # Always generate reports
            plan.add_step(PipelineStep.REPORT_GENERATION)
            report_deps = [PipelineStep.BEST_MODEL_SELECTION]
            if spec.explainability.enabled:
                report_deps.append(PipelineStep.EXPLAINABILITY)
            plan.add_dependency(PipelineStep.REPORT_GENERATION, report_deps)
        
        # Add inference (optional, not part of training pipeline)
        # plan.add_step(PipelineStep.INFERENCE)
        # plan.add_dependency(PipelineStep.INFERENCE, [PipelineStep.MODEL_REGISTRY])
        
        # Configure plan based on specification
        plan.enable_eda = True
        plan.enable_preprocessing = True
        plan.enable_feature_engineering = spec.preprocessing.feature_engineering
        plan.enable_validation = True
        plan.enable_hyperparameter_tuning = spec.hyperparameter_tuning.enabled
        plan.enable_statistical_tests = spec.statistical_tests.enabled
        plan.enable_explainability = spec.explainability.enabled
        plan.enable_model_comparison = len(spec.models) > 1
        plan.enable_report_generation = True
        
        # Set invalidation rules
        for dep in plan.dependencies:
            if dep.step == PipelineStep.PREPROCESSING:
                dep.invalidation_rule = "dataset_changed"
            elif dep.step == PipelineStep.MODEL_TRAINING:
                dep.invalidation_rule = "preprocessing_changed"
        
        return plan
    
    def update_plan_for_dataset(
        self, plan: PipelinePlan, dataset_profile: DatasetProfile
    ) -> PipelinePlan:
        """Update pipeline plan based on dataset profile.
        
        Args:
            plan: Existing pipeline plan
            dataset_profile: Dataset profile
        
        Returns:
            Updated pipeline plan
        """
        # Disable EDA if dataset is too small
        if dataset_profile.rows < 10:
            plan.enable_eda = False
            if PipelineStep.EDA in plan.steps:
                plan.steps.remove(PipelineStep.EDA)
        
        # Disable preprocessing if not needed
        if not dataset_profile.has_missing_values and not dataset_profile.has_duplicates:
            plan.enable_preprocessing = False
            if PipelineStep.PREPROCESSING in plan.steps:
                plan.steps.remove(PipelineStep.PREPROCESSING)
        
        # Disable statistical tests for small datasets
        if dataset_profile.rows < 50:
            plan.enable_statistical_tests = False
            if PipelineStep.STATISTICAL_TESTS in plan.steps:
                plan.steps.remove(PipelineStep.STATISTICAL_TESTS)
        
        # Add warnings to plan metadata
        if dataset_profile.issues:
            plan.metadata["dataset_issues"] = dataset_profile.issues
        if dataset_profile.warnings:
            plan.metadata["dataset_warnings"] = dataset_profile.warnings
        
        return plan
    
    def get_step_description(self, step: PipelineStep) -> str:
        """Get a human-readable description of a pipeline step."""
        descriptions = {
            PipelineStep.DATASET_ANALYSIS: "Analyze dataset structure and characteristics",
            PipelineStep.EDA: "Perform exploratory data analysis",
            PipelineStep.PREPROCESSING: "Apply preprocessing transformations",
            PipelineStep.FEATURE_ENGINEERING: "Engineer new features",
            PipelineStep.MODEL_TRAINING: "Train ML models",
            PipelineStep.VALIDATION: "Validate model performance",
            PipelineStep.HYPERPARAMETER_TUNING: "Optimize hyperparameters",
            PipelineStep.MODEL_EVALUATION: "Evaluate model performance",
            PipelineStep.STATISTICAL_TESTS: "Perform statistical tests",
            PipelineStep.MODEL_COMPARISON: "Compare model performance",
            PipelineStep.BEST_MODEL_SELECTION: "Select the best model",
            PipelineStep.EXPLAINABILITY: "Generate model explanations",
            PipelineStep.MODEL_REGISTRY: "Register model in registry",
            PipelineStep.REPORT_GENERATION: "Generate analysis report",
            PipelineStep.INFERENCE: "Perform inference with trained model",
        }
        return descriptions.get(step, "Unknown step")
    
    def validate_plan(self, plan: PipelinePlan) -> List[str]:
        """Validate a pipeline plan and return any issues.
        
        Args:
            plan: Pipeline plan to validate
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Check that all dependencies are satisfied
        for dep in plan.dependencies:
            if dep.step not in plan.steps:
                issues.append(f"Dependency step {dep.step} not in plan")
            for dep_step in dep.depends_on:
                if dep_step not in plan.steps:
                    issues.append(f"Dependent step {dep_step} not in plan")
        
        # Check for circular dependencies
        # (simplified check - full cycle detection would be more complex)
        
        # Check that dataset_analysis is always first
        if plan.steps and plan.steps[0] != PipelineStep.DATASET_ANALYSIS:
            issues.append("Dataset analysis should be the first step")
        
        return issues
