"""Explainability UI components for ML Lab.

This module provides UI components for model explainability including
feature importance, SHAP values, and other interpretability methods.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def render_explainability_config(spec: Any) -> Dict[str, Any]:
    """Render explainability configuration interface.
    
    Args:
        spec: ProjectSpecification
    
    Returns:
        Dictionary with explainability configuration
    """
    st.subheader("Explainability Configuration")
    
    explainability = spec.explainability
    
    # Enable/disable
    enabled = st.checkbox(
        "Enable Explainability",
        value=explainability.enabled,
        help="Generate explainability artifacts for trained models"
    )
    
    if not enabled:
        return {"enabled": False}
    
    # Method selection
    available_methods = ["feature_importance", "permutation", "shap", "lime"]
    selected_methods = st.multiselect(
        "Select Explainability Methods",
        options=available_methods,
        default=[m for m in available_methods if m in explainability.methods],
        help="Methods to use for model explanation"
    )
    
    # Method descriptions
    method_descriptions = {
        "feature_importance": "Built-in feature importance from models (e.g., tree-based models)",
        "permutation": "Permutation importance - measures feature importance by shuffling values",
        "shap": "SHAP values - game-theoretic approach to explain model predictions",
        "lime": "LIME - local interpretable model-agnostic explanations",
    }
    
    for method in selected_methods:
        st.info(method_descriptions.get(method, ""))
    
    # Advanced options
    st.markdown("### Advanced Options")
    
    n_samples = st.number_input(
        "Number of samples for explanation",
        min_value=10,
        max_value=10000,
        value=100,
        help="Number of samples to use for computing explanations"
    )
    
    background_samples = st.number_input(
        "Background samples (for SHAP)",
        min_value=10,
        max_value=1000,
        value=50,
        help="Number of background samples for SHAP explainer"
    )
    
    config = {
        "enabled": enabled,
        "methods": selected_methods,
        "n_samples": n_samples,
        "background_samples": background_samples,
    }
    
    return config


def render_feature_importance_plot(importance: Dict[str, float]) -> None:
    """Render feature importance plot.
    
    Args:
        importance: Dictionary mapping feature names to importance values
    """
    st.subheader("Feature Importance")
    
    if not importance:
        st.info("No feature importance data available")
        return
    
    # Create DataFrame and sort
    import pandas as pd
    importance_df = pd.DataFrame([
        {"Feature": k, "Importance": v}
        for k, v in importance.items()
    ]).sort_values("Importance", ascending=False)
    
    # Display table
    st.dataframe(importance_df.head(20), use_container_width=True)
    
    # Plot bar chart
    fig = px.bar(
        importance_df.head(20),
        x="Importance",
        y="Feature",
        orientation="h",
        title="Top 20 Feature Importance",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_shap_summary_plot(shap_values: Any, feature_names: List[str]) -> None:
    """Render SHAP summary plot placeholder.
    
    Args:
        shap_values: SHAP values array
        feature_names: List of feature names
    """
    st.subheader("SHAP Summary Plot")
    
    st.info("SHAP visualization requires shap library")
    
    # Placeholder visualization
    import pandas as pd
    import numpy as np
    
    # Create placeholder data for demonstration
    if isinstance(shap_values, np.ndarray):
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        shap_df = pd.DataFrame({
            "Feature": feature_names,
            "Mean |SHAP Value|": mean_abs_shap,
        }).sort_values("Mean |SHAP Value|", ascending=False)
        
        fig = px.bar(
            shap_df.head(20),
            x="Mean |SHAP Value|",
            y="Feature",
            orientation="h",
            title="Mean Absolute SHAP Values",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_permutation_importance_plot(importance: Dict[str, float], std: Optional[Dict[str, float]] = None) -> None:
    """Render permutation importance plot.
    
    Args:
        importance: Dictionary mapping feature names to importance values
        std: Optional dictionary of standard deviations
    """
    st.subheader("Permutation Importance")
    
    if not importance:
        st.info("No permutation importance data available")
        return
    
    import pandas as pd
    
    importance_df = pd.DataFrame([
        {"Feature": k, "Importance": v, "Std": std.get(k, 0) if std else 0}
        for k, v in importance.items()
    ]).sort_values("Importance", ascending=False)
    
    # Plot with error bars
    fig = px.bar(
        importance_df.head(20),
        x="Importance",
        y="Feature",
        error_y="Std" if std else None,
        orientation="h",
        title="Permutation Importance",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_local_explanation(sample_index: int, feature_values: Dict[str, float], explanations: Dict[str, Any]) -> None:
    """Render local explanation for a single prediction.
    
    Args:
        sample_index: Index of the sample
        feature_values: Dictionary of feature values
        explanations: Dictionary of explanation values
    """
    st.subheader(f"Local Explanation: Sample {sample_index}")
    
    # Display feature values
    st.markdown("### Feature Values")
    st.json(feature_values)
    
    # Display explanations
    st.markdown("### Explanation")
    
    if "shap_values" in explanations:
        st.markdown("#### SHAP Values")
        shap_df = pd.DataFrame([
            {"Feature": k, "SHAP Value": v}
            for k, v in explanations["shap_values"].items()
        ]).sort_values("SHAP Value", key=abs, ascending=False)
        
        st.dataframe(shap_df.head(10), use_container_width=True)
        
        # Plot
        fig = px.bar(
            shap_df.head(10),
            x="SHAP Value",
            y="Feature",
            orientation="h",
            title=f"SHAP Values for Sample {sample_index}",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if "lime_explanation" in explanations:
        st.markdown("#### LIME Explanation")
        st.json(explanations["lime_explanation"])


def render_explainability_ui(spec: Any) -> None:
    """Render complete explainability interface.
    
    Args:
        spec: ProjectSpecification
    """
    st.title("🔍 Model Explainability")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    # Configuration
    config = render_explainability_config(spec)
    
    st.markdown("---")
    
    # Load explainability results
    artifact_manager = st.session_state.artifact_manager
    project_id = spec.project_id
    
    try:
        # Try to load explainability artifacts
        feature_importance = artifact_manager.load_artifact(
            project_id, "explainability", "feature_importance.json"
        )
        
        if feature_importance:
            render_feature_importance_plot(feature_importance)
        
        st.markdown("---")
        
        # Permutation importance
        try:
            perm_importance = artifact_manager.load_artifact(
                project_id, "explainability", "permutation_importance.json"
            )
            perm_std = artifact_manager.load_artifact(
                project_id, "explainability", "permutation_std.json"
            )
            
            if perm_importance:
                render_permutation_importance_plot(perm_importance, perm_std)
        except Exception:
            pass
        
        st.markdown("---")
        
        # SHAP values
        try:
            shap_values = artifact_manager.load_artifact(
                project_id, "explainability", "shap_values.npy"
            )
            feature_names = artifact_manager.load_artifact(
                project_id, "explainability", "feature_names.json"
            )
            
            if shap_values is not None and feature_names:
                render_shap_summary_plot(shap_values, feature_names)
        except Exception:
            pass
        
        st.markdown("---")
        
        # Local explanation
        st.subheader("Local Explanations")
        
        sample_index = st.number_input(
            "Sample Index",
            min_value=0,
            max_value=1000,
            value=0,
        )
        
        if st.button("Generate Local Explanation"):
            try:
                feature_values = artifact_manager.load_artifact(
                    project_id, "explainability", f"sample_{sample_index}_features.json"
                )
                explanations = artifact_manager.load_artifact(
                    project_id, "explainability", f"sample_{sample_index}_explanation.json"
                )
                
                if feature_values and explanations:
                    render_local_explanation(sample_index, feature_values, explanations)
            except Exception as e:
                st.error(f"Error loading local explanation: {e}")
        
    except Exception as e:
        st.info(f"No explainability artifacts available. Train models with explainability enabled first: {e}")
