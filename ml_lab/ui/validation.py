"""Validation UI components for ML Lab.

This module provides Streamlit UI components for displaying validation
results, statistical tests, and model comparisons.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def display_validation_result(result: Any) -> None:
    """Display validation results in Streamlit.
    
    Args:
        result: ValidationResult from ValidationEngine
    """
    if result is None:
        st.warning("No validation results available")
        return
    
    st.subheader(f"Validation Results: {result.model_name}")
    
    # Display metadata
    with st.expander("Validation Metadata"):
        st.json(result.metadata)
    
    # Display metrics
    st.subheader("Cross-Validation Metrics")
    
    if result.metrics:
        # Create metrics summary table
        metrics_data = []
        for metric_name, metric_values in result.metrics.items():
            metrics_data.append({
                "Metric": metric_name,
                "Mean": metric_values.get("mean", 0),
                "Std": metric_values.get("std", 0),
                "Min": metric_values.get("min", 0),
                "Max": metric_values.get("max", 0),
            })
        
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True)
        
        # Plot metrics
        if len(metrics_df) > 0:
            fig = px.bar(
                metrics_df,
                x="Metric",
                y="Mean",
                error_y="Std",
                title="Cross-Validation Metrics with Standard Deviation",
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Display fold metrics
    if result.fold_metrics:
        st.subheader("Fold-wise Metrics")
        
        fold_df = pd.DataFrame(result.fold_metrics)
        st.dataframe(fold_df, use_container_width=True)
        
        # Plot fold comparison
        if len(fold_df) > 1:
            fig = go.Figure()
            for col in fold_df.columns:
                fig.add_trace(go.Box(y=fold_df[col], name=col))
            fig.update_layout(
                title="Fold-wise Metric Distribution",
                yaxis_title="Metric Value",
                xaxis_title="Metric",
            )
            st.plotly_chart(fig, use_container_width=True)


def display_model_comparison(comparison: Dict[str, Any]) -> None:
    """Display model comparison results.
    
    Args:
        comparison: Comparison results from ValidationEngine
    """
    st.subheader("Model Comparison")
    
    if not comparison.get("models"):
        st.warning("No models to compare")
        return
    
    # Display ranking
    st.subheader("Model Ranking")
    ranking_df = pd.DataFrame(comparison["models"])
    st.dataframe(ranking_df, use_container_width=True)
    
    # Highlight best model
    if comparison.get("best_model"):
        st.success(f"Best Model: **{comparison['best_model']}**")
    
    # Plot comparison
    if len(ranking_df) > 1:
        primary_metric = ranking_df.columns[1]  # Assume second column is primary metric
        fig = px.bar(
            ranking_df,
            x="name",
            y=primary_metric,
            title=f"Model Comparison by {primary_metric}",
            labels={"name": "Model", primary_metric: primary_metric},
        )
        st.plotly_chart(fig, use_container_width=True)


def display_statistical_test_results(results: Dict[str, Dict[str, Any]]) -> None:
    """Display statistical test results.
    
    Args:
        results: Dictionary of test results from StatisticalEngine
    """
    st.subheader("Statistical Test Results")
    
    if not results:
        st.warning("No statistical test results available")
        return
    
    # Display each test result
    for test_name, test_result in results.items():
        if test_result is None:
            continue
        
        if "error" in test_result:
            st.error(f"{test_name}: {test_result['error']}")
            continue
        
        with st.expander(f"{test_name}"):
            st.json(test_result)
            
            # Highlight significance
            if test_result.get("significant") or test_result.get("reject_null"):
                st.success("✓ Result is statistically significant")
            else:
                st.info("Result is not statistically significant")
            
            # Display p-value if available
            if "p_value" in test_result:
                p_value = test_result["p_value"]
                st.metric("p-value", f"{p_value:.5f}")


def display_statistical_test_summary(results: Dict[str, Dict[str, Any]]) -> None:
    """Display a summary table of statistical test results.
    
    Args:
        results: Dictionary of test results from StatisticalEngine
    """
    st.subheader("Statistical Test Summary")
    
    if not results:
        st.warning("No statistical test results available")
        return
    
    # Create summary table
    summary_data = []
    for test_name, test_result in results.items():
        if test_result is None or "error" in test_result:
            continue
        
        summary_data.append({
            "Test": test_name,
            "Statistic": test_result.get("statistic", "N/A"),
            "p-value": test_result.get("p_value", "N/A"),
            "Significant": test_result.get("significant") or test_result.get("reject_null", False),
        })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
    else:
        st.warning("No valid test results to display")


def display_training_history(history: Dict[str, List[float]]) -> None:
    """Display training history (loss curves, etc.).
    
    Args:
        history: Dictionary with training history
    """
    st.subheader("Training History")
    
    if not history:
        st.warning("No training history available")
        return
    
    # Create line plots for each metric
    for metric_name, values in history.items():
        fig = px.line(
            x=list(range(len(values))),
            y=values,
            title=f"{metric_name} over Epochs",
            labels={"x": "Epoch", "y": metric_name},
        )
        st.plotly_chart(fig, use_container_width=True)


def display_feature_importance(importance: Dict[str, float]) -> None:
    """Display feature importance.
    
    Args:
        importance: Dictionary mapping feature names to importance values
    """
    st.subheader("Feature Importance")
    
    if not importance:
        st.warning("No feature importance data available")
        return
    
    # Create DataFrame and sort
    importance_df = pd.DataFrame([
        {"Feature": k, "Importance": v} for k, v in importance.items()
    ]).sort_values("Importance", ascending=False)
    
    # Display table
    st.dataframe(importance_df, use_container_width=True)
    
    # Plot bar chart
    fig = px.bar(
        importance_df.head(20),  # Top 20 features
        x="Importance",
        y="Feature",
        orientation="h",
        title="Top 20 Feature Importance",
    )
    st.plotly_chart(fig, use_container_width=True)


def display_confusion_matrix(y_true, y_pred, class_names: Optional[List[str]] = None) -> None:
    """Display confusion matrix.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        class_names: Optional class names
    """
    from sklearn.metrics import confusion_matrix
    
    st.subheader("Confusion Matrix")
    
    cm = confusion_matrix(y_true, y_pred)
    
    if class_names is None:
        class_names = [f"Class {i}" for i in range(len(cm))]
    
    # Create heatmap
    fig = px.imshow(
        cm,
        labels=dict(x="Predicted", y="Actual", color="Count"),
        x=class_names,
        y=class_names,
        color_continuous_scale="Blues",
        title="Confusion Matrix",
    )
    
    # Add text annotations
    for i in range(len(cm)):
        for j in range(len(cm)):
            fig.add_annotation(
                x=j,
                y=i,
                text=str(cm[i, j]),
                showarrow=False,
                font=dict(color="white" if cm[i, j] > cm.max() / 2 else "black"),
            )
    
    st.plotly_chart(fig, use_container_width=True)


def display_roc_curve(y_true, y_proba) -> None:
    """Display ROC curve.
    
    Args:
        y_true: True labels
        y_proba: Predicted probabilities
    """
    from sklearn.metrics import roc_auc_score, roc_curve
    
    st.subheader("ROC Curve")
    
    try:
        fpr, tpr, _ = roc_curve(y_true, y_proba)
        auc = roc_auc_score(y_true, y_proba)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fpr,
            y=tpr,
            mode='lines',
            name=f'ROC Curve (AUC = {auc:.4f})',
        ))
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            name='Random Classifier',
            line=dict(dash='dash'),
        ))
        fig.update_layout(
            title="Receiver Operating Characteristic (ROC) Curve",
            xaxis_title="False Positive Rate",
            yaxis_title="True Positive Rate",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.metric("AUC", f"{auc:.4f}")
    except Exception as e:
        st.error(f"Could not display ROC curve: {e}")
