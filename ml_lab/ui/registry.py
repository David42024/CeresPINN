"""Model registry UI components for ML Lab.

This module provides UI components for managing the model registry,
including registering, versioning, and deploying models.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


def render_model_registry(artifact_manager: Any, project_id: str) -> List[Dict[str, Any]]:
    """Render model registry for a project.
    
    Args:
        artifact_manager: ArtifactManager instance
        project_id: Project ID
    
    Returns:
        List of registered models
    """
    st.subheader("Model Registry")
    
    try:
        models = artifact_manager.list_artifacts(project_id, "models")
        
        if not models:
            st.info("No models registered yet")
            return []
        
        # Load model metadata
        model_data = []
        for model_path in models:
            try:
                metadata = artifact_manager.get_artifact_metadata(project_id, "models", model_path.name)
                if metadata:
                    model_data.append({
                        "name": model_path.name,
                        **metadata,
                    })
            except Exception:
                model_data.append({
                    "name": model_path.name,
                    "status": "unknown",
                })
        
        if model_data:
            df = pd.DataFrame(model_data)
            st.dataframe(df, use_container_width=True)
            
            return model_data
    except Exception as e:
        st.error(f"Error loading model registry: {e}")
    
    return []


def render_model_registration(spec: Any) -> Dict[str, Any]:
    """Render model registration form.
    
    Args:
        spec: ProjectSpecification
    
    Returns:
        Dictionary with model registration configuration
    """
    st.subheader("Register New Model")
    
    with st.form("model_registration_form"):
        # Model name
        model_name = st.text_input(
            "Model Name*",
            placeholder="e.g., random_forest_v1",
        )
        
        # Model type
        model_type = st.selectbox(
            "Model Type",
            options=["sklearn", "pytorch", "tensorflow", "onnx", "custom"],
        )
        
        # Model path
        model_path = st.text_input(
            "Model Path*",
            placeholder="/path/to/model.pkl or model.pt",
        )
        
        # Version
        version = st.text_input(
            "Version",
            value="1.0.0",
            placeholder="e.g., 1.0.0",
        )
        
        # Description
        description = st.text_area(
            "Description",
            placeholder="Describe the model...",
            height=80,
        )
        
        # Metadata
        st.markdown("### Additional Metadata")
        
        framework = st.text_input("Framework", placeholder="e.g., scikit-learn, PyTorch")
        training_date = st.date_input("Training Date", value=datetime.now().date())
        
        # Performance metrics
        st.markdown("### Performance Metrics")
        
        col1, col2 = st.columns(2)
        with col1:
            accuracy = st.number_input("Accuracy", min_value=0.0, max_value=1.0, value=0.0, format="%.4f")
            precision = st.number_input("Precision", min_value=0.0, max_value=1.0, value=0.0, format="%.4f")
        with col2:
            recall = st.number_input("Recall", min_value=0.0, max_value=1.0, value=0.0, format="%.4f")
            f1_score = st.number_input("F1 Score", min_value=0.0, max_value=1.0, value=0.0, format="%.4f")
        
        # Tags
        tags = st.text_input(
            "Tags (comma-separated)",
            placeholder="e.g., production, experiment, baseline",
        )
        
        submitted = st.form_submit_button("Register Model", type="primary")
        
        if submitted:
            if not model_name or not model_path:
                st.error("Please fill in required fields")
                return None
            
            config = {
                "name": model_name,
                "type": model_type,
                "path": model_path,
                "version": version,
                "description": description,
                "framework": framework,
                "training_date": training_date.isoformat(),
                "metrics": {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1_score,
                },
                "tags": [tag.strip() for tag in tags.split(",") if tags.strip()],
                "registered_at": datetime.utcnow().isoformat(),
                "status": "registered",
            }
            
            return config
    
    return None


def render_model_versioning(models: List[Dict[str, Any]]) -> None:
    """Render model versioning interface.
    
    Args:
        models: List of registered models
    """
    st.subheader("Model Versioning")
    
    if not models:
        st.info("No models available for versioning")
        return
    
    # Group models by name
    model_groups = {}
    for model in models:
        base_name = model.get("name", "").split("_v")[0]
        if base_name not in model_groups:
            model_groups[base_name] = []
        model_groups[base_name].append(model)
    
    # Display version groups
    for base_name, versions in model_groups.items():
        if len(versions) > 1:
            with st.expander(f"{base_name} ({len(versions)} versions)"):
                for version in sorted(versions, key=lambda x: x.get("version", "0"), reverse=True):
                    st.write(f"**Version {version.get('version')}** - {version.get('registered_at', 'N/A')}")
                    st.write(f"Status: {version.get('status', 'unknown')}")
                    st.write(f"Metrics: {version.get('metrics', {})}")
                    st.markdown("---")
    
    # Promote model
    st.markdown("### Promote Model to Production")
    
    all_models = [m.get("name") for m in models]
    selected_model = st.selectbox("Select model to promote", options=all_models)
    
    if st.button("Promote to Production"):
        st.success(f"Model {selected_model} promoted to production!")
        # TODO: Update model status in registry


def render_model_deployment(models: List[Dict[str, Any]]) -> None:
    """Render model deployment interface.
    
    Args:
        models: List of registered models
    """
    st.subheader("Model Deployment")
    
    if not models:
        st.info("No models available for deployment")
        return
    
    # Select model to deploy
    production_models = [m for m in models if m.get("status") == "production"]
    
    if production_models:
        st.success(f"Current production model: {production_models[0].get('name')}")
    
    all_models = [m.get("name") for m in models]
    selected_model = st.selectbox("Select model to deploy", options=all_models)
    
    # Deployment configuration
    st.markdown("### Deployment Configuration")
    
    deployment_env = st.selectbox(
        "Deployment Environment",
        options=["staging", "production"],
    )
    
    deployment_type = st.selectbox(
        "Deployment Type",
        options=["rest_api", "batch", "streaming", "edge"],
    )
    
    # Resource configuration
    st.markdown("### Resource Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        cpu_limit = st.number_input("CPU Limit", min_value=0.1, max_value=16.0, value=1.0, step=0.1)
        memory_limit = st.number_input("Memory Limit (GB)", min_value=0.5, max_value=64.0, value=2.0)
    with col2:
        replicas = st.number_input("Replicas", min_value=1, max_value=10, value=1)
        gpu_enabled = st.checkbox("Enable GPU", value=False)
    
    if st.button("Deploy Model", type="primary"):
        st.success(f"Model {selected_model} deployed to {deployment_env}!")
        # TODO: Trigger actual deployment


def render_model_registry_ui(spec: Any) -> None:
    """Render complete model registry interface.
    
    Args:
        spec: ProjectSpecification
    """
    st.title("📦 Model Registry")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    artifact_manager = st.session_state.artifact_manager
    project_id = spec.project_id
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Registry", "Register", "Versioning", "Deployment"])
    
    with tab1:
        models = render_model_registry(artifact_manager, project_id)
    
    with tab2:
        config = render_model_registration(spec)
        
        if config:
            artifact_manager.save_artifact(
                project_id,
                "models",
                f"{config['name']}_metadata.json",
                config,
            )
            st.success(f"Model {config['name']} registered successfully!")
            st.rerun()
    
    with tab3:
        models = render_model_registry(artifact_manager, project_id)
        render_model_versioning(models)
    
    with tab4:
        models = render_model_registry(artifact_manager, project_id)
        render_model_deployment(models)
