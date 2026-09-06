"""EDA (Exploratory Data Analysis) UI components for ML Lab.

This module provides UI components for visualizing and exploring datasets.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_eda_overview(df: pd.DataFrame) -> None:
    """Render EDA overview section.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("EDA Overview")
    
    # Basic statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Numerical Columns", len(df.select_dtypes(include=[np.number]).columns))
    with col4:
        st.metric("Categorical Columns", len(df.select_dtypes(include=['object', 'category']).columns))
    
    # Data types
    st.markdown("### Data Types")
    dtype_counts = df.dtypes.value_counts()
    fig = px.pie(
        values=dtype_counts.values,
        names=dtype_counts.index,
        title="Data Type Distribution",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_univariate_analysis(df: pd.DataFrame) -> None:
    """Render univariate analysis for all columns.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("Univariate Analysis")
    
    # Column selector
    column = st.selectbox("Select column to analyze", df.columns)
    
    col_data = df[column]
    
    # Statistics
    st.markdown("### Statistics")
    
    if pd.api.types.is_numeric_dtype(col_data):
        stats_df = pd.DataFrame({
            "Statistic": ["Count", "Mean", "Std", "Min", "25%", "50%", "75%", "Max"],
            "Value": [
                col_data.count(),
                col_data.mean(),
                col_data.std(),
                col_data.min(),
                col_data.quantile(0.25),
                col_data.median(),
                col_data.quantile(0.75),
                col_data.max(),
            ]
        })
        st.dataframe(stats_df, use_container_width=True)
        
        # Distribution plot
        st.markdown("### Distribution")
        fig = px.histogram(
            col_data,
            nbins=30,
            title=f"Distribution of {column}",
            labels={"value": column, "count": "Frequency"},
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Box plot
        fig = px.box(
            y=col_data,
            title=f"Box Plot of {column}",
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # Categorical analysis
        value_counts = col_data.value_counts()
        
        stats_df = pd.DataFrame({
            "Statistic": ["Unique Values", "Most Frequent", "Count"],
            "Value": [
                col_data.nunique(),
                value_counts.index[0] if len(value_counts) > 0 else "N/A",
                value_counts.iloc[0] if len(value_counts) > 0 else 0,
            ]
        })
        st.dataframe(stats_df, use_container_width=True)
        
        # Bar plot
        if len(value_counts) <= 20:
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Distribution of {column}",
                labels={"x": column, "y": "Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Too many unique values ({len(value_counts)}) to display. Showing top 20.")
            fig = px.bar(
                x=value_counts.index[:20],
                y=value_counts.values[:20],
                title=f"Top 20 Values of {column}",
                labels={"x": column, "y": "Count"},
            )
            st.plotly_chart(fig, use_container_width=True)


def render_bivariate_analysis(df: pd.DataFrame) -> None:
    """Render bivariate analysis between two columns.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("Bivariate Analysis")
    
    # Column selectors
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Select X variable", df.columns, key="bivariate_x")
    with col2:
        y_col = st.selectbox("Select Y variable", df.columns, key="bivariate_y")
    
    if x_col == y_col:
        st.warning("Please select different columns for X and Y")
        return
    
    x_data = df[x_col]
    y_data = df[y_col]
    
    # Correlation (if both numeric)
    if pd.api.types.is_numeric_dtype(x_data) and pd.api.types.is_numeric_dtype(y_data):
        correlation = x_data.corr(y_data)
        st.metric("Correlation", f"{correlation:.3f}")
        
        # Scatter plot
        fig = px.scatter(
            x=x_data,
            y=y_data,
            title=f"{x_col} vs {y_col}",
            labels={"x": x_col, "y": y_col},
            opacity=0.6,
        )
        st.plotly_chart(fig, use_container_width=True)
        
    # Box plot by category
    elif pd.api.types.is_numeric_dtype(x_data) and pd.api.types.is_categorical_dtype(y_data):
        fig = px.box(
            x=y_data,
            y=x_data,
            title=f"{x_col} by {y_col}",
            labels={"x": y_col, "y": x_col},
        )
        st.plotly_chart(fig, use_container_width=True)
        
    elif pd.api.types.is_categorical_dtype(x_data) and pd.api.types.is_numeric_dtype(y_data):
        fig = px.box(
            x=x_data,
            y=y_data,
            title=f"{y_col} by {x_col}",
            labels={"x": x_col, "y": y_col},
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # Categorical vs categorical
        crosstab = pd.crosstab(x_data, y_data)
        st.dataframe(crosstab, use_container_width=True)
        
        fig = px.imshow(
            crosstab,
            title=f"{x_col} vs {y_col} Heatmap",
            labels=dict(x=x_col, y=y_col, color="Count"),
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_correlation_matrix(df: pd.DataFrame) -> None:
    """Render correlation matrix for numerical columns.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("Correlation Matrix")
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numerical_cols) < 2:
        st.info("Need at least 2 numerical columns for correlation analysis")
        return
    
    # Select columns
    selected_cols = st.multiselect(
        "Select columns for correlation",
        options=numerical_cols,
        default=numerical_cols[:10],
    )
    
    if not selected_cols:
        return
    
    corr_matrix = df[selected_cols].corr()
    
    # Heatmap
    fig = px.imshow(
        corr_matrix,
        labels=dict(x="Feature", y="Feature", color="Correlation"),
        x=selected_cols,
        y=selected_cols,
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        title="Correlation Matrix",
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # High correlations
    high_corr = []
    for i in range(len(selected_cols)):
        for j in range(i + 1, len(selected_cols)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > 0.7:
                high_corr.append({
                    "Feature 1": selected_cols[i],
                    "Feature 2": selected_cols[j],
                    "Correlation": corr_val,
                })
    
    if high_corr:
        st.warning("High correlations found (|r| > 0.7):")
        st.dataframe(pd.DataFrame(high_corr), use_container_width=True)


def render_missing_values_heatmap(df: pd.DataFrame) -> None:
    """Render missing values heatmap.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("Missing Values Heatmap")
    
    missing = df.isna()
    
    if not missing.any().any():
        st.success("No missing values found!")
        return
    
    # Create heatmap
    fig = px.imshow(
        missing,
        title="Missing Values Heatmap",
        labels=dict(x="Column", y="Row", color="Missing"),
        color_continuous_scale="Reds",
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Missing by column
    missing_by_col = missing.sum()
    missing_pct = (missing_by_col / len(df)) * 100
    
    missing_df = pd.DataFrame({
        "Column": missing_by_col.index,
        "Missing Count": missing_by_col.values,
        "Missing %": missing_pct.values,
    }).sort_values("Missing Count", ascending=False)
    
    missing_df = missing_df[missing_df["Missing Count"] > 0]
    
    if len(missing_df) > 0:
        st.dataframe(missing_df, use_container_width=True)


def render_outlier_detection(df: pd.DataFrame) -> None:
    """Render outlier detection using IQR method.
    
    Args:
        df: DataFrame to analyze
    """
    st.subheader("Outlier Detection")
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numerical_cols:
        st.info("No numerical columns found")
        return
    
    # Select column
    column = st.selectbox("Select column for outlier detection", numerical_cols)
    
    col_data = df[column].dropna()
    
    # IQR method
    Q1 = col_data.quantile(0.25)
    Q3 = col_data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Values", len(col_data))
    with col2:
        st.metric("Outliers", len(outliers))
    with col3:
        st.metric("Outlier %", f"{len(outliers) / len(col_data) * 100:.2f}%")
    
    # Box plot with outliers highlighted
    fig = px.box(
        y=col_data,
        title=f"Box Plot of {column} (Outliers in Red)",
    )
    
    # Add outlier markers
    outlier_indices = col_data[(col_data < lower_bound) | (col_data > upper_bound)].index
    fig.add_trace(go.Scatter(
        x=[0] * len(outlier_indices),
        y=col_data[outlier_indices],
        mode='markers',
        marker=dict(color='red', size=8),
        name='Outliers',
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Outlier values
    if len(outliers) > 0:
        st.markdown("### Outlier Values")
        st.dataframe(outliers.to_frame(), use_container_width=True)


def render_target_analysis(df: pd.DataFrame, target_column: str) -> None:
    """Render target variable analysis.
    
    Args:
        df: DataFrame to analyze
        target_column: Name of target column
    """
    st.subheader(f"Target Analysis: {target_column}")
    
    if target_column not in df.columns:
        st.error(f"Target column '{target_column}' not found in dataset")
        return
    
    target_data = df[target_column]
    
    # Basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Missing Values", target_data.isna().sum())
    with col2:
        st.metric("Unique Values", target_data.nunique())
    with col3:
        st.metric("Data Type", str(target_data.dtype))
    
    # Analysis based on type
    if pd.api.types.is_numeric_dtype(target_data):
        st.markdown("### Numerical Target")
        
        stats_df = pd.DataFrame({
            "Statistic": ["Mean", "Std", "Min", "25%", "Median", "75%", "Max"],
            "Value": [
                target_data.mean(),
                target_data.std(),
                target_data.min(),
                target_data.quantile(0.25),
                target_data.median(),
                target_data.quantile(0.75),
                target_data.max(),
            ]
        })
        st.dataframe(stats_df, use_container_width=True)
        
        # Distribution
        fig = px.histogram(
            target_data,
            nbins=30,
            title=f"Target Distribution: {target_column}",
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.markdown("### Categorical Target")
        
        value_counts = target_data.value_counts()
        
        # Distribution
        fig = px.bar(
            x=value_counts.index,
            y=value_counts.values,
            title=f"Target Distribution: {target_column}",
            labels={"x": target_column, "y": "Count"},
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Class imbalance check
        if len(value_counts) > 1:
            max_count = value_counts.max()
            min_count = value_counts.min()
            imbalance_ratio = min_count / max_count
            
            st.metric("Imbalance Ratio", f"{imbalance_ratio:.3f}")
            
            if imbalance_ratio < 0.5:
                st.warning("Target is imbalanced. Consider using stratified sampling or class weights.")
            else:
                st.success("Target is reasonably balanced.")


def render_feature_target_correlation(df: pd.DataFrame, target_column: str) -> None:
    """Render correlation between features and target.
    
    Args:
        df: DataFrame to analyze
        target_column: Name of target column
    """
    st.subheader("Feature-Target Correlation")
    
    if target_column not in df.columns:
        st.error(f"Target column '{target_column}' not found in dataset")
        return
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if target_column not in numerical_cols:
        st.info("Target column is not numerical. Cannot compute correlation.")
        return
    
    feature_cols = [col for col in numerical_cols if col != target_column]
    
    if not feature_cols:
        st.info("No numerical features found")
        return
    
    # Compute correlations
    correlations = df[feature_cols + [target_column]].corr()[target_column].drop(target_column)
    
    # Sort by absolute correlation
    correlations_sorted = correlations.abs().sort_values(ascending=False)
    
    # Plot
    fig = px.bar(
        x=correlations_sorted.index,
        y=correlations_sorted.values,
        title=f"Feature Correlation with {target_column}",
        labels={"x": "Feature", "y": "Absolute Correlation"},
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Table
    corr_df = pd.DataFrame({
        "Feature": correlations.index,
        "Correlation": correlations.values,
    }).sort_values("Correlation", key=abs, ascending=False)
    
    st.dataframe(corr_df, use_container_width=True)


def render_eda_report(df: pd.DataFrame, target_column: Optional[str] = None) -> None:
    """Render complete EDA report.
    
    Args:
        df: DataFrame to analyze
        target_column: Optional target column
    """
    st.title("📊 Exploratory Data Analysis Report")
    st.markdown("---")
    
    # Overview
    render_eda_overview(df)
    st.markdown("---")
    
    # Target analysis
    if target_column:
        render_target_analysis(df, target_column)
        st.markdown("---")
        render_feature_target_correlation(df, target_column)
        st.markdown("---")
    
    # Univariate analysis
    render_univariate_analysis(df)
    st.markdown("---")
    
    # Bivariate analysis
    render_bivariate_analysis(df)
    st.markdown("---")
    
    # Correlation matrix
    render_correlation_matrix(df)
    st.markdown("---")
    
    # Missing values
    render_missing_values_heatmap(df)
    st.markdown("---")
    
    # Outliers
    render_outlier_detection(df)
