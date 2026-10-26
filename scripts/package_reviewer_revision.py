"""Package only the scientific revision, with explicit provenance and checksums."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'deliverables/revision_20261026'
REV=ROOT/'docs/q1_artifacts/revision_20261026'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit_path=REV/'audit.json';a=json.loads(audit_path.read_text())
    # Record hashes after the final non-numerical source cleanup, without
    # replacing numerical results or claiming an unperformed retraining run.
    for entry in a['inputs']:
        entry['sha256']=hashlib.sha256((ROOT/entry['path']).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    audit_path.write_text(json.dumps(a,indent=2,allow_nan=False),encoding='utf-8')
    revision_scripts=['revision_scientific_audit.py','revision_figures.py','build_revised_article.py',
        'generate_q1_revision_artifacts.py','generate_q1_extended_audit.py','run_temporal_validation.py',
        'reproduce.py','package_reviewer_revision.py','render_revision_word.ps1',
        'revision_reference_audit.py','write_revision_reference_ledger.py',
        'acquire_bushland_data.py','prepare_bushland_data.py','validate_bushland_coupling.py','verify_bushland_sources.py',
        'reacquire_county_climate.py','verify_reacquired_county.py','audit_reacquired_county.py','audit_geographic_districts.py',
        'package_public_research.py']
    files=[ROOT/'LICENSE',ROOT/'README.md',ROOT/'requirements-repro.txt',ROOT/'requirements-revision.txt',
           ROOT/'requirements-revision-test.txt',
           ROOT/'reproducibility/manifest.json',ROOT/'data/README.md',
           ROOT/'data/cerespinn_training_iowa.csv',ROOT/'data/cerespinn_training_preprocessed.csv',
           ROOT/'data/cerespinn_county_audit.csv',ROOT/'backend/inference.py',ROOT/'backend/coupled_crop.py',ROOT/'backend/app.py',
           ROOT/'package.json',ROOT/'package-lock.json',ROOT/'tsconfig.json',ROOT/'vite.config.ts',ROOT/'index.html',
           ROOT/'tests/pinn-wiring.test.ts',
           ROOT/'backend/tests/test_coupled_crop.py',
           ROOT/'backend/tests/test_reacquired_source_integrity.py',
           ROOT/'backend/training/__init__.py',ROOT/'backend/training/config.py',ROOT/'backend/training/pinn.py',
           ROOT/'backend/training/dataset.py',ROOT/'backend/data/noaa_cag.py',ROOT/'backend/data/config.py',
           ROOT/'backend/training/train_v4_spatial.py',ROOT/'backend/tests/test_spatial_training_holdout.py',
           ROOT/'backend/tests/test_revision_scientific_integrity.py',ROOT/'backend/tests/test_physics_monotonicity.py',
           ROOT/'backend/tests/test_inference.py',ROOT/'backend/tests/test_training.py',ROOT/'backend/tests/conftest.py',
           ROOT/'backend/models/cerespinn_pinn.pt',ROOT/'backend/models/cerespinn_metadata.json',
           ROOT/'output/cerespinn_reporte_balance_hidrico.xlsx',ROOT/'output/cerespinn_reporte_biomasa_lai.xlsx']
    files += [ROOT/'scripts'/s for s in revision_scripts]
    files += [p for p in (ROOT/'src').rglob('*') if p.is_file()]
    files += [p for folder in ['data/external/bushland','data/bushland_processed','data/reacquired'] for p in (ROOT/folder).rglob('*') if p.is_file()]
    files += [p for p in (ROOT/'docs/q1_artifacts').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [p for p in DEST.iterdir() if p.is_file() and p.suffix in ['.docx','.md','.xlsx']]
    if (DEST/'PUBLICACION_GITHUB.json').exists():files.append(DEST/'PUBLICACION_GITHUB.json')
    files=sorted(set(files))
    missing=[str(p.relative_to(ROOT)) for p in files if not p.exists()]
    if missing:raise FileNotFoundError(missing)
    original=ROOT/'manuscript_source.docx'
    if not original.exists():original=Path(r'C:\Users\USERJSSV\Downloads\CeresPINN_LucanoNieves_RojasVillgas.docx')
    manifest={'schema_version':1,'date':'2026-10-26','base_commit':a['base_commit'],
       'release_status':'local review bundle; not a public Git/DOI release',
       'scientific_status':'External-source coupled-process evaluation completed with poor later-season grain transportability; national neural field validation and causal management effects remain unavailable',
       'integrity':'SHA-256 over exact packaged bytes',
       'source_manuscript':{'path':'manuscript_source.docx','bytes':original.stat().st_size,'sha256':sha(original)},
       'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
    manifest_path=DEST/'MANIFIESTO_REVISION.json'
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=DEST/'CeresPINN_evidencia_reproducible.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
        z.write(manifest_path,'MANIFIESTO_REVISION.json')
        z.write(original,'manuscript_source.docx')
    # Validate every packaged research file against the manifest.
    with zipfile.ZipFile(archive) as z:
        for f in manifest['files']+[manifest['source_manuscript']]:
            if hashlib.sha256(z.read(f['path'])).hexdigest()!=f['sha256']:
                raise RuntimeError(f'Archive integrity failure: {f["path"]}')
    print(f'Verified {len(files)} packaged files; archive bytes={archive.stat().st_size}')


if __name__=='__main__':main()
