"""Audit compatibility and source-level coverage of the USDA 2008–2011 trials.

This is a retrospective data-quality inventory, not an estimated treatment
effect or a validation of the deployed predictor. Preserve the original books.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import re

import openpyxl

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/external/colorado_irrigation_2008_2011'
OUT=ROOT/'docs/q1_artifacts/colorado_early_comparability_20261026'
TARGETS={1:100,2:85,3:75,4:70,5:55,6:40}


def valid_number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def load_trial(year,manifest):
    name=f'LIRF Maize {year} r1_0.xlsx'
    source=next(row for row in manifest['files'] if row['name']==name)
    path=SOURCE/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
        raise ValueError(f'Source workbook checksum mismatch: {name}')
    wb=openpyxl.load_workbook(path,read_only=True,data_only=True)
    try:
        sheet=wb['Seasonal']
        header=[cell.value for cell in sheet[25]][:9]
        if header[:3]!=['Tmnt','Block','Plot']:
            raise ValueError(f'Unexpected source layout: {name} row 25')
        records=[]
        for rowno,row in enumerate(sheet.iter_rows(min_row=26,max_row=49,values_only=True),26):
            treatment,block,plot,_,lai,biomass,hi,yield_standard,yield_dry=row[:9]
            if treatment not in TARGETS or block not in (1,2,3,4):
                raise ValueError(f'Invalid treatment or block in {name} row {rowno}')
            if not isinstance(plot,str) or not re.fullmatch(r'[ABCD][1-4][1-6]',plot) or int(plot[1])!=block:
                raise ValueError(f'Invalid plot/block identity in {name} row {rowno}')
            if not all(valid_number(v) for v in (biomass,hi,yield_standard,yield_dry)):
                raise ValueError(f'Missing required crop measurement in {name} row {rowno}')
            records.append({'year':year,'treatment':int(treatment),'target_percent_of_full':TARGETS[treatment],
                'block':int(block),'plot':plot,'lai_max':float(lai) if valid_number(lai) else None,
                'biomass_dry_kg_ha':float(biomass),'harvest_index':float(hi),
                'yield_15_5pct_kg_ha':float(yield_standard),'yield_dry_kg_ha':float(yield_dry),
                'source_file':name,'source_sheet':'Seasonal','source_row':rowno})
        if len({(r['treatment'],r['block']) for r in records})!=24:
            raise ValueError(f'Incomplete treatment/block combinations in {name}')
        if len({r['plot'] for r in records})!=24:
            raise ValueError(f'Duplicate plot identifiers in {name}')
        return records,source
    finally:
        wb.close()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((SOURCE/'acquisition_manifest.json').read_text(encoding='utf-8'))
    all_records=[];coverage=[];source_hashes=[]
    for year in range(2008,2012):
        records,source=load_trial(year,manifest);all_records.extend(records)
        source_hashes.append({'file':source['name'],'sha256':source['sha256']})
        mismatch=max(abs(r['yield_dry_kg_ha']-.845*r['yield_15_5pct_kg_ha']) for r in records)
        coverage.append({'year':year,'plot_years':len(records),'treatments':6,'blocks':4,
            'lai_observed':sum(r['lai_max'] is not None for r in records),
            'biomass_observed':len(records),'yield_observed':len(records),
            'dry_yield_conversion_max_abs_difference_kg_ha':mismatch})
    output=OUT/'plot_inventory.csv'
    with output.open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(all_records[0]));writer.writeheader();writer.writerows(all_records)
    result={'study_doi':manifest['doi'],'metadata_and_source_review':'retrospective; no treatment effects fitted',
        'target_percent':TARGETS,'coverage':coverage,'source_workbooks':source_hashes,
        'source_methodology_sha256':next(x['sha256'] for x in manifest['files'] if x['name']=='LIRF Methodology r1.pdf'),
        'yield_unit':'kg/ha at 15.5% grain moisture and kg/ha dry mass, separate columns',
        'compatibility':'common site, randomized-block design and yield units; treatment definitions differ, no automatic code or percentage mapping',
        'limitations':'one research site; four years; 2011 nitrogen differs for some treatments; observed LAI missing by design; 2012–2013 stage-specific treatments differ',
        'total_plot_years':len(all_records),'inventory_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    (OUT/'inventory.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'coverage':coverage,'total_plot_years':len(all_records)},indent=2))


if __name__=='__main__':main()
