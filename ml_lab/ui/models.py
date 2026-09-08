"""Model selection and training UI components for ML Lab.

This module provides UI components for selecting models, configuring
hyperparameters, and triggering training.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import streamlit as st


def render_model_catalog(catalog: Any, problem_type: str, data_type: str, spec: Any = None) -> List[str]:
    """Render model catalog with filtering and strict FICHA 5 alignment.
    
    Args:
        catalog: ModelCatalog instance
        problem_type: Type of ML problem
        data_type: Type of data
        spec: Optional ProjectSpecification
    
    Returns:
        List of selected model names
    """
    st.subheader("Model Catalog")
    
    # Check if project is aligned with FICHA 5 (CeresPINN Digital Twin)
    is_ficha5 = False
    if spec is not None:
        proj_text = f"{getattr(spec, 'project_name', '')} {getattr(spec, 'description', '')} {getattr(spec, 'domain', '')}".lower()
        is_ficha5 = any(k in proj_text for k in [
            "cerespinn", "maize", "ficha 5", "ficha5", "cmip6", "ssp",
            "climate-adaptive", "digital twin", "drought-resilient", "crop model", "agriculture"
        ])
    
    if is_ficha5:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(59, 130, 246, 0.12)); 
                        padding: 16px 20px; border-radius: 8px; border-left: 5px solid #10b981; margin-bottom: 20px;">
                <h4 style="margin:0; color:#10b981; font-weight:700;">🌽 MODELO REQUERIDO POR FICHA 5</h4>
                <p style="margin:6px 0 0 0; font-size:14px; line-height:1.5;">
                    <strong>Modelo Principal:</strong> <code>cerespinn</code> (Physics-Informed Neural Network que integra ecuaciones de pérdida física de DSSAT/CERES: acumulación de biomasa RUE, desarrollo fenológico GDD y balance hídrico ET).<br>
                    <strong>Baselines de Comparación Opcionales:</strong> <code>xgboost</code> y <code>random_forest</code>.<br>
                    <em>Los modelos no pertinentes para Ficha 5 (SVM, regresión lineal genérica, redes no informadas por física) han sido filtrados para cumplir con el protocolo experimental.</em>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        only_ficha5 = st.checkbox(
            "🎯 Entrenar únicamente con especificación FICHA 5 (CeresPINN + baselines agronómicos)",
            value=True,
            help="Mantiene únicamente cerespinn y baselines comparativos válidos según la metodología de Ficha 5."
        )
    else:
        only_ficha5 = False

    # Get recommended models
    if is_ficha5:
        recommended_models = ["cerespinn"]
    else:
        recommended_models = catalog.get_recommended_models(problem_type, data_type)
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_interpretable = st.checkbox("Interpretable Only")
    with col2:
        filter_fast = st.checkbox("Fast Training Only")
    with col3:
        filter_memory_efficient = st.checkbox("Memory Efficient Only")
    
    # Get all models for problem type
    all_models = catalog.get_models_by_problem_type(problem_type)
    
    # Apply filters
    filtered_models = []
    for model_metadata in all_models:
        if only_ficha5 and model_metadata.name not in ("cerespinn", "xgboost", "random_forest"):
            continue
        if filter_interpretable and not model_metadata.interpretable:
            continue
        if filter_fast and not model_metadata.fast_training:
            continue
        if filter_memory_efficient and not model_metadata.memory_efficient:
            continue
        filtered_models.append(model_metadata)
    
    # Prioritize cerespinn at the very top
    filtered_models.sort(
        key=lambda m: (0 if m.name == "cerespinn" else (1 if m.name in ("xgboost", "random_forest") else 2))
    )
    
    # Display models
    st.markdown(f"### Available Models ({len(filtered_models)})")
    
    selected_models = []
    
    for model_metadata in filtered_models:
        is_primary = model_metadata.name == "cerespinn"
        title_badge = f"🌽 {model_metadata.name} (REQUERIDO POR FICHA 5)" if is_primary else model_metadata.name
        
        with st.expander(title_badge, expanded=is_primary):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Description:** {model_metadata.description}")
                st.write(f"**Category:** {model_metadata.category.value}")
            
            with col2:
                st.write(f"**Requires Scaling:** {model_metadata.requires_scaling}")
                st.write(f"**Handles Missing:** {model_metadata.handles_missing}")
            
            if is_primary:
                st.markdown(
                    """
                    **🔬 Ficha 5 Physics-Informed Constraints:**
                    - *Loss Término 1 (Biomasa):* Eficiencia de uso de radiación (RUE) acoplada a forzamiento radiativo CMIP6.
                    - *Loss Término 2 (Fenología):* Grados Día de Crecimiento (GDD acumulado para fechas de floración y madurez fisiológica).
                    - *Loss Término 3 (Balance Hídrico):* Evapotranspiración real/potencial (ET) y estrés hídrico edáfico (SoilGrids 2.0).
                    """
                )
            
            # Metadata
            with st.expander("Additional Information"):
                st.write(f"**Handles Categorical:** {model_metadata.handles_categorical}")
                st.write(f"**Interpretable:** {model_metadata.interpretable}")
                st.write(f"**Fast Training:** {model_metadata.fast_training}")
                st.write(f"**Fast Inference:** {model_metadata.fast_inference}")
                st.write(f"**Memory Efficient:** {model_metadata.memory_efficient}")
                
                if model_metadata.dependencies:
                    st.write(f"**Dependencies:** {', '.join(model_metadata.dependencies)}")
            
            # Default hyperparameters
            if model_metadata.default_hyperparameters:
                with st.expander("Default Hyperparameters"):
                    st.json(model_metadata.default_hyperparameters)
            
            # Selection checkbox: for FICHA 5, ONLY cerespinn is preselected by default
            is_preselected = (model_metadata.name == "cerespinn") if is_ficha5 else (model_metadata.name in recommended_models)
            if st.checkbox(
                f"Select {model_metadata.name}",
                value=is_preselected,
                key=f"select_{model_metadata.name}",
            ):
                selected_models.append(model_metadata.name)
    
    return selected_models


def render_model_hyperparameters(spec: Any, selected_models: List[str]) -> Dict[str, Dict[str, Any]]:
    """Render hyperparameter configuration for selected models.
    
    Args:
        spec: ProjectSpecification
        selected_models: List of selected model names
    
    Returns:
        Dictionary mapping model names to hyperparameters
    """
    st.subheader("Hyperparameter Configuration")
    
    use_defaults = st.checkbox("Use Default Hyperparameters", value=True)
    
    hyperparameters = {}
    
    def _get_spec_models(s: Any) -> list:
        if s is None:
            return []
        raw = getattr(s, "models", [])
        return raw if isinstance(raw, list) else []

    def _get_model_name(m: Any) -> str:
        if isinstance(m, dict):
            return str(m.get("name", ""))
        return str(getattr(m, "name", ""))

    def _get_model_params(m: Any) -> dict:
        if isinstance(m, dict):
            return dict(m.get("parameters", {}) or {})
        return dict(getattr(m, "parameters", {}) or {})

    models_list = _get_spec_models(spec)

    if not use_defaults:
        for model_name in selected_models:
            with st.expander(f"{model_name}"):
                model_config = next((m for m in models_list if _get_model_name(m) == model_name), None)
                params = _get_model_params(model_config) if model_config else {}
                
                if params:
                    for param_name, param_value in params.items():
                        if isinstance(param_value, (int, float)):
                            new_value = st.number_input(
                                param_name,
                                value=float(param_value),
                                key=f"hyperparam_{model_name}_{param_name}",
                            )
                        elif isinstance(param_value, bool):
                            new_value = st.checkbox(param_name, value=param_value, key=f"hyperparam_{model_name}_{param_name}")
                        else:
                            new_value = st.text_input(
                                param_name,
                                value=str(param_value),
                                key=f"hyperparam_{model_name}_{param_name}",
                            )
                        
                        # Convert back to appropriate type
                        if isinstance(param_value, int):
                            new_value = int(new_value)
                        elif isinstance(param_value, float):
                            new_value = float(new_value)
                        elif isinstance(param_value, bool):
                            pass  # Already bool
                        else:
                            try:
                                if isinstance(param_value, int):
                                    new_value = int(new_value)
                                elif isinstance(param_value, float):
                                    new_value = float(new_value)
                            except ValueError:
                                pass
                        
                        hyperparameters[model_name] = hyperparameters.get(model_name, {})
                        hyperparameters[model_name][param_name] = new_value
                else:
                    st.info("No default hyperparameters available")
    
    return hyperparameters


def render_training_config(spec: Any) -> Dict[str, Any]:
    """Render training configuration interface.
    
    Args:
        spec: ProjectSpecification
    
    Returns:
        Dictionary with training configuration
    """
    st.subheader("Training Configuration")
    
    # Validation
    st.markdown("### Validation")
    
    use_project_validation = st.checkbox("Use Project Validation Settings", value=True)
    
    if not use_project_validation:
        validation_strategy = st.selectbox(
            "Validation Strategy",
            options=["train_test_split", "k_fold", "stratified_k_fold", "time_series_split"],
            index=3,  # default to time_series_split for climate digital twins
        )
        n_splits = st.number_input("N Splits", min_value=2, max_value=10, value=5)
        test_size = st.slider("Test Size", 0.1, 0.5, 0.2)
    else:
        val_obj = getattr(spec, "validation", {})
        if isinstance(val_obj, dict):
            raw_strat = val_obj.get("strategy", "time_series_split")
            n_splits = val_obj.get("n_splits", 5)
            test_size = val_obj.get("test_size", 0.2)
        else:
            raw_strat = getattr(val_obj, "strategy", "time_series_split")
            n_splits = getattr(val_obj, "n_splits", 5)
            test_size = getattr(val_obj, "test_size", 0.2)
        validation_strategy = getattr(raw_strat, "value", str(raw_strat))
        st.info(f"📋 **Estrategia FICHA 5:** `{validation_strategy}` (Hindcast histórico 1990–2020 vs USDA NASS ground truth, {n_splits} splits temporales).")
    
    # Training parameters
    st.markdown("### Training Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        random_state = st.number_input("Random State", value=42)
        epochs = st.number_input("Epochs (for neural networks)", min_value=1, max_value=1000, value=10)
    with col2:
        batch_size = st.number_input("Batch Size", min_value=1, max_value=512, value=128)
        learning_rate = st.number_input("Learning Rate", value=0.001, format="%.4f")
    
    # Advanced options
    st.markdown("### Advanced Options")
    
    enable_early_stopping = st.checkbox("Enable Early Stopping", value=False)
    if enable_early_stopping:
        early_stopping_patience = st.number_input("Early Stopping Patience", min_value=1, max_value=50, value=10)
    else:
        early_stopping_patience = None
    
    enable_checkpointing = st.checkbox("Enable Model Checkpointing", value=True)
    enable_logging = st.checkbox("Enable Detailed Logging", value=True)
    
    config = {
        "validation": {
            "strategy": validation_strategy,
            "n_splits": n_splits,
            "test_size": test_size,
        },
        "training": {
            "random_state": random_state,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
        },
        "advanced": {
            "early_stopping": enable_early_stopping,
            "early_stopping_patience": early_stopping_patience,
            "checkpointing": enable_checkpointing,
            "logging": enable_logging,
        },
    }
    
    return config


def render_model_training_ui(spec: Any, catalog: Any, training_engine: Any) -> None:
    """Render complete model training interface.
    
    Args:
        spec: ProjectSpecification
        catalog: ModelCatalog instance
        training_engine: TrainingEngine instance
    """
    st.title("🧠 Model Training")
    st.markdown("---")
    
    if not st.session_state.get("current_project"):
        st.warning("Please select a project first")
        return
    
    # Check if dataset is available in state, preprocessed memory, or on disk
    from pathlib import Path
    has_dataset = (
        st.session_state.get("current_dataset") is not None
        or st.session_state.get("preprocessed_df") is not None
        or getattr(spec, "dataset_path", None) is not None
        or Path("data/cerespinn_training_preprocessed.csv").exists()
        or Path("data/cerespinn_training_iowa.csv").exists()
    )
    if not has_dataset:
        st.warning("Please analyze or preprocess a dataset first")
        return
    
    # Model selection (with spec passed for FICHA 5 awareness)
    prob_type = spec.problem_type.value if hasattr(spec.problem_type, "value") else str(spec.problem_type)
    dat_type = spec.data_type.value if hasattr(spec.data_type, "value") else str(spec.data_type)
    selected_models = render_model_catalog(
        catalog,
        prob_type,
        dat_type,
        spec=spec,
    )
    
    if not selected_models:
        st.warning("Please select at least one model")
        return
    
    st.markdown("---")
    
    # Hyperparameters
    hyperparameters = render_model_hyperparameters(spec, selected_models)
    
    st.markdown("---")
    
    # Training configuration
    training_config = render_training_config(spec)
    
    st.markdown("---")
    
    # Summary
    st.subheader("Training Summary")
    
    st.write(f"**Models to train:** {', '.join(selected_models)}")
    st.write(f"**Validation strategy:** {training_config['validation']['strategy']}")
    st.write(f"**Random state:** {training_config['training']['random_state']}")
    
    # Train button
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Training", type="primary"):
            import numpy as np
            import pandas as pd

            dataset_path = getattr(spec, "dataset_path", None)
            target = getattr(spec, "target_variable", None)
            
            df = None
            if "preprocessed_df" in st.session_state and st.session_state["preprocessed_df"] is not None:
                df = st.session_state["preprocessed_df"]
            elif dataset_path:
                try:
                    df = pd.read_csv(dataset_path)
                except Exception as e:
                    st.error(f"Could not load dataset: {e}")
                    df = None
            else:
                for cand in [Path("data/cerespinn_training_preprocessed.csv"), Path("data/cerespinn_training_iowa.csv")]:
                    if cand.exists():
                        df = pd.read_csv(cand)
                        break

            if df is None:
                st.error("No dataset found. Please apply preprocessing or analyze a dataset first.")
            else:
                if not target or target not in df.columns:
                    if "yield_bu_acre" in df.columns:
                        target = "yield_bu_acre"
                    else:
                        st.error(f"Target variable '{target}' not found in dataset columns.")
                        df = None

                if df is not None:
                    feature_cols = [c for c in df.columns if c != target]
                    numeric = df[feature_cols].select_dtypes(include=[np.number])
                    frame = pd.concat([numeric, df[[target]]], axis=1).dropna()
                    if frame.empty or len(numeric.columns) == 0:
                        st.error("No usable numeric data after dropping missing values.")
                    else:
                        X = frame[numeric.columns].to_numpy(dtype=float)
                        y = pd.to_numeric(frame[target], errors="coerce").dropna().to_numpy(dtype=float)
                        X = X[: len(y)]
                        feature_names = list(numeric.columns)
                        schedule = {
                            "epochs": int(training_config["training"]["epochs"]),
                            "batch_size": int(training_config["training"]["batch_size"]),
                            "learning_rate": float(training_config["training"]["learning_rate"]),
                        }
                        merged_hp = {}
                        for m in selected_models:
                            base = dict(hyperparameters.get(m, {}) or {})
                            base.update(schedule)
                            merged_hp[m] = base
                        proj_id = getattr(spec, "project_id", None) or (spec.get("project_id") if isinstance(spec, dict) else "cerespinn-maize-digital-twin")
                        with st.spinner("Training models (Physics loss: Biomass + Phenology + Water Balance)..."):
                            results = training_engine.train_multiple_models(
                                model_names=selected_models,
                                X=X,
                                y=y,
                                feature_names=feature_names,
                                target_name=target,
                                hyperparameters=merged_hp,
                                project_id=proj_id,
                            )
                        st.session_state["training_results"] = results
                        for m, res in results.items():
                            if res is None:
                                err_detail = getattr(training_engine, "last_errors", {}).get(m, "Error desconocido durante la ejecución.")
                                st.error(f"❌ **{m}**: El entrenamiento falló.")
                                with st.expander(f"Ver detalle del error ({m})", expanded=True):
                                    st.code(err_detail)
                            else:
                                st.success(f"✅ **{m}** entrenado exitosamente.")
                                st.json(res.metrics)
                        
                        st.info("💡 **Siguiente paso según la FICHA 5:** Dirígete a la pestaña **'Validation'** para verificar el Hindcast histórico (1990–2020) y a **'Statistical Tests'** para ejecutar el test KS, t-test pareado y el análisis de sensibilidad de Sobol.")
    
    with col2:
        if st.button("Save Configuration"):
            config = {
                "models": selected_models,
                "hyperparameters": hyperparameters,
                "training": training_config,
            }
            artifact_manager = st.session_state.artifact_manager
            proj_id = getattr(spec, "project_id", None) or (spec.get("project_id") if isinstance(spec, dict) else "cerespinn-maize-digital-twin")
            artifact_manager.save_artifact(
                proj_id,
                "experiments",
                "training_config.json",
                config,
            )
            st.success("Configuration saved!")
