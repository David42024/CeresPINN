"""Experiment management UI components for ML Lab.

This module provides UI components for managing ML experiments including
creating, tracking, and comparing experiments.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


def render_experiment_list(artifact_manager: Any, project_id: str) -> List[Dict[str, Any]]:
    """Render list of experiments for a project.
    
    Args:
        artifact_manager: ArtifactManager instance
        project_id: Project ID
    
    Returns:
        List of experiment metadata
    """
    st.subheader("Experiments")
    
    try:
        experiments = artifact_manager.list_artifacts(project_id, "experiments")
        
        if not experiments:
            st.info("No experiments run yet")
            return []
        
        # Discover experiments from either metadata or result artifacts. Metadata
        # can be empty because save_artifact stores the experiment config as data.
        experiment_data = []
        experiment_names = set()
        for exp_path in experiments:
            if not exp_path.is_file():
                continue
            name = exp_path.name
            if name.endswith("_metadata.json"):
                experiment_names.add(name[:-len("_metadata.json")])
            elif name.endswith("_results.json"):
                experiment_names.add(name[:-len("_results.json")])

        for experiment_name in sorted(experiment_names, reverse=True):
            row = {"name": experiment_name}
            metadata_name = f"{experiment_name}_metadata.json"
            results_name = f"{experiment_name}_results.json"

            try:
                metadata = artifact_manager.load_artifact(
                    project_id, "experiments", metadata_name
                )
                if isinstance(metadata, dict):
                    row.update(metadata)
            except (FileNotFoundError, TypeError, ValueError):
                pass

            try:
                result = artifact_manager.load_artifact(
                    project_id, "experiments", results_name
                )
                if isinstance(result, dict):
                    row.setdefault("status", result.get("status", "unknown"))
                    row.setdefault("completed_at", result.get("completed_at"))
                    row["model_results"] = result.get("model_results", {})
            except (FileNotFoundError, TypeError, ValueError):
                row.setdefault("status", "pending")

            experiment_data.append(row)
        
        if experiment_data:
            # Display as table
            df = pd.DataFrame(experiment_data)
            st.dataframe(df, use_container_width=True)
            
            return experiment_data
    except Exception as e:
        st.error(f"Error loading experiments: {e}")
    
    return []


def render_experiment_form(spec: Any) -> Dict[str, Any]:
    """Render experiment creation form.
    
    Args:
        spec: ProjectSpecification
    
    Returns:
        Dictionary with experiment configuration
    """
    st.subheader("Create New Experiment")
    
    with st.form("experiment_form"):
        # Experiment name
        experiment_name = st.text_input(
            "Experiment Name",
            value=f"{spec.project_name}_exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
        
        # Description
        description = st.text_area(
            "Description",
            placeholder="Describe the purpose of this experiment...",
            height=80,
        )
        
        # Model selection
        st.markdown("### Model Selection")
        
        available_models = [m.name for m in spec.models if m.enabled]
        selected_models = st.multiselect(
            "Select models to train",
            options=available_models,
            default=available_models,
        )
        
        # Hyperparameters
        st.markdown("### Hyperparameters")
        
        use_default_hyperparams = st.checkbox(
            "Use default hyperparameters",
            value=True,
        )
        
        hyperparams = {}
        if not use_default_hyperparams:
            for model_name in selected_models:
                with st.expander(f"{model_name} Hyperparameters"):
                    model_config = next((m for m in spec.models if m.name == model_name), None)
                    if model_config and model_config.parameters:
                        for param_name, param_value in model_config.parameters.items():
                            if isinstance(param_value, (int, float)):
                                new_value = st.number_input(param_name, value=param_value, key=f"param_{model_name}_{param_name}")
                            else:
                                new_value = st.text_input(param_name, value=str(param_value), key=f"param_{model_name}_{param_name}")
                            hyperparams[f"{model_name}.{param_name}"] = new_value
        
        # Validation configuration
        st.markdown("### Validation Configuration")
        
        use_project_validation = st.checkbox(
            "Use project validation settings",
            value=True,
        )
        
        if not use_project_validation:
            validation_strategy = st.selectbox(
                "Validation Strategy",
                options=["train_test_split", "k_fold", "stratified_k_fold", "time_series_split"],
            )
            n_splits = st.number_input("N Splits", min_value=2, max_value=10, value=5)
            test_size = st.slider("Test Size", 0.1, 0.5, 0.2)
        else:
            validation_strategy = spec.validation.strategy.value
            n_splits = spec.validation.n_splits
            test_size = spec.validation.test_size
        
        # Additional options
        st.markdown("### Additional Options")
        
        enable_early_stopping = st.checkbox("Enable Early Stopping", value=False)
        enable_checkpointing = st.checkbox("Enable Model Checkpointing", value=True)
        enable_logging = st.checkbox("Enable Detailed Logging", value=True)
        
        submitted = st.form_submit_button("Create Experiment", type="primary")
        
        if submitted:
            if not selected_models:
                st.error("Please select at least one model")
                return None
            
            config = {
                "name": experiment_name,
                "description": description,
                "models": selected_models,
                "hyperparameters": hyperparams if hyperparams else {},
                "validation": {
                    "strategy": validation_strategy,
                    "n_splits": n_splits,
                    "test_size": test_size,
                },
                "options": {
                    "early_stopping": enable_early_stopping,
                    "checkpointing": enable_checkpointing,
                    "logging": enable_logging,
                },
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending",
            }
            
            return config
    
    return None


def render_experiment_comparison(artifact_manager: Any, project_id: str) -> None:
    """Render experiment comparison interface.
    
    Args:
        artifact_manager: ArtifactManager instance
        project_id: Project ID
    """
    st.subheader("Experiment Comparison")
    
    # Load experiments
    experiments = render_experiment_list(artifact_manager, project_id)
    
    if not experiments or len(experiments) < 2:
        st.info("Need at least 2 experiments to compare")
        return
    
    # Select experiments to compare
    experiment_names = [exp["name"] for exp in experiments]
    selected_experiments = st.multiselect(
        "Select experiments to compare",
        options=experiment_names,
        default=experiment_names[:2],
    )
    
    if len(selected_experiments) < 2:
        st.warning("Select at least 2 experiments to compare")
        return
    
    # Load results for selected experiments
    results = []
    for exp_name in selected_experiments:
        try:
            result_name = f"{exp_name}_results.json"
            result = artifact_manager.load_artifact(project_id, "experiments", result_name)
            if result:
                results.append({"experiment": exp_name, **result})
        except Exception:
            pass
    
    if not results:
        st.warning("No results found for selected experiments")
        return
    
    # Create comparison table
    comparison_df = pd.DataFrame(results)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Plot comparison
    if len(results) > 0:
        # Get metric columns
        metric_cols = [
            col for col in comparison_df.columns if col not in ["experiment", "model"]
        ]
        
        if metric_cols:
            # Melt for plotting
            melted_df = comparison_df.melt(
                id_vars=["experiment", "model"],
                value_vars=metric_cols,
                var_name="metric",
                value_name="value",
            )
            
            fig = px.bar(
                melted_df,
                x="experiment",
                y="value",
                color="metric",
                title="Experiment Comparison",
                barmode="group",
            )
            st.plotly_chart(fig, use_container_width=True)


def render_experiment_details(artifact_manager: Any, project_id: str, experiment_name: str) -> None:
    """Render detailed view of a single experiment.
    
    Args:
        artifact_manager: ArtifactManager instance
        project_id: Project ID
        experiment_name: Name of the experiment
    """
    st.subheader(f"Experiment Details: {experiment_name}")
    
    # Load metadata
    try:
        metadata = artifact_manager.get_artifact_metadata(project_id, "experiments", f"{experiment_name}_metadata.json")
        if metadata:
            with st.expander("Experiment Metadata", expanded=True):
                st.json(metadata)
    except Exception as e:
        st.error(f"Error loading metadata: {e}")
    
    # Load results
    try:
        result = artifact_manager.load_artifact(project_id, "experiments", f"{experiment_name}_results.json")
        if result:
            st.markdown("### Results")
            st.json(result)
    except Exception as e:
        st.error(f"Error loading results: {e}")
    
    # Load training history
    try:
        history = artifact_manager.load_artifact(project_id, "experiments", f"{experiment_name}_history.json")
        if history:
            from ui.validation import display_training_history
            display_training_history(history)
    except Exception as e:
        st.info(f"No training history available: {e}")


def render_experiment_tracking(spec: Any, artifact_manager: Any) -> None:
    """Render complete experiment tracking interface.
    
    Args:
        spec: ProjectSpecification
        artifact_manager: ArtifactManager instance
    """
    st.title("🧪 Experiment Tracking")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    project_id = spec.project_id
    
    # ✅ Mostrar experimento recién completado si existe en session state
    if st.session_state.get("experiment_just_completed", False):
        exp_name = st.session_state.get("last_completed_exp", "")
        metrics = st.session_state.get("last_completed_metrics", {})
        if exp_name and metrics:
            st.success(f"🎉 Experimento **{exp_name}** completado exitosamente!")
            st.metric("R²", f"{metrics.get('r2', 0):.4f}")
            st.metric("MAE", f"{metrics.get('mae', 0):.2f}")
            st.metric("RMSE", f"{metrics.get('rmse', 0):.2f}")
            st.metric("MAPE", f"{metrics.get('mape', 0):.2%}")
            st.markdown("---")
            st.info("💡 **Next step (FICHA 5):** Go to **'Validation'** for Hindcast verification (1990–2020) and **'Statistical Tests'** for KS test, paired t-test, and Sobol sensitivity analysis.")
            # Reset the flag
            st.session_state.experiment_just_completed = False
            st.session_state.last_completed_exp = ""
            st.session_state.last_completed_metrics = {}
    # Si no hay experimento completado recientemente, continuar normalmente
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Experiments", "New Experiment", "Comparison"])
    
    with tab1:
        experiments = render_experiment_list(artifact_manager, project_id)
        
        if experiments:
            st.markdown("---")
            selected_experiment = st.selectbox(
                "Select experiment to view details",
                options=[exp["name"] for exp in experiments],
            )
            
            if selected_experiment:
                render_experiment_details(artifact_manager, project_id, selected_experiment)
    
    with tab2:
        config = render_experiment_form(spec)
        
        if config:
            # Save experiment configuration
            artifact_manager.save_artifact(
                project_id,
                "experiments",
                f"{config['name']}_metadata.json",
                config,
            )
            
            st.success(f"Experiment '{config['name']}' created!")
            
            # ── Execute the experiment ──────────────────────────────
            import numpy as np
            import pandas as pd
            from pathlib import Path as _Path

            training_engine = st.session_state.get("training_engine")
            if training_engine is None:
                st.error("Training engine not initialised. Please go to Model Training first.")
            else:
                # 1. Load dataset (same logic as model training UI)
                dataset_path = getattr(spec, "dataset_path", None)
                target = getattr(spec, "target_variable", None)

                df = None
                if st.session_state.get("preprocessed_df") is not None:
                    df = st.session_state["preprocessed_df"]
                elif dataset_path:
                    try:
                        df = pd.read_csv(dataset_path)
                    except Exception:
                        df = None
                else:
                    for cand in [_Path("data/cerespinn_training_preprocessed.csv"),
                                 _Path("data/cerespinn_training_iowa.csv")]:
                        if cand.exists():
                            df = pd.read_csv(cand)
                            break

                if df is None:
                    st.error("No dataset found. Please preprocess or upload a dataset first.")
                else:
                    # Resolve target column
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

                            # Merge hyperparameters from experiment config
                            merged_hp = {}
                            exp_hp = config.get("hyperparameters", {})
                            for m in config["models"]:
                                base = {}
                                # Collect any dotted-key hyperparams (e.g. "cerespinn.hidden_dim")
                                for k, v in exp_hp.items():
                                    if k.startswith(f"{m}."):
                                        base[k.split(".", 1)[1]] = v
                                merged_hp[m] = base

                            # Update training engine config from experiment validation settings
                            val_cfg = config.get("validation", {})
                            training_engine.config.validation_strategy = val_cfg.get("strategy", "time_series_split")
                            training_engine.config.n_splits = val_cfg.get("n_splits", 5)
                            training_engine.config.test_size = val_cfg.get("test_size", 0.2)

                            exp_name = config["name"]

                            with st.spinner(f"🔬 Running experiment **{exp_name}** …"):
                                results = training_engine.train_multiple_models(
                                    model_names=config["models"],
                                    X=X,
                                    y=y,
                                    feature_names=feature_names,
                                    target_name=target,
                                    hyperparameters=merged_hp,
                                    project_id=project_id,
                                )

                            # 2. Collect results and save
                            experiment_results = {
                                "name": exp_name,
                                "status": "completed",
                                "completed_at": datetime.utcnow().isoformat(),
                                "model_results": {},
                            }
                            any_success = False

                            for m, res in results.items():
                                if res is None:
                                    err_detail = getattr(training_engine, "last_errors", {}).get(m, "Unknown error")
                                    experiment_results["model_results"][m] = {
                                        "status": "failed",
                                        "error": str(err_detail)[:500],
                                    }
                                    st.error(f"❌ **{m}**: Training failed.")
                                    with st.expander(f"Error details ({m})", expanded=False):
                                        st.code(err_detail)
                                else:
                                    any_success = True
                                    experiment_results["model_results"][m] = {
                                        "status": "success",
                                        "metrics": {k: round(float(v), 6) for k, v in res.metrics.items()},
                                        "model_path": str(res.model_path) if res.model_path else None,
                                    }
                                    st.success(f"✅ **{m}** trained successfully.")
                                    st.json(res.metrics)

                            if not any_success:
                                experiment_results["status"] = "failed"

                            # Persist results
                            artifact_manager.save_artifact(
                                project_id,
                                "experiments",
                                f"{exp_name}_results.json",
                                experiment_results,
                            )

                            # Update metadata status
                            config["status"] = experiment_results["status"]
                            config["completed_at"] = experiment_results["completed_at"]
                            artifact_manager.save_artifact(
                                project_id,
                                "experiments",
                                f"{config['name']}_metadata.json",
                                config,
                            )

                            # ✅ FORZAR REFRESH para que se vea la lista actualizada
                            # Esto recarga la UI para mostrar el experimento recién entrenado
                            st.session_state.experiment_just_completed = True
                            st.session_state.last_completed_exp = exp_name
                            st.session_state.last_completed_metrics = res.metrics if any_success else {}
                            st.rerun()

                            if any_success:
                                st.balloons()
                                st.success(f"✅ **{m}** entrenado exitosamente")
                                st.json(res.metrics)
                                st.info("💡 **Next step (FICHA 5):** Go to **'Validation'** for Hindcast verification (1990–2020) and **'Statistical Tests'** for KS test, paired t-test, and Sobol sensitivity analysis.")
    
    with tab3:
        render_experiment_comparison(artifact_manager, project_id)

