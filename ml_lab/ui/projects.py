"""Project management UI components for ML Lab.

This module provides UI components for creating, editing, and managing projects.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from core.model_registry import export_project, import_project


def render_project_form(
    project_analyzer: Any,
    existing_spec: Optional[Any] = None,
) -> Optional[Any]:
    """Render project creation/edit form.
    
    Args:
        project_analyzer: ProjectAnalyzer instance
        existing_spec: Optional existing ProjectSpecification for editing
    
    Returns:
        ProjectSpecification if created/updated, None otherwise
    """
    is_edit = existing_spec is not None
    
    if is_edit:
        st.subheader("Edit Project")
    else:
        st.subheader("Create New Project")
    
    with st.form("project_form"):
        # Basic Information
        st.markdown("### Basic Information")
        
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input(
                "Project Name*",
                value=existing_spec.project_name if is_edit else "",
                placeholder="e.g., Customer Churn Prediction",
            )
        with col2:
            domain = st.text_input(
                "Domain*",
                value=existing_spec.domain if is_edit else "",
                placeholder="e.g., finance, healthcare, retail",
            )
        
        description = st.text_area(
            "Description*",
            value=existing_spec.description if is_edit else "",
            placeholder="Describe your ML problem in natural language...",
            height=100,
        )
        
        business_objective = st.text_area(
            "Business Objective*",
            value=existing_spec.business_objective if is_edit else "",
            placeholder="What is the business/research objective?",
            height=80,
        )
        
        # Data Information
        st.markdown("### Data Information")
        
        col1, col2 = st.columns(2)
        with col1:
            target_variable = st.text_input(
                "Target Variable (optional)",
                value=existing_spec.target_variable if is_edit else "",
                placeholder="e.g., churn, yield, price",
            )
        with col2:
            dataset_path_str = st.text_input(
                "Dataset Path (optional)",
                value=str(existing_spec.dataset_path) if is_edit and existing_spec.dataset_path else "",
                placeholder="Path to your dataset",
            )
        
        # Constraints
        st.markdown("### Constraints")
        
        constraints_text = st.text_area(
            "Constraints (optional, one per line)",
            value="\n".join(existing_spec.constraints) if is_edit and existing_spec.constraints else "",
            placeholder="e.g.,\nMust be interpretable\nTraining time < 1 hour\nMemory limit: 4GB",
            height=80,
        )
        
        # Advanced Options
        with st.expander("Advanced Options"):
            st.markdown("### Problem Type Override")
            problem_type = st.selectbox(
                "Problem Type",
                options=["auto", "binary_classification", "multiclass_classification", "regression", "clustering", "time_series_forecasting"],
                index=0,
                help="Select 'auto' to let ML Lab detect the problem type from your description",
            )
            
            st.markdown("### Data Type Override")
            data_type = st.selectbox(
                "Data Type",
                options=["auto", "tabular", "image", "text", "time_series"],
                index=0,
                help="Select 'auto' to let ML Lab detect the data type",
            )
            
            st.markdown("### Objective Override")
            objective = st.selectbox(
                "Objective",
                options=["auto", "prediction", "explanation", "optimization"],
                index=0,
                help="Select 'auto' to let ML Lab detect the objective",
            )
        
        submitted = st.form_submit_button(
            "Update Project" if is_edit else "Create Project",
            type="primary",
        )
        
        if submitted:
            # Validation
            if not project_name or not domain or not description or not business_objective:
                st.error("Please fill in all required fields")
                return None
            
            # Parse constraints
            constraints_list = [c.strip() for c in constraints_text.split("\n") if c.strip()] if constraints_text else []
            
            # Convert dataset path
            dataset_path_obj = Path(dataset_path_str) if dataset_path_str else None
            
            # Analyze project context
            with st.spinner("Analyzing project context..."):
                spec = project_analyzer.analyze(
                    project_name=project_name,
                    description=description,
                    domain=domain,
                    business_objective=business_objective,
                    constraints=constraints_list,
                    dataset_path=dataset_path_obj,
                    target_variable=target_variable if target_variable else None,
                )
            
            # Apply overrides if specified
            if problem_type != "auto":
                from core.project import ProblemType
                spec.problem_type = ProblemType(problem_type)
            
            if data_type != "auto":
                from core.project import DataType
                spec.data_type = DataType(data_type)
            
            if objective != "auto":
                from core.project import Objective
                spec.objective = Objective(objective)
            
            return spec
    
    return None


def render_project_list(project_analyzer: Any) -> Optional[str]:
    """Render list of projects with search and filter capabilities.
    
    Args:
        project_analyzer: ProjectAnalyzer instance
    
    Returns:
        Selected project ID or None
    """
    st.subheader("Projects")
    
    # Import functionality
    with st.expander("Import Project"):
        uploaded_file = st.file_uploader("Upload project export JSON", type=["json"])
        if uploaded_file:
            try:
                import json
                export_data = json.load(uploaded_file)
                if import_project(export_data):
                    st.success("Project imported successfully!")
                    st.rerun()
                else:
                    st.error("Failed to import project")
            except Exception as e:
                st.error(f"Error importing project: {e}")
    
    # Search
    search_query = st.text_input("Search projects", placeholder="Search by name or description...")
    
    # Load projects from database if available
    from core.model_registry import list_projects, search_projects
    
    projects = None
    if search_query:
        projects = search_projects(search_query)
    else:
        projects = list_projects()
    
    if not projects:
        st.info("No projects found")
        return None
    
    # Display projects
    for project in projects:
        with st.expander(f"{project['project_name']} ({project['status']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Domain:** {project['domain']}")
                st.write(f"**Problem Type:** {project['problem_type']}")
                st.write(f"**Data Type:** {project['data_type']}")
            
            with col2:
                st.write(f"**Created:** {project['created_at']}")
                st.write(f"**Updated:** {project['updated_at']}")
                st.write(f"**Status:** {project['status']}")
            
            st.write(f"**Description:** {project['description']}")
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("Select", key=f"select_{project['id']}"):
                    return project['id']
            
            with col2:
                if st.button("Export", key=f"export_{project['id']}"):
                    export_data = export_project(project['id'])
                    if export_data:
                        import json
                        st.download_button(
                            "Download Export",
                            data=json.dumps(export_data, indent=2),
                            file_name=f"{project['project_name']}_export.json",
                            mime="application/json",
                        )
            
            with col3:
                if st.button("Delete", key=f"delete_{project['id']}"):
                    from core.model_registry import delete_project
                    if delete_project(project['id']):
                        st.success("Project deleted!")
                        st.rerun()
    
    return None


def render_project_settings(spec: Any) -> None:
    """Render project settings panel.
    
    Args:
        spec: ProjectSpecification
    """
    st.subheader("Project Settings")
    
    # Validation Settings
    with st.expander("Validation Settings"):
        col1, col2 = st.columns(2)
        with col1:
            new_strategy = st.selectbox(
                "Validation Strategy",
                options=["train_test_split", "k_fold", "stratified_k_fold", "time_series_split"],
                index=["train_test_split", "k_fold", "stratified_k_fold", "time_series_split"].index(
                    spec.validation.strategy.value
                ),
            )
        with col2:
            new_n_splits = st.number_input(
                "N Splits",
                min_value=2,
                max_value=20,
                value=spec.validation.n_splits,
            )
        
        new_test_size = st.slider(
            "Test Size",
            min_value=0.1,
            max_value=0.5,
            value=spec.validation.test_size,
            step=0.05,
        )
        
        if st.button("Update Validation Settings"):
            from core.project import ValidationStrategy
            spec.validation.strategy = ValidationStrategy(new_strategy)
            spec.validation.n_splits = new_n_splits
            spec.validation.test_size = new_test_size
            st.success("Validation settings updated!")
    
    # Model Settings
    with st.expander("Model Settings"):
        st.write("Enable/Disable models:")
        
        for i, model in enumerate(spec.models):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_enabled = st.checkbox(
                    model.name,
                    value=model.enabled,
                    key=f"model_{i}",
                )
            with col2:
                if st.button("Configure", key=f"config_model_{i}"):
                    st.session_state.configuring_model = model
                    st.rerun()
            
            if new_enabled != model.enabled:
                model.enabled = new_enabled
        
        if st.button("Update Model Settings"):
            st.success("Model settings updated!")
    
    # Preprocessing Settings
    with st.expander("Preprocessing Settings"):
        col1, col2 = st.columns(2)
        with col1:
            new_handle_missing = st.checkbox(
                "Handle Missing Values",
                value=spec.preprocessing.handle_missing,
            )
            new_handle_duplicates = st.checkbox(
                "Handle Duplicates",
                value=spec.preprocessing.handle_duplicates,
            )
        with col2:
            new_handle_outliers = st.checkbox(
                "Handle Outliers",
                value=spec.preprocessing.handle_outliers,
            )
            new_feature_engineering = st.checkbox(
                "Feature Engineering",
                value=spec.preprocessing.feature_engineering,
            )
        
        col1, col2 = st.columns(2)
        with col1:
            new_scaling = st.selectbox(
                "Scaling Method",
                options=["None", "standard", "minmax", "robust"],
                index=["None", "standard", "minmax", "robust"].index(
                    spec.preprocessing.scaling or "None"
                ),
            )
        with col2:
            new_encoding = st.selectbox(
                "Encoding Method",
                options=["None", "onehot", "label", "target"],
                index=["None", "onehot", "label", "target"].index(
                    spec.preprocessing.encoding or "None"
                ),
            )
        
        if st.button("Update Preprocessing Settings"):
            spec.preprocessing.handle_missing = new_handle_missing
            spec.preprocessing.handle_duplicates = new_handle_duplicates
            spec.preprocessing.handle_outliers = new_handle_outliers
            spec.preprocessing.feature_engineering = new_feature_engineering
            spec.preprocessing.scaling = new_scaling if new_scaling != "None" else None
            spec.preprocessing.encoding = new_encoding if new_encoding != "None" else None
            st.success("Preprocessing settings updated!")
    
    # Explainability Settings
    with st.expander("Explainability Settings"):
        new_enabled = st.checkbox(
            "Enable Explainability",
            value=spec.explainability.enabled,
        )
        
        if new_enabled:
            available_methods = ["shap", "feature_importance", "permutation", "lime"]
            selected_methods = st.multiselect(
                "Explainability Methods",
                options=available_methods,
                default=[m for m in available_methods if m in spec.explainability.methods],
            )
        else:
            selected_methods = []
        
        if st.button("Update Explainability Settings"):
            spec.explainability.enabled = new_enabled
            spec.explainability.methods = selected_methods
            st.success("Explainability settings updated!")
    
    # Statistical Test Settings
    with st.expander("Statistical Test Settings"):
        new_enabled = st.checkbox(
            "Enable Statistical Tests",
            value=spec.statistical_tests.enabled,
        )
        
        if new_enabled:
            available_tests = ["paired_t_test", "ks_test", "mcnemar_test", "cochran_q_test", "bootstrap_ci"]
            selected_tests = st.multiselect(
                "Statistical Tests",
                options=available_tests,
                default=[t for t in available_tests if t in spec.statistical_tests.tests],
            )
            
            new_alpha = st.slider(
                "Significance Level (alpha)",
                min_value=0.01,
                max_value=0.2,
                value=spec.statistical_tests.alpha,
                step=0.01,
            )
        else:
            selected_tests = []
            new_alpha = spec.statistical_tests.alpha
        
        if st.button("Update Statistical Test Settings"):
            spec.statistical_tests.enabled = new_enabled
            spec.statistical_tests.tests = selected_tests
            spec.statistical_tests.alpha = new_alpha
            st.success("Statistical test settings updated!")
    
    # Save button
    st.markdown("---")
    if st.button("Save All Settings", type="primary"):
        artifact_manager = st.session_state.artifact_manager
        artifact_manager.save_project_specification(spec)
        st.success("Project settings saved!")
