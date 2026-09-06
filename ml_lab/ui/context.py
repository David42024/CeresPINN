"""Context Analyzer UI components for ML Lab.

This module provides UI components for analyzing project context
and generating project specifications.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st


def render_context_analyzer(project_analyzer: Any, spec: Optional[Any] = None) -> Optional[Any]:
    """Render context analyzer interface.
    
    Args:
        project_analyzer: ProjectAnalyzer instance
        spec: Optional existing ProjectSpecification to re-analyze
    
    Returns:
        Analyzed ProjectSpecification or None
    """
    st.subheader("Context Analyzer")
    
    st.markdown("""
    Describe your ML problem in natural language, and ML Lab will analyze the context
    to automatically detect the problem type, data type, objective, and recommend
    appropriate models, metrics, and validation strategies.
    """)
    
    with st.form("context_analyzer_form"):
        # Project Information
        st.markdown("### Project Information")
        
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input(
                "Project Name*",
                value=spec.project_name if spec else "",
                placeholder="e.g., Customer Churn Prediction",
            )
        with col2:
            domain = st.text_input(
                "Domain*",
                value=spec.domain if spec else "",
                placeholder="e.g., finance, healthcare, retail",
            )
        
        description = st.text_area(
            "Problem Description*",
            value=spec.description if spec else "",
            placeholder="Describe your ML problem in natural language...\n\nExample: I want to predict which customers will churn based on their usage patterns, demographics, and support interactions.",
            height=120,
        )
        
        business_objective = st.text_area(
            "Business Objective*",
            value=spec.business_objective if spec else "",
            placeholder="What is the business/research objective?\n\nExample: Identify at-risk customers to implement retention strategies and reduce churn rate.",
            height=80,
        )
        
        # Data Information
        st.markdown("### Data Information (Optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            target_variable = st.text_input(
                "Target Variable",
                value=spec.target_variable if spec else "",
                placeholder="e.g., churn, yield, price",
            )
        with col2:
            dataset_path = st.text_input(
                "Dataset Path",
                value=str(spec.dataset_path) if spec and spec.dataset_path else "",
                placeholder="/path/to/dataset.csv",
            )
        
        # Constraints
        st.markdown("### Constraints (Optional)")
        
        constraints = st.text_area(
            "Constraints (one per line)",
            value="\n".join(spec.constraints) if spec and spec.constraints else "",
            placeholder="e.g.,\nMust be interpretable\nTraining time < 1 hour\nMemory limit: 4GB",
            height=80,
        )
        
        # Analyze button
        submitted = st.form_submit_button("Analyze Context", type="primary")
        
        if submitted:
            if not project_name or not domain or not description or not business_objective:
                st.error("Please fill in all required fields")
                return None
            
            # Parse constraints
            constraints_list = [c.strip() for c in constraints.split("\n") if c.strip()] if constraints else []
            
            # Convert dataset path
            from pathlib import Path
            dataset_path_obj = Path(dataset_path) if dataset_path else None
            
            # Analyze context
            with st.spinner("Analyzing project context..."):
                analyzed_spec = project_analyzer.analyze(
                    project_name=project_name,
                    description=description,
                    domain=domain,
                    business_objective=business_objective,
                    constraints=constraints_list,
                    dataset_path=dataset_path_obj,
                    target_variable=target_variable if target_variable else None,
                )
            
            return analyzed_spec
    
    return None


def render_analysis_results(spec: Any) -> None:
    """Render analysis results from ProjectAnalyzer.
    
    Args:
        spec: ProjectSpecification from ProjectAnalyzer
    """
    st.subheader("Analysis Results")
    
    # Detected Information
    st.markdown("### Detected Information")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Problem Type:** {spec.problem_type.value}")
    with col2:
        st.info(f"**Data Type:** {spec.data_type.value}")
    with col3:
        st.info(f"**Objective:** {spec.objective.value}")
    
    st.markdown("---")
    
    # Recommended Configuration
    st.markdown("### Recommended Configuration")
    
    # Validation
    with st.expander("Validation Strategy"):
        st.write(f"**Strategy:** {spec.validation.strategy.value}")
        st.write(f"**Test Size:** {spec.validation.test_size}")
        st.write(f"**N Splits:** {spec.validation.n_splits}")
        st.caption("Selected based on problem type and data characteristics")
    
    # Metrics
    with st.expander("Metrics"):
        st.write(f"**Primary Metric:** {spec.metrics.primary}")
        st.write(f"**Secondary Metrics:** {', '.join(spec.metrics.secondary)}")
        st.write(f"**Optimization Direction:** {spec.metrics.direction}")
        st.caption("Selected based on problem type")
    
    # Models
    with st.expander("Recommended Models"):
        for model in spec.models:
            status = "✓" if model.enabled else "✗"
            st.write(f"{status} **{model.name}**")
            if model.parameters:
                st.caption(f"Default params: {model.parameters}")
        st.caption("Selected based on problem type and data type")
    
    # Preprocessing
    with st.expander("Preprocessing"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Handle Missing:** {spec.preprocessing.handle_missing}")
            st.write(f"**Handle Duplicates:** {spec.preprocessing.handle_duplicates}")
        with col2:
            st.write(f"**Handle Outliers:** {spec.preprocessing.handle_outliers}")
            st.write(f"**Feature Engineering:** {spec.preprocessing.feature_engineering}")
        st.write(f"**Scaling:** {spec.preprocessing.scaling}")
        st.write(f"**Encoding:** {spec.preprocessing.encoding}")
        st.caption("Selected based on data type and problem requirements")
    
    # Explainability
    with st.expander("Explainability"):
        st.write(f"**Enabled:** {spec.explainability.enabled}")
        if spec.explainability.enabled:
            st.write(f"**Methods:** {', '.join(spec.explainability.methods)}")
        st.caption("Selected based on objective")
    
    # Statistical Tests
    with st.expander("Statistical Tests"):
        st.write(f"**Enabled:** {spec.statistical_tests.enabled}")
        if spec.statistical_tests.enabled:
            st.write(f"**Tests:** {', '.join(spec.statistical_tests.tests)}")
            st.write(f"**Alpha:** {spec.statistical_tests.alpha}")
        st.caption("Selected based on problem type")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save Project", type="primary"):
            artifact_manager = st.session_state.artifact_manager
            artifact_manager.save_project_specification(spec)
            st.session_state.current_project = spec
            st.success("Project saved successfully!")
    
    with col2:
        if st.button("Modify Configuration"):
            st.session_state.editing_configuration = True
            st.rerun()
    
    with col3:
        if st.button("Re-analyze"):
            st.session_state.reanalyze = True
            st.rerun()


def render_configuration_editor(spec: Any) -> None:
    """Render configuration editor for modifying analysis results.
    
    Args:
        spec: ProjectSpecification to edit
    """
    st.subheader("Modify Configuration")
    
    st.markdown("You can override the automatically detected configuration below.")
    
    # Problem Type
    st.markdown("### Problem Type")
    from core.project import ProblemType
    problem_types = [pt.value for pt in ProblemType]
    current_problem_type = spec.problem_type.value
    
    new_problem_type = st.selectbox(
        "Problem Type",
        options=problem_types,
        index=problem_types.index(current_problem_type),
    )
    
    # Data Type
    st.markdown("### Data Type")
    from core.project import DataType
    data_types = [dt.value for dt in DataType]
    current_data_type = spec.data_type.value
    
    new_data_type = st.selectbox(
        "Data Type",
        options=data_types,
        index=data_types.index(current_data_type),
    )
    
    # Objective
    st.markdown("### Objective")
    from core.project import Objective
    objectives = [obj.value for obj in Objective]
    current_objective = spec.objective.value
    
    new_objective = st.selectbox(
        "Objective",
        options=objectives,
        index=objectives.index(current_objective),
    )
    
    # Validation Strategy
    st.markdown("### Validation Strategy")
    from core.project import ValidationStrategy
    validation_strategies = [vs.value for vs in ValidationStrategy]
    current_validation = spec.validation.strategy.value
    
    new_validation = st.selectbox(
        "Validation Strategy",
        options=validation_strategies,
        index=validation_strategies.index(current_validation),
    )
    
    # Primary Metric
    st.markdown("### Primary Metric")
    new_primary_metric = st.text_input(
        "Primary Metric",
        value=spec.metrics.primary,
    )
    
    # Apply changes
    if st.button("Apply Changes", type="primary"):
        spec.problem_type = ProblemType(new_problem_type)
        spec.data_type = DataType(new_data_type)
        spec.objective = Objective(new_objective)
        spec.validation.strategy = ValidationStrategy(new_validation)
        spec.metrics.primary = new_primary_metric
        
        st.session_state.editing_configuration = False
        st.success("Configuration updated!")
        st.rerun()
    
    if st.button("Cancel"):
        st.session_state.editing_configuration = False
        st.rerun()


def render_context_tips() -> None:
    """Render tips for writing effective context descriptions."""
    st.subheader("Tips for Effective Context Descriptions")
    
    with st.expander("How to write a good problem description"):
        st.markdown("""
        **Include:**
        - What you're trying to predict or classify
        - The type of data you have (tabular, images, text, time series)
        - The scale of your data (number of samples, features)
        - Any domain-specific constraints or requirements
        
        **Example:**
        "I have a dataset of 10,000 customers with 50 features including demographics,
        usage patterns, and support interactions. I want to predict which customers will
        churn in the next 3 months. The model needs to be interpretable so we can explain
        predictions to stakeholders."
        """)
    
    with st.expander("How to describe business objectives"):
        st.markdown("""
        **Include:**
        - The business goal or research question
        - How the predictions will be used
        - Any success criteria or thresholds
        - Constraints on model deployment (latency, interpretability, etc.)
        
        **Example:**
        "Identify at-risk customers to implement targeted retention strategies.
        The goal is to reduce churn rate by 15% while maintaining a precision of at
        least 80% to avoid unnecessary retention costs."
        """)
    
    with st.expander("Common constraints to consider"):
        st.markdown("""
        **Performance constraints:**
        - Training time limits
        - Inference latency requirements
        - Memory usage limits
        
        **Business constraints:**
        - Interpretability requirements
        - Fairness and bias considerations
        - Regulatory compliance (GDPR, HIPAA, etc.)
        
        **Technical constraints:**
        - Deployment environment (cloud, edge, mobile)
        - Integration requirements
        - Monitoring and maintenance needs
        """)
