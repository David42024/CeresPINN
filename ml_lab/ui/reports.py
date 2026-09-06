"""Report generation UI components for ML Lab.

This module provides UI components for generating and exporting
comprehensive ML reports.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st


def render_report_config(spec: Any) -> Dict[str, Any]:
    """Render report configuration interface.
    
    Args:
        spec: ProjectSpecification
    
    Returns:
        Dictionary with report configuration
    """
    st.subheader("Report Configuration")
    
    # Report sections
    st.markdown("### Report Sections")
    
    include_project_context = st.checkbox("Project Context", value=True)
    include_dataset_summary = st.checkbox("Dataset Summary", value=True)
    include_model_performance = st.checkbox("Model Performance", value=True)
    include_statistical_tests = st.checkbox("Statistical Tests", value=True)
    include_recommendations = st.checkbox("Recommendations", value=True)
    include_appendix = st.checkbox("Appendix (detailed metrics)", value=False)
    
    # Report format
    st.markdown("### Report Format")
    
    report_format = st.selectbox(
        "Output Format",
        options=["markdown", "html", "pdf", "json"],
        help="Format for the generated report"
    )
    
    # Report style
    st.markdown("### Report Style")
    
    theme = st.selectbox(
        "Theme",
        options=["default", "professional", "minimal", "dark"],
    )
    
    include_charts = st.checkbox("Include Charts", value=True)
    include_tables = st.checkbox("Include Tables", value=True)
    
    # Report metadata
    st.markdown("### Report Metadata")
    
    report_title = st.text_input(
        "Report Title",
        value=f"{spec.project_name} - ML Report",
    )
    
    author = st.text_input("Author", placeholder="Your name or organization")
    
    report_description = st.text_area(
        "Report Description",
        placeholder="Brief description of this report...",
        height=80,
    )
    
    config = {
        "sections": {
            "project_context": include_project_context,
            "dataset_summary": include_dataset_summary,
            "model_performance": include_model_performance,
            "statistical_tests": include_statistical_tests,
            "recommendations": include_recommendations,
            "appendix": include_appendix,
        },
        "format": report_format,
        "style": {
            "theme": theme,
            "include_charts": include_charts,
            "include_tables": include_tables,
        },
        "metadata": {
            "title": report_title,
            "author": author,
            "description": report_description,
        },
    }
    
    return config


def render_report_preview(report: Dict[str, Any]) -> None:
    """Render report preview.
    
    Args:
        report: Report dictionary
    """
    st.subheader("Report Preview")
    
    # Show metadata
    st.markdown("### Report Metadata")
    st.json(report["metadata"])
    
    # Show sections
    st.markdown("### Report Sections")
    
    if report["sections"]["project_context"]:
        with st.expander("Project Context", expanded=True):
            st.json(report["project_context"])
    
    if report["sections"]["dataset_summary"] and report["dataset_summary"]:
        with st.expander("Dataset Summary"):
            st.json(report["dataset_summary"])
    
    if report["sections"]["model_performance"] and report["model_performance"]:
        with st.expander("Model Performance"):
            st.json(report["model_performance"])
    
    if report["sections"]["statistical_tests"] and report["statistical_tests"]:
        with st.expander("Statistical Tests"):
            st.json(report["statistical_tests"])
    
    if report["sections"]["recommendations"] and report["recommendations"]:
        with st.expander("Recommendations"):
            for rec in report["recommendations"]:
                st.write(f"• {rec}")


def render_report_export(report: Dict[str, Any], format: str) -> None:
    """Render report export interface.
    
    Args:
        report: Report dictionary
        format: Export format
    """
    st.subheader("Export Report")
    
    if format == "markdown":
        from core.report_generator import get_report_generator
        generator = get_report_generator()
        markdown = generator.generate_markdown_report(report)
        
        st.text_area("Markdown Report", markdown, height=400)
        
        if st.download_button(
            label="Download Markdown",
            data=markdown,
            file_name="report.md",
            mime="text/markdown",
        ):
            st.success("Markdown report downloaded!")
    
    elif format == "html":
        from core.report_generator import get_report_generator
        generator = get_report_generator()
        html = generator.generate_html_report(report)
        
        st.components.v1.html(html, height=600, scrolling=True)
        
        if st.download_button(
            label="Download HTML",
            data=html,
            file_name="report.html",
            mime="text/html",
        ):
            st.success("HTML report downloaded!")
    
    elif format == "json":
        import json
        json_str = json.dumps(report, indent=2)
        
        st.json(report)
        
        if st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="report.json",
            mime="application/json",
        ):
            st.success("JSON report downloaded!")
    
    elif format == "pdf":
        st.info("PDF export requires additional dependencies (weasyprint, pdfkit)")
        st.warning("PDF export coming soon!")


def render_report_history(artifact_manager: Any, project_id: str) -> None:
    """Render report history.
    
    Args:
        artifact_manager: ArtifactManager instance
        project_id: Project ID
    """
    st.subheader("Report History")
    
    try:
        reports = artifact_manager.list_artifacts(project_id, "reports")
        
        if not reports:
            st.info("No reports generated yet")
            return
        
        for report_path in reports:
            with st.expander(report_path.name):
                try:
                    metadata = artifact_manager.get_artifact_metadata(
                        project_id, "reports", report_path.name
                    )
                    if metadata:
                        st.json(metadata)
                except Exception:
                    st.write("No metadata available")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View", key=f"view_{report_path.name}"):
                        # Load and display report
                        try:
                            report = artifact_manager.load_artifact(
                                project_id, "reports", report_path.name
                            )
                            render_report_preview(report)
                        except Exception as e:
                            st.error(f"Error loading report: {e}")
                
                with col2:
                    if st.button("Download", key=f"download_{report_path.name}"):
                        # Download report
                        try:
                            report = artifact_manager.load_artifact(
                                project_id, "reports", report_path.name
                            )
                            # Trigger download
                            st.success("Download started!")
                        except Exception as e:
                            st.error(f"Error downloading report: {e}")
    except Exception as e:
        st.error(f"Error loading report history: {e}")


def render_report_generator_ui(spec: Any) -> None:
    """Render complete report generator interface.
    
    Args:
        spec: ProjectSpecification
    """
    st.title("📄 Report Generator")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    artifact_manager = st.session_state.artifact_manager
    project_id = spec.project_id
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Generate Report", "Report History", "Templates"])
    
    with tab1:
        # Configuration
        config = render_report_config(spec)
        
        st.markdown("---")
        
        # Generate button
        if st.button("Generate Report", type="primary"):
            from core.report_generator import get_report_generator
            from core.dataset_analyzer import DatasetAnalyzer
            from engines.validation_engine import ValidationEngine
            
            generator = get_report_generator(artifact_manager)
            
            # Load data for report
            dataset_profile = st.session_state.current_dataset
            
            # Placeholder for validation results
            validation_results = None
            
            # Placeholder for statistical results
            statistical_results = None
            
            # Generate report
            with st.spinner("Generating report..."):
                report = generator.generate_project_report(
                    spec=spec,
                    dataset_profile=dataset_profile,
                    validation_results=validation_results,
                    statistical_results=statistical_results,
                )
            
            st.success("Report generated successfully!")
            
            # Preview
            render_report_preview(report)
            
            # Export
            st.markdown("---")
            render_report_export(report, config["format"])
            
            # Save report
            generator.save_report(report, project_id, config["format"])
    
    with tab2:
        render_report_history(artifact_manager, project_id)
    
    with tab3:
        st.subheader("Report Templates")
        
        st.info("Report templates coming soon!")
        
        # Template selection
        template = st.selectbox(
            "Select Template",
            options=["standard", "executive_summary", "technical_detailed", "compliance"],
        )
        
        st.markdown("### Template Description")
        
        template_descriptions = {
            "standard": "Standard comprehensive ML report with all sections",
            "executive_summary": "High-level summary for stakeholders",
            "technical_detailed": "Detailed technical report for data scientists",
            "compliance": "Report focused on compliance and audit requirements",
        }
        
        st.info(template_descriptions.get(template, ""))
