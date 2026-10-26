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

## County extension for the reviewer revision

`cerespinn_county_audit.csv` freezes 3,460 local processed Iowa county-years
across 99 counties. It is a separate NASS-NOAA baseline dataset, not spatial
training data for the archived neural checkpoint. A new public USDA CSV and 297 complete NOAA responses now document the current-source reconstruction. All 3,460 yield targets agree within rounding. NOAA climate agrees through 2024; 56 cells across three variables differ in 2025. Both versions and every raw checksum are retained, without claiming recovery of the original acquisition bytes. April–September seasonal temperature and precipitation
are retained. NOAA CAG `cdd` means cooling degree days, not consecutive dry
days. It and heuristic GDD, heat-day counts, and VPD are excluded from the
new county benchmark. The reproducible evaluation holds out counties and all
post-2017 years within each fit; 696 county-years still share only eight
distinct test years.

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


### External-source measured-state extension (October 26, 2026)

Public USDA Bushland raw workbooks, checksums and processed measurements are preserved for six seasons. `scripts/prepare_bushland_data.py` and `scripts/validate_bushland_coupling.py` reproduce a separate coupled-process experiment: calibration 1989/1990/1994/2013, evaluation 2016/2018. Later-season grain RMSE is 3248.07 kg/ha versus 1604.19 for Ridge. This negative result is retained; it does not validate the archived neural checkpoint or causal management recommendations. See `docs/q1_artifacts/bushland/README.md` for the fixed protocol, units, substitutions and limitations. The local revision ZIP includes the selected original public files.
