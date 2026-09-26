"""Training pipeline for Ruta A (regional, no SSP replication)."""
import os
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.neural_network import MLPRegressor

from backend.training.config import TrainConfig, DataConfig
from backend.training.dataset import build_dataset

def main():
    print("Iniciando entrenamiento Ruta A (Fase 5)...")
    train_config = TrainConfig()
    data_config = DataConfig()
    
    X_train, y_train, X_test, y_test, info = build_dataset(train_config, data_config)
    
    print(f"Dataset cargado: {info.get('n_rows')} filas totales (Ruta A sin replicación).")
    print(f"Train: {len(X_train)} filas, Test: {len(X_test)} filas.")
    
    models = {
        "Ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0))
        ]),
        "RandomForest": RandomForestRegressor(
            n_estimators=100, max_depth=5, min_samples_leaf=2, random_state=train_config.seed
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=100, max_depth=5, min_samples_leaf=2, random_state=train_config.seed
        ),
        "MLP_Small": Pipeline([
            ("scaler", StandardScaler()),
            ("model", MLPRegressor(
                hidden_layer_sizes=(32, 16), activation='relu',
                max_iter=500, alpha=0.01, random_state=train_config.seed
            ))
        ])
    }
    
    results = []
    
    for name, model in models.items():
        print(f"\\nEntrenando {name}...")
        model.fit(X_train, y_train)
        
        y_pred_test = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
        r2 = r2_score(y_test, y_pred_test)
        bias = float(np.mean(y_pred_test - y_test))
        
        print(f"Resultados {name}: MAE={mae:.2f}, RMSE={rmse:.2f}, R2={r2:.4f}, Sesgo={bias:.2f}")
        
        results.append({
            "model_name": name,
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "bias": bias
        })
        
    # Save comparison to an artifact
    output_dir = train_config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = output_dir / "ruta_a_model_comparison.json"
    
    comparison_path.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_info": info,
        "results": results
    }, indent=2), encoding="utf-8")
    
    print(f"\\nComparación guardada en {comparison_path}")

if __name__ == "__main__":
    main()
