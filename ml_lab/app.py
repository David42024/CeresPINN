"""ML Lab - Streamlit Main Application.

This is the main entry point for the ML Lab Streamlit application.
It provides navigation to various ML Lab features including project management,
dataset analysis, model training, validation, and reporting.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add ml_lab to path
ml_lab_path = Path(__file__).parent
if str(ml_lab_path) not in sys.path:
    sys.path.insert(0, str(ml_lab_path))

from core.artifact_manager import get_artifact_manager
from core.dataset_analyzer import DatasetAnalyzer
from core.model_catalog import get_catalog
from core.project_analyzer import ProjectAnalyzer
from core.report_generator import get_report_generator
from engines.statistical_engine import get_statistical_engine
from engines.training_engine import TrainingEngine
from engines.validation_engine import ValidationEngine
from ui import (
    display_validation_result,
    render_model_comparison_ui,
    render_context_analyzer,
    render_dataset_analyzer_ui,
    render_eda_report,
    render_explainability_ui,
    render_experiment_tracking,
    render_inference_ui,
    render_model_training_ui,
    render_preprocessing_pipeline,
    render_project_form,
    render_model_registry_ui,
    render_report_generator_ui,
    render_statistical_test_ui,
    render_tuning_ui,
)


def set_page_config():
    """Set Streamlit page configuration."""
    st.set_page_config(
        page_title="ML Lab",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def initialize_session_state():
    """Initialize session state variables."""
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "current_dataset" not in st.session_state:
        st.session_state.current_dataset = None
    if "project_analyzer" not in st.session_state:
        st.session_state.project_analyzer = ProjectAnalyzer()
    if "dataset_analyzer" not in st.session_state:
        st.session_state.dataset_analyzer = DatasetAnalyzer()
    if "artifact_manager" not in st.session_state:
        st.session_state.artifact_manager = get_artifact_manager()
    if "training_engine" not in st.session_state:
        st.session_state.training_engine = TrainingEngine(artifact_manager=get_artifact_manager())
    if "validation_engine" not in st.session_state:
        st.session_state.validation_engine = ValidationEngine(artifact_manager=get_artifact_manager())
    if "model_catalog" not in st.session_state:
        st.session_state.model_catalog = get_catalog()
    if "statistical_engine" not in st.session_state:
        st.session_state.statistical_engine = get_statistical_engine()
    if "report_generator" not in st.session_state:
        st.session_state.report_generator = get_report_generator(get_artifact_manager())


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.title("🧪 ML Lab")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Projects",
                "New Project",
                "Context Analyzer",
                "Dataset Analysis",
                "EDA",
                "Preprocessing",
                "Model Training",
                "Experiments",
                "Validation",
                "Model Comparison",
                "Hyperparameter Tuning",
                "Statistical Tests",
                "Explainability",
                "Model Registry",
                "Inference",
                "Reports",
            ],
            label_visibility="collapsed",
        )
        
        st.markdown("---")
        
        # Current project info
        if st.session_state.current_project:
            st.subheader("Current Project")
            st.text(st.session_state.current_project.project_name)
            st.caption(f"ID: {st.session_state.current_project.project_id}")
            if st.button("Close Project"):
                st.session_state.current_project = None
                st.rerun()
        else:
            st.info("No project selected")
        
        st.markdown("---")
        
        # Quick actions
        st.subheader("Quick Actions")
        if st.button("Create New Project"):
            st.session_state.selected_page = "New Project"
            st.rerun()
        
        st.markdown("---")
        
        # About
        st.subheader("About")
        st.caption("ML Lab v1.0")
        st.caption("Domain-agnostic ML platform")
    
    return page


def render_dashboard():
    """Render the main dashboard page."""
    st.title("📊 Dashboard")
    st.markdown("---")
    
    # Overview stats
    col1, col2, col3, col4 = st.columns(4)
    
    artifact_manager = st.session_state.artifact_manager
    projects = artifact_manager.list_projects()
    
    with col1:
        st.metric("Total Projects", len(projects))
    
    with col2:
        st.metric("Active Project", 1 if st.session_state.current_project else 0)
    
    with col3:
        st.metric("Models Trained", "0")  # TODO: Get from artifact manager
    
    with col4:
        st.metric("Experiments Run", "0")  # TODO: Get from artifact manager
    
    st.markdown("---")
    
    # Recent projects
    st.subheader("Recent Projects")
    
    if projects:
        for project_id in projects[-5:]:  # Last 5 projects
            try:
                spec = artifact_manager.load_project_specification(project_id)
                with st.expander(f"{spec.project_name} ({project_id})"):
                    st.write(f"**Domain:** {spec.domain}")
                    st.write(f"**Problem Type:** {spec.problem_type.value}")
                    st.write(f"**Created:** {spec.created_at}")
                    st.write(f"**Status:** {spec.status}")
                    
                    if st.button(f"Open {spec.project_name}", key=f"open_{project_id}"):
                        st.session_state.current_project = spec
                        st.rerun()
            except Exception as e:
                st.error(f"Error loading project {project_id}: {e}")
    else:
        st.info("No projects found. Create your first project to get started!")
    
    st.markdown("---")
    
    # Quick start guide
    st.subheader("Quick Start Guide")
    
    with st.expander("How to use ML Lab"):
        st.markdown("""
        1. **Create a Project**: Go to "New Project" and describe your ML problem
        2. **Upload Dataset**: Upload your data in the "Dataset Analysis" section
        3. **Analyze Context**: Let ML Lab analyze your project context
        4. **Train Models**: Select and train models from the catalog
        5. **Validate**: Validate your models with cross-validation
        6. **Test Statistics**: Run statistical tests on your results
        7. **Generate Reports**: Export comprehensive reports
        """)


def render_projects():
    """Render the projects management page."""
    st.title("📁 Projects")
    st.markdown("---")
    
    artifact_manager = st.session_state.artifact_manager
    projects = artifact_manager.list_projects()
    
    if not projects:
        st.info("No projects found. Create your first project!")
        if st.button("Create New Project"):
            st.session_state.selected_page = "New Project"
            st.rerun()
        return
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Search projects", placeholder="Search by name or ID...")
    with col2:
        status_filter = st.selectbox("Filter by status", ["All", "planned", "running", "completed", "failed"])
    
    # Filter projects
    filtered_projects = []
    for project_id in projects:
        try:
            spec = artifact_manager.load_project_specification(project_id)
            if search and search.lower() not in spec.project_name.lower() and search.lower() not in project_id.lower():
                continue
            if status_filter != "All" and spec.status != status_filter:
                continue
            filtered_projects.append(spec)
        except Exception:
            continue
    
    # Display projects
    for spec in filtered_projects:
        with st.expander(f"{spec.project_name} ({spec.project_id})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Domain:** {spec.domain}")
                st.write(f"**Problem:** {spec.problem_type.value}")
            
            with col2:
                st.write(f"**Status:** {spec.status}")
                st.write(f"**Created:** {spec.created_at}")
            
            with col3:
                st.write(f"**Objective:** {spec.objective.value}")
                st.write(f"**Data Type:** {spec.data_type.value}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Open", key=f"open_{spec.project_id}"):
                    st.session_state.current_project = spec
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{spec.project_id}"):
                    artifact_manager.delete_project(spec.project_id)
                    st.rerun()
            with col3:
                if st.button("Export", key=f"export_{spec.project_id}"):
                    # TODO: Export project
                    st.info("Export functionality coming soon")


def render_new_project():
    """Render the new project creation page."""
    st.title("➕ New Project")
    st.markdown("---")
    
    project_analyzer = st.session_state.project_analyzer
    
    # Use UI component for project form
    spec = render_project_form(project_analyzer)
    
    if spec:
        # Save project
        artifact_manager = st.session_state.artifact_manager
        artifact_manager.save_project_specification(spec)
        
        st.success(f"Project '{spec.project_name}' created successfully!")
        st.session_state.current_project = spec
        st.rerun()


def render_context_analyzer():
    """Render the context analyzer page."""
    st.title("🔍 Context Analyzer")
    st.markdown("---")
    
    project_analyzer = st.session_state.project_analyzer
    
    # Use UI component for context analyzer
    spec = render_context_analyzer(project_analyzer, st.session_state.current_project)
    
    if spec:
        from ui import render_analysis_results
        render_analysis_results(spec)


def render_dataset_analysis():
    """Render the dataset analysis page."""
    st.title("📊 Dataset Analysis")
    st.markdown("---")
    
    dataset_analyzer = st.session_state.dataset_analyzer
    
    # Use UI component for dataset analyzer
    profile = render_dataset_analyzer_ui(dataset_analyzer, st.session_state.current_project)
    
    if profile:
        st.session_state.current_dataset = profile
        st.success("Dataset analysis completed!")
    
    # Update spec if dataset was analyzed
    if profile and st.session_state.current_project:
        from core.project_analyzer import ProjectAnalyzer
        project_analyzer = ProjectAnalyzer()
        st.session_state.current_project = project_analyzer.refine_from_dataset(
            st.session_state.current_project, profile
        )
        st.session_state.artifact_manager.save_project_specification(st.session_state.current_project)


def render_placeholder_page(page_name: str):
    """Render a placeholder page for features not yet implemented."""
    st.title(f"🚧 {page_name}")
    st.markdown("---")
    st.info(f"{page_name} is coming soon!")
    st.markdown("This feature is under development and will be available in a future release.")


def render_eda_page():
    """Render EDA page."""
    st.title("📊 Exploratory Data Analysis")
    st.markdown("---")
    
    if not st.session_state.current_dataset:
        st.warning("Please analyze a dataset first")
        return
    
    # Load dataset
    import pandas as pd
    dataset_analyzer = st.session_state.dataset_analyzer
    df = dataset_analyzer._load_tabular(st.session_state.current_project.dataset_path)
    
    target_column = st.session_state.current_project.target_variable if st.session_state.current_project else None
    
    render_eda_report(df, target_column)


def render_preprocessing_page():
    """Render Preprocessing page."""
    st.title("🔧 Preprocessing")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    if not st.session_state.current_dataset:
        st.warning("Please analyze a dataset first")
        return
    
    # Load dataset
    import pandas as pd
    dataset_analyzer = st.session_state.dataset_analyzer
    df = dataset_analyzer._load_tabular(st.session_state.current_project.dataset_path)
    
    render_preprocessing_pipeline(df, st.session_state.current_project)


def render_model_training_page():
    """Render Model Training page."""
    st.title("🧠 Model Training")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    if not st.session_state.current_dataset:
        st.warning("Please analyze a dataset first")
        return
    
    catalog = st.session_state.model_catalog
    training_engine = st.session_state.training_engine
    
    render_model_training_ui(st.session_state.current_project, catalog, training_engine)


def render_experiments_page():
    """Render Experiments page."""
    st.title("🧪 Experiments")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    artifact_manager = st.session_state.artifact_manager
    
    render_experiment_tracking(st.session_state.current_project, artifact_manager)


def render_validation_page():
    """Render Validation page."""
    st.title("✅ Validation")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    validation_engine = st.session_state.validation_engine
    
    # Show validation configuration
    st.subheader("Validation Configuration")
    st.write(f"**Strategy:** {st.session_state.current_project.validation.strategy.value}")
    st.write(f"**N Splits:** {st.session_state.current_project.validation.n_splits}")
    st.write(f"**Test Size:** {st.session_state.current_project.validation.test_size}")
    
    st.markdown("---")
    st.info("Run model training first to generate validation results")


def render_model_comparison_page():
    """Render Model Comparison page."""
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return

    validation_engine = st.session_state.validation_engine

    render_model_comparison_ui(validation_engine, st.session_state.current_project)


def render_tuning_page():
    """Render Hyperparameter Tuning page."""
    st.title("🎛️ Hyperparameter Tuning")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    render_tuning_ui(st.session_state.current_project)


def render_statistical_tests_page():
    """Render Statistical Tests page."""
    st.title("📊 Statistical Tests")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    statistical_engine = st.session_state.statistical_engine
    render_statistical_test_ui(statistical_engine, st.session_state.current_project)


def render_explainability_page():
    """Render Explainability page."""
    st.title("🔍 Model Explainability")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    render_explainability_ui(st.session_state.current_project)


def render_model_registry_page():
    """Render Model Registry page."""
    st.title("📦 Model Registry")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    render_model_registry_ui(st.session_state.current_project)


def render_inference_page():
    """Render Inference page."""
    st.title("🔮 Model Inference")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    render_inference_ui(st.session_state.current_project)


def render_reports_page():
    """Render Reports page."""
    st.title("📄 Report Generator")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    render_report_generator_ui(st.session_state.current_project)


def main():
    """Main application entry point."""
    set_page_config()
    initialize_session_state()
    
    page = render_sidebar()
    
    # Route to appropriate page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Projects":
        render_projects()
    elif page == "New Project":
        render_new_project()
    elif page == "Context Analyzer":
        render_context_analyzer()
    elif page == "Dataset Analysis":
        render_dataset_analysis()
    elif page == "EDA":
        render_eda_page()
    elif page == "Preprocessing":
        render_preprocessing_page()
    elif page == "Model Training":
        render_model_training_page()
    elif page == "Experiments":
        render_experiments_page()
    elif page == "Validation":
        render_validation_page()
    elif page == "Model Comparison":
        render_model_comparison_page()
    elif page == "Hyperparameter Tuning":
        render_tuning_page()
    elif page == "Statistical Tests":
        render_statistical_tests_page()
    elif page == "Explainability":
        render_explainability_page()
    elif page == "Model Registry":
        render_model_registry_page()
    elif page == "Inference":
        render_inference_page()
    elif page == "Reports":
        render_reports_page()


if __name__ == "__main__":
    main()
