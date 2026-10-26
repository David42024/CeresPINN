import json
import pytest
from scripts.audit_colorado_early_study import SOURCE, load_trial


def manifest():
    return json.loads((SOURCE/'acquisition_manifest.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize(('year','n_lai'), [(2008,0),(2009,5),(2010,16),(2011,24)])
def test_plot_coverage_and_recorded_grain_units(year,n_lai):
    rows,_=load_trial(year,manifest())
    assert len(rows)==24
    assert len({(r['treatment'],r['block']) for r in rows})==24
    assert sum(r['lai_max'] is not None for r in rows)==n_lai
    assert all(r['yield_dry_kg_ha']==pytest.approx(.845*r['yield_15_5pct_kg_ha']) for r in rows)
    assert all(r['source_sheet']=='Seasonal' and 26<=r['source_row']<=49 for r in rows)


def test_rejects_a_changed_source_hash_without_altering_the_workbook():
    source=manifest()
    record=next(row for row in source['files'] if row['name']=='LIRF Maize 2008 r1_0.xlsx')
    record['sha256']='0'*64
    with pytest.raises(ValueError,match='checksum mismatch'):
        load_trial(2008,source)
