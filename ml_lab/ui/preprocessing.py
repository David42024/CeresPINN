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


def render_scaling_config(df: pd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    """Render scaling configuration with intelligent defaults.
    
    Args:
        df: DataFrame to analyze
        target_column: Optional target column to exclude from feature scaling
    
    Returns:
        Dictionary with scaling configuration
    """
    st.subheader("Feature Scaling Configuration")
    
    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numerical_cols:
        st.info("No numerical columns found")
        return {}
    
    # Exclude target column, temporal index, and constant columns from default feature scaling
    def is_target_or_temporal(col: str) -> bool:
        c_low = col.lower()
        if target_column and target_column.lower() in c_low:
            return True
        if "yield" in c_low or c_low in ("year", "yr", "date", "time"):
            return True
        return False

    default_cols = [
        c for c in numerical_cols 
        if not is_target_or_temporal(c) and df[c].nunique() > 1
    ]
    if not default_cols:
        default_cols = [c for c in numerical_cols if not is_target_or_temporal(c)]
    
    st.info(f"Found {len(numerical_cols)} numerical columns. Recommended features to scale: {len(default_cols)}")
    
    # Select columns to scale
    cols_to_scale = st.multiselect(
        "Select feature columns to scale (excluding target variable):",
        options=numerical_cols,
        default=default_cols,
        help="The target variable and temporal columns should typically remain unscaled or scaled separately."
    )
    
    if not cols_to_scale:
        return {}
    
    # Scaling method
    method = st.selectbox(
        "Scaling Method",
        options=["standard", "minmax", "robust", "maxabs"],
        help="Method for scaling features (StandardScaler is recommended for PINN/ML)."
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
    
    st.info(f"Found {len(categorical_cols)} categorical column(s): {', '.join(categorical_cols)}")
    
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
        options=["onehot", "label", "ordinal"],
        help="One-hot encoding creates binary indicator columns (ideal for CMIP6 scenarios)."
    )
    
    config = {
        "method": method,
        "columns": cols_to_encode,
    }
    
    return config


def render_constant_features_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Render constant feature removal configuration."""
    st.subheader("Constant & Zero-Variance Features")
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
    if constant_cols:
        st.warning(f"Detected {len(constant_cols)} constant column(s) with zero variance: **{', '.join(constant_cols)}** (e.g. seasonal_cdd). Keeping constant features causes numerical singularity.")
        drop_constants = st.checkbox("Remove constant features from training set", value=True)
        return {"drop_constants": drop_constants, "columns": constant_cols}
    else:
        st.info("No constant features found.")
        return {"drop_constants": False, "columns": []}


def render_outlier_config(df: pd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    """Render outlier handling configuration with domain safeguards.
    
    Args:
        df: DataFrame to analyze
        target_column: Optional target column
    
    Returns:
        Dictionary with outlier configuration
    """
    st.subheader("Outlier Handling Configuration")
    
    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numerical_cols:
        st.info("No numerical columns found")
        return {}
    
    # Detection method
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        detection_method = st.selectbox(
            "Detection Method",
            options=["iqr", "zscore"],
            help="Method for detecting outliers"
        )
    with col_d2:
        handling_strategy = st.selectbox(
            "Handling Strategy",
            options=["ignore", "cap", "remove"],
            index=0,
            help="In climate and crop yield data, extreme drought events (e.g. 2012) are physically real. 'ignore' or 'cap' is recommended over deleting rows."
        )
    
    config = {
        "detection_method": detection_method,
        "handling_strategy": handling_strategy,
    }
    
    if detection_method == "iqr":
        config["iqr_multiplier"] = st.slider("IQR Multiplier", 1.0, 3.0, 1.5)
    elif detection_method == "zscore":
        config["z_threshold"] = st.slider("Z-Score Threshold", 1.0, 5.0, 3.0)
    
    # Default columns to check (exclude target and constant)
    default_cols = [
        c for c in numerical_cols 
        if c != target_column and df[c].nunique() > 1 and c.lower() not in ("year", "yr", "date")
    ]
    
    cols_to_check = st.multiselect(
        "Select feature columns to check for outliers (excluding target to preserve climate extremes):",
        options=numerical_cols,
        default=default_cols,
    )
    config["columns"] = cols_to_check
    
    return config


def apply_preprocessing_pipeline(
    df: pd.DataFrame,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """Execute the configured preprocessing transformations on the dataframe."""
    import numpy as np
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder

    df_proc = df.copy()

    # 1. Drop constant features
    if config.get("constants", {}).get("drop_constants") and config["constants"].get("columns"):
        cols_to_drop = [c for c in config["constants"]["columns"] if c in df_proc.columns]
        if cols_to_drop:
            df_proc = df_proc.drop(columns=cols_to_drop)

    # 2. Handle missing values
    missing_cfg = config.get("missing", {})
    if missing_cfg and df_proc.isna().sum().sum() > 0:
        strat = missing_cfg.get("strategy", "mean")
        if strat == "drop_rows":
            df_proc = df_proc.dropna()
        elif strat == "drop_cols":
            df_proc = df_proc.dropna(axis=1)
        elif strat == "mean":
            num_cols = df_proc.select_dtypes(include=[np.number]).columns
            df_proc[num_cols] = df_proc[num_cols].fillna(df_proc[num_cols].mean())
        elif strat == "median":
            num_cols = df_proc.select_dtypes(include=[np.number]).columns
            df_proc[num_cols] = df_proc[num_cols].fillna(df_proc[num_cols].median())

    # 3. Handle outliers
    outliers_cfg = config.get("outliers", {})
    h_strat = outliers_cfg.get("handling_strategy", "ignore")
    outlier_cols = outliers_cfg.get("columns", [])
    if h_strat != "ignore" and outlier_cols:
        for col in outlier_cols:
            if col in df_proc.columns and pd.api.types.is_numeric_dtype(df_proc[col]):
                q1 = df_proc[col].quantile(0.25)
                q3 = df_proc[col].quantile(0.75)
                iqr = q3 - q1
                mult = outliers_cfg.get("iqr_multiplier", 1.5)
                lower = q1 - mult * iqr
                upper = q3 + mult * iqr
                if h_strat == "cap":
                    df_proc[col] = df_proc[col].clip(lower=lower, upper=upper)
                elif h_strat == "remove":
                    df_proc = df_proc[(df_proc[col] >= lower) & (df_proc[col] <= upper)]

    # 4. Categorical encoding
    encoding_cfg = config.get("encoding", {})
    enc_cols = [c for c in encoding_cfg.get("columns", []) if c in df_proc.columns]
    enc_method = encoding_cfg.get("method", "onehot")
    if enc_cols:
        if enc_method == "onehot":
            df_proc = pd.get_dummies(df_proc, columns=enc_cols, drop_first=False, dtype=float)
        elif enc_method in ("label", "ordinal"):
            for col in enc_cols:
                le = LabelEncoder()
                df_proc[col] = le.fit_transform(df_proc[col].astype(str))

    # 5. Feature scaling
    scaling_cfg = config.get("scaling", {})
    scale_cols = [c for c in scaling_cfg.get("columns", []) if c in df_proc.columns]
    scale_method = scaling_cfg.get("method", "standard")
    if scale_cols:
        if scale_method == "standard":
            scaler = StandardScaler()
        elif scale_method == "minmax":
            scaler = MinMaxScaler(feature_range=scaling_cfg.get("feature_range", (0.0, 1.0)))
        elif scale_method == "robust":
            scaler = RobustScaler()
        else:
            scaler = StandardScaler()

        scaled_vals = scaler.fit_transform(df_proc[scale_cols])
        df_proc[scale_cols] = scaled_vals

    return df_proc


def render_preprocessing_pipeline(df: pd.DataFrame, spec: Any) -> Dict[str, Any]:
    """Render complete preprocessing pipeline configuration and execution.
    
    Args:
        df: DataFrame to preprocess
        spec: ProjectSpecification
    
    Returns:
        Dictionary with complete preprocessing configuration
    """
    st.title("🔧 Preprocessing Pipeline")
    st.markdown("---")
    
    target_column = getattr(spec, "target_variable", None)
    if not target_column and "yield_bu_acre" in df.columns:
        target_column = "yield_bu_acre"
    
    config = {}
    
    # Constant features
    with st.expander("Constant & Zero-Variance Features", expanded=True):
        config["constants"] = render_constant_features_config(df)
    
    # Missing values
    with st.expander("Missing Values", expanded=False):
        config["missing"] = render_missing_value_strategy(df)
    
    # Scaling
    with st.expander("Feature Scaling", expanded=True):
        config["scaling"] = render_scaling_config(df, target_column)
    
    # Encoding
    with st.expander("Categorical Encoding", expanded=True):
        config["encoding"] = render_encoding_config(df)
    
    # Outliers
    with st.expander("Outlier Handling", expanded=False):
        config["outliers"] = render_outlier_config(df, target_column)
    
    # Summary
    st.markdown("---")
    st.subheader("Pipeline Summary")
    
    summary = []
    if config.get("constants", {}).get("drop_constants"):
        summary.append(f"Drop constant features: {', '.join(config['constants']['columns'])}")
    if config.get("missing"):
        summary.append(f"Missing values: {config['missing'].get('strategy', 'None')}")
    if config.get("scaling"):
        summary.append(f"Scaling: {config['scaling'].get('method', 'None')} on {len(config['scaling'].get('columns', []))} feature columns")
    if config.get("encoding"):
        summary.append(f"Encoding: {config['encoding'].get('method', 'None')} on {len(config['encoding'].get('columns', []))} categorical columns")
    if config.get("outliers"):
        summary.append(f"Outliers: {config['outliers'].get('handling_strategy', 'ignore')} ({config['outliers'].get('detection_method', 'iqr')})")
    
    for item in summary:
        st.write(f"• {item}")
    
    # Apply button
    st.markdown("---")
    if st.button("Apply Preprocessing Pipeline", type="primary"):
        with st.spinner("Executing transformations..."):
            df_preprocessed = apply_preprocessing_pipeline(df, config)
        
        st.session_state["preprocessed_df"] = df_preprocessed
        st.session_state["preprocessing_config"] = config
        
        # Save to preprocessed file
        from pathlib import Path
        save_dir = Path("data")
        save_dir.mkdir(exist_ok=True)
        preprocessed_path = save_dir / "cerespinn_training_preprocessed.csv"
        df_preprocessed.to_csv(preprocessed_path, index=False)
        
        if spec:
            spec.dataset_path = str(preprocessed_path)
            if hasattr(st.session_state, "artifact_manager"):
                st.session_state.artifact_manager.save_project_specification(spec)
        
        st.success(f"✅ Preprocessing pipeline applied successfully! Cleaned dataset saved to `{preprocessed_path}`.")
        
        # Display Before vs After
        st.markdown("### Preprocessing Results")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Original Shape", f"{df.shape[0]} × {df.shape[1]}")
        with c2:
            st.metric("Cleaned Shape", f"{df_preprocessed.shape[0]} × {df_preprocessed.shape[1]}")
        with c3:
            st.metric("Features Encoded", len(config.get("encoding", {}).get("columns", [])))
        with c4:
            st.metric("Features Scaled", len(config.get("scaling", {}).get("columns", [])))
        
        st.dataframe(df_preprocessed.head(10), use_container_width=True)
        st.info("💡 The preprocessed dataset is now linked and ready for **Model Training**.")
        return config
    
    return config
