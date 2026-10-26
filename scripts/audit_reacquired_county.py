"""Quantify source-version differences without changing the frozen benchmark."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.revision_scientific_audit import county
from scripts.verify_reacquired_county import main as verify_sources
OUT=ROOT/'docs/q1_artifacts/reacquired_20261026'


def main():
    fidelity=verify_sources(allow_source_drift=True,verbose=False)
    if fidelity['unmatched_county_years'] or fidelity['variables']['yield_kg_ha']['rows_within_tolerance']!=3460:
        raise ValueError('Unresolved source coverage or target discrepancy')
    # Climate differences are the subject of this audit, not silently corrected.
    source=ROOT/'data/reacquired/cerespinn_county_rebuilt.csv'
    result=county(source,OUT,'Rebuilt from a newly downloaded full USDA CSV and 297 complete NOAA JSON responses; raw hashes verified; climate differences from frozen table disclosed')
    before=json.loads((ROOT/'docs/q1_artifacts/revision_20261026/audit.json').read_text())['county']
    orig={v['model']:v for v in before['scores']}
    for v in result['scores']:v['rmse_difference_from_frozen_kg_ha']=v['rmse_kg_ha']-orig[v['model']]['rmse_kg_ha']
    result.update(source_csv_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  original_checkpoint_unchanged=True,original_frozen_csv_unchanged=True,
                  interpretation='Retrospective source-version robustness check, not a pristine independent validation or test-driven model selection')
    (OUT/'reacquired_county_benchmark.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({'input_rows':result['input_rows'],'counties':result['counties'],
                      'test_county_years':result['test_county_years'],'scores':result['scores']},indent=2))


if __name__=='__main__':main()
