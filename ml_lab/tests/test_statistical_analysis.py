import numpy as np
import pandas as pd
from ml_lab.statistical_analysis import (
    holm_adjust, cluster_codes, bootstrap_weights, clustered_bootstrap, inference, difference_effect)


def test_holm_controls_family_and_preserves_order():
    assert np.allclose(holm_adjust([0.04, 0.001, 0.02]), [0.04, 0.003, 0.04])
    assert holm_adjust([1.0, 1.0]) == [1.0, 1.0]


def test_bootstrap_preserves_crossed_clusters():
    frame = pd.DataFrame([{'year': year, 'fips': str(county)}
                          for year in range(5) for county in range(5)])
    weights = bootstrap_weights(cluster_codes(frame), np.random.default_rng(42)).reshape(5, 5)
    assert np.linalg.matrix_rank(weights) <= 1
    assert weights.sum() == 25


def test_cluster_bootstrap_reproducible():
    frame = pd.DataFrame([{'year': year, 'fips': str(county)}
                          for year in range(5) for county in range(5)])
    values = np.arange(len(frame))
    a, samples_a = clustered_bootstrap(frame, lambda w: np.average(values, weights=w), 100)
    b, samples_b = clustered_bootstrap(frame, lambda w: np.average(values, weights=w), 100)
    assert np.array_equal(samples_a, samples_b)
    assert a[0] == b[0] == values.mean()


def test_identical_paired_errors_have_zero_interval_and_p_one():
    result = inference(0, np.zeros(100))
    assert result['ci_lower'] == result['ci_upper'] == 0
    assert result['p_value'] == 1


def test_effect_sign_and_difference():
    values = np.array([1., 2., 3., 11., 12., 13.])
    groups = np.array([0, 0, 0, 1, 1, 1])
    delta, g = difference_effect(values, groups, np.ones(6), 1, 0)
    assert delta == 10
    assert g > 0


def test_insufficient_clusters_are_rejected():
    frame = pd.DataFrame({'year': [2000] * 10, 'fips': list(range(10))})
    try:
        cluster_codes(frame)
    except ValueError:
        return
    raise AssertionError('Insufficient clusters must prevent inference.')
