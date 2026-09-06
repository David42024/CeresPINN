"""Model comparison UI components for ML Lab.

This module provides UI components for comparing multiple models
and their performance metrics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_model_comparison_table(results: Dict[str, Any]) -> None:
    """Render model comparison table.
    
    Args:
        results: Dictionary mapping model names to validation results
    """
    st.subheader("Model Comparison Table")
    
    if not results:
        st.info("No model results available for comparison")
        return
    
    # Build comparison data
    comparison_data = []
    for model_name, result in results.items():
        if result and hasattr(result, 'metrics'):
            for metric_name, metric_values in result.metrics.items():
                comparison_data.append({
                    "Model": model_name,
                    "Metric": metric_name,
                    "Mean": metric_values.get("mean", 0),
                    "Std": metric_values.get("std", 0),
                    "Min": metric_values.get("min", 0),
                    "Max": metric_values.get("max", 0),
                })
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)


def render_metric_comparison_plot(results: Dict[str, Any], primary_metric: str = "f1") -> None:
    """Render metric comparison plot.
    
    Args:
        results: Dictionary mapping model names to validation results
        primary_metric: Primary metric to compare
    """
    st.subheader(f"Metric Comparison: {primary_metric}")
    
    if not results:
        st.info("No model results available")
        return
    
    # Extract metric values
    metric_data = []
    for model_name, result in results.items():
        if result and hasattr(result, 'metrics'):
            metric_values = result.metrics.get(primary_metric)
            if metric_values:
                metric_data.append({
                    "Model": model_name,
                    "Value": metric_values.get("mean", 0),
                    "Std": metric_values.get("std", 0),
                })
    
    if metric_data:
        df = pd.DataFrame(metric_data)
        
        # Bar plot with error bars
        fig = px.bar(
            df,
            x="Model",
            y="Value",
            error_y="Std",
            title=f"Model Comparison by {primary_metric}",
            labels={"Value": primary_metric, "Std": "Standard Deviation"},
        )
        st.plotly_chart(fig, use_container_width=True)


def render_radar_comparison(results: Dict[str, Any], metrics: List[str]) -> None:
    """Render radar chart for multi-metric comparison.
    
    Args:
        results: Dictionary mapping model names to validation results
        metrics: List of metrics to compare
    """
    st.subheader("Multi-Metric Radar Comparison")
    
    if not results or not metrics:
        st.info("No results or metrics available")
        return
    
    # Build radar data
    radar_data = []
    for model_name, result in results.items():
        if result and hasattr(result, 'metrics'):
            metric_values = []
            for metric in metrics:
                metric_data = result.metrics.get(metric)
                if metric_data:
                    metric_values.append(metric_data.get("mean", 0))
                else:
                    metric_values.append(0)
            
            radar_data.append({
                "Model": model_name,
                **{metric: val for metric, val in zip(metrics, metric_values)},
            })
    
    if radar_data:
        df = pd.DataFrame(radar_data)
        
        fig = go.Figure()
        
        for model_name in df["Model"].unique():
            model_data = df[df["Model"] == model_name]
            fig.add_trace(go.Scatterpolar(
                r=model_data[metrics].values[0],
                theta=metrics,
                fill='toself',
                name=model_name,
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
            title="Multi-Metric Comparison",
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_ranking_comparison(results: Dict[str, Any], primary_metric: str = "f1") -> None:
    """Render model ranking comparison.
    
    Args:
        results: Dictionary mapping model names to validation results
        primary_metric: Primary metric for ranking
    """
    st.subheader("Model Ranking")
    
    if not results:
        st.info("No model results available")
        return
    
    # Build ranking data
    ranking_data = []
    for model_name, result in results.items():
        if result and hasattr(result, 'metrics'):
            metric_values = result.metrics.get(primary_metric)
            if metric_values:
                ranking_data.append({
                    "Model": model_name,
                    primary_metric: metric_values.get("mean", 0),
                    "Std": metric_values.get("std", 0),
                })
    
    if ranking_data:
        df = pd.DataFrame(ranking_data)
        df = df.sort_values(primary_metric, ascending=False)
        df["Rank"] = range(1, len(df) + 1)
        
        st.dataframe(df, use_container_width=True)
        
        # Highlight best model
        if len(df) > 0:
            best_model = df.iloc[0]
            st.success(f"🏆 Best Model: {best_model['Model']} ({primary_metric}: {best_model[primary_metric]:.4f})")


def render_statistical_comparison(results: Dict[str, Any]) -> None:
    """Render statistical comparison between models.
    
    Args:
        results: Dictionary mapping model names to validation results
    """
    st.subheader("Statistical Comparison")
    
    if not results or len(results) < 2:
        st.info("Need at least 2 models for statistical comparison")
        return
    
    # Select models to compare
    model_names = list(results.keys())
    model1 = st.selectbox("Select Model 1", options=model_names, key="compare_model1")
    model2 = st.selectbox("Select Model 2", options=model_names, key="compare_model2")
    
    if model1 == model2:
        st.warning("Please select different models")
        return
    
    # Get fold metrics for comparison
    result1 = results.get(model1)
    result2 = results.get(model2)
    
    if not result1 or not result2 or not hasattr(result1, 'fold_metrics') or not hasattr(result2, 'fold_metrics'):
        st.info("Fold metrics not available for statistical comparison")
        return
    
    # Perform paired t-test on primary metric
    from scipy import stats
    
    primary_metric = result1.metrics.keys()
    if primary_metric:
        metric_name = list(primary_metric)[0]
        
        fold_values1 = [fold.get(metric_name, 0) for fold in result1.fold_metrics]
        fold_values2 = [fold.get(metric_name, 0) for fold in result2.fold_metrics]
        
        if len(fold_values1) > 1 and len(fold_values2) > 1:
            t_stat, p_value = stats.ttest_rel(fold_values1, fold_values2)
            
            st.metric(f"Paired t-test p-value", f"{p_value:.4f}")
            
            if p_value < 0.05:
                st.success(f"Significant difference found between {model1} and {model2}")
            else:
                st.info(f"No significant difference between {model1} and {model2}")


def render_model_comparison_ui(validation_engine: Any, spec: Any) -> None:
    """Render complete model comparison interface.
    
    Args:
        validation_engine: ValidationEngine instance
        spec: ProjectSpecification
    """
    st.title("🔍 Model Comparison")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    # Load validation results
    artifact_manager = st.session_state.artifact_manager
    project_id = spec.project_id
    
    try:
        # Load validation results from artifacts
        validation_results = {}
        # TODO: Load actual validation results
        # For now, use placeholder
        
        if not validation_results:
            st.info("No validation results available. Run model training first.")
            return
        
        # Primary metric selection
        available_metrics = set()
        for result in validation_results.values():
            if result and hasattr(result, 'metrics'):
                available_metrics.update(result.metrics.keys())
        
        primary_metric = st.selectbox(
            "Primary Metric for Comparison",
            options=list(available_metrics),
            index=0 if available_metrics else 0,
        )
        
        st.markdown("---")
        
        # Comparison tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Table", "Metric Plot", "Radar", "Statistical"])
        
        with tab1:
            render_model_comparison_table(validation_results)
        
        with tab2:
            render_metric_comparison_plot(validation_results, primary_metric)
        
        with tab3:
            metrics_to_compare = st.multiselect(
                "Select metrics for radar comparison",
                options=list(available_metrics),
                default=list(available_metrics)[:5],
            )
            render_radar_comparison(validation_results, metrics_to_compare)
        
        with tab4:
            render_statistical_comparison(validation_results)
        
        st.markdown("---")
        render_ranking_comparison(validation_results, primary_metric)
        
    except Exception as e:
        st.error(f"Error loading validation results: {e}")
