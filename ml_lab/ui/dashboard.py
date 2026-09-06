"""Dashboard UI components for ML Lab.

This module provides dashboard components for displaying project overview,
statistics, and quick actions.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_project_overview(spec: Any) -> None:
    """Render project overview section.
    
    Args:
        spec: ProjectSpecification
    """
    st.subheader("Project Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Project ID", spec.project_id[:8] + "...")
    
    with col2:
        st.metric("Status", spec.status)
    
    with col3:
        st.metric("Created", spec.created_at.strftime("%Y-%m-%d"))
    
    st.markdown("---")
    
    # Project details
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Domain:**", spec.domain)
        st.write("**Problem Type:**", spec.problem_type.value)
        st.write("**Objective:**", spec.objective.value)
    
    with col2:
        st.write("**Data Type:**", spec.data_type.value)
        st.write("**Target Variable:**", spec.target_variable or "Not specified")
        st.write("**Last Updated:**", spec.updated_at.strftime("%Y-%m-%d") if spec.updated_at else "Never")


def render_pipeline_status(plan: Any) -> None:
    """Render pipeline execution status.
    
    Args:
        plan: PipelinePlan from PipelineEngine
    """
    st.subheader("Pipeline Status")
    
    # Overall progress
    progress = plan.progress_percentage
    st.progress(progress / 100)
    st.caption(f"Progress: {progress:.1f}%")
    
    # Step status
    if plan.step_executions:
        st.markdown("### Pipeline Steps")
        
        for step in plan.steps:
            execution = plan.step_executions.get(step)
            if execution:
                status_emoji = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "skipped": "⏭️",
                }.get(execution.status.value, "❓")
                
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(f"{status_emoji} {step.value}")
                with col2:
                    st.write(execution.status.value)
                with col3:
                    if execution.elapsed_seconds:
                        st.write(f"{execution.elapsed_seconds:.1f}s")


def render_model_comparison(results: Dict[str, Any]) -> None:
    """Render model comparison results.
    
    Args:
        results: Model comparison results
    """
    st.subheader("Model Comparison")
    
    if not results:
        st.info("No model comparison results available")
        return
    
    # Create comparison table
    comparison_data = []
    for model_name, result in results.items():
        if result and hasattr(result, 'metrics'):
            for metric_name, metric_values in result.metrics.items():
                comparison_data.append({
                    "Model": model_name,
                    "Metric": metric_name,
                    "Value": metric_values.get("mean", 0),
                    "Std": metric_values.get("std", 0),
                })
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
        
        # Plot comparison
        if len(df) > 0:
            fig = px.bar(
                df,
                x="Model",
                y="Value",
                color="Metric",
                title="Model Performance Comparison",
                barmode="group",
            )
            st.plotly_chart(fig, use_container_width=True)


def render_dataset_statistics(profile: Any) -> None:
    """Render dataset statistics.
    
    Args:
        profile: DatasetProfile from DatasetAnalyzer
    """
    st.subheader("Dataset Statistics")
    
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
    
    # Data quality
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Numerical Features:**", len(profile.numerical_features))
        st.write("**Categorical Features:**", len(profile.categorical_features))
        st.write("**Temporal Features:**", len(profile.temporal_features))
    
    with col2:
        st.write("**Has Missing:**", profile.has_missing_values)
        st.write("**Has Duplicates:**", profile.has_duplicates)
        st.write("**Has Outliers:**", profile.has_outliers)
    
    # Issues and warnings
    if profile.issues:
        st.error("Issues:")
        for issue in profile.issues:
            st.write(f"• {issue}")
    
    if profile.warnings:
        st.warning("Warnings:")
        for warning in profile.warnings:
            st.write(f"• {warning}")


def render_quick_actions(spec: Any) -> None:
    """Render quick action buttons.
    
    Args:
        spec: ProjectSpecification
    """
    st.subheader("Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Analyze Dataset", use_container_width=True):
            st.session_state.selected_page = "Dataset Analysis"
            st.rerun()
    
    with col2:
        if st.button("🧠 Train Models", use_container_width=True):
            st.session_state.selected_page = "Model Training"
            st.rerun()
    
    with col3:
        if st.button("✅ Validate Models", use_container_width=True):
            st.session_state.selected_page = "Validation"
            st.rerun()
    
    with col4:
        if st.button("📈 Statistical Tests", use_container_width=True):
            st.session_state.selected_page = "Statistical Tests"
            st.rerun()


def render_recent_experiments(artifact_manager: Any, project_id: str) -> None:
    """Render recent experiments.
    
    Args:
        artifact_manager: ArtifactManager instance
        project_id: Project ID
    """
    st.subheader("Recent Experiments")
    
    try:
        experiments = artifact_manager.list_artifacts(project_id, "experiments")
        
        if not experiments:
            st.info("No experiments run yet")
            return
        
        for exp_path in experiments[-5:]:  # Last 5 experiments
            with st.expander(exp_path.name):
                # Load experiment metadata
                try:
                    metadata = artifact_manager.get_artifact_metadata(project_id, "experiments", exp_path.name)
                    if metadata:
                        st.json(metadata)
                except Exception:
                    st.write("No metadata available")
    except Exception as e:
        st.error(f"Error loading experiments: {e}")


def render_artifact_summary(artifact_manager: Any, project_id: str) -> None:
    """Render artifact storage summary.
    
    Args:
        artifact_manager: ArtifactManager instance
        project_id: Project ID
    """
    st.subheader("Artifact Storage")
    
    try:
        sizes = artifact_manager.get_project_size(project_id)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Size", f"{sizes.get('total', 0) / 1024 / 1024:.2f} MB")
        
        with col2:
            n_artifacts = len([s for k, s in sizes.items() if k != 'total'])
            st.metric("Artifact Types", n_artifacts)
        
        with col3:
            st.metric("Project ID", project_id[:8] + "...")
        
        # Breakdown by type
        if len(sizes) > 1:
            st.markdown("### Storage Breakdown")
            breakdown_data = []
            for artifact_type, size in sizes.items():
                if artifact_type != 'total':
                    breakdown_data.append({
                        "Type": artifact_type,
                        "Size (MB)": size / 1024 / 1024,
                    })
            
            if breakdown_data:
                df = pd.DataFrame(breakdown_data)
                st.dataframe(df, use_container_width=True)
                
                fig = px.pie(
                    df,
                    values="Size (MB)",
                    names="Type",
                    title="Artifact Storage Distribution",
                )
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading artifact summary: {e}")
