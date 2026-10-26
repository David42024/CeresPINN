# CeresPINN scientific revision of October 26 2026

This Git snapshot contains code, public source data, frozen inputs, trained-checkpoint
metadata, protocols, predictions and audit results. The revision is published as ordinary Git files on branch
`codex/scientific-revision-2026-10-26`; no ZIP release asset is required.
Use the full Git commit identifier to cite or reproduce this exact revision.

The authors' original and corrected manuscripts, manuscript-text builder and
private editorial response are excluded. Manuscript-authoring commands mentioned
in the repository README are therefore outside this public revision's scope.

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
score nor acceptance is implied by this scientific revision.
