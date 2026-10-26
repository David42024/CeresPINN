"""Prepare a reviewable public-release asset without publishing anything.

Excludes the original/corrected manuscripts, manuscript text builder, private
editorial response and local document-authoring helpers. All included research
files receive independent exact-byte hashes in the public manifest.
"""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'deliverables/revision_20261026'
EXCLUDED={'manuscript_source.docx','MANIFIESTO_REVISION.json',
          'scripts/build_revised_article.py','scripts/package_reviewer_revision.py',
          'scripts/revision_reference_audit.py','scripts/write_revision_reference_ledger.py',
          'scripts/render_revision_word.ps1','docs/q1_artifacts/revision_20261026/manuscript_integrity.json',
          'docs/q1_artifacts/revision_20261026/final_verification.json'}
README='''# CeresPINN research artifacts for public-release review

This archive contains code, public source data, frozen inputs, trained-checkpoint
metadata, protocols, predictions and audit results. It is prepared locally and
has not been uploaded or published by this packaging operation.

The authors' original and corrected manuscripts, manuscript-text builder and
private editorial response are excluded. Manuscript-authoring commands mentioned
in the repository README are therefore outside this public archive's scope.

Install requirements-revision.txt in Python 3.11 (CPU). Scientific commands:

    python scripts/reproduce.py --verify-only
    python scripts/revision_scientific_audit.py
    python scripts/audit_reacquired_county.py
    python scripts/audit_geographic_districts.py
    python scripts/verify_bushland_sources.py
    python scripts/prepare_bushland_data.py
    python scripts/validate_bushland_coupling.py
    python scripts/revision_figures.py

For tests, install requirements-revision-test.txt and run the seven included
backend/tests/test_*.py files (24 tests). Frontend source and its seven wiring
checks are included; npm ci installs the pinned package-lock.json dependencies.

Key findings: simple regressions outperform the archived neural checkpoint in
the reported comparisons. The 20-year rolling audit and two geographic exclusion
designs do not establish national neural geographic validity. Reacquired USDA
data match all 3460 regional targets; disclosed NOAA differences affect 2025 only.
The separately calibrated Bushland process has weak later-season grain skill
despite exact numerical water accounting. No causal agronomic recommendation,
operational digital twin, new PINN algorithm, or predictive superiority is claimed.

Raw-source manifests identify USDA NASS, NOAA and the USDA Bushland collection,
with source URLs, retrieval dates and exact-byte hashes. Code is MIT licensed;
underlying source-data terms remain applicable. Original national raw records and
the original CMIP6 extraction remain unavailable. Neither an external editorial
score nor acceptance is implied by this release candidate.
'''


def main():
    src=DEST/'CeresPINN_evidencia_reproducible.zip';files={}
    with zipfile.ZipFile(src) as archive:
        private=json.loads(archive.read('MANIFIESTO_REVISION.json'))
        for name in archive.namelist():
            if name in EXCLUDED or name.startswith('deliverables/') or name.endswith('.docx'):continue
            if Path(name).name.startswith('.env'):raise ValueError('Environment file must never be published')
            files[name]=archive.read(name)
    files['README_PUBLIC_RELEASE.md']=README.encode()
    manifest={'schema_version':1,'prepared_date':'2026-10-26','status':'local release candidate; not published',
              'repository':'https://github.com/David42024/CeresPINN','base_commit':private['base_commit'],
              'manuscripts_and_private_editorial_response_included':False,
              'files':[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sorted(files.items())]}
    path=DEST/'MANIFIESTO_PUBLICO.json';path.write_text(json.dumps(manifest,indent=2))
    files[path.name]=path.read_bytes()
    target=DEST/'CeresPINN_artefactos_publicables.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in files.items():z.writestr(name,data)
    with zipfile.ZipFile(target) as z:
        for rec in manifest['files']:
            if hashlib.sha256(z.read(rec['path'])).hexdigest()!=rec['sha256']:raise ValueError('Public artifact hash mismatch')
        assert not any(n.endswith('.docx') or n.startswith('deliverables/') for n in z.namelist())
        assert 'scripts/build_revised_article.py' not in z.namelist()
    print(f'Prepared, not published: {target.name}; {len(manifest["files"])} research files; {target.stat().st_size} bytes')


if __name__=='__main__':main()
