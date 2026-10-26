# CeresPINN

[![Reproducibility](https://github.com/David42024/CeresPINN/actions/workflows/reproducibility.yml/badge.svg)](https://github.com/David42024/CeresPINN/actions/workflows/reproducibility.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Scientific Foundation & Methodological Alignment

CeresPINN is designed to address critical gaps identified in recent agro-climatic literature:

1. **Monotonicity-informed yield model:** The trained PyTorch MLP applies differentiable monotonicity constraints on temperature and precipitation inside the training domain. It does not solve the Richards PDE, and the constraints do not guarantee behavior outside the observed data range.
2. **Interactive scenario exploration:** The checkpoint and deterministic seasonal simulator support fast comparisons through `/api/simulate`. No direct speed comparison with process-based crop models is claimed.
3. **Georeferenced records:** PostgreSQL/PostGIS stores field geometry and metadata. The current yield checkpoint does not use coordinates or soil parameters as neural-network inputs, so field comparisons are exploratory rather than validated spatial predictions.

- **Data:**
  - **Climate features:** Regional summaries derived from NASA NEX-GDDP-CMIP6.
  - **Yield target:** USDA NASS annual maize yield, reduced to a national median by year.
  - **Tracked processed input:** `data/cerespinn_training_iowa.csv` (66,480 rows, 1990–2025). The three SSP copies of a year share one observed yield and are never treated as independent validation years.


## Architecture

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Python
- Simulation: PINN-inspired agronomic climate engine
- Data: NetCDF / CMIP6-compatible climate inputs
- Persistence: PostgreSQL with PostGIS (real database, optional mock fallback)
- AI Assistant: Google Gemini API (google-genai)
- Auth: Demo login (frontend-only, fixed credentials)

## Reproduce the scientific results

### October 26, 2026 reviewer revision

The additional audit is `python scripts/revision_scientific_audit.py`, using
`requirements-revision.txt`. Its frozen outputs are in
`docs/q1_artifacts/revision_20261026/`. Five expanding temporal blocks cover
20 distinct test years (2006–2025): the regularized network obtained RMSE
1085.04 kg/ha versus 999.04 for Ridge. The separate internal Iowa baseline
experiment uses 3,460 processed county-years and tests 696 future observations
in held-out counties. It does not validate the national checkpoint spatially.
The regional current-source reconstruction now preserves a USDA CSV and 297 NOAA JSON responses; all yields match, with disclosed small 2025 climate differences. Original national acquisition provenance remains incomplete. NOAA cooling degree days and
heuristic daily climate proxies are excluded from the county benchmark.

The corrected manuscript and private editorial response are retained locally.
The public scientific revision contains code, public source data and audit
results as Git files. See [the revision instructions](README_PUBLIC_RELEASE.md)
for scope, limitations and reproduction commands.

The repository includes the processed datasets, active checkpoint, exact model
metadata, Q1 scripts, generated artifacts and pinned scientific dependencies.
No API key, database, network download or deployment secret is required for the
reproduction pipeline.

### 1) Clone and create an isolated Python environment

```bash
git clone https://github.com/David42024/CeresPINN.git
cd CeresPINN
python -m venv .venv-repro
```

Activate it on Linux/macOS:

```bash
source .venv-repro/bin/activate
```

Or on Windows PowerShell:

```powershell
.\.venv-repro\Scripts\Activate.ps1
```

### 2) Install the pinned scientific environment

```bash
python -m pip install --upgrade pip
python -m pip install --requirement requirements-repro.txt
```

### 3) Run the complete offline reproduction

```bash
python scripts/reproduce.py
```

The command verifies SHA-256 digests and row counts, regenerates both Q1 audit
sets, trains ten seeds for the prospective temporal experiment and validates all
expected outputs. To verify committed inputs and existing artifacts without
retraining:

```bash
python scripts/reproduce.py --verify-only
```

Primary outputs:

- `docs/q1_artifacts/q1_statistics.json`: checkpoint hindcast, inferential tests,
  baselines, robustness and timing.
- `docs/q1_artifacts/extended/`: multi-seed, sensitivity and audit tables.
- `docs/q1_artifacts/temporal/`: prospective experiment trained on 1990–2017
  and tested strictly on 2018–2025.

The prospective ten-seed ensemble regenerated for the revision obtained RMSE
**800.58 kg ha⁻¹**, MAE **613.76 kg ha⁻¹** and R² **−0.6052** across eight
independent test years in the environment recorded in its JSON artifact. This
is evidence of weak temporal extrapolation, not a successful external
validation. The complete machine-readable result and bootstrap intervals are in
`docs/q1_artifacts/temporal/temporal_validation_1990_2017_to_2018_2025.json`.

GitHub Actions executes the same reproduction command on every push and pull
request and publishes the regenerated evidence as a workflow artifact. Dataset
provenance, limitations and checksums are documented in `data/README.md` and
`reproducibility/manifest.json`.

### Software verification

```bash
python -m pip install --requirement backend/requirements.txt pytest
python -m pytest backend/tests -q -p no:cacheprovider
python -m pip install --requirement requirements-streamlit.txt
python -m pytest tests/test_streamlit_app.py -q -p no:cacheprovider
npm ci
npm run lint
npm run test:pinn-wiring
npm run build
```

## Local development

### 1) Install frontend dependencies

```bash
npm install
```

### 2) Install backend dependencies

```bash
python -m pip install -r backend/requirements.txt
```

### 3) Copy environment config

```bash
copy .env.example .env
```

### 4) Start the backend

```bash
npm run dev:backend
```

### 5) Start the frontend

```bash
npm run dev
```

The frontend proxies `/api/*` to `http://localhost:8000`.

## Production deployment (real PINN inference)

The production path is intentionally strict: Render validates the committed
`backend/models/cerespinn_pinn.pt` checkpoint during the Docker build and starts
FastAPI with `CERESPINN_REQUIRE_MODEL=1`. A missing checkpoint, incompatible
weights, or unavailable PyTorch fails the deployment instead of serving the
calibrated surrogate.

Required deployment settings:

- **Render:** deploy using `render.yaml`; `FRONTEND_ORIGINS` is set to the public
  production alias `https://ceres-pinn.vercel.app`. Keep
  `CERESPINN_REQUIRE_MODEL=1`, `CERESPINN_REQUIRE_DATABASE=1`, and
  `CERESPINN_REQUIRE_REAL_DATA=1`, and `CERESPINN_MODEL_DIR=/app/backend/models`.
  Set `DATABASE_URL` to a real PostgreSQL connection string and
  `GEMINI_API_KEY` as a secret; production refuses the SQLite/mock fallback.
  `FRONTEND_ORIGIN_REGEX` is already scoped to the generated `ceres-pinn`
  Vercel Preview URLs; add any custom domain explicitly to `FRONTEND_ORIGINS`.
- **Vercel:** set `VITE_API_BASE_URL` to the public Render service URL, without a
  trailing slash (for example `https://your-service.onrender.com`). Set it for
  Production and Preview, then redeploy because Vite embeds it at build time.
- Verify `GET /api/model/status` returns `status: "ready"` and
  `inference_mode: "pinn"`. The frontend rejects any other mode in production.
- Verify `GET /api/chatbot/status` returns `status: "ready"`. The Gemini key is
  backend-only: do not create `VITE_GEMINI_API_KEY` or commit it to `.env`.

The active checkpoint and metadata are intentionally versioned. If the model is
retrained, replace both files together so weights and normalization remain in sync.

## API endpoints

- `GET /api/health`
- `GET /api/model/status`
- `GET /api/fields`
- `POST /api/simulate`
- `GET /api/scenarios`
- `POST /api/chatbot`
- `GET /api/chatbot/status`
- `GET /api/reports`

## Database note

PostgreSQL with PostGIS is supported via the `DATABASE_URL` environment variable. If the database is unavailable, the backend falls back to a mock in-memory flow so the app remains operable during local development.

## AI Assistant & Authentication

- **Chatbot:** A floating chatbot assistant powered by the Google Gemini API
  (google-genai) is available across the app. It answers questions about the
  platform and, when a simulation is active, about the current simulation
  results/context. The yield predictor is the tracked PyTorch MLP with local
  monotonicity regularization; Gemini is used only for the conversational
  assistant and never produces crop or climate predictions.
- **Login:** A demo login screen validates against a fixed set of demo
  credentials on the frontend (matching the existing DEMO_USERS roles:
  admin, researcher, farmer, consultant). This is for demonstration/
  presentation purposes; there is no password field yet in the `users`
  database table.

## License and data availability

Source code is distributed under the [MIT License](LICENSE). The exact processed
research tables used by the scripts are versioned under `data/`; their USDA NASS
and NASA NEX-GDDP-CMIP6 provenance and reuse notices are documented in
`data/README.md`.


## How to cite this revision

Lucano Nieves, D. A., and Rojas Villegas, G. D. (2026). CeresPINN scientific
revision of October 26 2026. Source code, public data and audit results.
Repository: https://github.com/David42024/CeresPINN, branch
`codex/scientific-revision-2026-10-26`. Include the full commit identifier from
`git rev-parse HEAD` when citing a checkout. This is a software revision; no
journal publication, DOI or editorial acceptance is claimed.

### External-source measured-state extension (October 26, 2026)

Public USDA Bushland raw workbooks, checksums and processed measurements are preserved for six seasons. `scripts/prepare_bushland_data.py` and `scripts/validate_bushland_coupling.py` reproduce a separate coupled-process experiment: calibration 1989/1990/1994/2013, evaluation 2016/2018. Later-season grain RMSE is 3248.07 kg/ha versus 1604.19 for Ridge. This negative result is retained; it does not validate the archived neural checkpoint or causal management recommendations. See `docs/q1_artifacts/bushland/README.md` for the fixed protocol, units, substitutions and limitations. The Git revision includes the selected original public source files.
