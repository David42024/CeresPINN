"""Preprocessing UI components for ML Lab.

This module provides UI components for configuring and applying data preprocessing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


def render_preprocessing_config(spec: Any) -> None:
    """Render preprocessing configuration interface.
    
    Args:
        spec: ProjectSpecification
    """
    st.subheader("Preprocessing Configuration")
    
    preprocessing = spec.preprocessing
    
    # Basic options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_handle_missing = st.checkbox(
            "Handle Missing Values",
            value=preprocessing.handle_missing,
            help="Impute or remove missing values"
        )
    
    with col2:
        new_handle_duplicates = st.checkbox(
            "Handle Duplicates",
            value=preprocessing.handle_duplicates,
            help="Remove duplicate rows"
        )
    
    with col3:
        new_handle_outliers = st.checkbox(
            "Handle Outliers",
            value=preprocessing.handle_outliers,
            help="Detect and handle outlier values"
        )
    
    st.markdown("---")
    
    # Scaling options
    st.markdown("### Feature Scaling")
    
    scaling_options = ["None", "standard", "minmax", "robust"]
    current_scaling = preprocessing.scaling or "None"
    
    new_scaling = st.selectbox(
        "Scaling Method",
        options=scaling_options,
        index=scaling_options.index(current_scaling),
        help="Standardize or normalize numerical features"
    )
    
    if new_scaling != "None":
        st.info(f"Selected scaling: {new_scaling}")
    
    st.markdown("---")
    
    # Encoding options
    st.markdown("### Categorical Encoding")
    
    encoding_options = ["None", "onehot", "label", "target"]
    current_encoding = preprocessing.encoding or "None"
    
    new_encoding = st.selectbox(
        "Encoding Method",
        options=encoding_options,
        index=encoding_options.index(current_encoding),
        help="Encode categorical features"
    )
    
    if new_encoding != "None":
        st.info(f"Selected encoding: {new_encoding}")
    
    st.markdown("---")
    
    # Feature engineering
    st.markdown("### Feature Engineering")
    
    new_feature_engineering = st.checkbox(
        "Enable Feature Engineering",
        value=preprocessing.feature_engineering,
        help="Generate additional features from existing ones"
    )
    
    if new_feature_engineering:
        st.info("Feature engineering will generate polynomial features, interaction terms, etc.")
    
    st.markdown("---")
    
    # Feature selection
    st.markdown("### Feature Selection")
    
    new_feature_selection = st.checkbox(
        "Enable Feature Selection",
        value=preprocessing.feature_selection,
        help="Select most important features automatically"
    )
    
    if new_feature_selection:
        st.info("Feature selection will use methods like mutual information, chi-square, etc.")
    
    st.markdown("---")
    
    # Custom transformations
    st.markdown("### Custom Transformations")
    
    if preprocessing.custom_transformations:
        st.write("Current custom transformations:")
        for i, transform in enumerate(preprocessing.custom_transformations):
            with st.expander(f"Transformation {i+1}"):
                st.json(transform)
    
    # Add new transformation
    with st.expander("Add Custom Transformation"):
        transform_type = st.selectbox(
            "Transformation Type",
            options=["log", "sqrt", "boxcox", "yeo-johnson", "custom"],
        )
        
        if transform_type == "custom":
            custom_formula = st.text_input("Custom Formula (using pandas syntax)")
            if custom_formula:
                st.caption("Example: np.log1p(x) for log(1+x) transformation")
        
        if st.button("Add Transformation"):
            new_transform = {"type": transform_type}
            if transform_type == "custom":
                new_transform["formula"] = custom_formula
            
            preprocessing.custom_transformations.append(new_transform)
            st.success("Transformation added!")
            st.rerun()
    
    # Apply changes
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Apply Changes", type="primary"):
            preprocessing.handle_missing = new_handle_missing
            preprocessing.handle_duplicates = new_handle_duplicates
            preprocessing.handle_outliers = new_handle_outliers
            preprocessing.scaling = new_scaling if new_scaling != "None" else None
            preprocessing.encoding = new_encoding if new_encoding != "None" else None
            preprocessing.feature_engineering = new_feature_engineering
            preprocessing.feature_selection = new_feature_selection
            
            st.success("Preprocessing configuration updated!")
    
    with col2:
        if st.button("Reset to Defaults"):
            from core.project import PreprocessingConfig
            spec.preprocessing = PreprocessingConfig()
            st.success("Reset to defaults!")
            st.rerun()


def render_missing_value_strategy(df: pd.DataFrame) -> Dict[str, Any]:
    """Render missing value strategy configuration.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Dictionary with missing value strategy configuration
    """
    st.subheader("Missing Value Strategy")
    
    missing = df.isna().sum()
    missing_cols = missing[missing > 0]
    
    if len(missing_cols) == 0:
        st.success("No missing values found!")
        return {}
    
    st.info(f"Found {len(missing_cols)} columns with missing values")
    
    # Show missing by column
    missing_df = pd.DataFrame({
        "Column": missing_cols.index,
        "Missing Count": missing_cols.values,
        "Missing %": (missing_cols.values / len(df) * 100).round(2),
    })
    st.dataframe(missing_df, use_container_width=True)
    
    # Strategy selection
    st.markdown("### Strategy Selection")
    
    strategy = st.selectbox(
        "Overall Strategy",
        options=["drop", "mean", "median", "mode", "constant", "forward_fill", "backward_fill", "knn"],
        help="How to handle missing values"
    )
    
    config = {"strategy": strategy}
    
    if strategy == "constant":
        fill_value = st.number_input("Fill Value", value=0)
        config["fill_value"] = fill_value
    
    if strategy == "knn":
        n_neighbors = st.number_input("KNN Neighbors", min_value=1, max_value=20, value=5)
        config["n_neighbors"] = n_neighbors
    
    # Per-column override
    st.markdown("### Per-Column Override")
    
    with st.expander("Configure per-column strategies"):
        for col in missing_cols.index:
            col_strategy = st.selectbox(
                f"{col}",
                options=["use_default", "drop", "mean", "median", "mode", "constant", "forward_fill", "backward_fill"],
                key=f"missing_{col}",
            )
            
            if col_strategy != "use_default":
                if col_strategy == "constant":
                    fill_value = st.number_input(f"Fill value for {col}", value=0, key=f"fill_{col}")
                    config[col] = {"strategy": col_strategy, "fill_value": fill_value}
                else:
                    config[col] = {"strategy": col_strategy}
    
    return config


def render_scaling_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Render scaling configuration.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Dictionary with scaling configuration
    """
    st.subheader("Feature Scaling Configuration")
    
    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numerical_cols:
        st.info("No numerical columns found")
        return {}
    
    st.info(f"Found {len(numerical_cols)} numerical columns")
    
    # Select columns to scale
    cols_to_scale = st.multiselect(
        "Select columns to scale",
        options=numerical_cols,
        default=numerical_cols,
    )
    
    if not cols_to_scale:
        return {}
    
    # Scaling method
    method = st.selectbox(
        "Scaling Method",
        options=["standard", "minmax", "robust", "maxabs", "normalizer"],
        help="Method for scaling features"
    )
    
    config = {
        "method": method,
        "columns": cols_to_scale,
    }
    
    # Method-specific parameters
    if method == "minmax":
        feature_range = st.slider("Feature Range", 0.0, 1.0, (0.0, 1.0))
        config["feature_range"] = feature_range
    
    if method == "robust":
        quantile_range = st.slider("Quantile Range", 0.0, 1.0, (25.0, 75.0))
        config["quantile_range"] = quantile_range
    
    return config


def render_encoding_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Render categorical encoding configuration.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Dictionary with encoding configuration
    """
    st.subheader("Categorical Encoding Configuration")
    
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not categorical_cols:
        st.info("No categorical columns found")
        return {}
    
    st.info(f"Found {len(categorical_cols)} categorical columns")
    
    # Select columns to encode
    cols_to_encode = st.multiselect(
        "Select columns to encode",
        options=categorical_cols,
        default=categorical_cols,
    )
    
    if not cols_to_encode:
        return {}
    
    # Encoding method
    method = st.selectbox(
        "Encoding Method",
        options=["onehot", "label", "target", "ordinal"],
        help="Method for encoding categorical features"
    )
    
    config = {
        "method": method,
        "columns": cols_to_encode,
    }
    
    # Per-column override
    if method != "onehot":
        with st.expander("Configure per-column methods"):
            for col in cols_to_encode:
                col_method = st.selectbox(
                    f"{col}",
                    options=["use_default", "onehot", "label", "target"],
                    key=f"encode_{col}",
                )
                
                if col_method != "use_default":
                    if col not in config:
                        config["per_column"] = {}
                    config["per_column"][col] = col_method
    
    return config


def render_outlier_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Render outlier handling configuration.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        Dictionary with outlier configuration
    """
    st.subheader("Outlier Handling Configuration")
    
    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numerical_cols:
        st.info("No numerical columns found")
        return {}
    
    # Detection method
    detection_method = st.selectbox(
        "Detection Method",
        options=["iqr", "zscore", "isolation_forest", "local_outlier_factor"],
        help="Method for detecting outliers"
    )
    
    config = {"detection_method": detection_method}
    
    # Method-specific parameters
    if detection_method == "iqr":
        iqr_multiplier = st.slider("IQR Multiplier", 1.0, 3.0, 1.5)
        config["iqr_multiplier"] = iqr_multiplier
    
    if detection_method == "zscore":
        z_threshold = st.slider("Z-Score Threshold", 1.0, 5.0, 3.0)
        config["z_threshold"] = z_threshold
    
    if detection_method == "isolation_forest":
        contamination = st.slider("Contamination", 0.01, 0.5, 0.1)
        config["contamination"] = contamination
    
    # Handling strategy
    handling_strategy = st.selectbox(
        "Handling Strategy",
        options=["remove", "cap", "transform", "ignore"],
        help="How to handle detected outliers"
    )
    
    config["handling_strategy"] = handling_strategy
    
    # Select columns
    cols_to_check = st.multiselect(
        "Select columns to check for outliers",
        options=numerical_cols,
        default=numerical_cols,
    )
    
    config["columns"] = cols_to_check
    
    return config


def render_preprocessing_pipeline(df: pd.DataFrame, spec: Any) -> Dict[str, Any]:
    """Render complete preprocessing pipeline configuration.
    
    Args:
        df: DataFrame to preprocess
        spec: ProjectSpecification
    
    Returns:
        Dictionary with complete preprocessing configuration
    """
    st.title("🔧 Preprocessing Pipeline")
    st.markdown("---")
    
    config = {}
    
    # Missing values
    with st.expander("Missing Values", expanded=True):
        config["missing"] = render_missing_value_strategy(df)
    
    # Scaling
    with st.expander("Feature Scaling"):
        config["scaling"] = render_scaling_config(df)
    
    # Encoding
    with st.expander("Categorical Encoding"):
        config["encoding"] = render_encoding_config(df)
    
    # Outliers
    with st.expander("Outlier Handling"):
        config["outliers"] = render_outlier_config(df)
    
    # Summary
    st.markdown("---")
    st.subheader("Pipeline Summary")
    
    summary = []
    if config.get("missing"):
        summary.append(f"Missing values: {config['missing'].get('strategy', 'N/A')}")
    if config.get("scaling"):
        summary.append(f"Scaling: {config['scaling'].get('method', 'N/A')} on {len(config['scaling'].get('columns', []))} columns")
    if config.get("encoding"):
        summary.append(f"Encoding: {config['encoding'].get('method', 'N/A')} on {len(config['encoding'].get('columns', []))} columns")
    if config.get("outliers"):
        summary.append(f"Outliers: {config['outliers'].get('detection_method', 'N/A')}")
    
    for item in summary:
        st.write(f"• {item}")
    
    # Apply button
    st.markdown("---")
    if st.button("Apply Preprocessing Pipeline", type="primary"):
        st.success("Preprocessing pipeline applied!")
        # TODO: Actually apply preprocessing
        return config
    
    return config
