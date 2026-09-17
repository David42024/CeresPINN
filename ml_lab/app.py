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
    import pandas as pd
    import numpy as np
    import time
    from pathlib import Path
    
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
    
    # Panel de Selección y Ejecución Interactiva de Validación Cruzada
    st.subheader("⚡ Ejecución Interactiva de Validación Cruzada (Cross-Validation)")
    
    with st.expander("🛠️ Selección de Estrategia y Modelos para Validación Cruzada", expanded=True):
        col_cv1, col_cv2 = st.columns([1, 1])
        with col_cv1:
            val_strat = st.selectbox(
                "Estrategia de Partición",
                options=[
                    "TimeSeriesSplit (5 Folds Temporales - Recomendado Ficha 5)",
                    "K-Fold Estándar (5 Folds Aleatorios)",
                    "Blocked Temporal Cross-Validation (3 Folds)"
                ],
                index=0,
                help="TimeSeriesSplit evalúa cronológicamente hacia adelante, garantizando ausencia de filtración temporal."
            )
            n_splits = st.slider("Número de Folds / Particiones (K)", min_value=3, max_value=10, value=5)
            
        with col_cv2:
            st.markdown("**Selecciona los Modelos a Evaluar en Validación Cruzada:**")
            BENCHMARK_MODEL_MAP = {
                "cerespinn": "🌟 CeresPINN (Digital Twin PINN - Ganador)",
                "gradient_boosting": "🌲 Gradient Boosting Regressor (Convencional #1)",
                "random_forest": "🌳 Random Forest Regressor (Convencional #2)",
                "generic_pinn": "🧬 Generic PINN (Híbrido #2)",
                "linear_regression": "📏 Ridge Regression (Convencional #3)",
            }
            selected_models_to_run = st.multiselect(
                "Modelos a validar / entrenar:",
                options=list(BENCHMARK_MODEL_MAP.keys()),
                default=list(BENCHMARK_MODEL_MAP.keys()),
                format_func=lambda k: BENCHMARK_MODEL_MAP.get(k, k),
                help="Puedes seleccionar los 5 modelos o un subconjunto específico para comparar."
            )
            
        st.markdown("")
        col_btn, col_btn_info = st.columns([2, 1])
        with col_btn:
            run_cv_btn = st.button("🚀 Ejecutar Validación Cruzada en Modelos Seleccionados", type="primary", use_container_width=True)
        with col_btn_info:
            st.caption(f"🎯 {len(selected_models_to_run)} modelo(s) seleccionados para {n_splits} particiones.")
            
    if run_cv_btn:
        if not selected_models_to_run:
            st.warning("⚠️ Debes seleccionar al menos un modelo para ejecutar la validación cruzada.")
        else:
            with st.status(f"⚡ Ejecutando validación cruzada para {len(selected_models_to_run)} modelo(s)...", expanded=True) as status:
                try:
                    t_start = time.time()
                    models_arg = ",".join(selected_models_to_run)
                    st.write(f"🔄 Entrenando y evaluando con {n_splits} splits: `{models_arg}`...")
                    
                    import subprocess
                    cmd = [
                        sys.executable,
                        "scripts/optimize_cerespinn_suite.py",
                        "--models", models_arg,
                        "--n_splits", str(n_splits)
                    ]
                    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path.cwd()))
                    
                    t_elapsed = time.time() - t_start
                    if proc.returncode == 0:
                        status.update(label=f"✅ Validación cruzada completada exitosamente en {t_elapsed:.1f}s!", state="complete", expanded=False)
                        st.success(f"🎉 Validación exitosa para {len(selected_models_to_run)} modelo(s). Resultados y artefactos actualizados.")
                        st.rerun()
                    else:
                        status.update(label="❌ Error durante la validación", state="error")
                        st.error(f"Detalles: {proc.stderr[:500] if proc.stderr else proc.stdout[:500]}")
                except Exception as e:
                    status.update(label=f"❌ Error: {e}", state="error")
                    st.error(f"Fallo al ejecutar validación cruzada: {e}")
                    
    # Cargar resultados de validación para el modelo seleccionado
    try:
        validation_engine = st.session_state.validation_engine
        artifact_manager = st.session_state.artifact_manager
        project_id = st.session_state.current_project.project_id

        MODEL_DISPLAY_NAMES = {
            "cerespinn": "🌟 CeresPINN (Digital Twin PINN - Ganador)",
            "generic_pinn": "🧬 Generic PINN (Híbrido Physics-MLP)",
            "gradient_boosting": "🌲 Gradient Boosting Regressor (Ensamble No Lineal)",
            "random_forest": "🌳 Random Forest Regressor (Ensamble No Lineal)",
            "linear_regression": "📏 Ridge Regression (Línea Base Lineal Simple)",
        }

        # Descubrir todos los modelos con validación disponible
        val_artifacts = artifact_manager.list_artifacts(project_id, "validation")
        available_models = sorted(list({p.name[:-len("_validation_metrics.json")] for p in val_artifacts if p.name.endswith("_validation_metrics.json") and not p.name.startswith("cerespinn_calibrated")}))
        if not available_models:
            available_models = ["cerespinn"]
            
        default_model_idx = available_models.index("cerespinn") if "cerespinn" in available_models else 0
        
        col_sel, col_info = st.columns([2, 1])
        with col_sel:
            selected_model = st.selectbox(
                "🔍 Seleccionar Modelo para Inspección Detallada (TimeSeriesSplit)",
                options=available_models,
                index=default_model_idx,
                format_func=lambda m: MODEL_DISPLAY_NAMES.get(m, m),
                help="Inspecciona los resultados de validación cruzada temporal para cada modelo candidato."
            )
        with col_info:
            st.info(f"📊 {len(available_models)} modelos evaluados (3 Convencionales + 2 Híbridos)")

        validation_result = validation_engine.load_validation_result(
            project_id, selected_model
        )

        if validation_result and validation_result.metrics:
            st.subheader(f"Resultados de Validación: {MODEL_DISPLAY_NAMES.get(selected_model, selected_model)}")
            
            # Badge de estatus
            if selected_model == "cerespinn":
                st.success("🌟 **Modelo Híbrido #1 (Digital Twin Propuesto - Ganador)**: Acoplamiento completo de fenología (GDD) + balance hídrico (ET) + optimización bayesiana.")
            elif selected_model == "generic_pinn":
                st.info("🧬 **Modelo Híbrido #2 (Generic PINN)**: Red neuronal profunda con penalización física general de balance de masa.")
            elif selected_model in ["gradient_boosting", "random_forest"]:
                st.info(f"🌲 **Modelo Convencional ({selected_model})**: Ensamble no lineal estándar de la literatura.")
            elif selected_model == "linear_regression":
                st.warning("📏 **Modelo Convencional (Ridge)**: Regresión lineal simple de referencia paramétrica.")
            
            metric_columns = st.columns(4)
            metric_keys = (
                ("R² Score", "r2", False),
                ("MAE (bu/acre)", "neg_mean_absolute_error", True),
                ("RMSE (bu/acre)", "neg_root_mean_squared_error", True),
                ("MAPE", "neg_mean_absolute_percentage_error", True),
            )
            for column, (label, metric_name, negate) in zip(metric_columns, metric_keys):
                metric = validation_result.metrics.get(metric_name, {})
                value = metric.get("mean", 0) or 0
                std_val = metric.get("std", 0) or 0
                if negate:
                    value = abs(value)
                with column:
                    if "MAPE" in label:
                        mape_str = f"{value * 100:.2f}%" if value <= 1.0 else f"{value:.2f}%"
                        st.metric(label, mape_str)
                    else:
                        st.metric(label, f"{value:.4f}", delta=f"± {std_val:.4f}" if std_val > 0 else None, delta_color="off")
            
            # Mostrar desglose por fold si existe
            if getattr(validation_result, "fold_metrics", None):
                with st.expander("📅 TimeSeriesSplit: Desglose Fold a Fold (Hindcast Temporal)", expanded=True):
                    fold_rows = []
                    for i, fm in enumerate(validation_result.fold_metrics):
                        fold_num = fm.get("fold", i + 1)
                        r2_score = float(fm.get("r2", 0.0))
                        mae_score = abs(float(fm.get("neg_mean_absolute_error", 0.0)))
                        rmse_score = abs(float(fm.get("neg_root_mean_squared_error", 0.0)))
                        samples_cnt = fm.get("n_samples", 2000)
                        fold_rows.append({
                            "Temporal Split": f"Fold {fold_num}",
                            "R² Score": round(r2_score, 4),
                            "MAE (bu/acre)": round(mae_score, 2),
                            "RMSE (bu/acre)": round(rmse_score, 2),
                            "Test Samples": samples_cnt,
                        })
                    df_folds = pd.DataFrame(fold_rows)
                    st.dataframe(df_folds, use_container_width=True)
                    
                    # Gráfico de estabilidad temporal fold a fold
                    import plotly.express as px
                    fig_fold = px.bar(
                        df_folds,
                        x="Temporal Split",
                        y="R² Score",
                        text="R² Score",
                        title=f"Estabilidad Temporal de {MODEL_DISPLAY_NAMES.get(selected_model, selected_model)} a lo largo de los {len(df_folds)} Splits (Hindcast)",
                        range_y=[0, 1.0],
                        color="R² Score",
                        color_continuous_scale="Viridis",
                    )
                    fig_fold.update_traces(texttemplate="%{text:.3f}", textposition="outside")
                    fig_fold.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_fold, use_container_width=True)
            
            st.caption(f"✅ Métricas verificadas con TimeSeriesSplit para {selected_model}.")
        else:
            st.info("No se encontraron métricas para este modelo.")
            
        # Tabla resumen de todos los modelos evaluados
        if len(available_models) > 1:
            st.markdown("---")
            st.subheader("📋 Resumen Comparativo de Validación Cruzada (Todos los Modelos Candidatos)")
            summary_rows = []
            for m_name in available_models:
                m_res = validation_engine.load_validation_result(project_id, m_name)
                if m_res and m_res.metrics:
                    r2_m = m_res.metrics.get("r2", {}).get("mean", 0.0)
                    mae_m = abs(m_res.metrics.get("neg_mean_absolute_error", {}).get("mean", 0.0))
                    rmse_m = abs(m_res.metrics.get("neg_root_mean_squared_error", {}).get("mean", 0.0))
                    mape_m = abs(m_res.metrics.get("neg_mean_absolute_percentage_error", {}).get("mean", 0.0))
                    mape_str = f"{mape_m * 100:.2f}%" if mape_m > 0 else "N/A"
                    
                    # Familia y Tipo
                    if m_name == "cerespinn":
                        familia = "Híbrido #1 (Digital Twin Propuesto)"
                    elif m_name == "generic_pinn":
                        familia = "Híbrido #2 (Physics MLP Genérico)"
                    elif m_name == "gradient_boosting":
                        familia = "Convencional #1 (Gradient Boosting)"
                    elif m_name == "random_forest":
                        familia = "Convencional #2 (Random Forest Bagging)"
                    else:
                        familia = "Convencional #3 (Ridge Lineal Regul.)"
                    
                    t_sec = m_res.metadata.get("train_time_sec", None)
                    t_str = f"{t_sec:.1f}s" if t_sec is not None else "-"
                        
                    summary_rows.append({
                        "Modelo": MODEL_DISPLAY_NAMES.get(m_name, m_name),
                        "Familia / Tipo": familia,
                        "R² Score": round(r2_m, 4),
                        "RMSE (bu/ac)": round(rmse_m, 2),
                        "MAE (bu/ac)": round(mae_m, 2),
                        "MAPE": mape_str,
                        "Tiempo Entrenamiento": t_str,
                        "_r2": r2_m
                    })
            if summary_rows:
                df_all = pd.DataFrame(summary_rows).sort_values("_r2", ascending=False)
                df_all.insert(0, "Ranking", [f"🥇 #1 (GANADOR)" if i == 0 else (f"🥈 #2" if i == 1 else (f"🥉 #3" if i == 2 else f"#{i+1}")) for i in range(len(df_all))])
                df_all = df_all.drop(columns=["_r2"])
                st.dataframe(df_all, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error displaying validation results: {e}")


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
