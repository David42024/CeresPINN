import numpy as np
import pandas as pd
from ml_lab.training_data import observed_targets, temporal_partitions


def test_missing_targets_are_excluded_and_real_zero_is_preserved():
    df = pd.DataFrame({'year': [2000] * 5, 'yield_kg_ha': [np.nan, np.inf, 'invalid', 0, 100]})
    clean, excluded = observed_targets(df)
    assert excluded == 3
    assert list(clean.yield_kg_ha) == [0, 100]


def test_year_partitions_are_disjoint_and_chronological():
    df = pd.DataFrame({'year': np.repeat(np.arange(2000, 2010), 2),
                       'yield_kg_ha': np.tile([100, 200], 10)})
    parts, excluded = temporal_partitions(df)
    assert excluded == 0
    assert sum(map(len, parts)) == len(df)
    assert parts[0].year.max() < parts[1].year.min()
    assert parts[1].year.max() < parts[2].year.min()
    assert not (set(parts[0].index) & set(parts[2].index))
    assert not (set(parts[1].index) & set(parts[2].index))


def test_held_out_values_do_not_change_training_data():
    df = pd.DataFrame({'year': np.repeat(np.arange(2000, 2010), 2),
                       'yield_kg_ha': np.tile([100, 200], 10)})
    before, _ = temporal_partitions(df)
    df.loc[df.year >= 2006, 'yield_kg_ha'] *= 1000
    after, _ = temporal_partitions(df)
    pd.testing.assert_frame_equal(before[0], after[0])


def test_insufficient_years_are_rejected():
    df = pd.DataFrame({'year': [2000, 2001], 'yield_kg_ha': [100, 200]})
    try:
        temporal_partitions(df)
    except ValueError:
        return
    raise AssertionError('An independent three-way split must require three years.')
