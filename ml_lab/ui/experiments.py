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
        
        # Load experiment metadata
        experiment_data = []
        for exp_path in experiments:
            try:
                metadata = artifact_manager.get_artifact_metadata(project_id, "experiments", exp_path.name)
                if metadata:
                    experiment_data.append({
                        "name": exp_path.name,
                        **metadata,
                    })
            except Exception:
                experiment_data.append({
                    "name": exp_path.name,
                    "status": "unknown",
                })
        
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
            result_path = Path(exp_name.replace("_metadata.json", "_results.json"))
            result = artifact_manager.load_artifact(project_id, "experiments", result_path.name)
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
        metric_cols = [col for col in comparison_df.columns if col not in ["experiment", "model"]]
        
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
            
            # TODO: Trigger experiment execution
            st.info("Experiment execution coming soon!")
    
    with tab3:
        render_experiment_comparison(artifact_manager, project_id)
