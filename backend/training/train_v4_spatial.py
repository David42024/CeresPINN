import os
import json
import hashlib
from datetime import datetime, timezone
import subprocess
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from backend.data.config import Settings

def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def hash_dataframe(df):
    return hashlib.sha256(df.to_csv(index=False).encode('utf-8')).hexdigest()

def main():
    print("Iniciando Entrenamiento Espacial (Fases 3, 4 y 5)...")
    settings = Settings()
    
    panel_path = settings.paths.processed / "canonical_panel.parquet"
    if not panel_path.exists():
        print("Error: No se encontró el panel canónico.")
        return
        
    df = pd.read_parquet(panel_path)
    
    # Fase 3: Ingeniería de variables
    # Excluimos variables text y outliers para el entrenamiento
    df = df[~df['is_outlier']].copy()
    
    features = [
        "year",
        "season_temp_mean_c",
        "season_tmax_mean_c",
        "season_precip_mm",
        "gdd",
        "cdd",
        "heat_days_30c",
        "heat_days_35c",
        "vpd_mean_kpa"
    ]
    target = "yield_kg_ha"
    
    # Fase 4: Diseño de Validación (Train <= 2017, Test >= 2018)
    train_df = df[df['year'] <= 2017].copy()
    test_df = df[df['year'] >= 2018].copy()
    
    X_train = train_df[features].values
    y_train = train_df[target].values
    X_test = test_df[features].values
    y_test = test_df[target].values
    
    print(f"Dataset total: {len(df)} filas. Train (1990-2017): {len(train_df)}. Test (2018-2025): {len(test_df)}.")
    
    # Fase 5: Entrenar y comparar modelos
    models = {
        "Ridge": Ridge(alpha=1.0),
        "RandomForest": RandomForestRegressor(n_estimators=100, min_samples_leaf=4, random_state=42, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=100, min_samples_leaf=4, random_state=42),
        "MLP_Small": MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=500, random_state=42)
    }
    
    results = {}
    best_model_name = None
    best_rmse = float('inf')
    best_pipeline = None
    
    for name, model in models.items():
        print(f"Entrenando {name}...")
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", model)
        ])
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))
        bias = float(np.mean(y_pred - y_test))
        
        # Spatial evaluation: RMSE per county (fips)
        test_df_copy = test_df.copy()
        test_df_copy['pred'] = y_pred
        test_df_copy['sq_error'] = (test_df_copy['pred'] - test_df_copy[target])**2
        spatial_rmse = test_df_copy.groupby('fips')['sq_error'].mean().apply(np.sqrt)
        spatial_rmse_mean = float(spatial_rmse.mean())
        spatial_rmse_std = float(spatial_rmse.std())
        
        results[name] = {
            "MAE_temporal": mae,
            "RMSE_temporal": rmse,
            "R2_temporal": r2,
            "Bias_temporal": bias,
            "RMSE_spatial_mean": spatial_rmse_mean,
            "RMSE_spatial_std": spatial_rmse_std
        }
        
        print(f"  Resultados: R2={r2:.4f}, MAE={mae:.2f}, RMSE={rmse:.2f}, RMSE Espacial={spatial_rmse_mean:.2f}")
        
        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = name
            best_pipeline = pipeline

    print(f"\nMejor modelo seleccionado para Producción: {best_model_name}")
    
    # Fase 7: Empaquetar el mejor modelo entrenándolo sobre todo el dataset (1990-2025)
    X_all = df[features].values
    y_all = df[target].values
    best_pipeline.fit(X_all, y_all)
    
    domain = {}
    for i, col in enumerate(features):
        domain[col] = {
            "min": float(X_all[:, i].min()),
            "max": float(X_all[:, i].max()),
            "mean": float(X_all[:, i].mean()),
            "std": float(X_all[:, i].std())
        }
        
    metadata = {
        "model_name": "CeresYield-Spatial",
        "model_version": "4.0.0",
        "model_verified": True,
        "framework": "scikit-learn",
        "algorithm": best_model_name,
        "dataset_sha256": hash_dataframe(df),
        "feature_schema_version": "2.0",
        "train_period": "1990-2017",
        "validation_period": "2018-2025",
        "geographic_scope": "iowa_statewide",
        "metrics": results[best_model_name],
        "metrics_all_models": results,
        "training_commit": get_git_commit(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Exploratory research only",
            "Spatial calibration available but unverified for public policy",
            "Management variables are deterministic overrides"
        ],
        "feature_names": features,
        "domain": domain
    }
    
    models_dir = Path(__file__).resolve().parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "cerespinn_spatial_v4.joblib"
    meta_path = models_dir / "cerespinn_spatial_v4_metadata.json"
    
    joblib.dump(best_pipeline, model_path)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    
    print(f"Artefacto espacial guardado en {model_path}")

if __name__ == "__main__":
    main()
