"""Retrospective convergence sensitivity; does not select or deploy a model.

Repeat the fixed regional audit with the same folds, features and seeds, increasing
the iteration ceiling from 300 to 1000. Results already inspected remain the same
test set, so this is not a new independent validation or prospective selection.
"""
from pathlib import Path
import copy
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import audit_regional_neural_transfer as base

OUT = ROOT / 'docs/q1_artifacts/regional_convergence_20261026'
PROTOCOL = copy.deepcopy(base.PROTOCOL)
PROTOCOL['version'] = 2
PROTOCOL['training']['max_iter'] = 1000
PROTOCOL['comparison'] = 'Retrospective sensitivity to iteration ceiling; same folds, seeds, inputs and test years as the 300-iteration audit; no model selection.'
PROTOCOL['limitations'] += '; previously evaluated outcomes; convergence does not establish predictive validity or county calibration'


def main():
    old_out, old_protocol, old_mlp = base.OUT, base.PROTOCOL, base.mlp
    try:
        base.OUT, base.PROTOCOL = OUT, PROTOCOL
        def extended_mlp(seed):
            estimator = old_mlp(seed)
            estimator.set_params(regressor__mlpregressor__max_iter=1000)
            return estimator
        base.mlp = extended_mlp
        base.main()
    finally:
        base.OUT, base.PROTOCOL, base.mlp = old_out, old_protocol, old_mlp
    old = json.loads((old_out / 'metrics.json').read_text(encoding='utf-8'))
    new = json.loads((OUT / 'metrics.json').read_text(encoding='utf-8'))
    if old['input_sha256'] != new['input_sha256']:
        raise ValueError('The new experiment does not use the original input bytes')
    before = {x['model']: x for x in old['scores']}
    after = {x['model']: x for x in new['scores']}
    comparison = []
    for model in sorted(before):
        def count(metrics):
            return sum(item['convergence_warning'] for fold in metrics['folds']
                       for name, runs in fold['convergence'].items() if name == model for item in runs)
        comparison.append({'model': model, 'rmse_300': before[model]['rmse_kg_ha'],
                           'rmse_1000': after[model]['rmse_kg_ha'],
                           'warnings_300': count(old), 'warnings_1000': count(new)})
    (OUT/'comparison.json').write_text(json.dumps(comparison, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(comparison, indent=2))


if __name__ == '__main__':
    main()
