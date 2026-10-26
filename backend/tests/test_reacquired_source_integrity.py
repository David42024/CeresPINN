"""Source-drift permission must never hide unit errors or changed targets."""
import csv,hashlib,json,shutil
from pathlib import Path
import pytest
from scripts import verify_reacquired_county as audit

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture
def sources(tmp_path,monkeypatch):
    if not (ROOT/'data/reacquired/noaa-cag/acquisition_manifest.json').exists():
        pytest.skip('Research source bundle not installed')
    shutil.copytree(ROOT/'data/reacquired',tmp_path/'data/reacquired')
    shutil.copy2(ROOT/'data/cerespinn_county_audit.csv',tmp_path/'data/cerespinn_county_audit.csv')
    monkeypatch.setattr(audit,'ROOT',tmp_path)
    monkeypatch.setattr(audit,'RAW',tmp_path/'data/reacquired')
    monkeypatch.setattr(audit,'OUT',tmp_path/'results')
    return tmp_path


def test_disclosed_climate_drift_does_not_become_exact_fidelity(sources):
    result=audit.main(allow_source_drift=True,verbose=False)
    assert result['raw_file_integrity_verified'] and result['yield_numerical_fidelity_verified']
    assert result['climate_difference_years']==[2025]
    assert result['climate_exact_fidelity_verified'] is False
    assert result['verified'] is False
    with pytest.raises(RuntimeError,match='New climate source values differ'):
        audit.main(verbose=False)


def test_changed_noaa_units_are_rejected_even_with_matching_checksum(sources):
    p=sources/'data/reacquired/noaa-cag/acquisition_manifest.json';manifest=json.loads(p.read_text())
    rec=next(r for r in manifest['files'] if r['variable']=='tavg')
    raw=sources/rec['path'];body=json.loads(raw.read_text());body['description']['units']='Degrees Celsius'
    raw.write_text(json.dumps(body));rec['bytes']=raw.stat().st_size;rec['sha256']=hashlib.sha256(raw.read_bytes()).hexdigest()
    p.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='Wrong NOAA units'):
        audit.main(allow_source_drift=True,verbose=False)


def test_climate_drift_flag_cannot_accept_changed_yield(sources):
    p=sources/'data/reacquired/nass/acquisition_manifest.json';manifest=json.loads(p.read_text());raw=sources/manifest['path']
    with raw.open(newline='') as f:rows=list(csv.reader(f))
    headers=rows[0];code=headers.index('County ANSI');value=headers.index('Value')
    row=next(r for r in rows[1:] if r[code]);row[value]=str(float(row[value])+100)
    with raw.open('w',newline='') as f:csv.writer(f,quoting=csv.QUOTE_ALL).writerows(rows)
    manifest['bytes']=raw.stat().st_size;manifest['sha256']=hashlib.sha256(raw.read_bytes()).hexdigest();p.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError,match='cannot authorize a target change'):
        audit.main(allow_source_drift=True,verbose=False)
