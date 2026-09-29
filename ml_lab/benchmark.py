"""Run all candidates on one chronological train/validation/test partition."""
import hashlib
import numpy as np
from ml_lab.training_data import temporal_partitions


def rank_candidates(rows):
    valid = [row for row in rows if np.isfinite(row['validation_r2']) and
             np.isfinite(row['validation_rmse_kg_ha'])]
    return sorted(valid, key=lambda r: (-r['validation_r2'], r['validation_rmse_kg_ha'], r['model']))


def run_benchmark(df, epochs=300, physics_weight=0.5, progress=None):
    import pandas as pd
    import torch
    from datetime import datetime, timezone
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge
    from sklearn.neural_network import MLPRegressor
    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, StackingRegressor
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    from backend.training.config import TrainConfig
    from backend.training.pinn import CeresPINN, physics_loss

    parts, excluded = temporal_partitions(df)
    features = [name for name in ['year', 'season_temp_mean_c', 'season_tmax_mean_c',
        'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa'] if name in df.columns]
    if not {'season_tmax_mean_c', 'season_precip_mm'}.issubset(features):
        raise ValueError('Se requieren temperatura máxima y precipitación para comparar la red regularizada.')
    X = [p[features].replace([np.inf, -np.inf], np.nan) for p in parts]
    y = [p.yield_kg_ha.to_numpy() for p in parts]
    if len(y[0]) < 5:
        raise ValueError('El ensamble requiere al menos cinco observaciones de entrenamiento.')

    def pipeline(model):
        return Pipeline([('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
                         ('scaler', StandardScaler()), ('model', model)])

    mlp = lambda: MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=600, random_state=42)
    candidates = {
        'Ridge': pipeline(Ridge(alpha=1)),
        'Random Forest': pipeline(RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)),
        'HistGradientBoosting': pipeline(HistGradientBoostingRegressor(random_state=42)),
        'MLP': pipeline(mlp()),
        'Ensamble Ridge y MLP': StackingRegressor(
            estimators=[('ridge', pipeline(Ridge())), ('mlp', pipeline(mlp()))],
            final_estimator=Ridge(), cv=5),
    }
    rows, predictions = [], {}
    # Select using common validation only. Test cannot affect model choice.
    for number, (name, model) in enumerate(candidates.items()):
        if progress:
            progress(number / 6, f'Entrenando {name}')
        model.fit(X[0], y[0])
        pred = model.predict(X[1])
        rows.append({'model': name, 'validation_r2': float(r2_score(y[1], pred)),
                     'validation_rmse_kg_ha': float(np.sqrt(mean_squared_error(y[1], pred)))})
    if progress:
        progress(5 / 6, 'Entrenando CeresPINN PyTorch')
    preprocessing = Pipeline([('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
                              ('scaler', StandardScaler())])
    train_x = preprocessing.fit_transform(X[0])
    target_scaler = StandardScaler()
    train_y = target_scaler.fit_transform(y[0].reshape(-1, 1)).ravel()
    xt = torch.tensor(train_x, dtype=torch.float32)
    yt = torch.tensor(train_y, dtype=torch.float32)
    torch.manual_seed(42)
    cfg = TrainConfig(feature_names=features, loss_physics_weight=physics_weight)
    network = CeresPINN(cfg, len(features))
    optimizer = torch.optim.Adam(network.parameters(), lr=0.001, weight_decay=1e-5)
    for epoch in range(epochs):
        network.train()
        optimizer.zero_grad()
        pred, _ = network(xt)
        loss = torch.nn.functional.mse_loss(pred, yt) + physics_loss(network, xt, cfg)
        loss.backward()
        optimizer.step()
        if progress and (epoch + 1) % 10 == 0:
            progress((5 + (epoch + 1) / epochs) / 6,
                     f'Entrenando CeresPINN PyTorch: época {epoch + 1}/{epochs}')
    network.eval()

    def neural_predict(frame):
        with torch.no_grad():
            values, _ = network(torch.tensor(preprocessing.transform(frame), dtype=torch.float32))
        return target_scaler.inverse_transform(values.numpy().reshape(-1, 1)).ravel()

    neural_name = 'CeresPINN PyTorch'
    pred = neural_predict(X[1])
    rows.append({'model': neural_name, 'validation_r2': float(r2_score(y[1], pred)),
                 'validation_rmse_kg_ha': float(np.sqrt(mean_squared_error(y[1], pred)))})
    ranking = rank_candidates(rows)
    if len(ranking) != 6:
        raise ValueError('La ejecución produjo métricas no finitas; no se publicará un ranking parcial.')
    winner = ranking[0]['model']
    for row in rows:
        name = row['model']
        pred = neural_predict(X[2]) if name == neural_name else candidates[name].predict(X[2])
        if not np.isfinite(pred).all():
            raise ValueError(f'Predicciones no finitas en prueba: {name}')
        row.update(test_r2=float(r2_score(y[2], pred)),
                   test_rmse_kg_ha=float(np.sqrt(mean_squared_error(y[2], pred))),
                   test_mae_kg_ha=float(mean_absolute_error(y[2], pred)), test_rows=len(y[2]))
        predictions[name] = [float(value) for value in pred]
    fingerprint = hashlib.sha256(pd.util.hash_pandas_object(
        df[features + ['yield_kg_ha']], index=True).values.tobytes()).hexdigest()
    if progress:
        progress(1.0, 'Benchmark completo')
    return {'created_at': datetime.now(timezone.utc).isoformat(), 'dataset_sha256': fingerprint,
            'protocol': 'chronological_train_validation_test', 'selection': 'validation_r2_then_rmse',
            'winner': winner, 'features': features, 'excluded_rows': excluded,
            'configuration': {'seed': 42, 'pytorch_epochs': epochs, 'physics_weight': physics_weight},
            'partitions': {name: {'years': sorted(int(v) for v in part.year.unique()), 'rows': len(part)}
                           for name, part in zip(['train', 'validation', 'test'], parts)},
            'results': rows, 'test_observed': [float(v) for v in y[2]],
            'test_years': [int(v) for v in parts[2].year],
            'test_counties': parts[2].fips.astype(str).tolist() if 'fips' in parts[2] else [None] * len(y[2]),
            'test_predictions': predictions}
