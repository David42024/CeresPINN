"""Statistical tests UI components for ML Lab.

This module provides UI components for running and visualizing
statistical tests on model results.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import streamlit as st


def render_statistical_test_selector(statistical_engine: Any, problem_type: str) -> List[str]:
    """Render statistical test selector based on problem type.
    
    Args:
        statistical_engine: StatisticalEngine instance
        problem_type: Type of ML problem
    
    Returns:
        List of selected test names
    """
    st.subheader("Select Statistical Tests")
    
    # Get applicable tests
    applicable_tests = statistical_engine.get_tests_for_problem_type(problem_type)
    
    if not applicable_tests:
        st.info("No statistical tests available for this problem type")
        return []
    
    # Display tests with descriptions
    selected_tests = []
    
    for test in applicable_tests:
        with st.expander(f"{test.name}"):
            st.write(f"**Description:** {test.description}")
            st.write(f"**Requires Observations:** {test.requires_observations}")
            st.write(f"**Requires Projections:** {test.requires_projections}")
            
            if st.checkbox(f"Enable {test.name}", key=f"select_test_{test.name}"):
                selected_tests.append(test.name)
    
    return selected_tests


def render_test_parameters(test_name: str) -> Dict[str, Any]:
    """Render test-specific parameter configuration.
    
    Args:
        test_name: Name of the statistical test
    
    Returns:
        Dictionary with test parameters
    """
    st.subheader(f"Test Parameters: {test_name}")
    
    params = {}
    
    # Common parameters
    alpha = st.slider(
        "Significance Level (alpha)",
        min_value=0.01,
        max_value=0.2,
        value=0.05,
        step=0.01,
    )
    params["alpha"] = alpha
    
    # Test-specific parameters
    if test_name == "bootstrap_ci":
        n_bootstrap = st.number_input(
            "Number of Bootstrap Samples",
            min_value=100,
            max_value=10000,
            value=1000,
        )
        seed = st.number_input("Random Seed", value=42)
        params["n_bootstrap"] = n_bootstrap
        params["seed"] = seed
    
    if test_name == "mcnemar_test":
        st.info("McNemar's test requires y_true, y_pred1, and y_pred2")
    
    if test_name == "cochran_q_test":
        st.info("Cochran's Q test requires y_true and multiple predictions")
    
    return params


def render_test_input_data(test_name: str) -> Dict[str, Any]:
    """Render input data configuration for statistical test.
    
    Args:
        test_name: Name of the statistical test
    
    Returns:
        Dictionary with input data configuration
    """
    st.subheader(f"Input Data: {test_name}")
    
    input_config = {}
    
    # Determine required inputs based on test
    if test_name in ["ks_test", "paired_t_test", "independent_t_test", "wilcoxon_test", "mann_whitney_test"]:
        st.info("This test requires two samples")
        
        sample1_source = st.selectbox(
            "Sample 1 Source",
            options=["upload", "experiment_result", "manual"],
        )
        sample2_source = st.selectbox(
            "Sample 2 Source",
            options=["upload", "experiment_result", "manual"],
        )
        
        input_config["sample1_source"] = sample1_source
        input_config["sample2_source"] = sample2_source
    
    elif test_name in ["mcnemar_test", "cochran_q_test"]:
        st.info("This test requires predictions from multiple models")
        
        input_config["require_predictions"] = True
    
    elif test_name == "bootstrap_ci":
        st.info("This test requires a single sample")
        
        sample_source = st.selectbox(
            "Sample Source",
            options=["upload", "experiment_result", "manual"],
        )
        input_config["sample_source"] = sample_source
    
    return input_config


def render_statistical_test_results(results: Dict[str, Dict[str, Any]]) -> None:
    """Render statistical test results with visualization.
    
    Args:
        results: Dictionary of test results from StatisticalEngine
    """
    st.subheader("Statistical Test Results")
    
    if not results:
        st.info("No statistical test results available")
        return
    
    # Summary table
    summary_data = []
    for test_name, test_result in results.items():
        if test_result and "error" not in test_result:
            summary_data.append({
                "Test": test_name,
                "Statistic": test_result.get("statistic", "N/A"),
                "p-value": test_result.get("p_value", "N/A"),
                "Significant": test_result.get("significant") or test_result.get("reject_null", False),
            })
    
    if summary_data:
        import pandas as pd
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
    
    # Detailed results
    st.markdown("---")
    for test_name, test_result in results.items():
        if test_result is None:
            continue
        
        if "error" in test_result:
            st.error(f"{test_name}: {test_result['error']}")
            continue
        
        with st.expander(f"{test_name} Details", expanded=True):
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
                
                # Visual indicator
                if p_value < 0.001:
                    st.success("Very strong evidence against null hypothesis")
                elif p_value < 0.01:
                    st.success("Strong evidence against null hypothesis")
                elif p_value < 0.05:
                    st.success("Moderate evidence against null hypothesis")
                elif p_value < 0.1:
                    st.warning("Weak evidence against null hypothesis")
                else:
                    st.info("No significant evidence against null hypothesis")


def render_statistical_test_ui(statistical_engine: Any, spec: Any) -> None:
    """Render complete statistical test interface.
    
    Args:
        statistical_engine: StatisticalEngine instance
        spec: ProjectSpecification
    """
    st.title("📊 Statistical Tests")
    st.markdown("---")
    
    if not st.session_state.current_project:
        st.warning("Please select a project first")
        return
    
    # Test selection
    selected_tests = render_statistical_test_selector(
        statistical_engine,
        spec.problem_type.value,
    )
    
    if not selected_tests:
        st.warning("Please select at least one statistical test")
        return
    
    st.markdown("---")
    
    # Configure parameters for each test
    test_configs = {}
    for test_name in selected_tests:
        with st.expander(f"Configure {test_name}"):
            params = render_test_parameters(test_name)
            input_config = render_test_input_data(test_name)
            test_configs[test_name] = {
                "parameters": params,
                "input_config": input_config,
            }
    
    st.markdown("---")
    
    # Run tests button
    if st.button("Run Statistical Tests", type="primary"):
        st.info("Running statistical tests...")
        
        # TODO: Integrate with actual data and run tests
        # results = statistical_engine.run_tests(selected_tests, ...)
        
        # Placeholder results
        results = {}
        for test_name in selected_tests:
            results[test_name] = {
                "test": test_name,
                "statistic": 2.5,
                "p_value": 0.012,
                "significant": True,
                "alpha": test_configs[test_name]["parameters"]["alpha"],
            }
        
        render_statistical_test_results(results)
        
        # Save results
        if results:
            artifact_manager = st.session_state.artifact_manager
            artifact_manager.save_artifact(
                spec.project_id,
                "statistical_tests",
                "test_results.json",
                results,
            )
            st.success("Test results saved!")
