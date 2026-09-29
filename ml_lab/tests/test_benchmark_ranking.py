from ml_lab.benchmark import rank_candidates


def test_selection_ignores_test_scores():
    rows = [{'model': 'A', 'validation_r2': 0.8, 'validation_rmse_kg_ha': 100, 'test_r2': -10},
            {'model': 'B', 'validation_r2': 0.7, 'validation_rmse_kg_ha': 110, 'test_r2': 0.99}]
    assert rank_candidates(rows)[0]['model'] == 'A'


def test_tie_break_and_negative_r2():
    rows = [{'model': 'A', 'validation_r2': -0.2, 'validation_rmse_kg_ha': 200},
            {'model': 'B', 'validation_r2': -0.2, 'validation_rmse_kg_ha': 100}]
    assert rank_candidates(rows)[0]['model'] == 'B'


def test_nonfinite_metrics_are_excluded():
    assert rank_candidates([{'model': 'A', 'validation_r2': float('nan'),
                             'validation_rmse_kg_ha': 100}]) == []
