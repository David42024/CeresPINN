"""ML Lab - Streamlit Main Application.

This is the main entry point for the ML Lab Streamlit application.
It provides navigation to various ML Lab features including project management,
dataset analysis, model training, validation, and reporting.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import importlib

# Add ml_lab to path
ml_lab_path = Path(__file__).parent
if str(ml_lab_path) not in sys.path:
    sys.path.insert(0, str(ml_lab_path))

# Ensure all ml_lab submodules are reloaded on rerun
for mod_name in list(sys.modules.keys()):
    if any(mod_name.startswith(p) for p in ("ui", "core", "engines", "models")):
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            pass

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
    if "project_analyzer" not in st.session_state:
        st.session_state.project_analyzer = ProjectAnalyzer()
    if "current_project" not in st.session_state or st.session_state.current_project is None:
        try:
            projects = st.session_state.project_analyzer.list_projects()
            st.session_state.current_project = projects[0] if projects else None
        except Exception:
            st.session_state.current_project = None
    if "current_dataset" not in st.session_state:
        st.session_state.current_dataset = None
    if "preprocessed_df" not in st.session_state:
        st.session_state.preprocessed_df = None
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
        
    # Ensure current_project is fully deserialized (Streamlit can sometimes mangle dataclasses to dicts across reruns)
    cp = st.session_state.get("current_project")
    if cp is not None:
        if isinstance(cp, dict):
            from core.project import ProjectSpecification
            st.session_state.current_project = ProjectSpecification.from_dict(cp)
        elif isinstance(getattr(cp, 'models', None), list) and len(cp.models) > 0 and isinstance(cp.models[0], dict):
            from core.project import ProjectSpecification
            st.session_state.current_project = ProjectSpecification.from_dict(cp.to_dict())
        elif hasattr(cp, 'validation') and isinstance(cp.validation, dict):
            from core.project import ProjectSpecification
            st.session_state.current_project = ProjectSpecification.from_dict(cp.to_dict())


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


def render_context_analyzer_page():
    """Render the context analyzer page."""
    st.title("🔍 Context Analyzer")
    st.markdown("---")
    
    project_analyzer = st.session_state.project_analyzer
    
    # Use UI component for context analyzer
    spec = render_context_analyzer(project_analyzer, st.session_state.current_project)
    
    if spec:
        st.session_state.current_project = spec
        from ui import render_analysis_results
        render_analysis_results(spec)
    elif st.session_state.current_project:
        from ui import render_analysis_results
        render_analysis_results(st.session_state.current_project)


def render_dataset_analysis():
    """Render the dataset analysis page."""
    st.title("📊 Dataset Analysis")
    st.markdown("---")
    
    dataset_analyzer = st.session_state.dataset_analyzer
    
    # Use UI component for dataset analyzer
    profile = render_dataset_analyzer_ui(dataset_analyzer, st.session_state.current_project)
    
    if profile:
        st.session_state.current_dataset = profile
        if st.session_state.current_project and hasattr(profile, "dataset_path") and profile.dataset_path:
            st.session_state.current_project.dataset_path = profile.dataset_path
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


def _resolve_active_dataset_path() -> Optional[Path]:
    """Helper to resolve the path of the active dataset from state or defaults."""
    if st.session_state.get("current_dataset") and getattr(st.session_state.current_dataset, "dataset_path", None):
        p = Path(st.session_state.current_dataset.dataset_path)
        if p.exists():
            return p
    if st.session_state.get("current_project") and getattr(st.session_state.current_project, "dataset_path", None):
        p = Path(st.session_state.current_project.dataset_path)
        if p.exists():
            return p
    for cand in [
        Path("data/cerespinn_training_iowa.csv"),
        Path("C:/Users/USERJSSV/AppData/Local/Temp/ml_lab_uploads/cerespinn_training_iowa.csv"),
    ]:
        if cand.exists():
            return cand
    return None


def render_eda_page():
    """Render EDA page."""
    # Ensure current_project is loaded if available
    if not st.session_state.current_project:
        try:
            projects = st.session_state.project_analyzer.list_projects()
            st.session_state.current_project = projects[0] if projects else None
        except Exception:
            pass

    dataset_path = _resolve_active_dataset_path()
    if not dataset_path:
        st.warning("Please upload and analyze a dataset first in 'Dataset Analysis'.")
        return

    # Load dataset
    dataset_analyzer = st.session_state.dataset_analyzer
    try:
        df = dataset_analyzer._load_tabular(dataset_path)
    except Exception as e:
        st.error(f"Failed to load dataset ({dataset_path}): {e}")
        return

    target_column = None
    if st.session_state.current_project and getattr(st.session_state.current_project, "target_variable", None):
        target_column = st.session_state.current_project.target_variable
    elif "yield_bu_acre" in df.columns:
        target_column = "yield_bu_acre"

    render_eda_report(df, target_column)


def render_preprocessing_page():
    """Render Preprocessing page."""
    st.title("🔧 Preprocessing")
    st.markdown("---")
    
    if not st.session_state.current_project:
        try:
            projects = st.session_state.project_analyzer.list_projects()
            st.session_state.current_project = projects[0] if projects else None
        except Exception:
            pass

    if not st.session_state.current_project:
        st.warning("Please select or configure a project first in 'Context Analyzer'")
        return

    dataset_path = _resolve_active_dataset_path()
    if not dataset_path:
        st.warning("Please upload and analyze a dataset first in 'Dataset Analysis'")
        return

    dataset_analyzer = st.session_state.dataset_analyzer
    try:
        df = dataset_analyzer._load_tabular(dataset_path)
    except Exception as e:
        st.error(f"Failed to load dataset ({dataset_path}): {e}")
        return

    render_preprocessing_pipeline(df, st.session_state.current_project)


def render_model_training_page():
    """Render Model Training page."""
    st.title("🧠 Model Training")
    st.markdown("---")
    
    if not st.session_state.current_project:
        try:
            projects = st.session_state.project_analyzer.list_projects()
            st.session_state.current_project = projects[0] if projects else None
        except Exception:
            pass

    if not st.session_state.current_project:
        st.warning("Please select or configure a project first in 'Context Analyzer'")
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
    training_engine = st.session_state.training_engine
    
    # Show validation configuration
    st.subheader("Validation Configuration")
    st.write(f"**Strategy:** {st.session_state.current_project.validation.strategy.value}")
    st.write(f"**N Splits:** {st.session_state.current_project.validation.n_splits}")
    st.write(f"**Test Size:** {st.session_state.current_project.validation.test_size}")
    
    st.markdown("---")
    
    # Botón para ejecutar validación nueva con datos actuales
    if st.button("🔄 Run New Validation with Current Training Data"):
        with st.spinner("Running validation with current training data..."):
            try:
                import pandas as pd
                from pathlib import Path
                
                # Cargar el modelo entrenado más reciente
                project_id = st.session_state.current_project.project_id
                model = training_engine.load_model(project_id, "cerespinn")
                
                # Cargar los datos de entrenamiento actuales (misma lógica que en models.py)
                target = getattr(st.session_state.current_project, "target_variable", None)
                df = None
                
                # Intentar cargar desde el dataset preprocesado o el original
                for cand in [Path("data/cerespinn_training_preprocessed.csv"), Path("data/cerespinn_training_iowa.csv")]:
                    if cand.exists():
                        df = pd.read_csv(cand)
                        break
                
                if df is None:
                    st.error("No dataset found. Please apply preprocessing or analyze a dataset first.")
                else:
                    # Auto-detect target column if not specified
                    if target is None or target not in df.columns:
                        # Try common target column names
                        for possible_target in ["yield_bu_acre", "yield (continuous, bushels/acre)", "yield", "target"]:
                            if possible_target in df.columns:
                                target = possible_target
                                break
                        if target is None or target not in df.columns:
                            st.error(f"Target variable not found in dataset columns. Available columns: {list(df.columns)}")
                            df = None
                    
                    if df is not None:
                        # Preparar X y y para validación
                        feature_cols = [c for c in df.columns if c != target]
                        numeric = df[feature_cols].select_dtypes(include=[np.number])
                        frame = pd.concat([numeric, df[[target]]], axis=1).dropna()
                        
                        if frame.empty or len(numeric.columns) == 0:
                            st.error("No usable numeric data after dropping missing values.")
                        else:
                            X = frame[numeric.columns].to_numpy(dtype=float)
                            y = pd.to_numeric(frame[target], errors="coerce").dropna().to_numpy(dtype=float)
                            X = X[: len(y)]
                            
                            # Ejecutar validación con el modelo y datos actuales
                            validation_result = validation_engine.validate_model(
                                model=model,
                                X=X,
                            y=y,
                            model_name="cerespinn",
                            problem_type="regression",
                            project_id=project_id,
                        )
                        
                        st.success("✅ Validation completed successfully!")
                        st.rerun()
            except Exception as e:
                st.error(f"Validation failed: {e}")
    
    # Cargar resultados de validación para el modelo cerespinn (único modelo entrenado)
    # Esto evita mostrar métricas de runs anteriores con peor desempeño
    try:
        validation_engine = st.session_state.validation_engine
        project_id = st.session_state.current_project.project_id
        # Cargar específicamente los metrics de cerespinn
        validation_result = validation_engine.load_validation_result(
            project_id, "cerespinn"
        )
        # Si no hay resultados, validation_result será None

        if validation_result and validation_result.metrics:
            st.subheader("Validation Results")
            st.success(f"Model: {validation_result.model_name}")
            metric_columns = st.columns(3)
            metric_keys = (
                ("R2", "r2", False),
                ("MAE", "neg_mean_absolute_error", True),
                ("RMSE", "neg_root_mean_squared_error", True),
            )
            for column, (label, metric_name, negate) in zip(metric_columns, metric_keys):
                metric = validation_result.metrics.get(metric_name, {})
                value = metric.get("mean", 0) or 0
                if negate:
                    value = abs(value)
                with column:
                    st.metric(label, f"{value:.4f}")
            st.info("Using results from previous training. Click 'Run New Validation' to validate with current data.")
        else:
            st.info("Run model training first to generate validation results")
    except Exception as e:
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
        render_context_analyzer_page()
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
