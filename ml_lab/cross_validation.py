"""Year-forward and county-disjoint folds, including nested model selection."""
import numpy as np
import pandas as pd
from ml_lab.training_data import observed_targets


def validation_folds(data, protocol, n_splits=3):
    if protocol == 'temporal':
        labels = pd.to_numeric(data.year, errors='raise').to_numpy()
        unique = np.sort(np.unique(labels))
        if len(unique) < n_splits + 1:
            raise ValueError(f'Se requieren al menos {n_splits + 1} años para este protocolo.')
        blocks = np.array_split(unique, n_splits + 1)
        folds = [(np.flatnonzero(np.isin(labels, np.concatenate(blocks[:i]))),
                  np.flatnonzero(np.isin(labels, blocks[i]))) for i in range(1, len(blocks))]
    elif protocol == 'spatial':
        if 'fips' not in data or data.fips.isna().any():
            raise ValueError('La validación espacial requiere claves FIPS completas.')
        labels = data.fips.astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5).to_numpy()
        unique = np.unique(labels)
        if len(unique) < n_splits:
            raise ValueError(f'Se requieren al menos {n_splits} condados.')
        folds = [(np.flatnonzero(~np.isin(labels, group)), np.flatnonzero(np.isin(labels, group)))
                 for group in np.array_split(unique, n_splits)]
    else:
        raise ValueError('Protocolo desconocido.')
    for train, test in folds:
        if len(train) < 2 or len(test) < 2 or data.iloc[test].yield_kg_ha.nunique() < 2:
            raise ValueError('Cada fold necesita al menos dos filas y variación del objetivo evaluado.')
    return folds


def fit_predict(train, test, features, algorithm, params):
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, VotingRegressor
    from sklearn.neural_network import MLPRegressor
    X = train[features].replace([np.inf, -np.inf], np.nan)
    Xt = test[features].replace([np.inf, -np.inf], np.nan)
    prep = Pipeline([('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
                     ('scale', StandardScaler())])
    y = train.yield_kg_ha.to_numpy()
    if algorithm == 'PyTorch':
        import torch
        from backend.training.pinn import CeresPINN, physics_loss
        from backend.training.config import TrainConfig
        torch.manual_seed(42)
        x = torch.tensor(prep.fit_transform(X), dtype=torch.float32)
        target_scale = StandardScaler()
        target = torch.tensor(target_scale.fit_transform(y.reshape(-1, 1)).ravel(), dtype=torch.float32)
        cfg = TrainConfig(feature_names=features, loss_physics_weight=params.get('physics_weight', 0.5))
        model = CeresPINN(cfg, len(features))
        optimizer = torch.optim.Adam(model.parameters(), lr=params.get('lr', 0.001))
        for _ in range(params.get('epochs', 100)):
            model.train()
            optimizer.zero_grad()
            pred, _ = model(x)
            loss = torch.nn.functional.mse_loss(pred, target) + physics_loss(model, x, cfg)
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            pred, _ = model(torch.tensor(prep.transform(Xt), dtype=torch.float32))
        return target_scale.inverse_transform(pred.numpy().reshape(-1, 1)).ravel()
    constructors = {
        'Ridge': lambda: Ridge(**params),
        'Random Forest': lambda: RandomForestRegressor(random_state=42, **params),
        'HistGradientBoosting': lambda: HistGradientBoostingRegressor(random_state=42, early_stopping=False, **params),
        'MLP': lambda: MLPRegressor(random_state=42, max_iter=600, early_stopping=False, **params),
        'Ensamble Ridge y MLP': lambda: VotingRegressor([('ridge', Ridge()),
            ('mlp', MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=600, random_state=42))]),
    }
    model = Pipeline([('prep', prep), ('model', constructors[algorithm]())])
    model.fit(X, y)
    return model.predict(Xt)


def run_cross_validation(df, protocol, nested=False, n_splits=3, epochs=100, progress=None):
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    data, excluded = observed_targets(df)
    year = pd.to_numeric(data.year, errors='coerce')
    valid = np.isfinite(year)
    excluded += int((~valid).sum())
    data = data.loc[valid].copy()
    data['year'] = year.loc[valid]
    if protocol == 'spatial':
        valid = data.fips.notna() if 'fips' in data else pd.Series(False, index=data.index)
        excluded += int((~valid).sum())
        data = data.loc[valid].copy()
    data = data.reset_index(drop=True)
    features = [f for f in ['year', 'season_temp_mean_c', 'season_tmax_mean_c',
        'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa'] if f in data]
    if not {'season_tmax_mean_c', 'season_precip_mm'}.issubset(features):
        raise ValueError('PyTorch requiere temperatura máxima y precipitación.')
    outer = validation_folds(data, protocol, n_splits)
    # Validate all inner splits before starting any expensive fits.
    inner = [validation_folds(data.iloc[tr].reset_index(drop=True), protocol, 2)
             for tr, _ in outer] if nested else None
    candidates = {
        'Ridge': [{'alpha': 0.1}, {'alpha': 10}],
        'Random Forest': [{'n_estimators': 100, 'max_depth': 10}, {'n_estimators': 100, 'max_depth': 20}],
        'HistGradientBoosting': [{'learning_rate': 0.05}, {'learning_rate': 0.1}],
        'MLP': [{'hidden_layer_sizes': (32, 16)}, {'hidden_layer_sizes': (64, 32)}],
        'Ensamble Ridge y MLP': [{}],
        'PyTorch': [{'epochs': epochs, 'physics_weight': 0.1}, {'epochs': epochs, 'physics_weight': 0.5}],
    }
    rows = []
    total = len(outer) * len(candidates)
    for fold, (tr, te) in enumerate(outer):
        training, testing = data.iloc[tr].reset_index(drop=True), data.iloc[te].reset_index(drop=True)
        for algorithm, options in candidates.items():
            if progress:
                progress(len(rows) / total, f'Fold externo {fold + 1}: {algorithm}')
            best = options[0]
            inner_score = None
            if nested:
                scored = []
                for option in options:
                    scores = []
                    for itr, ite in inner[fold]:
                        pred = fit_predict(training.iloc[itr], training.iloc[ite], features, algorithm, option)
                        scores.append(r2_score(training.iloc[ite].yield_kg_ha, pred))
                    scored.append((float(np.mean(scores)), option))
                if not all(np.isfinite(value) for value, _ in scored):
                    raise ValueError('Métricas internas no finitas; búsqueda interrumpida.')
                inner_score, best = max(scored, key=lambda entry: entry[0])
            pred = fit_predict(training, testing, features, algorithm, best)
            if not np.isfinite(pred).all():
                raise ValueError('Predicciones no finitas; evaluación interrumpida.')
            rows.append({'model': algorithm, 'fold': fold + 1, 'r2': float(r2_score(testing.yield_kg_ha, pred)),
                'rmse_kg_ha': float(np.sqrt(mean_squared_error(testing.yield_kg_ha, pred))),
                'mae_kg_ha': float(mean_absolute_error(testing.yield_kg_ha, pred)),
                'train_rows': len(training), 'test_rows': len(testing), 'selected_params': best,
                'inner_selection_r2': inner_score,
                'train_years': sorted(int(v) for v in training.year.unique()),
                'test_years': sorted(int(v) for v in testing.year.unique()),
                'train_counties': sorted(training.fips.astype(str).unique()) if 'fips' in training else [],
                'test_counties': sorted(testing.fips.astype(str).unique()) if 'fips' in testing else []})
    if progress:
        progress(1.0, 'Evaluación completa')
    return {'protocol': protocol, 'nested': nested, 'outer_folds': n_splits, 'inner_folds': 2 if nested else 0,
            'excluded_rows': excluded, 'features': features,
            'metric_name': f'R2_{protocol}_' + ('nested_cv' if nested else 'cv'), 'results': rows}
