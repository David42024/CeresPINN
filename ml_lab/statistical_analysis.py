"""Cluster-aware exploratory inference for county-year panels."""
from itertools import combinations
import numpy as np
import pandas as pd


def holm_adjust(p_values):
    p = np.asarray(p_values, dtype=float)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('Los valores p deben ser finitos y pertenecer a [0,1].')
    order = np.argsort(p)
    adjusted = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    result = np.empty_like(p)
    result[order] = adjusted
    return result.tolist()


def cluster_codes(frame):
    if not {'year', 'fips'}.issubset(frame.columns) or frame[['year', 'fips']].isna().any().any():
        raise ValueError('Se requieren year y fips completos para controlar ambas dependencias.')
    county = frame.fips.astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5)
    years, ny = pd.factorize(frame.year)
    counties, nc = pd.factorize(county)
    if len(ny) < 5 or len(nc) < 5:
        raise ValueError('Se requieren al menos cinco años y cinco condados para inferencia agrupada.')
    return years, counties, len(ny), len(nc)


def bootstrap_weights(codes, rng):
    years, counties, ny, nc = codes
    # Pigeonhole bootstrap: independently resample row and column clusters.
    yw = np.bincount(rng.integers(ny, size=ny), minlength=ny)
    cw = np.bincount(rng.integers(nc, size=nc), minlength=nc)
    return yw[years] * cw[counties]


def clustered_bootstrap(frame, statistic, replicates=500, seed=42):
    codes = cluster_codes(frame)
    rng = np.random.default_rng(seed)
    observed = np.atleast_1d(statistic(np.ones(len(frame))))
    if not np.isfinite(observed).all():
        raise ValueError('Estadístico no definido en la muestra original.')
    samples = []
    for _ in range(replicates):
        values = np.atleast_1d(statistic(bootstrap_weights(codes, rng)))
        if values.shape == observed.shape and np.isfinite(values).all():
            samples.append(values)
    if len(samples) < max(50, int(0.9 * replicates)):
        raise ValueError('Demasiadas réplicas degeneradas. Amplía los grupos o revisa los umbrales.')
    return observed, np.asarray(samples)


def inference(observed, samples, alpha=0.05):
    lower, upper = np.quantile(samples, [alpha / 2, 1 - alpha / 2])
    centered = samples - observed
    p = (1 + np.sum(np.abs(centered) >= abs(observed))) / (len(samples) + 1)
    return {'estimate': float(observed), 'ci_lower': float(lower), 'ci_upper': float(upper),
            'p_value': float(p), 'valid_replicates': len(samples)}


def difference_effect(y, groups, weights, left, right):
    means, variances, counts = [], [], []
    for group in [left, right]:
        mask = groups == group
        w, values = weights[mask], y[mask]
        n = w.sum()
        if n < 2:
            return [np.nan, np.nan]
        mean = np.average(values, weights=w)
        means.append(mean)
        variances.append(np.sum(w * (values - mean) ** 2) / (n - 1))
        counts.append(n)
    difference = means[0] - means[1]
    pooled = np.sqrt(sum((n - 1) * v for n, v in zip(counts, variances)) / (sum(counts) - 2))
    if pooled == 0:
        return [difference, np.nan]
    g = (1 - 3 / (4 * sum(counts) - 9)) * difference / pooled
    return [difference, g]


def fitted_ks_cluster_bootstrap(frame, replicates=500, seed=42):
    """KS calibrated under an additive Gaussian county/year random-effects null.

    Mean and scale are re-estimated in every simulated sample. This is an
    approximate model-based diagnostic, not the ordinary IID KS p-value.
    """
    from scipy import stats
    years, counties, ny, nc = cluster_codes(frame)
    y = frame.yield_kg_ha.to_numpy(dtype=float)
    centered = y - y.mean()
    county_effect = np.zeros(nc)
    year_effect = np.zeros(ny)
    for _ in range(10):
        county_effect = np.bincount(counties, weights=centered - year_effect[years], minlength=nc) / np.bincount(counties)
        year_effect = np.bincount(years, weights=centered - county_effect[counties], minlength=ny) / np.bincount(years)
    residual = centered - county_effect[counties] - year_effect[years]
    scales = [county_effect.std(ddof=1), year_effect.std(ddof=1), residual.std(ddof=1)]
    def statistic(values):
        scale = values.std(ddof=1)
        return float(stats.kstest(values, 'norm', args=(values.mean(), scale)).statistic) if scale > 0 else np.nan
    observed = statistic(y)
    rng = np.random.default_rng(seed)
    simulated = []
    for _ in range(replicates):
        sample = (rng.normal(0, scales[0], nc)[counties] + rng.normal(0, scales[1], ny)[years]
                  + rng.normal(0, scales[2], len(y)))
        simulated.append(statistic(sample))
    if not np.isfinite([observed] + simulated).all():
        raise ValueError('Normalidad no evaluable: muestra o simulaciones degeneradas.')
    return {'test': 'KS normalidad con calibración paramétrica agrupada', 'estimate': observed,
            'p_value': float((1 + np.sum(np.asarray(simulated) >= observed)) / (replicates + 1)),
            'null_model': 'Gaussian additive county/year random effects; plug-in variance estimates',
            'refit_mean_scale_each_replicate': True}


def panel_suite(df, threshold, percentiles=(33, 66), replicates=500, alpha=0.05):
    from scipy import stats
    columns = ['year', 'fips', 'yield_kg_ha', 'season_tmax_mean_c', 'season_precip_mm']
    if not set(columns).issubset(df.columns):
        raise ValueError('Faltan columnas necesarias del panel.')
    data = df[columns].copy()
    for c in columns:
        if c != 'fips':
            data[c] = pd.to_numeric(data[c], errors='coerce')
    data = data.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    cluster_codes(data)
    low, high = percentiles
    if not 0 < low < high < 100:
        raise ValueError('Los percentiles deben satisfacer 0 < inferior < superior < 100.')
    y = data.yield_kg_ha.to_numpy()
    heat = (data.season_tmax_mean_c.to_numpy() > threshold).astype(int)
    p_low, p_high = np.percentile(data.season_precip_mm, [low, high])
    rain = np.digitize(data.season_precip_mm.to_numpy(), [p_low, p_high], right=True)
    diagnostics = []
    for label, groups, n in [('Temperatura', heat, 2), ('Precipitación', rain, 3)]:
        for group in range(n):
            mask = groups == group
            sub = data[mask]
            if len(sub) < 5 or sub.year.nunique() < 3 or sub.fips.nunique() < 3:
                raise ValueError(f'{label}, grupo {group}: requiere ≥5 filas, ≥3 años y ≥3 condados.')
            diagnostics.append({'factor': label, 'group': group, 'rows': len(sub),
                                'years': sub.year.nunique(), 'counties': sub.fips.nunique()})
    results, bootstrap_rows = [], []
    for label, groups, pairs in [('Temperatura cálida menos fresca', heat, [(1, 0)]),
                                 ('Precipitación', rain, list(combinations(range(3), 2)))]:
        for left, right in pairs:
            observed, samples = clustered_bootstrap(data,
                lambda w: difference_effect(y, groups, w, left, right), replicates)
            result = inference(observed[0], samples[:, 0], alpha)
            effect = inference(observed[1], samples[:, 1], alpha)
            result.update(test=f'{label}: {left} menos {right}', effect_hedges_g=effect['estimate'],
                          effect_ci_lower=effect['ci_lower'], effect_ci_upper=effect['ci_upper'])
            results.append(result)
            bootstrap_rows.extend({'test': result['test'], 'difference_kg_ha': float(v)} for v in samples[:, 0])
    # Omnibus comparison uses the joint centered bootstrap of group contrasts.
    def contrasts(w):
        means = []
        for group in range(3):
            mask = rain == group
            if w[mask].sum() < 2:
                return [np.nan, np.nan]
            means.append(np.average(y[mask], weights=w[mask]))
        return [means[0] - means[2], means[1] - means[2]]
    observed, samples = clustered_bootstrap(data, contrasts, replicates)
    scale = samples.std(axis=0, ddof=1)
    if np.any(scale == 0):
        raise ValueError('Varianza de contrastes nula; prueba global no definida.')
    statistic = np.max(np.abs(observed / scale))
    simulated = np.max(np.abs((samples - observed) / scale), axis=1)
    results.append({'test': 'Comparación global de medias de precipitación (bootstrap agrupado)',
                    'estimate': float(statistic),
                    'p_value': float((1 + np.sum(simulated >= statistic)) / (len(simulated) + 1))})
    rain_samples = [y[rain == group] for group in range(3)]
    residuals = np.concatenate([values - values.mean() for values in rain_samples])
    levene = stats.levene(*rain_samples, center='median')
    shapiro = stats.shapiro(residuals[:5000])
    f_stat = stats.f_oneway(*rain_samples)
    thermal_t = stats.ttest_ind(y[heat == 1], y[heat == 0], equal_var=False)
    total_ss = np.sum((y - y.mean()) ** 2)
    eta2 = sum(len(v) * (v.mean() - y.mean()) ** 2 for v in rain_samples) / total_ss
    def eta_squared(w):
        if w.sum() < 2:
            return np.nan
        mean = np.average(y, weights=w)
        total = np.sum(w * (y - mean) ** 2)
        if total == 0:
            return np.nan
        between = 0.0
        for group in range(3):
            mask = rain == group
            if w[mask].sum() == 0:
                return np.nan
            between += w[mask].sum() * (np.average(y[mask], weights=w[mask]) - mean) ** 2
        return between / total
    _, eta_samples = clustered_bootstrap(data, eta_squared, replicates)
    eta_interval = np.quantile(eta_samples[:, 0], [alpha / 2, 1 - alpha / 2])
    normality = fitted_ks_cluster_bootstrap(data, replicates)
    results.append(normality)
    for variable in ['season_tmax_mean_c', 'season_precip_mm']:
        x = data[variable].to_numpy()
        for method in ['Pearson', 'Spearman']:
            def correlation(w):
                indices = np.repeat(np.arange(len(data)), w.astype(int))
                if len(indices) < 3 or np.std(x[indices]) == 0 or np.std(y[indices]) == 0:
                    return np.nan
                return (stats.pearsonr(x[indices], y[indices]).statistic if method == 'Pearson'
                        else stats.spearmanr(x[indices], y[indices]).statistic)
            observed, samples = clustered_bootstrap(data, correlation, replicates)
            row = inference(observed[0], samples[:, 0], alpha)
            row.update(test=f'{method}: {variable} frente a rendimiento', effect='correlation')
            results.append(row)
    adjusted = holm_adjust([r['p_value'] for r in results])
    for row, p in zip(results, adjusted):
        row.update(p_holm=p, reject=p < alpha)
    return {'results': results, 'bootstrap': bootstrap_rows, 'groups': diagnostics,
            'excluded_rows': len(df) - len(data), 'alpha': alpha, 'replicates': replicates,
            'dependence': 'two-way county/year pigeonhole bootstrap',
            'anova_diagnostics': {'levene_statistic': float(levene.statistic),
                'levene_p_iid_diagnostic_only': float(levene.pvalue),
                'shapiro_residual_p_iid_diagnostic_only': float(shapiro.pvalue),
                'shapiro_rows': min(len(residuals), 5000),
                'anova_F_descriptive_only': float(f_stat.statistic), 'eta_squared': float(eta2),
                'welch_t_temperature_descriptive_only': float(thermal_t.statistic),
                'eta_squared_ci_lower': float(eta_interval[0]), 'eta_squared_ci_upper': float(eta_interval[1]),
                'iid_independence_assumption': False,
                'classical_anova_inference_enabled': False},
            'rain_thresholds_mm': [float(p_low), float(p_high)], 'temperature_threshold': threshold}


def paired_model_tests(report, replicates=500, alpha=0.05):
    if 'test_counties' not in report:
        raise ValueError('El benchmark antiguo no contiene condados de prueba. Ejecuta nuevamente el benchmark.')
    frame = pd.DataFrame({'year': report['test_years'], 'fips': report['test_counties'],
                          'observed': report['test_observed']})
    results = []
    for left, right in combinations(report['test_predictions'], 2):
        a = np.asarray(report['test_predictions'][left], dtype=float)
        b = np.asarray(report['test_predictions'][right], dtype=float)
        if len(a) != len(frame) or len(b) != len(frame):
            raise ValueError('Las predicciones no corresponden a las mismas observaciones.')
        delta = np.abs(a - frame.observed.to_numpy()) - np.abs(b - frame.observed.to_numpy())
        if not np.isfinite(delta).all():
            raise ValueError('Errores no finitos en el benchmark.')
        observed, samples = clustered_bootstrap(frame, lambda w: np.average(delta, weights=w), replicates)
        row = inference(observed[0], samples[:, 0], alpha)
        deviation = delta.std(ddof=1)
        row.update(test=f'{left} menos {right}', paired_dz=float(delta.mean() / deviation) if deviation else None)
        if deviation > 0:
            def standardized(w):
                if w.sum() <= 1:
                    return np.nan
                mean = np.average(delta, weights=w)
                variance = np.sum(w * (delta - mean) ** 2) / (w.sum() - 1)
                return mean / np.sqrt(variance) if variance > 0 else np.nan
            try:
                _, standardized_samples = clustered_bootstrap(frame, standardized, replicates)
                interval = np.quantile(standardized_samples[:, 0], [alpha / 2, 1 - alpha / 2])
                row.update(paired_dz_ci_lower=float(interval[0]), paired_dz_ci_upper=float(interval[1]))
            except ValueError:
                row.update(paired_dz_ci_lower=None, paired_dz_ci_upper=None)
        results.append(row)
    adjusted = holm_adjust([r['p_value'] for r in results])
    for row, p in zip(results, adjusted):
        row.update(p_holm=p, reject=p < alpha)
    return results
