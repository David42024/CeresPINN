# Processed research data

This directory contains the exact processed tables used by the committed
checkpoint and by the reproducibility scripts. Neither file contains secrets
or user records.

## Files

- `cerespinn_training_iowa.csv` — 66,480 rows; years 1990–2025; long format
  with three SSP scenario copies. The Q1 scripts deterministically reduce it to
  one median row per scenario-year (108 rows). Yield is the annual USDA NASS
  median and climate features are derived from the locally harvested NASA
  NEX-GDDP-CMIP6 regional summary.
- `cerespinn_training_preprocessed.csv` — the same 66,480 observations after
  feature scaling and one-hot encoding. It is retained to document the earlier
  preprocessing stage; the checkpoint audit uses the long-format file above.

The three scenario rows for a year share the same observed yield. They are not
three independent yield observations. All reported validation metrics therefore
keep complete years in one partition and are calculated after aggregation to
independent annual observations.

## Provenance and permitted reuse

- Yield source: USDA National Agricultural Statistics Service (NASS), Quick
  Stats. USDA attribution is retained in the project documentation.
- Climate source: NASA NEX-GDDP-CMIP6. NASA source acknowledgement and the
  dataset citation remain required when redistributing derived results.
- Project code is distributed under the repository's MIT `LICENSE`. Source-data
  terms continue to govern the underlying USDA and NASA observations; this
  repository does not claim ownership over those source observations.

## Integrity

Run the following from the repository root to verify the tracked inputs and
regenerate every Q1 artifact:

```bash
python scripts/reproduce.py
```

The expected row counts and SHA-256 digests are stored in
`reproducibility/manifest.json`.
