"""Dataset UI components for ML Lab.

This module provides UI components for dataset upload, analysis,
and visualization.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_dataset_upload(spec: Optional[Any] = None) -> Optional[Path]:
    """Render dataset upload interface.
    
    Args:
        spec: Optional ProjectSpecification to associate with dataset
    
    Returns:
        Path to uploaded dataset or None
    """
    st.subheader("Upload Dataset")
    
    st.markdown("""
    Upload your dataset for analysis. Supported formats: CSV, Parquet, Excel, JSON.
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "parquet", "xlsx", "xls", "json"],
        help="Supported formats: CSV, Parquet, Excel, JSON",
    )
    
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # Save to temporary location
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "ml_lab_uploads"
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.info(f"Dataset saved to: {file_path}")
        
        # Update spec if provided
        if spec:
            spec.dataset_path = file_path
        
        return file_path
    
    # Alternative: provide path
    st.markdown("---")
    st.markdown("### Or Provide Dataset Path")
    
    dataset_path_str = st.text_input(
        "Dataset Path",
        placeholder="/path/to/dataset.csv",
    )
    
    if st.button("Load from Path"):
        if dataset_path_str:
            dataset_path = Path(dataset_path_str)
            if dataset_path.exists():
                st.success(f"Dataset found: {dataset_path}")
                
                if spec:
                    spec.dataset_path = dataset_path
                
                return dataset_path
            else:
                st.error(f"Dataset not found: {dataset_path_str}")
    
    return None


def render_dataset_preview(df: pd.DataFrame, max_rows: int = 10) -> None:
    """Render dataset preview.
    
    Args:
        df: DataFrame to preview
        max_rows: Maximum number of rows to display
    """
    st.subheader("Dataset Preview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Memory (MB)", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f}")
    
    st.dataframe(df.head(max_rows), use_container_width=True)
    
    # Column information
    st.markdown("---")
    st.subheader("Column Information")
    
    col_info = []
    for col in df.columns:
        col_info.append({
            "Column": col,
            "Type": str(df[col].dtype),
            "Non-Null": df[col].count(),
            "Null": df[col].isna().sum(),
            "Unique": df[col].nunique(),
        })
    
    col_df = pd.DataFrame(col_info)
    st.dataframe(col_df, use_container_width=True)


def render_dataset_analysis(profile: Any) -> None:
    """Render dataset analysis results.
    
    Args:
        profile: DatasetProfile from DatasetAnalyzer
    """
    st.subheader("Dataset Analysis Results")
    
    # Overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", profile.rows)
    with col2:
        st.metric("Columns", profile.columns)
    with col3:
        st.metric("Memory (MB)", f"{profile.memory_mb:.2f}")
    with col4:
        st.metric("Missing %", f"{profile.total_missing_percentage:.2f}")
    
    st.markdown("---")
    
    # Data Quality
    st.subheader("Data Quality")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Has Missing Values:**", profile.has_missing_values)
        st.write("**Total Missing:**", profile.total_missing_count)
    with col2:
        st.write("**Has Duplicates:**", profile.has_duplicates)
        st.write("**Duplicate Count:**", profile.duplicate_count)
    with col3:
        st.write("**Has Outliers:**", profile.has_outliers)
        st.write("**Outlier Columns:**", len(profile.outlier_columns))
    
    # Feature types
    st.markdown("---")
    st.subheader("Feature Types")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Numerical", len(profile.numerical_features))
    with col2:
        st.metric("Categorical", len(profile.categorical_features))
    with col3:
        st.metric("Temporal", len(profile.temporal_features))
    with col4:
        st.metric("Boolean", len(profile.boolean_features))
    
    # Column profiles
    st.markdown("---")
    st.subheader("Column Profiles")
    
    for col_profile in profile.column_profiles:
        with st.expander(f"{col_profile.name} ({col_profile.dtype})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Data Type:** {col_profile.data_type.value}")
                st.write(f"**Unique Values:** {col_profile.unique_count}")
                st.write(f"**Missing:** {col_profile.missing_count} ({col_profile.missing_percentage:.2f}%)")
            
            with col2:
                st.write(f"**Cardinality:** {col_profile.cardinality}")
                st.write(f"**Is Constant:** {col_profile.is_constant}")
                st.write(f"**Is Identifier:** {col_profile.is_identifier}")
            
            if col_profile.data_type.value == "numerical":
                st.write(f"**Min:** {col_profile.min_value}")
                st.write(f"**Max:** {col_profile.max_value}")
                st.write(f"**Mean:** {col_profile.mean_value}")
                st.write(f"**Std:** {col_profile.std_value}")
                st.write(f"**Outliers:** {col_profile.outlier_count} ({col_profile.outlier_percentage:.2f}%)")
            
            if col_profile.data_type.value == "categorical":
                if col_profile.categories:
                    st.write("**Categories:**", ", ".join(col_profile.categories[:10]))
                    if len(col_profile.categories) > 10:
                        st.write(f"... and {len(col_profile.categories) - 10} more")
    
    # Correlations
    if profile.correlations:
        st.markdown("---")
        st.subheader("Correlations")
        
        corr_df = pd.DataFrame([
            {
                "Column 1": c.column1,
                "Column 2": c.column2,
                "Correlation": c.correlation,
            }
            for c in profile.correlations
        ])
        
        st.dataframe(corr_df, use_container_width=True)
        
        # High correlations
        if profile.high_correlation_pairs:
            st.warning(f"Found {len(profile.high_correlation_pairs)} highly correlated feature pairs (|r| > 0.8):")
            for col1, col2, corr in profile.high_correlation_pairs:
                st.write(f"• {col1} ↔ {col2}: {corr:.3f}")
    
    # Target information
    if profile.target_column:
        st.markdown("---")
        st.subheader("Target Information")
        
        st.write(f"**Target Column:** {profile.target_column}")
        st.write(f"**Target Type:** {profile.target_type.value}")
        
        if profile.target_type.value == "categorical":
            st.write(f"**Classes:** {', '.join(profile.target_classes)}")
            st.write(f"**Is Imbalanced:** {profile.is_imbalanced}")
            if profile.is_imbalanced:
                st.write(f"**Imbalance Ratio:** {profile.imbalance_ratio:.3f}")
            
            # Plot class distribution
            if profile.target_distribution:
                dist_df = pd.DataFrame([
                    {"Class": k, "Count": v}
                    for k, v in profile.target_distribution.items()
                ])
                fig = px.bar(
                    dist_df,
                    x="Class",
                    y="Count",
                    title="Target Class Distribution",
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.markdown("---")
    st.subheader("Recommendations")
    
    if profile.recommended_preprocessing:
        st.markdown("**Preprocessing:**")
        for rec in profile.recommended_preprocessing:
            st.write(f"• {rec}")
    
    if profile.recommended_validation:
        st.markdown("**Validation Strategy:**")
        st.write(f"• {profile.recommended_validation}")
    
    if profile.recommended_models:
        st.markdown("**Recommended Models:**")
        for model in profile.recommended_models:
            st.write(f"• {model}")
    
    if profile.recommended_metrics:
        st.markdown("**Recommended Metrics:**")
        for metric in profile.recommended_metrics:
            st.write(f"• {metric}")
    
    # Issues and warnings
    if profile.issues:
        st.markdown("---")
        st.error("Issues:")
        for issue in profile.issues:
            st.write(f"• {issue}")
    
    if profile.warnings:
        st.markdown("---")
        st.warning("Warnings:")
        for warning in profile.warnings:
            st.write(f"• {warning}")


def render_dataset_statistics(df: pd.DataFrame) -> None:
    """Render statistical summary of dataset.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("Statistical Summary")
    
    # Numerical columns
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if numerical_cols:
        st.markdown("### Numerical Columns")
        st.dataframe(df[numerical_cols].describe(), use_container_width=True)
    
    # Categorical columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if categorical_cols:
        st.markdown("### Categorical Columns")
        for col in categorical_cols:
            with st.expander(col):
                value_counts = df[col].value_counts()
                st.dataframe(value_counts.head(20), use_container_width=True)
                if len(value_counts) > 20:
                    st.caption(f"Showing top 20 of {len(value_counts)} unique values")


def render_missing_values_analysis(df: pd.DataFrame) -> None:
    """Render missing values analysis.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("Missing Values Analysis")
    
    missing = df.isna().sum()
    missing_pct = (missing / len(df)) * 100
    
    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing.values,
        "Missing %": missing_pct.values,
    }).sort_values("Missing Count", ascending=False)
    
    missing_df = missing_df[missing_df["Missing Count"] > 0]
    
    if len(missing_df) > 0:
        st.dataframe(missing_df, use_container_width=True)
        
        # Plot missing values
        fig = px.bar(
            missing_df.head(20),
            x="Column",
            y="Missing %",
            title="Missing Values by Column (%)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No missing values found!")


def render_correlation_heatmap(df: pd.DataFrame) -> None:
    """Render correlation heatmap for numerical columns.
    
    Args:
        df: DataFrame to analyze
    """
    import numpy as np
    
    st.subheader("Correlation Heatmap")
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numerical_cols) > 1:
        corr_matrix = df[numerical_cols].corr()
        
        fig = px.imshow(
            corr_matrix,
            labels=dict(x="Feature", y="Feature", color="Correlation"),
            x=numerical_cols,
            y=numerical_cols,
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
            title="Feature Correlation Heatmap",
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need at least 2 numerical columns for correlation analysis")


def render_distribution_plots(df: pd.DataFrame) -> None:
    """Render distribution plots for numerical columns.
    
    Args:
        df: DataFrame to analyze
    """
    import numpy as np
    
    st.subheader("Feature Distributions")
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if numerical_cols:
        # Select columns to plot
        selected_cols = st.multiselect(
            "Select columns to plot",
            options=numerical_cols,
            default=numerical_cols[:5],
        )
        
        if selected_cols:
            for col in selected_cols:
                fig = px.histogram(
                    df[col],
                    nbins=30,
                    title=f"Distribution of {col}",
                    labels={"value": col, "count": "Frequency"},
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No numerical columns found")


def render_dataset_analyzer_ui(dataset_analyzer: Any, spec: Optional[Any] = None) -> Optional[Any]:
    """Render complete dataset analyzer UI.
    
    Args:
        dataset_analyzer: DatasetAnalyzer instance
        spec: Optional ProjectSpecification
    
    Returns:
        DatasetProfile if analyzed, None otherwise
    """
    # Upload or load dataset
    dataset_path = render_dataset_upload(spec)
    
    if dataset_path is None:
        return None
    
    # Load dataset
    try:
        df = dataset_analyzer._load_tabular(dataset_path)
        st.success(f"Dataset loaded successfully: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        return None
    
    # Show preview
    render_dataset_preview(df)
    
    # Show statistics
    render_dataset_statistics(df)
    
    # Analyze button
    st.markdown("---")
    if st.button("Run Full Analysis", type="primary"):
        with st.spinner("Analyzing dataset..."):
            target_column = spec.target_variable if spec else None
            profile = dataset_analyzer.analyze(dataset_path, target_column)
        
        render_dataset_analysis(profile)
        
        # Update spec if provided
        if spec:
            from core.project_analyzer import ProjectAnalyzer
            project_analyzer = ProjectAnalyzer()
            spec = project_analyzer.refine_from_dataset(spec, profile)
        
        return profile
    
    # Quick analyses
    st.markdown("---")
    st.subheader("Quick Analyses")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Missing Values"):
            render_missing_values_analysis(df)
    with col2:
        if st.button("Correlations"):
            render_correlation_heatmap(df)
    with col3:
        if st.button("Distributions"):
            render_distribution_plots(df)
    with col4:
        if st.button("Full Analysis"):
            with st.spinner("Analyzing dataset..."):
                target_column = spec.target_variable if spec else None
                profile = dataset_analyzer.analyze(dataset_path, target_column)
            render_dataset_analysis(profile)
            return profile
    
    return None
