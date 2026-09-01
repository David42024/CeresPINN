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

## API endpoints

- `GET /api/health`
- `GET /api/model/status`
- `GET /api/fields`
- `POST /api/simulate`
- `GET /api/scenarios`
- `GET /api/reports`

## Database note

PostgreSQL with PostGIS is supported via the `DATABASE_URL` environment variable. If the database is unavailable, the backend falls back to a mock in-memory flow so the app remains operable during local development.

## Important note

This project intentionally does not depend on Gemini APIs. The AI layer is replaced by a local scientific simulation backend and a real data layer.
