import numpy as np
import pandas as pd
from ml_lab.cross_validation import validation_folds


def panel():
    return pd.DataFrame([{'year': year, 'fips': str(county), 'yield_kg_ha': 100 + year + county}
                         for year in range(2000, 2012) for county in range(8)])


def test_temporal_folds_only_evaluate_future_years():
    data = panel()
    for train, test in validation_folds(data, 'temporal', 3):
        assert data.iloc[train].year.max() < data.iloc[test].year.min()
        assert not set(train) & set(test)


def test_spatial_folds_hold_out_whole_counties():
    data = panel()
    covered = []
    for train, test in validation_folds(data, 'spatial', 3):
        assert not set(data.iloc[train].fips) & set(data.iloc[test].fips)
        covered.extend(test)
    assert sorted(covered) == list(range(len(data)))


def test_inner_folds_never_include_outer_test_rows():
    data = panel()
    for protocol in ['temporal', 'spatial']:
        for outer_train, outer_test in validation_folds(data, protocol, 3):
            training = data.iloc[outer_train].reset_index(drop=True)
            for inner_train, inner_test in validation_folds(training, protocol, 2):
                assert not set(outer_train[inner_train]) & set(outer_test)
                assert not set(outer_train[inner_test]) & set(outer_test)


def test_spatial_normalizes_fips_aliases():
    data = panel()
    data.loc[data.index[::2], 'fips'] = data.loc[data.index[::2], 'fips'].map(lambda v: v + '.0')
    for train, test in validation_folds(data, 'spatial', 3):
        normalize = lambda series: set(series.str.replace(r'\.0$', '', regex=True).str.zfill(5))
        assert not normalize(data.iloc[train].fips) & normalize(data.iloc[test].fips)
