import pandas as pd
import numpy as np
from ml_lab.eda_quality import temporal_outlier_audit


def test_evaluation_values_do_not_change_training_thresholds():
    df = pd.DataFrame({'year': list(range(2000, 2010)),
                       'yield_kg_ha': [100, 110, 90, 100, 105, 95, 110, 90, 100, 100]})
    original = temporal_outlier_audit(df)
    df.loc[df.year >= 2008, 'yield_kg_ha'] = [1000000000, -1000000000]
    changed = temporal_outlier_audit(df)
    assert original['lower'] == changed['lower']
    assert original['upper'] == changed['upper']
    assert not changed['remove'][changed['evaluation']].any()
    assert changed['outlier'][changed['evaluation']].all()


def test_only_training_outliers_are_removed_and_missing_values_are_flagged():
    df = pd.DataFrame({'year': [2000] * 21 + [2001, 2002],
                       'yield_kg_ha': [100] * 20 + [10000, 1e9, np.nan]})
    audit = temporal_outlier_audit(df)
    assert int(audit['remove'].sum()) == 1
    assert not audit['remove'][audit['evaluation']].any()
    assert audit['invalid'].iloc[-1]


def test_constant_training_data_has_finite_thresholds():
    df = pd.DataFrame({'year': [2000, 2000, 2001], 'yield_kg_ha': [100, 100, 200]})
    audit = temporal_outlier_audit(df)
    assert audit['lower'] == audit['upper'] == 100
    assert not audit['remove'].any()
