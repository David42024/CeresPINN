from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .pipelines_api import router as pipelines_router
import backend.inference as inference_mod
import backend.db as db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort DB init + seed; never crashes when DB is unavailable.
    db.init_db()
    db.seed_if_empty()
    yield


app = FastAPI(title="CeresPINN Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipelines_router)


class SimulationRequest(BaseModel):
    field_id: str
    scenario: str
    target_year: int
    planting_date: str
    maize_variety: str
    irrigation_strategy: str
    soil_moisture_initial_percent: float
    nitrogen_application_kg_ha: float
    carbon_dioxide_ppm: float
    temperature_anomaly_c: float
    precipitation_anomaly_percent: float


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "cerespinn-backend",
        "database": "postgresql+postgis",
        "model": "pinn-maize-ensemble",
    }


@app.get("/api/model/status")
def model_status() -> Dict[str, Any]:
    return {
        "model_name": "CeresPINN-maize-v2.5",
        "status": "ready",
        "backend": "FastAPI",
        "framework": "PyTorch/TensorFlow-ready",
        "cmip6_source": "CMIP6 NetCDF",
        "database": "PostgreSQL/PostGIS",
    }


@app.get("/api/fields")
def list_fields() -> List[Dict[str, Any]]:
    """Return fields from Postgres, falling back to the deterministic mock."""
    rows = db.list_fields()
    if rows is not None:
        return rows
    return [
        {
            "id": "field-bajio-02",
            "name": "Rancho Santa Elena - Módulo 4",
            "location_name": "Celaya, Guanajuato",
            "country": "México",
            "center_lat": 20.5222,
            "center_lng": -100.8123,
            "area_hectares": 48.0,
            "current_crop": "Maíz Blanco Híbrido Resiliente",
        },
        {
            "id": "field-iowa-01",
            "name": "Parcela Experimental Ames Norte",
            "location_name": "Story County, Iowa",
            "country": "Estados Unidos",
            "center_lat": 42.0308,
            "center_lng": -93.6319,
            "area_hectares": 64.5,
            "current_crop": "Zea mays L. (Maíz Grano)",
        },
    ]


@app.get("/api/scenarios")
def scenarios() -> List[Dict[str, Any]]:
    """Return climate scenarios from Postgres, falling back to the mock."""
    rows = db.list_scenarios()
    if rows is not None:
        return rows
    return [
        {"id": "SSP1-2.6", "label": "Sustainable pathway", "risk": "low"},
        {"id": "SSP3-7.0", "label": "Regional rivalry", "risk": "medium"},
        {"id": "SSP5-8.5", "label": "Fossil-fueled development", "risk": "high"},
    ]


@app.post("/api/simulate")
def simulate(payload: SimulationRequest) -> Dict[str, Any]:
    """Run a simulation, using the trained PINN when available, else a deterministic mock.

    The response always carries `inference_mode` ('pinn' | 'mock') so callers can
    distinguish real model inference from the fallback.
    """
    inv = inference_mod.get_inference()
    payload_dict = payload.model_dump()

    if inv.available:
        bu_per_acre = inv.predict_yield_bu_acre(payload_dict)
        if bu_per_acre is not None:
            # Convert bu/acre (maize, ~ 62.7 kg/bu @ 15.5% moisture ) to kg/ha.
            kg_per_ha = bu_per_acre * 62.77 * 2.47105
            projected_yield = max(0, kg_per_ha)
            inference_mode = "pinn"
        else:
            projected_yield = _mock_yield(payload)
            inference_mode = "mock-unavailable"
    else:
        projected_yield = _mock_yield(payload)
        inference_mode = "mock"

    response = _build_simulation_response(
        payload, projected_yield=projected_yield, inference_mode=inference_mode,
    )
    # Best-effort persistence of the simulation result (never blocks/fails).
    if db.available():
        import json as _json

        db.save_simulation(
            {
                **response,
                "_payload_json": _json.dumps(payload.model_dump(), ensure_ascii=False),
            }
        )
    return response


def _mock_yield(payload: SimulationRequest) -> float:
    """Deterministic fallback matching the previous placeholder behaviour."""
    projected_yield = 7800 + (payload.target_year % 10) * 120
    if payload.irrigation_strategy == "deficit_50":
        projected_yield *= 0.94
    if payload.scenario == "SSP5-8.5":
        projected_yield *= 0.86
    return projected_yield


def _build_simulation_response(
    payload: SimulationRequest,
    projected_yield: float,
    inference_mode: str,
) -> Dict[str, Any]:
    return {
        "id": f"sim-{payload.field_id}-{payload.target_year}",
        "field_id": payload.field_id,
        "scenario": payload.scenario,
        "target_year": payload.target_year,
        "inference_mode": inference_mode,
        "projected_yield_kg_ha": round(projected_yield),
        "potential_yield_kg_ha": 9200,
        "yield_loss_due_to_drought_percent": round(max(0, 100 - (projected_yield / 9200) * 100), 1),
        "total_biomass_kg_ha": round(projected_yield * 1.34),
        "total_water_consumed_mm": 360,
        "water_productivity_kg_m3": 1.7,
        "peak_water_stress_index": 0.67,
        "avg_water_stress_index": 0.41,
        "drought_resilience_score": 74,
        "economic_return_usd_ha": 1225,
        "daily_records": [
            {
                "dap": 1,
                "gdd_accumulated": 12,
                "stage": "Emergence",
                "soil_moisture_top": 0.27,
                "soil_moisture_avg": 0.24,
                "cwsi": 0.18,
                "temp_max_c": 28.4,
                "temp_min_c": 17.2,
            },
            {
                "dap": 35,
                "gdd_accumulated": 320,
                "stage": "V6",
                "soil_moisture_top": 0.23,
                "soil_moisture_avg": 0.21,
                "cwsi": 0.36,
                "temp_max_c": 30.9,
                "temp_min_c": 18.8,
            },
            {
                "dap": 70,
                "gdd_accumulated": 860,
                "stage": "VT (Tasseling)",
                "soil_moisture_top": 0.19,
                "soil_moisture_avg": 0.18,
                "cwsi": 0.59,
                "temp_max_c": 34.5,
                "temp_min_c": 21.1,
            },
        ],
        "alerts": [
            {
                "id": "alert-1",
                "level": "warning",
                "title": "High drought stress risk",
                "description": "The leading scenario suggests elevated water stress during tasseling.",
                "timing": "VT-R1",
                "recommended_action": "Apply strategic deficit irrigation or shift sowing date.",
            }
        ],
        "agronomic_recommendations": [
            "Delay sowing by 10-15 days to avoid peak drought stress.",
            "Maintain at least 50% plant available water during VT-R1.",
            "Evaluate a short-cycle genotype under SSP5-8.5.",
        ],
    }


@app.get("/api/reports")
def reports() -> Dict[str, Any]:
    """Return reports from Postgres (unwrapped), falling back to the mock."""
    rows = db.get_reports()
    if rows:
        # Keep the contract: expose `regions` (stored inside payload).
        row = rows[0]
        payload = row.get("payload", {}) or {}
        return {
            "title": row["title"],
            "generated_at": row["generated_at"],
            "summary": row["summary"],
            "regions": payload.get("regions", []),
        }
    return {
        "title": "CeresPINN seasonal summary",
        "generated_at": "2026-08-30T00:00:00Z",
        "summary": "Yield outlook remains stable under moderate warming but degrades under severe drought stress.",
        "regions": [
            {"name": "Bajío", "yield_kg_ha": 7500},
            {"name": "Iowa", "yield_kg_ha": 8400},
            {"name": "Pampas", "yield_kg_ha": 7800},
        ],
    }


@app.get("/api/health/database")
def database_health() -> Dict[str, Any]:
    """Return a live Postgres/PostGIS health report, or a mock-flag payload."""
    d = db.health()
    if d is not None:
        return d
    return {
        "database": "postgres",
        "postgis": "available",
        "status": "mock-or-live",
        "note": "DATABASE_URL no configurada o BD inalcanzable: se usa el mock.",
    }
