"""Report Generator - Generate comprehensive ML reports.

This module provides functionality to generate comprehensive reports
for ML projects including model performance, validation results,
statistical tests, and recommendations.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class ReportGenerator:
    """Generate comprehensive ML reports."""
    
    def __init__(self, artifact_manager: Optional[Any] = None):
        """Initialize the report generator.
        
        Args:
            artifact_manager: ArtifactManager instance for loading data
        """
        self.artifact_manager = artifact_manager
    
    def generate_project_report(
        self,
        spec: Any,
        dataset_profile: Optional[Any] = None,
        validation_results: Optional[Dict[str, Any]] = None,
        statistical_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive project report.
        
        Args:
            spec: ProjectSpecification
            dataset_profile: Optional DatasetProfile
            validation_results: Optional validation results
            statistical_results: Optional statistical test results
        
        Returns:
            Dictionary with report content
        """
        report = {
            "metadata": {
                "project_name": spec.project_name,
                "project_id": spec.project_id,
                "domain": spec.domain,
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.0",
            },
            "project_context": self._generate_project_context(spec),
            "dataset_summary": self._generate_dataset_summary(dataset_profile) if dataset_profile else None,
            "model_performance": self._generate_model_performance(validation_results) if validation_results else None,
            "statistical_tests": self._generate_statistical_summary(statistical_results) if statistical_results else None,
            "recommendations": self._generate_recommendations(spec, dataset_profile, validation_results),
        }
        
        return report
    
    def _generate_project_context(self, spec: Any) -> Dict[str, Any]:
        """Generate project context section.
        
        Args:
            spec: ProjectSpecification
        
        Returns:
            Dictionary with project context
        """
        return {
            "description": spec.description,
            "business_objective": spec.business_objective,
            "problem_type": spec.problem_type.value,
            "data_type": spec.data_type.value,
            "objective": spec.objective.value,
            "constraints": spec.constraints,
            "target_variable": spec.target_variable,
        }
    
    def _generate_dataset_summary(self, profile: Any) -> Dict[str, Any]:
        """Generate dataset summary section.
        
        Args:
            profile: DatasetProfile
        
        Returns:
            Dictionary with dataset summary
        """
        return {
            "rows": profile.rows,
            "columns": profile.columns,
            "memory_mb": profile.memory_mb,
            "numerical_features": len(profile.numerical_features),
            "categorical_features": len(profile.categorical_features),
            "temporal_features": len(profile.temporal_features),
            "missing_percentage": profile.total_missing_percentage,
            "has_duplicates": profile.has_duplicates,
            "has_outliers": profile.has_outliers,
            "data_quality": "Good" if profile.total_missing_percentage < 5 else "Needs attention",
            "issues": profile.issues,
            "warnings": profile.warnings,
        }
    
    def _generate_model_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate model performance section.
        
        Args:
            results: Validation results
        
        Returns:
            Dictionary with model performance
        """
        performance = {}
        
        for model_name, result in results.items():
            if result and hasattr(result, 'metrics'):
                performance[model_name] = {
                    "metrics": result.metrics,
                    "fold_metrics": result.fold_metrics if hasattr(result, 'fold_metrics') else [],
                    "metadata": result.metadata if hasattr(result, 'metadata') else {},
                }
        
        return performance
    
    def _generate_statistical_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate statistical tests summary.
        
        Args:
            results: Statistical test results
        
        Returns:
            Dictionary with statistical summary
        """
        summary = {}
        
        for test_name, test_result in results.items():
            if test_result and "error" not in test_result:
                summary[test_name] = {
                    "statistic": test_result.get("statistic"),
                    "p_value": test_result.get("p_value"),
                    "significant": test_result.get("significant") or test_result.get("reject_null", False),
                    "alpha": test_result.get("alpha"),
                }
        
        return summary
    
    def _generate_recommendations(
        self,
        spec: Any,
        dataset_profile: Optional[Any] = None,
        validation_results: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Generate recommendations based on analysis.
        
        Args:
            spec: ProjectSpecification
            dataset_profile: Optional DatasetProfile
            validation_results: Optional validation results
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Dataset recommendations
        if dataset_profile:
            if dataset_profile.total_missing_percentage > 10:
                recommendations.append("Consider implementing missing value imputation strategy")
            
            if dataset_profile.has_duplicates:
                recommendations.append("Review and handle duplicate records")
            
            if dataset_profile.has_outliers:
                recommendations.append("Investigate and handle outlier values")
            
            if dataset_profile.is_imbalanced:
                recommendations.append("Consider using stratified sampling or class weights for imbalanced data")
        
        # Model recommendations
        if validation_results:
            best_model = None
            best_score = -float('inf')
            
            for model_name, result in validation_results.items():
                if result and hasattr(result, 'metrics'):
                    primary_metric = result.metrics.get(spec.metrics.primary)
                    if primary_metric:
                        score = primary_metric.get("mean", 0)
                        if score > best_score:
                            best_score = score
                            best_model = model_name
            
            if best_model:
                recommendations.append(f"Best performing model: {best_model} with {spec.metrics.primary} = {best_score:.4f}")
        
        # General recommendations
        if spec.explainability.enabled:
            recommendations.append("Model explainability is enabled - review feature importance for insights")
        
        if spec.statistical_tests.enabled:
            recommendations.append("Statistical tests are enabled - review test results for significance")
        
        return recommendations
    
    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown report.
        
        Args:
            report: Report dictionary
        
        Returns:
            Markdown string
        """
        lines = []
        
        # Header
        lines.append(f"# ML Lab Project Report")
        lines.append(f"**Project:** {report['metadata']['project_name']}")
        lines.append(f"**Generated:** {report['metadata']['generated_at']}")
        lines.append("")
        
        # Project Context
        lines.append("## Project Context")
        context = report['project_context']
        lines.append(f"- **Domain:** {context['domain']}")
        lines.append(f"- **Problem Type:** {context['problem_type']}")
        lines.append(f"- **Data Type:** {context['data_type']}")
        lines.append(f"- **Objective:** {context['objective']}")
        lines.append(f"- **Description:** {context['description']}")
        lines.append("")
        
        # Dataset Summary
        if report['dataset_summary']:
            lines.append("## Dataset Summary")
            ds = report['dataset_summary']
            lines.append(f"- **Rows:** {ds['rows']}")
            lines.append(f"- **Columns:** {ds['columns']}")
            lines.append(f"- **Memory:** {ds['memory_mb']:.2f} MB")
            lines.append(f"- **Numerical Features:** {ds['numerical_features']}")
            lines.append(f"- **Categorical Features:** {ds['categorical_features']}")
            lines.append(f"- **Missing %:** {ds['missing_percentage']:.2f}%")
            lines.append(f"- **Data Quality:** {ds['data_quality']}")
            lines.append("")
            
            if ds['issues']:
                lines.append("### Issues")
                for issue in ds['issues']:
                    lines.append(f"- {issue}")
                lines.append("")
        
        # Model Performance
        if report['model_performance']:
            lines.append("## Model Performance")
            for model_name, perf in report['model_performance'].items():
                lines.append(f"### {model_name}")
                for metric_name, metric_values in perf['metrics'].items():
                    lines.append(f"- **{metric_name}:** {metric_values['mean']:.4f} ± {metric_values['std']:.4f}")
                lines.append("")
        
        # Statistical Tests
        if report['statistical_tests']:
            lines.append("## Statistical Tests")
            for test_name, test_result in report['statistical_tests'].items():
                significance = "✓ Significant" if test_result['significant'] else "✗ Not significant"
                lines.append(f"- **{test_name}:** p-value = {test_result['p_value']:.4f} ({significance})")
            lines.append("")
        
        # Recommendations
        if report['recommendations']:
            lines.append("## Recommendations")
            for rec in report['recommendations']:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report.
        
        Args:
            report: Report dictionary
        
        Returns:
            HTML string
        """
        html = f"""
        <html>
        <head>
            <title>{report['metadata']['project_name']} - ML Lab Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
                .recommendation {{ background: #e7f3ff; padding: 10px; margin: 5px 0; border-left: 4px solid #2196F3; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>ML Lab Project Report</h1>
            <p><strong>Project:</strong> {report['metadata']['project_name']}</p>
            <p><strong>Generated:</strong> {report['metadata']['generated_at']}</p>
            
            <h2>Project Context</h2>
            <p><strong>Domain:</strong> {report['project_context']['domain']}</p>
            <p><strong>Problem Type:</strong> {report['project_context']['problem_type']}</p>
            <p><strong>Description:</strong> {report['project_context']['description']}</p>
        """
        
        # Add dataset summary
        if report['dataset_summary']:
            ds = report['dataset_summary']
            html += f"""
            <h2>Dataset Summary</h2>
            <div class="metric"><strong>Rows:</strong> {ds['rows']}</div>
            <div class="metric"><strong>Columns:</strong> {ds['columns']}</div>
            <div class="metric"><strong>Memory:</strong> {ds['memory_mb']:.2f} MB</div>
            <div class="metric"><strong>Missing %:</strong> {ds['missing_percentage']:.2f}%</div>
            """
        
        # Add recommendations
        if report['recommendations']:
            html += "<h2>Recommendations</h2>"
            for rec in report['recommendations']:
                html += f'<div class="recommendation">{rec}</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def save_report(
        self,
        report: Dict[str, Any],
        project_id: str,
        format: str = "json",
    ) -> Path:
        """Save report to artifacts.
        
        Args:
            report: Report dictionary
            project_id: Project ID
            format: Output format (json, markdown, html)
        
        Returns:
            Path to saved report
        """
        if not self.artifact_manager:
            raise ValueError("Artifact manager not configured")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filename = f"report_{timestamp}.json"
            self.artifact_manager.save_artifact(
                project_id,
                "reports",
                filename,
                report,
            )
        elif format == "markdown":
            markdown = self.generate_markdown_report(report)
            filename = f"report_{timestamp}.md"
            self.artifact_manager.save_artifact(
                project_id,
                "reports",
                filename,
                markdown,
            )
        elif format == "html":
            html = self.generate_html_report(report)
            filename = f"report_{timestamp}.html"
            self.artifact_manager.save_artifact(
                project_id,
                "reports",
                filename,
                html,
            )
        
        return Path(f"reports/{filename}")


def get_report_generator(artifact_manager: Optional[Any] = None) -> ReportGenerator:
    """Get the global report generator instance.
    
    Args:
        artifact_manager: Optional ArtifactManager instance
    
    Returns:
        ReportGenerator instance
    """
    return ReportGenerator(artifact_manager)
