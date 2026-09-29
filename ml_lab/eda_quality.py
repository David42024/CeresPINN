"""Dataset quality checks with thresholds fitted only on training years."""
import math
import numpy as np
import pandas as pd


def temporal_outlier_audit(df, train_fraction=0.8):
    if not {'year', 'yield_kg_ha'}.issubset(df.columns):
        raise ValueError('Se requieren las columnas year y yield_kg_ha.')
    years = pd.to_numeric(df['year'], errors='coerce')
    unique_years = sorted(years.dropna().unique())
    if len(unique_years) < 2:
        raise ValueError('Se requieren al menos dos años para separar entrenamiento y evaluación.')
    count = min(len(unique_years) - 1, max(1, math.floor(len(unique_years) * train_fraction)))
    train = years.isin(unique_years[:count])
    evaluation = years.isin(unique_years[count:])
    target = pd.to_numeric(df['yield_kg_ha'], errors='coerce')
    values = target[train].replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 2:
        raise ValueError('Se requieren al menos dos rendimientos finitos en entrenamiento.')
    mean, std = float(values.mean()), float(values.std())
    finite = pd.Series(np.isfinite(target), index=df.index)
    outlier = finite & ((target < mean - 3 * std) | (target > mean + 3 * std))
    invalid = ~finite | years.isna()
    return {'train': train, 'evaluation': evaluation, 'outlier': outlier,
            'invalid': invalid, 'remove': train & outlier,
            'mean': mean, 'std': std, 'lower': mean - 3 * std,
            'upper': mean + 3 * std, 'train_years': unique_years[:count],
            'evaluation_years': unique_years[count:]}
