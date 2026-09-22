## Scientific Foundation & Methodological Alignment

CeresPINN is designed to address critical gaps identified in recent agro-climatic literature:

1. **Physics-Informed Consistency:** Unlike pure data-driven "black box" models that fail under unprecedented climate conditions (Yu et al., 2025), our simulation engine uses PINN architectures. This ensures that all predictions strictly adhere to agronomic partial differential equations (PDEs) governing soil-water-crop dynamics, preventing ecological feedback loops (Zhang et al., 2025).
2. **Beyond Static Yield Predictions:** While traditional models focus solely on crop yield, CeresPINN incorporates climate stressors to evaluate risks to the **Harvestable Fraction (HF)**, preventing the systematic underestimation of food security risks under CMIP6 extreme heat and drought scenarios (Xiao et al., 2025).
3. **Computational Efficiency for Real-Time DT:** By leveraging a PINN-inspired emulator, CeresPINN bypasses the prohibitive computational costs of traditional pixel-based Data Assimilation (DA), enabling rapid, high-resolution scenario testing (`/api/scenarios`) suitable for real-time Digital Twin applications.
4. **Spatial Awareness:** Powered by PostGIS, the backend natively handles the spatial heterogeneity of regional climate data (NetCDF/CMIP6), mitigating the "mixed pixel" biases common in large-scale agricultural monitoring.

- **Data:** 
  - **Climate Projections:** Downscaled and bias-corrected CMIP6 (e.g., NASA NEX-GDDP) NetCDF inputs for future SSP scenarios.
  - **Historical Baseline:** CHIRPS (precipitation) and ERA5-Land (temperature/radiation) for historical model calibration.
  - **Ground Truth:** Agricultural census data (e.g., USDA NASS or regional equival


## Architecture

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Python
- Simulation: PINN-inspired agronomic climate engine
- Data: NetCDF / CMIP6-compatible climate inputs
- Persistence: PostgreSQL with PostGIS (real database, optional mock fallback)
- AI Assistant: Google Gemini API (google-genai)
- Auth: Demo login (frontend-only, fixed credentials)

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
  results/context. The core PINN-based simulation engine itself remains a
  local, physics-informed scientific model — Gemini is only used for the
  conversational assistant layer, not for the crop/climate predictions.
- **Login:** A demo login screen validates against a fixed set of demo
  credentials on the frontend (matching the existing DEMO_USERS roles:
  admin, researcher, farmer, consultant). This is for demonstration/
  presentation purposes; there is no password field yet in the `users`
  database table.
