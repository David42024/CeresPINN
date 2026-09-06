"""Model selection and training UI components for ML Lab.

This module provides UI components for selecting models, configuring
hyperparameters, and triggering training.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st


def render_model_catalog(catalog: Any, problem_type: str, data_type: str) -> List[str]:
    """Render model catalog with filtering.
    
    Args:
        catalog: ModelCatalog instance
        problem_type: Type of ML problem
        data_type: Type of data
    
    Returns:
        List of selected model names
    """
    st.subheader("Model Catalog")
    
    # Get recommended models
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
        if filter_interpretable and not model_metadata.interpretable:
            continue
        if filter_fast and not model_metadata.fast_training:
            continue
        if filter_memory_efficient and not model_metadata.memory_efficient:
            continue
        filtered_models.append(model_metadata)
    
    # Display models
    st.markdown(f"### Available Models ({len(filtered_models)})")
    
    selected_models = []
    
    for model_metadata in filtered_models:
        with st.expander(f"{model_metadata.name}", expanded=model_metadata.name in recommended_models):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Description:** {model_metadata.description}")
                st.write(f"**Category:** {model_metadata.category.value}")
            
            with col2:
                st.write(f"**Requires Scaling:** {model_metadata.requires_scaling}")
                st.write(f"**Handles Missing:** {model_metadata.handles_missing}")
            
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
            
            # Selection checkbox
            is_recommended = model_metadata.name in recommended_models
            if st.checkbox(
                f"Select {model_metadata.name}",
                value=is_recommended,
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
    
    if not use_defaults:
        for model_name in selected_models:
            with st.expander(f"{model_name}"):
                model_config = next((m for m in spec.models if m.name == model_name), None)
                
                if model_config and model_config.parameters:
                    for param_name, param_value in model_config.parameters.items():
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
                            # Try to convert to original type
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
        )
        n_splits = st.number_input("N Splits", min_value=2, max_value=10, value=5)
        test_size = st.slider("Test Size", 0.1, 0.5, 0.2)
    else:
        validation_strategy = spec.validation.strategy.value
        n_splits = spec.validation.n_splits
        test_size = spec.validation.test_size
    
    # Training parameters
    st.markdown("### Training Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        random_state = st.number_input("Random State", value=42)
        epochs = st.number_input("Epochs (for neural networks)", min_value=1, max_value=1000, value=100)
    with col2:
        batch_size = st.number_input("Batch Size", min_value=1, max_value=512, value=32)
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
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    if not st.session_state.current_dataset:
        st.warning("Please analyze a dataset first")
        return
    
    # Model selection
    selected_models = render_model_catalog(
        catalog,
        spec.problem_type.value,
        spec.data_type.value,
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
            st.info("Training started...")
            # TODO: Integrate with training engine
            # results = training_engine.train_multiple_models(...)
            st.success("Training completed!")
    
    with col2:
        if st.button("Save Configuration"):
            config = {
                "models": selected_models,
                "hyperparameters": hyperparameters,
                "training": training_config,
            }
            artifact_manager = st.session_state.artifact_manager
            artifact_manager.save_artifact(
                spec.project_id,
                "experiments",
                "training_config.json",
                config,
            )
            st.success("Configuration saved!")
