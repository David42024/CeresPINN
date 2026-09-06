"""Statistical Engine - Generalized statistical tests for ML Lab.

This module provides generalized statistical tests adapted from CeresPINN's
validation.py for use in ML Lab. It removes domain-specific hardcodes and
provides configurable statistical analysis for any ML problem.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats


class StatisticalTest:
    """Configuration for a statistical test."""
    
    def __init__(
        self,
        name: str,
        description: str,
        test_fn: Callable,
        applicable_problem_types: List[str],
        requires_observations: bool = True,
        requires_projections: bool = False,
        alpha: float = 0.05,
    ):
        self.name = name
        self.description = description
        self.test_fn = test_fn
        self.applicable_problem_types = applicable_problem_types
        self.requires_observations = requires_observations
        self.requires_projections = requires_projections
        self.alpha = alpha


class StatisticalEngine:
    """Generalized statistical testing engine for ML Lab.
    
    This engine provides configurable statistical tests for model validation,
    hypothesis testing, and uncertainty analysis. It removes domain-specific
    hardcodes from CeresPINN's validation.py and makes the tests applicable
    to any ML problem.
    """
    
    def __init__(self):
        """Initialize the statistical engine."""
        self._tests: Dict[str, StatisticalTest] = {}
        self._register_builtin_tests()
    
    def register_test(self, test: StatisticalTest) -> None:
        """Register a statistical test.
        
        Args:
            test: StatisticalTest to register
        """
        self._tests[test.name] = test
    
    def get_test(self, name: str) -> Optional[StatisticalTest]:
        """Get a test by name.
        
        Args:
            name: Name of the test
        
        Returns:
            StatisticalTest or None if not found
        """
        return self._tests.get(name)
    
    def get_tests_for_problem_type(self, problem_type: str) -> List[StatisticalTest]:
        """Get applicable tests for a problem type.
        
        Args:
            problem_type: Type of ML problem
        
        Returns:
            List of applicable StatisticalTests
        """
        return [
            test for test in self._tests.values()
            if problem_type in test.applicable_problem_types
        ]
    
    def run_test(
        self,
        test_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run a specific statistical test.
        
        Args:
            test_name: Name of the test to run
            **kwargs: Test-specific parameters
        
        Returns:
            Dictionary with test results
        """
        test = self.get_test(test_name)
        if test is None:
            raise ValueError(f"Test not found: {test_name}")
        
        return test.test_fn(alpha=test.alpha, **kwargs)
    
    def run_tests(
        self,
        test_names: List[str],
        **kwargs,
    ) -> Dict[str, Dict[str, Any]]:
        """Run multiple statistical tests.
        
        Args:
            test_names: Names of tests to run
            **kwargs: Test-specific parameters
        
        Returns:
            Dictionary mapping test names to results
        """
        results = {}
        for test_name in test_names:
            try:
                results[test_name] = self.run_test(test_name, **kwargs)
            except Exception as e:
                results[test_name] = {"error": str(e)}
        return results
    
    def _register_builtin_tests(self) -> None:
        """Register built-in statistical tests."""
        
        # KS Test - Distribution comparison
        def ks_test(alpha: float = 0.05, sample1: np.ndarray = None, sample2: np.ndarray = None, **kwargs) -> Dict[str, Any]:
            """Kolmogorov-Smirnov two-sample test."""
            if sample1 is None or sample2 is None:
                raise ValueError("KS test requires sample1 and sample2")
            
            stat, pvalue = stats.ks_2samp(sample1, sample2)
            return {
                "test": "Kolmogorov-Smirnov (two-sample)",
                "statistic": round(float(stat), 4),
                "p_value": round(float(pvalue), 5),
                "alpha": alpha,
                "null_hypothesis": "distributions are equal",
                "reject_null": bool(pvalue < alpha),
                "n_sample1": len(sample1),
                "n_sample2": len(sample2),
            }
        
        self.register_test(StatisticalTest(
            name="ks_test",
            description="Two-sample Kolmogorov-Smirnov test for distribution comparison",
            test_fn=ks_test,
            applicable_problem_types=["regression", "classification", "binary_classification", "multiclass_classification"],
            requires_observations=True,
            requires_projections=True,
        ))
        
        # Paired t-test - Mean comparison
        def paired_t_test(alpha: float = 0.05, sample1: np.ndarray = None, sample2: np.ndarray = None, **kwargs) -> Dict[str, Any]:
            """Paired t-test for comparing means."""
            if sample1 is None or sample2 is None:
                raise ValueError("Paired t-test requires sample1 and sample2")
            
            diffs = sample1 - sample2
            t_stat, p_value = stats.ttest_1samp(diffs, 0.0)
            mean_diff = float(np.mean(diffs))
            
            return {
                "test": "Paired t-test (one-sample on differences)",
                "statistic": round(float(t_stat), 4),
                "p_value": round(float(p_value), 5),
                "alpha": alpha,
                "significant": bool(p_value < alpha),
                "mean_difference": round(mean_diff, 4),
                "mean_sample1": round(float(np.mean(sample1)), 4),
                "mean_sample2": round(float(np.mean(sample2)), 4),
                "n_samples": len(sample1),
            }
        
        self.register_test(StatisticalTest(
            name="paired_t_test",
            description="Paired t-test for comparing paired sample means",
            test_fn=paired_t_test,
            applicable_problem_types=["regression", "classification"],
            requires_observations=True,
            requires_projections=True,
        ))
        
        # Independent t-test - Mean comparison
        def independent_t_test(alpha: float = 0.05, sample1: np.ndarray = None, sample2: np.ndarray = None, **kwargs) -> Dict[str, Any]:
            """Independent two-sample t-test."""
            if sample1 is None or sample2 is None:
                raise ValueError("Independent t-test requires sample1 and sample2")
            
            t_stat, p_value = stats.ttest_ind(sample1, sample2)
            
            return {
                "test": "Independent two-sample t-test",
                "statistic": round(float(t_stat), 4),
                "p_value": round(float(p_value), 5),
                "alpha": alpha,
                "significant": bool(p_value < alpha),
                "mean_sample1": round(float(np.mean(sample1)), 4),
                "mean_sample2": round(float(np.mean(sample2)), 4),
                "std_sample1": round(float(np.std(sample1)), 4),
                "std_sample2": round(float(np.std(sample2)), 4),
                "n_sample1": len(sample1),
                "n_sample2": len(sample2),
            }
        
        self.register_test(StatisticalTest(
            name="independent_t_test",
            description="Independent two-sample t-test for comparing means",
            test_fn=independent_t_test,
            applicable_problem_types=["regression", "classification"],
            requires_observations=True,
            requires_projections=True,
        ))
        
        # McNemar's test - Classification comparison
        def mcnemar_test(alpha: float = 0.05, y_true: np.ndarray = None, y_pred1: np.ndarray = None, y_pred2: np.ndarray = None, **kwargs) -> Dict[str, Any]:
            """McNemar's test for comparing classifier performance."""
            if y_true is None or y_pred1 is None or y_pred2 is None:
                raise ValueError("McNemar's test requires y_true, y_pred1, and y_pred2")
            
            # Build contingency table
            n00 = np.sum((y_pred1 == y_true) & (y_pred2 == y_true))
            n01 = np.sum((y_pred1 == y_true) & (y_pred2 != y_true))
            n10 = np.sum((y_pred1 != y_true) & (y_pred2 == y_true))
            n11 = np.sum((y_pred1 != y_true) & (y_pred2 != y_true))
            
            # McNemar's test statistic
            if n01 + n10 == 0:
                chi2 = 0.0
                p_value = 1.0
            else:
                chi2 = (abs(n01 - n10) - 1) ** 2 / (n01 + n10)
                p_value = 1 - stats.chi2.cdf(chi2, df=1)
            
            return {
                "test": "McNemar's test for classifier comparison",
                "statistic": round(float(chi2), 4),
                "p_value": round(float(p_value), 5),
                "alpha": alpha,
                "significant": bool(p_value < alpha),
                "contingency_table": {"n00": int(n00), "n01": int(n01), "n10": int(n10), "n11": int(n11)},
                "accuracy1": round(float(n00 + n01) / len(y_true), 4),
                "accuracy2": round(float(n00 + n10) / len(y_true), 4),
            }
        
        self.register_test(StatisticalTest(
            name="mcnemar_test",
            description="McNemar's test for comparing classifier performance",
            test_fn=mcnemar_test,
            applicable_problem_types=["binary_classification", "multiclass_classification"],
            requires_observations=True,
            requires_projections=True,
        ))
        
        # Cochran's Q test - Multiple classifier comparison
        def cochran_q_test(alpha: float = 0.05, y_true: np.ndarray = None, predictions: List[np.ndarray] = None, **kwargs) -> Dict[str, Any]:
            """Cochran's Q test for comparing multiple classifiers."""
            if y_true is None or predictions is None:
                raise ValueError("Cochran's Q test requires y_true and predictions")
            
            n = len(y_true)
            k = len(predictions)
            
            # Count successes per classifier
            successes = np.array([np.sum(pred == y_true) for pred in predictions])
            
            # Count successes per sample
            sample_successes = np.sum([pred == y_true for pred in predictions], axis=0)
            
            # Cochran's Q statistic
            total_successes = np.sum(successes)
            sum_sq_successes = np.sum(successes ** 2)
            
            if k == 1 or n == 0:
                q_stat = 0.0
                p_value = 1.0
            else:
                numerator = (k - 1) * (k * sum_sq_successes - total_successes ** 2)
                denominator = k * total_successes - np.sum(sample_successes ** 2)
                if denominator == 0:
                    q_stat = 0.0
                    p_value = 1.0
                else:
                    q_stat = numerator / denominator
                    p_value = 1 - stats.chi2.cdf(q_stat, df=k - 1)
            
            return {
                "test": "Cochran's Q test for multiple classifier comparison",
                "statistic": round(float(q_stat), 4),
                "p_value": round(float(p_value), 5),
                "alpha": alpha,
                "significant": bool(p_value < alpha),
                "n_classifiers": k,
                "n_samples": n,
                "accuracies": [round(float(s / n), 4) for s in successes],
            }
        
        self.register_test(StatisticalTest(
            name="cochran_q_test",
            description="Cochran's Q test for comparing multiple classifiers",
            test_fn=cochran_q_test,
            applicable_problem_types=["binary_classification", "multiclass_classification"],
            requires_observations=True,
            requires_projections=True,
        ))
        
        # Bootstrap confidence interval
        def bootstrap_ci(alpha: float = 0.05, sample: np.ndarray = None, n_bootstrap: int = 1000, seed: int = 42, **kwargs) -> Dict[str, Any]:
            """Bootstrap confidence interval for sample statistics."""
            if sample is None:
                raise ValueError("Bootstrap CI requires sample")
            
            rng = np.random.default_rng(seed)
            boot_means = np.empty(n_bootstrap)
            for i in range(n_bootstrap):
                idx = rng.integers(0, len(sample), size=len(sample))
                boot_means[i] = sample[idx].mean()
            
            ci_lower = (alpha / 2) * 100
            ci_upper = (1 - alpha / 2) * 100
            lo, hi = np.percentile(boot_means, [ci_lower, ci_upper])
            
            return {
                "test": "Bootstrap confidence interval",
                "mean": round(float(sample.mean()), 4),
                "std": round(float(sample.std()), 4),
                "ci_lower": round(float(lo), 4),
                "ci_upper": round(float(hi), 4),
                "confidence_level": round(1 - alpha, 2),
                "n_bootstrap": n_bootstrap,
                "n_samples": len(sample),
            }
        
        self.register_test(StatisticalTest(
            name="bootstrap_ci",
            description="Bootstrap confidence interval for sample statistics",
            test_fn=bootstrap_ci,
            applicable_problem_types=["regression", "classification", "binary_classification", "multiclass_classification"],
            requires_observations=True,
            requires_projections=False,
        ))
        
        # Wilcoxon signed-rank test
        def wilcoxon_test(alpha: float = 0.05, sample1: np.ndarray = None, sample2: np.ndarray = None, **kwargs) -> Dict[str, Any]:
            """Wilcoxon signed-rank test for paired samples."""
            if sample1 is None or sample2 is None:
                raise ValueError("Wilcoxon test requires sample1 and sample2")
            
            stat, p_value = stats.wilcoxon(sample1, sample2)
            
            return {
                "test": "Wilcoxon signed-rank test",
                "statistic": round(float(stat), 4),
                "p_value": round(float(p_value), 5),
                "alpha": alpha,
                "significant": bool(p_value < alpha),
                "mean_sample1": round(float(np.mean(sample1)), 4),
                "mean_sample2": round(float(np.mean(sample2)), 4),
                "n_samples": len(sample1),
            }
        
        self.register_test(StatisticalTest(
            name="wilcoxon_test",
            description="Wilcoxon signed-rank test for paired samples (non-parametric)",
            test_fn=wilcoxon_test,
            applicable_problem_types=["regression", "classification"],
            requires_observations=True,
            requires_projections=True,
        ))
        
        # Mann-Whitney U test
        def mann_whitney_test(alpha: float = 0.05, sample1: np.ndarray = None, sample2: np.ndarray = None, **kwargs) -> Dict[str, Any]:
            """Mann-Whitney U test for independent samples."""
            if sample1 is None or sample2 is None:
                raise ValueError("Mann-Whitney test requires sample1 and sample2")
            
            stat, p_value = stats.mannwhitneyu(sample1, sample2)
            
            return {
                "test": "Mann-Whitney U test (non-parametric)",
                "statistic": round(float(stat), 4),
                "p_value": round(float(p_value), 5),
                "alpha": alpha,
                "significant": bool(p_value < alpha),
                "mean_sample1": round(float(np.mean(sample1)), 4),
                "mean_sample2": round(float(np.mean(sample2)), 4),
                "n_sample1": len(sample1),
                "n_sample2": len(sample2),
            }
        
        self.register_test(StatisticalTest(
            name="mann_whitney_test",
            description="Mann-Whitney U test for independent samples (non-parametric)",
            test_fn=mann_whitney_test,
            applicable_problem_types=["regression", "classification"],
            requires_observations=True,
            requires_projections=True,
        ))
    
    def list_tests(self) -> List[str]:
        """List all registered test names."""
        return list(self._tests.keys())


# Global statistical engine instance
_engine = StatisticalEngine()


def get_statistical_engine() -> StatisticalEngine:
    """Get the global statistical engine instance."""
    return _engine
