import json
from pathlib import Path
from typing import Dict, Any
from backend.inference import get_inference

def full_report() -> Dict[str, Any]:
    """Returns the true statistical report from the deployed model metadata."""
    inv = get_inference()
    if not inv.adapter.available:
        return {"error": "Active model not found"}
        
    meta = inv.adapter.metadata
    metrics = meta.get("metrics", meta.get("test_metrics", {}))
    
    # We map the real metrics to the format expected by the frontend where possible.
    # The frontend expects 'hindcast_metrics' (with r2, rmse)
    
    report = {
        "hindcast_metrics": {
            "r2": metrics.get("R2_temporal", metrics.get("r2")),
            "rmse": metrics.get("RMSE_temporal", metrics.get("rmse")),
            "mae": metrics.get("MAE_temporal", metrics.get("mae")),
            "bias": metrics.get("Bias_temporal", metrics.get("bias")),
        },
        "spatial_metrics": {
            "rmse_mean": metrics.get("RMSE_spatial_mean"),
            "rmse_std": metrics.get("RMSE_spatial_std"),
        },
        "t_test_results": {
            "status": "not_computed",
            "null_hypothesis": "The trained model maintains >15% yield loss under extreme climate.",
            "p_value": None,
            "t_statistic": None,
            "mean_difference_pct": None,
            "h1_supported": None,
        },
        "sobol_indices": {
            "status": "not_computed",
            "tmax": {"S1": None, "ST": None},
            "precip": {"S1": None, "ST": None},
            "cdd": {"S1": None, "ST": None}
        },
        "ensemble_uncertainty": {
            "status": "not_computed",
            "method": "Real prediction intervals from Scikit-Learn (Not downscaled GCM spread)",
            "scenarios": {}
        }
    }
    
    return report

def hindcast() -> Dict[str, Any]:
    return {"status": "deprecated, see full_report"}
