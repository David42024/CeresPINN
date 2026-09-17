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
    """Render model comparison table with side-by-side metrics.
    
    Args:
        results: Dictionary mapping model names to validation results
    """
    st.subheader("Model Comparison Table (TimeSeriesSplit Benchmark)")
    
    if not results:
        st.info("No model results available for comparison")
        return
    
    # Build side-by-side summary data
    table_rows = []
    for model_name, result in results.items():
        if result and hasattr(result, 'metrics'):
            m = result.metrics
            r2_val = m.get("r2", {}).get("mean", None) if isinstance(m.get("r2"), dict) else m.get("r2", None)
            rmse_raw = m.get("neg_root_mean_squared_error", m.get("rmse", {}))
            rmse_val = abs(rmse_raw.get("mean", 0.0)) if isinstance(rmse_raw, dict) else (abs(float(rmse_raw)) if rmse_raw is not None else None)
            mae_raw = m.get("neg_mean_absolute_error", m.get("mae", {}))
            mae_val = abs(mae_raw.get("mean", 0.0)) if isinstance(mae_raw, dict) else (abs(float(mae_raw)) if mae_raw is not None else None)
            mape_raw = m.get("neg_mean_absolute_percentage_error", m.get("mape", {}))
            mape_val = abs(mape_raw.get("mean", 0.0)) if isinstance(mape_raw, dict) else (abs(float(mape_raw)) if mape_raw is not None else None)
            
            table_rows.append({
                "Model": model_name,
                "R² Score": round(float(r2_val), 4) if r2_val is not None else "N/A",
                "RMSE (bu/acre)": round(float(rmse_val), 2) if rmse_val is not None else "N/A",
                "MAE (bu/acre)": round(float(mae_val), 2) if mae_val is not None else "N/A",
                "MAPE": f"{mape_val * 100:.2f}%" if mape_val and mape_val > 0 else "N/A",
                "_r2_sort": float(r2_val) if r2_val is not None else -999.0
            })
    
    if table_rows:
        df_summary = pd.DataFrame(table_rows).sort_values("_r2_sort", ascending=False)
        ranks = [f"🥇 #{i+1}" if i == 0 else (f"🥈 #{i+1}" if i == 1 else (f"🥉 #{i+1}" if i == 2 else f"#{i+1}")) for i in range(len(df_summary))]
        df_summary.insert(1, "Rank", ranks)
        df_display = df_summary.drop(columns=["_r2_sort"])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Best model highlight
        best_name = df_summary.iloc[0]["Model"]
        best_r2 = df_summary.iloc[0]["R² Score"]
        st.success(f"🏆 **Mejor Modelo Global:** `{best_name}` con **R² = {best_r2}** (evaluado con validación cruzada temporal TimeSeriesSplit).")


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
    
    # Perform paired t-test on chosen metric
    from scipy import stats
    
    common_metrics = [m for m in result1.metrics.keys() if m in result2.metrics]
    if not common_metrics:
        common_metrics = list(result1.metrics.keys())
    
    default_m_idx = common_metrics.index("r2") if "r2" in common_metrics else 0
    metric_name = st.selectbox("Select Metric for Paired t-test:", options=common_metrics, index=default_m_idx)
    
    fold_values1 = [fold.get(metric_name, 0) for fold in result1.fold_metrics]
    fold_values2 = [fold.get(metric_name, 0) for fold in result2.fold_metrics]
    
    if len(fold_values1) > 1 and len(fold_values2) > 1:
        t_stat, p_value = stats.ttest_rel(fold_values1, fold_values2)
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric(f"Paired t-test t-statistic", f"{t_stat:.4f}")
        with c2:
            st.metric(f"Paired t-test p-value", f"{p_value:.4f}")
        
        if p_value < 0.05:
            st.success(f"✅ Statistically significant difference found between **{model1}** and **{model2}** (p < 0.05).")
        else:
            st.info(f"ℹ️ No statistically significant difference between **{model1}** and **{model2}** (p ≥ 0.05).")


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
        val_artifacts = artifact_manager.list_artifacts(project_id, "validation")
        val_model_names = set()
        for p in val_artifacts:
            if p.name.endswith("_validation_metrics.json"):
                val_model_names.add(p.name[:-len("_validation_metrics.json")])
        
        for m_name in sorted(val_model_names):
            res = validation_engine.load_validation_result(project_id, m_name)
            if res and res.metrics:
                validation_results[m_name] = res

        # Also check models directory if any model was trained but not in validation
        model_artifacts = artifact_manager.list_artifacts(project_id, "models")
        for p in model_artifacts:
            if p.name.endswith("_metrics.json"):
                m_name = p.name[:-len("_metrics.json")]
                if m_name not in validation_results:
                    raw_data = artifact_manager.load_artifact(project_id, "models", p.name)
                    metrics_dict = raw_data.get("metrics", raw_data) if isinstance(raw_data, dict) else {}
                    formatted = {}
                    for k, v in metrics_dict.items():
                        if isinstance(v, dict):
                            formatted[k] = v
                        elif isinstance(v, (int, float)):
                            formatted[k] = {"mean": float(v), "std": 0.0, "min": float(v), "max": float(v)}
                    from engines.validation_engine import ValidationResult
                    validation_results[m_name] = ValidationResult(
                        model_name=m_name,
                        metrics=formatted
                    )
        
        if not validation_results:
            st.info("No validation results available. Run model training first.")
            return
        
        # Primary metric selection
        available_metrics = set()
        for result in validation_results.values():
            if result and hasattr(result, 'metrics'):
                available_metrics.update(result.metrics.keys())
        
        metric_list = sorted(list(available_metrics))
        default_idx = 0
        if "r2" in metric_list:
            default_idx = metric_list.index("r2")
        elif "neg_root_mean_squared_error" in metric_list:
            default_idx = metric_list.index("neg_root_mean_squared_error")
        elif "rmse" in metric_list:
            default_idx = metric_list.index("rmse")
        
        primary_metric = st.selectbox(
            "Primary Metric for Comparison",
            options=metric_list,
            index=default_idx,
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
