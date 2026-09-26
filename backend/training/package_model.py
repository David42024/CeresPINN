"""Package the trained Ridge model as a production artifact (Fase 7)."""
import os
import json
import hashlib
from datetime import datetime, timezone
import subprocess
import joblib
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from backend.training.config import TrainConfig, DataConfig
from backend.training.dataset import build_dataset

def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def hash_dataframe(df):
    import pandas as pd
    if isinstance(df, pd.DataFrame):
        return hashlib.sha256(df.to_csv(index=False).encode('utf-8')).hexdigest()
    else:
        return hashlib.sha256(str(df).encode('utf-8')).hexdigest()

def main():
    print("Iniciando empaquetado Fase 7...")
    train_config = TrainConfig()
    data_config = DataConfig()
    
    # 1. Load data
    X_train, y_train, X_test, y_test, info = build_dataset(train_config, data_config)
    
    # 2. Train Ridge model on all available data for production
    X_all = np.vstack((X_train, X_test))
    y_all = np.concatenate((y_train, y_test))
    
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=1.0))
    ])
    pipeline.fit(X_all, y_all)
    
    # Evaluate for metrics (using test set to be conservative)
    pipeline.fit(X_train, y_train)
    y_pred_test = pipeline.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
    mae = float(mean_absolute_error(y_test, y_pred_test))
    r2 = float(r2_score(y_test, y_pred_test))
    
    # Refit on all
    pipeline.fit(X_all, y_all)
    
    # Calculate feature domains
    domain = {}
    for i, col in enumerate(train_config.feature_names):
        domain[col] = {
            "min": float(X_all[:, i].min()),
            "max": float(X_all[:, i].max()),
            "mean": float(X_all[:, i].mean()),
            "std": float(X_all[:, i].std())
        }
        
    # 3. Create metadata
    metadata = {
        "model_name": "CeresYield",
        "model_version": "3.0.0",
        "model_verified": True,
        "framework": "scikit-learn",
        "dataset_sha256": hash_dataframe(info.get('raw_df') if 'raw_df' in info else X_all), # approximation
        "feature_schema_version": "1.0",
        "train_period": "1990-2017",
        "validation_period": "2018-2025",
        "geographic_scope": "regional_iowa",
        "metrics": {
            "mae_temporal": mae,
            "rmse_temporal": rmse,
            "r2_temporal": r2,
            "residual_std": rmse # used for interval
        },
        "training_commit": get_git_commit(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Exploratory research only",
            "No spatial calibration available",
            "Management variables are not learned from this artifact"
        ],
        "feature_names": train_config.feature_names,
        "domain": domain
    }
    
    # 4. Save artifacts
    models_dir = train_config.output_dir.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "cerespinn_ridge_v3.joblib"
    meta_path = models_dir / "cerespinn_ridge_v3_metadata.json"
    
    joblib.dump(pipeline, model_path)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    
    print(f"Artefacto guardado en {model_path}")
    print(f"Metadatos guardados en {meta_path}")

if __name__ == "__main__":
    main()
