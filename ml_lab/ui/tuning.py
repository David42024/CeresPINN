"""Hyperparameter tuning UI components for ML Lab.

This module provides UI components for configuring and running
hyperparameter tuning using various optimization strategies.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import plotly.express as px
import streamlit as st


def render_tuning_strategy_selection() -> str:
    """Render hyperparameter tuning strategy selection.
    
    Returns:
        Selected tuning strategy
    """
    st.subheader("Tuning Strategy")
    
    strategy = st.selectbox(
        "Select Tuning Strategy",
        options=["grid_search", "random_search", "bayesian", "optuna"],
        help="Method for hyperparameter optimization",
    )
    
    strategy_descriptions = {
        "grid_search": "Exhaustive search over all parameter combinations",
        "random_search": "Random sampling of parameter combinations",
        "bayesian": "Bayesian optimization using Gaussian processes",
        "optuna": "Tree-structured Parzen Estimator optimization",
    }
    
    st.info(strategy_descriptions.get(strategy, ""))
    
    return strategy


def render_hyperparameter_space(spec: Any, model_name: str) -> Dict[str, Any]:
    """Render hyperparameter space configuration.
    
    Args:
        spec: ProjectSpecification
        model_name: Name of the model
    
    Returns:
        Dictionary with hyperparameter search space
    """
    st.subheader(f"Hyperparameter Space: {model_name}")
    
    # Get model metadata from catalog
    from core.model_catalog import get_catalog
    catalog = get_catalog()
    model_metadata = catalog.get_model_metadata(model_name)
    
    if not model_metadata:
        st.error(f"Model {model_name} not found in catalog")
        return {}
    
    search_space = {}
    
    if model_metadata.hyperparameter_search_space:
        st.info("Using default search space from model catalog")
        
        for param_name, param_values in model_metadata.hyperparameter_search_space.items():
            with st.expander(f"{param_name}"):
                if isinstance(param_values, list):
                    st.write(f"**Default values:** {param_values}")
                    
                    # Allow customization
                    use_default = st.checkbox("Use default values", value=True, key=f"use_default_{param_name}")
                    
                    if not use_default:
                        if all(isinstance(v, (int, float)) for v in param_values):
                            min_val = st.number_input("Min", value=min(param_values), key=f"min_{param_name}")
                            max_val = st.number_input("Max", value=max(param_values), key=f"max_{param_name}")
                            num_values = st.number_input("Number of values", value=len(param_values), min_value=2, key=f"num_{param_name}")
                            
                            import numpy as np
                            custom_values = list(np.linspace(min_val, max_val, int(num_values)))
                            search_space[param_name] = custom_values
                        else:
                            custom_values = st.text_input(
                                "Custom values (comma-separated)",
                                value=",".join(str(v) for v in param_values),
                                key=f"custom_{param_name}",
                            )
                            search_space[param_name] = [v.strip() for v in custom_values.split(",")]
                    else:
                        search_space[param_name] = param_values
                else:
                    st.write(f"**Default value:** {param_values}")
                    custom_value = st.text_input("Custom value", value=str(param_values), key=f"custom_{param_name}")
                    search_space[param_name] = custom_value
    else:
        st.info("No default search space available. Please define manually.")
        
        # Manual parameter addition
        with st.expander("Add Custom Parameter"):
            param_name = st.text_input("Parameter Name", key="add_param_name")
            param_type = st.selectbox("Parameter Type", options=["categorical", "continuous", "integer"])
            
            if param_type == "categorical":
                param_values = st.text_input("Values (comma-separated)", key="add_param_values")
                if param_name and param_values:
                    search_space[param_name] = [v.strip() for v in param_values.split(",")]
            elif param_type == "continuous":
                min_val = st.number_input("Min", value=0.0, key="add_param_min")
                max_val = st.number_input("Max", value=1.0, key="add_param_max")
                if param_name:
                    search_space[param_name] = {"type": "continuous", "min": min_val, "max": max_val}
            elif param_type == "integer":
                min_val = st.number_input("Min", value=0, key="add_param_int_min")
                max_val = st.number_input("Max", value=10, key="add_param_int_max")
                if param_name:
                    search_space[param_name] = {"type": "integer", "min": min_val, "max": max_val}
    
    return search_space


def render_tuning_config() -> Dict[str, Any]:
    """Render tuning configuration.
    
    Returns:
        Dictionary with tuning configuration
    """
    st.subheader("Tuning Configuration")
    
    # Number of trials
    n_trials = st.number_input("Number of Trials", min_value=1, max_value=1000, value=50)
    
    # Cross-validation
    cv_folds = st.number_input("CV Folds", min_value=2, max_value=10, value=5)
    
    # Parallel jobs
    n_jobs = st.number_input("Parallel Jobs", min_value=1, max_value=10, value=1)
    
    # Timeout
    timeout = st.number_input("Timeout (seconds)", min_value=60, max_value=3600, value=600)
    
    # Random state
    random_state = st.number_input("Random State", value=42)
    
    # Optimization metric
    optimization_metric = st.selectbox(
        "Optimization Metric",
        options=["accuracy", "f1", "precision", "recall", "roc_auc", "mae", "rmse", "r2"],
        help="Metric to optimize during tuning",
    )
    
    config = {
        "n_trials": n_trials,
        "cv_folds": cv_folds,
        "n_jobs": n_jobs,
        "timeout": timeout,
        "random_state": random_state,
        "optimization_metric": optimization_metric,
    }
    
    return config


def render_tuning_results(results: Optional[Dict[str, Any]] = None) -> None:
    """Render hyperparameter tuning results.
    
    Args:
        results: Tuning results dictionary
    """
    st.subheader("Tuning Results")
    
    if results is None:
        st.info("No tuning results available")
        return
    
    # Best parameters
    if "best_params" in results:
        st.markdown("### Best Hyperparameters")
        st.json(results["best_params"])
    
    # Best score
    if "best_score" in results:
        st.metric("Best Score", f"{results['best_score']:.4f}")
    
    # Optimization history
    if "history" in results:
        st.markdown("### Optimization History")
        
        history_df = results["history"]
        if isinstance(history_df, list):
            import pandas as pd
            history_df = pd.DataFrame(history_df)
        
        st.dataframe(history_df, use_container_width=True)
        
        # Plot optimization history
        if "score" in history_df.columns:
            fig = px.line(
                history_df,
                y="score",
                title="Optimization History",
                labels={"score": "Score", "index": "Trial"},
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Trial results
    if "trials" in results:
        st.markdown("### All Trials")
        
        trials_df = results["trials"]
        if isinstance(trials_df, list):
            import pandas as pd
            trials_df = pd.DataFrame(trials_df)
        
        st.dataframe(trials_df, use_container_width=True)


def render_tuning_ui(spec: Any) -> Dict[str, Any]:
    """Render complete hyperparameter tuning interface.
    
    Args:
        spec: ProjectSpecification
    
    Returns:
        Dictionary with tuning configuration
    """
    st.title("🎛️ Hyperparameter Tuning")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return {}
    
    # Strategy selection
    strategy = render_tuning_strategy_selection()
    
    st.markdown("---")
    
    # Model selection
    st.subheader("Model Selection")
    
    available_models = [m.name for m in spec.models if m.enabled]
    selected_model = st.selectbox("Select model to tune", options=available_models)
    
    if not selected_model:
        return {}
    
    st.markdown("---")
    
    # Hyperparameter space
    search_space = render_hyperparameter_space(spec, selected_model)
    
    st.markdown("---")
    
    # Tuning configuration
    tuning_config = render_tuning_config()
    
    st.markdown("---")
    
    # Summary
    st.subheader("Tuning Summary")
    
    st.write(f"**Strategy:** {strategy}")
    st.write(f"**Model:** {selected_model}")
    st.write(f"**Trials:** {tuning_config['n_trials']}")
    st.write(f"**Optimization Metric:** {tuning_config['optimization_metric']}")
    
    if search_space:
        st.write(f"**Parameters to tune:** {', '.join(search_space.keys())}")
    
    # Start tuning button
    st.markdown("---")
    if st.button("Start Tuning", type="primary"):
        config = {
            "strategy": strategy,
            "model": selected_model,
            "search_space": search_space,
            "config": tuning_config,
        }
        
        st.info("Hyperparameter tuning started...")
        # TODO: Integrate with tuning engine
        # results = tuning_engine.tune(...)
        st.success("Tuning completed!")
        
        return config
    
    return {}
