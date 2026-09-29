"""Finite observed targets and chronological partitions for model evaluation."""
import numpy as np
import pandas as pd


def observed_targets(df):
    target = pd.to_numeric(df['yield_kg_ha'], errors='coerce')
    valid = np.isfinite(target)
    result = df.loc[valid].copy()
    result['yield_kg_ha'] = target.loc[valid]
    return result, int((~valid).sum())


def temporal_partitions(df):
    data, removed = observed_targets(df)
    years = pd.to_numeric(data['year'], errors='coerce')
    valid = np.isfinite(years)
    removed += int((~valid).sum())
    data = data.loc[valid].copy()
    data['year'] = years.loc[valid]
    unique = sorted(data['year'].unique())
    if len(unique) < 3:
        raise ValueError('Se requieren al menos tres años con rendimientos observados.')
    n_test = max(1, int(np.ceil(len(unique) * 0.2)))
    n_val = max(1, int(np.ceil(len(unique) * 0.2)))
    n_train = len(unique) - n_test - n_val
    if n_train < 1:
        raise ValueError('No hay suficientes años de entrenamiento.')
    groups = [unique[:n_train], unique[n_train:n_train+n_val], unique[n_train+n_val:]]
    parts = [data[data.year.isin(group)].copy() for group in groups]
    if any(len(part) < 2 or part.yield_kg_ha.nunique() < 2 for part in parts):
        raise ValueError('Cada partición requiere al menos dos observaciones y variación de rendimiento para calcular R².')
    return parts, removed
