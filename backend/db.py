"""Database access layer for CeresPINN (PostgreSQL + PostGIS on Supabase).

Design
  - Reads `DATABASE_URL` (e.g. `postgresql+psycopg2://user:pass@host/db`) once.
  - Uses SQLAlchemy with `pool_pre_ping` so stale Supabase connections are
    refreshed automatically.
  - Every accessor returns `None` / empty / raises `DatabaseUnavailable` when the
    DB is not configured or unreachable, so callers can fall back to the
    deterministic mocks — preserving the project's rigorous-fallback contract
    (never crash, never pretend).

Seed data matches the current backend mocks byte-for-byte, so switching from mock
to live DB does not change the API contract observed by the frontend.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


class DatabaseUnavailable(Exception):
    """Raised when the database is not configured or cannot be reached."""


_engine: Optional[Engine] = None
_checked = False


def get_engine() -> Optional[Engine]:
    """Return a lazy, cached SQLAlchemy engine, or None if DB not configured."""
    global _engine, _checked
    if _checked:
        return _engine
    _checked = True
    if not _DATABASE_URL:
        return None
    try:
        _engine = create_engine(_DATABASE_URL, pool_pre_ping=True, pool_recycle=600)
        # Force a round-trip so a misconfigured URL surfaces immediately.
        with _engine.connect():
            pass
    except SQLAlchemyError:
        _engine = None
    return _engine


def available() -> bool:
    return get_engine() is not None


@contextmanager
def _connect() -> Iterator[Any]:
    engine = get_engine()
    if engine is None:
        raise DatabaseUnavailable("DATABASE_URL no configurada o BD inalcanzable.")
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


def now_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS fields (
    id             TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    location_name  TEXT NOT NULL,
    country        TEXT NOT NULL,
    center_lat     DOUBLE PRECISION NOT NULL,
    center_lng     DOUBLE PRECISION NOT NULL,
    area_hectares  DOUBLE PRECISION NOT NULL,
    altitude_meters DOUBLE PRECISION NOT NULL DEFAULT 0,
    current_crop   TEXT NOT NULL,
    soil_profile   TEXT NOT NULL DEFAULT '{}',
    polygon        TEXT NOT NULL DEFAULT '{}',
    notes          TEXT
);

CREATE TABLE IF NOT EXISTS soil_profiles (
    id             TEXT PRIMARY KEY,
    label          TEXT NOT NULL,
    sand_percent   DOUBLE PRECISION NOT NULL,
    clay_percent   DOUBLE PRECISION NOT NULL,
    silt_percent   DOUBLE PRECISION NOT NULL,
    organic_matter_percent DOUBLE PRECISION NOT NULL,
    bulk_density   DOUBLE PRECISION NOT NULL,
    field_capacity DOUBLE PRECISION NOT NULL,
    wilting_point  DOUBLE PRECISION NOT NULL,
    saturation     DOUBLE PRECISION NOT NULL,
    saturated_conductivity_ks DOUBLE PRECISION NOT NULL,
    alpha_van_genuchten DOUBLE PRECISION NOT NULL,
    n_van_genuchten DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS scenarios (
    id    TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    risk  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    summary     TEXT NOT NULL,
    payload     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_registry (
    version            TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    architecture       TEXT NOT NULL,
    trained_date       TEXT NOT NULL,
    epochs             INT NOT NULL,
    richards_weight_lambda DOUBLE PRECISION NOT NULL,
    test_r2            DOUBLE PRECISION NOT NULL,
    test_rmse_kg_ha    DOUBLE PRECISION NOT NULL,
    active             BOOLEAN NOT NULL DEFAULT FALSE,
    status             TEXT NOT NULL,
    description        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_pipelines (
    id                 TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    source             TEXT NOT NULL,
    frequency          TEXT NOT NULL,
    last_sync          TEXT NOT NULL,
    status             TEXT NOT NULL,
    records_processed  TEXT NOT NULL,
    resolution         TEXT NOT NULL,
    description        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL,
    role          TEXT NOT NULL,
    avatar_url    TEXT,
    organization  TEXT,
    region        TEXT NOT NULL,
    preferences   TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS simulations (
    id             TEXT PRIMARY KEY,
    field_id       TEXT NOT NULL,
    scenario       TEXT NOT NULL,
    target_year    INT NOT NULL,
    inference_mode TEXT NOT NULL,
    projected_yield_kg_ha DOUBLE PRECISION NOT NULL,
    payload        TEXT NOT NULL,
    created_at     TEXT NOT NULL
);
"""


def init_db() -> None:
    """Create tables (and backfill new columns) if the database is configured. Never raises."""
    if not available():
        return
    _MIGRATIONS = [
        "ALTER TABLE fields ADD COLUMN IF NOT EXISTS altitude_meters DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE fields ADD COLUMN IF NOT EXISTS soil_profile TEXT NOT NULL DEFAULT '{}'",
        "ALTER TABLE fields ADD COLUMN IF NOT EXISTS polygon TEXT NOT NULL DEFAULT '{}'",
        "ALTER TABLE fields ADD COLUMN IF NOT EXISTS notes TEXT",
    ]
    try:
        with _connect() as conn:
            conn.execute(text(_SCHEMA))
            for stmt in _MIGRATIONS:
                conn.execute(text(stmt))
            conn.commit()
    except (SQLAlchemyError, DatabaseUnavailable):
        pass


# ---------------------------------------------------------------------------
# Seed — mirrors the current mocks so the contract stays identical
# ---------------------------------------------------------------------------
def seed_if_empty() -> None:
    """Insert the mock-equivalent rows when the tables are empty."""
    if not available():
        return
    try:
        with _connect() as conn:
            fields_count = conn.execute(text("SELECT count(*) FROM fields")).scalar() or 0
            soil_count = conn.execute(text("SELECT count(*) FROM soil_profiles")).scalar() or 0
            scenarios_count = conn.execute(text("SELECT count(*) FROM scenarios")).scalar() or 0
            reports_count = conn.execute(text("SELECT count(*) FROM reports")).scalar() or 0
            model_count = conn.execute(text("SELECT count(*) FROM model_registry")).scalar() or 0
            pipe_count = conn.execute(text("SELECT count(*) FROM ingestion_pipelines")).scalar() or 0
            users_count = conn.execute(text("SELECT count(*) FROM users")).scalar() or 0

            if soil_count == 0:
                INSERT = text(
                    """INSERT INTO soil_profiles
                       (id, label, sand_percent, clay_percent, silt_percent,
                        organic_matter_percent, bulk_density, field_capacity,
                        wilting_point, saturation, saturated_conductivity_ks,
                        alpha_van_genuchten, n_van_genuchten)
                       VALUES (:id, :label, :sand_percent, :clay_percent, :silt_percent,
                               :organic_matter_percent, :bulk_density, :field_capacity,
                               :wilting_point, :saturation, :saturated_conductivity_ks,
                               :alpha_van_genuchten, :n_van_genuchten)"""
                )
                for s in _SOIL_PROFILES_SEED:
                    conn.execute(INSERT, s)

            # Fields use UPSERT unconditionally so a pre-existing seed (e.g. the
            # earlier 2-field seed) is upgraded to the full 4-field record set.
            INSERT = text(
                """INSERT INTO fields
                   (id, name, location_name, country, center_lat, center_lng,
                    area_hectares, altitude_meters, current_crop, soil_profile,
                    polygon, notes)
                   VALUES (:id, :name, :location_name, :country, :center_lat,
                           :center_lng, :area_hectares, :altitude_meters,
                           :current_crop, :soil_profile, :polygon, :notes)
                   ON CONFLICT (id) DO UPDATE SET
                     name = EXCLUDED.name,
                     location_name = EXCLUDED.location_name,
                     country = EXCLUDED.country,
                     center_lat = EXCLUDED.center_lat,
                     center_lng = EXCLUDED.center_lng,
                     area_hectares = EXCLUDED.area_hectares,
                     altitude_meters = EXCLUDED.altitude_meters,
                     current_crop = EXCLUDED.current_crop,
                     soil_profile = EXCLUDED.soil_profile,
                     polygon = EXCLUDED.polygon,
                     notes = EXCLUDED.notes"""
            )
            for f in _FIELDS_SEED:
                conn.execute(INSERT, f)

            if scenarios_count == 0:
                INSERT = text("INSERT INTO scenarios (id, label, risk) VALUES (:id, :label, :risk)")
                for s in _SCENARIOS_SEED:
                    conn.execute(INSERT, s)

            if reports_count == 0:
                INSERT = text(
                    """INSERT INTO reports (id, title, generated_at, summary, payload)
                       VALUES (:id, :title, :generated_at, :summary, :payload)"""
                )
                conn.execute(INSERT, _REPORTS_SEED)

            if model_count == 0:
                INSERT = text(
                    """INSERT INTO model_registry
                       (version, name, architecture, trained_date, epochs,
                        richards_weight_lambda, test_r2, test_rmse_kg_ha, active,
                        status, description)
                       VALUES (:version, :name, :architecture, :trained_date, :epochs,
                               :richards_weight_lambda, :test_r2, :test_rmse_kg_ha,
                               :active, :status, :description)"""
                )
                for m in _MODEL_REGISTRY_SEED:
                    conn.execute(INSERT, m)

            if pipe_count == 0:
                INSERT = text(
                    """INSERT INTO ingestion_pipelines
                       (id, name, source, frequency, last_sync, status,
                        records_processed, resolution, description)
                       VALUES (:id, :name, :source, :frequency, :last_sync, :status,
                               :records_processed, :resolution, :description)"""
                )
                for p in _INGESTION_PIPELINES_SEED:
                    conn.execute(INSERT, p)

            if users_count == 0:
                INSERT = text(
                    """INSERT INTO users
                       (id, name, email, role, avatar_url, organization, region, preferences)
                       VALUES (:id, :name, :email, :role, :avatar_url, :organization,
                               :region, :preferences)"""
                )
                for u in _USERS_SEED:
                    conn.execute(INSERT, u)

            conn.commit()
    except (SQLAlchemyError, DatabaseUnavailable):
        pass


# Seed data (keep in sync with the mocks in app.py and src/data/mockData.ts)
_SOIL_PROFILES_SEED: List[Dict[str, Any]] = [
    {
        "id": "clay_loam",
        "label": "Franco Arcilloso (Clay Loam)",
        "sand_percent": 32, "clay_percent": 34, "silt_percent": 34,
        "organic_matter_percent": 3.2, "bulk_density": 1.35,
        "field_capacity": 0.32, "wilting_point": 0.16, "saturation": 0.48,
        "saturated_conductivity_ks": 85, "alpha_van_genuchten": 0.015, "n_van_genuchten": 1.45,
    },
    {
        "id": "sandy_loam",
        "label": "Franco Arenoso (Sandy Loam)",
        "sand_percent": 65, "clay_percent": 12, "silt_percent": 23,
        "organic_matter_percent": 1.8, "bulk_density": 1.48,
        "field_capacity": 0.22, "wilting_point": 0.09, "saturation": 0.41,
        "saturated_conductivity_ks": 240, "alpha_van_genuchten": 0.026, "n_van_genuchten": 1.75,
    },
    {
        "id": "silty_clay",
        "label": "Arcillo Limoso (Silty Clay)",
        "sand_percent": 10, "clay_percent": 48, "silt_percent": 42,
        "organic_matter_percent": 2.7, "bulk_density": 1.28,
        "field_capacity": 0.38, "wilting_point": 0.22, "saturation": 0.52,
        "saturated_conductivity_ks": 35, "alpha_van_genuchten": 0.010, "n_van_genuchten": 1.28,
    },
    {
        "id": "loam",
        "label": "Franco Ideal (Loam)",
        "sand_percent": 40, "clay_percent": 20, "silt_percent": 40,
        "organic_matter_percent": 3.8, "bulk_density": 1.32,
        "field_capacity": 0.28, "wilting_point": 0.13, "saturation": 0.46,
        "saturated_conductivity_ks": 120, "alpha_van_genuchten": 0.019, "n_van_genuchten": 1.55,
    },
]

import json as _json  # noqa: E402


def _field_seed() -> List[Dict[str, Any]]:
    return [
        {
            "id": "field-iowa-01",
            "name": "Parcela Experimental Ames Norte",
            "location_name": "Story County, Iowa",
            "country": "Estados Unidos",
            "center_lat": 42.0308,
            "center_lng": -93.6319,
            "area_hectares": 64.5,
            "altitude_meters": 295,
            "current_crop": "Zea mays L. (Maíz Grano)",
            "soil_profile": _json.dumps({"type": "clay_loam", "label": "Franco Arcilloso (Clay Loam)", "sandPercent": 32, "clayPercent": 34, "siltPercent": 34, "organicMatterPercent": 3.2, "bulkDensity": 1.35, "fieldCapacity": 0.32, "wiltingPoint": 0.16, "saturation": 0.48, "saturatedConductivityKs": 85, "alphaVanGenuchten": 0.015, "nVanGenuchten": 1.45}),
            "polygon": _json.dumps({"type": "Polygon", "coordinates": [[42.035, -93.638], [42.035, -93.625], [42.026, -93.625], [42.026, -93.638], [42.035, -93.638]]}),
            "notes": "Suelo Mollisol de alta fertilidad con historial DSSAT/APSIM para validación PINN.",
        },
        {
            "id": "field-bajio-02",
            "name": "Rancho Santa Elena - Módulo 4",
            "location_name": "Celaya, Guanajuato (El Bajío)",
            "country": "México",
            "center_lat": 20.5222,
            "center_lng": -100.8123,
            "area_hectares": 48.0,
            "altitude_meters": 1750,
            "current_crop": "Maíz Blanco Híbrido Resiliente",
            "soil_profile": _json.dumps({"type": "silty_clay", "label": "Arcillo Limoso (Silty Clay)", "sandPercent": 10, "clayPercent": 48, "siltPercent": 42, "organicMatterPercent": 2.7, "bulkDensity": 1.28, "fieldCapacity": 0.38, "wiltingPoint": 0.22, "saturation": 0.52, "saturatedConductivityKs": 35, "alphaVanGenuchten": 0.010, "nVanGenuchten": 1.28}),
            "polygon": _json.dumps({"type": "Polygon", "coordinates": [[20.528, -100.819], [20.529, -100.805], [20.516, -100.806], [20.515, -100.820], [20.528, -100.819]]}),
            "notes": "Vertisol arcilloso susceptible a estrés hídrico terminal y agrietamiento.",
        },
        {
            "id": "field-pampas-03",
            "name": "Estancia La Vanguardia - Lote 12",
            "location_name": "Pergamino, Buenos Aires",
            "country": "Argentina",
            "center_lat": -33.8961,
            "center_lng": -60.5736,
            "area_hectares": 120.0,
            "altitude_meters": 65,
            "current_crop": "Maíz Tardío Siembra Directa",
            "soil_profile": _json.dumps({"type": "loam", "label": "Franco Ideal (Loam)", "sandPercent": 40, "clayPercent": 20, "siltPercent": 40, "organicMatterPercent": 3.8, "bulkDensity": 1.32, "fieldCapacity": 0.28, "wiltingPoint": 0.13, "saturation": 0.46, "saturatedConductivityKs": 120, "alphaVanGenuchten": 0.019, "nVanGenuchten": 1.55}),
            "polygon": _json.dumps({"type": "Polygon", "coordinates": [[-33.890, -60.582], [-33.890, -60.564], [-33.902, -60.565], [-33.901, -60.583], [-33.890, -60.582]]}),
            "notes": "Argiudol típico con napa freática oscilante y alta retención de humedad.",
        },
        {
            "id": "field-ebro-04",
            "name": "Finca Riego Canal d'Urgell",
            "location_name": "Lleida, Cataluña",
            "country": "España",
            "center_lat": 41.6176,
            "center_lng": 0.6200,
            "area_hectares": 35.2,
            "altitude_meters": 190,
            "current_crop": "Maíz Ciclo Corto (FAO 400)",
            "soil_profile": _json.dumps({"type": "sandy_loam", "label": "Franco Arenoso (Sandy Loam)", "sandPercent": 65, "clayPercent": 12, "siltPercent": 23, "organicMatterPercent": 1.8, "bulkDensity": 1.48, "fieldCapacity": 0.22, "wiltingPoint": 0.09, "saturation": 0.41, "saturatedConductivityKs": 240, "alphaVanGenuchten": 0.026, "nVanGenuchten": 1.75}),
            "polygon": _json.dumps({"type": "Polygon", "coordinates": [[41.622, 0.614], [41.623, 0.626], [41.612, 0.627], [41.611, 0.615], [41.622, 0.614]]}),
            "notes": "Suelo calcáreo con restricción estricta de cupo de riego por sequía mediterránea.",
        },
    ]


_FIELDS_SEED: List[Dict[str, Any]] = _field_seed()

_SCENARIOS_SEED: List[Dict[str, Any]] = [
    {"id": "SSP1-2.6", "label": "Sustainable pathway", "risk": "low"},
    {"id": "SSP3-7.0", "label": "Regional rivalry", "risk": "medium"},
    {"id": "SSP5-8.5", "label": "Fossil-fueled development", "risk": "high"},
]

_REPORTS_SEED: Dict[str, Any] = {
    "id": "report-seasonal-2026",
    "title": "CeresPINN seasonal summary",
    "generated_at": "2026-08-30T00:00:00Z",
    "summary": (
        "Yield outlook remains stable under moderate warming but degrades under "
        "severe drought stress."
    ),
    "payload": (
        '{"regions":[{"name":"Bajío","yield_kg_ha":7500},'
        '{"name":"Iowa","yield_kg_ha":8400},'
        '{"name":"Pampas","yield_kg_ha":7800}]}'
    ),
}

_MODEL_REGISTRY_SEED: List[Dict[str, Any]] = [
    {
        "version": "v2.4.1-PINN-Ensemble",
        "name": "PINN Ceres-Richards V2.4 (Active Production)",
        "architecture": "Physics-Informed Deep ResNet + Automatic Differentiation PDE Loss",
        "trained_date": "2026-08-15",
        "epochs": 15000,
        "richards_weight_lambda": 0.45,
        "test_r2": 0.942,
        "test_rmse_kg_ha": 385,
        "active": True,
        "status": "production",
        "description": "Surrogate neural model enforcing 1D unsaturated Richards flow conservation & Priestley-Taylor ET constraints.",
    },
    {
        "version": "v2.3.0-PINN-Richards",
        "name": "PINN Richards Single-Soil V2.3",
        "architecture": "Physics-Informed MLP (6 layers x 256 units, tanh activation)",
        "trained_date": "2026-06-20",
        "epochs": 12000,
        "richards_weight_lambda": 0.35,
        "test_r2": 0.918,
        "test_rmse_kg_ha": 490,
        "active": False,
        "status": "staging",
        "description": "Calibrated on USDA NASS 2000-2025 multi-state corn records.",
    },
    {
        "version": "v1.8.2-Vanilla-LSTM",
        "name": "Empirical Baseline (Non-Physics LSTM)",
        "architecture": "Bidirectional LSTM + Dense Output",
        "trained_date": "2026-02-10",
        "epochs": 8000,
        "richards_weight_lambda": 0.0,
        "test_r2": 0.812,
        "test_rmse_kg_ha": 890,
        "active": False,
        "status": "archived",
        "description": "Baseline purely data-driven model without PDE physics regularization.",
    },
]

_INGESTION_PIPELINES_SEED: List[Dict[str, Any]] = [
    {
        "id": "pipe-chirps",
        "name": "CHIRPS Daily Precipitation Pipeline",
        "source": "UCSB Climate Hazards Center (FTP/GeoTIFF 0.05°)",
        "frequency": "Diario (06:00 UTC)",
        "last_sync": "2026-08-29 06:15:22 UTC",
        "status": "healthy",
        "records_processed": "14,892,100 grid points",
        "resolution": "0.05° (~5.3 km) downscaled to 100m",
        "description": "Descarga satelital combinada con estaciones pluviométricas para monitoreo de precipitación en tiempo real.",
    },
    {
        "id": "pipe-nasa-nex",
        "name": "NASA NEX-GDDP CMIP6 Climate Scenarios",
        "source": "NASA Earth Exchange (S3 Public Bucket / NetCDF4)",
        "frequency": "Semanal (Actualización de proyecciones)",
        "last_sync": "2026-08-28 18:40:00 UTC",
        "status": "healthy",
        "records_processed": "32 Ensemble Models (SSP1-2.6, SSP3-7.0, SSP5-8.5)",
        "resolution": "0.25° con Quantile Delta Mapping",
        "description": "Proyecciones climáticas globales con corrección de sesgo para temperatura extrema, radiación y VPD hasta 2050.",
    },
    {
        "id": "pipe-usda-nass",
        "name": "USDA NASS QuickStats Crop Harvest Yields",
        "source": "USDA National Agricultural Statistics Service API",
        "frequency": "Mensual",
        "last_sync": "2026-08-20 12:00:10 UTC",
        "status": "healthy",
        "records_processed": "45,200 County-Year Yield Observations",
        "resolution": "Nivel Condado / Parcela de calibración",
        "description": "Datos históricos de rendimiento de maíz (1990-2025) utilizados como loss empírica de entrenamiento.",
    },
]

_USERS_SEED: List[Dict[str, Any]] = [
    {
        "id": "usr-admin-1",
        "name": "Dra. Elena Vasconcelos",
        "email": "elena.vasconcelos@agriclimate-twin.org",
        "role": "admin",
        "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
        "organization": "Centro Internacional de Modelado Climático Agrícola",
        "region": "América Latina & Caribe",
        "preferences": _json.dumps({"unitSystem": "metric", "theme": "dark", "autoSaveSimulations": True, "highContrast3D": True, "emailAlerts": True}),
    },
    {
        "id": "usr-researcher-2",
        "name": "Dr. Marcus Vance",
        "email": "m.vance@agri-ai-lab.edu",
        "role": "researcher",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        "organization": "Global Crop Modeling Consortium",
        "region": "Norteamérica",
        "preferences": _json.dumps({"unitSystem": "metric", "theme": "dark", "autoSaveSimulations": True, "highContrast3D": False, "emailAlerts": True}),
    },
    {
        "id": "usr-farmer-3",
        "name": "Carlos Mendez R.",
        "email": "carlos.mendez@agrovalle.com",
        "role": "farmer",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
        "organization": "Asociación de Productores del Bajío",
        "region": "México Central",
        "preferences": _json.dumps({"unitSystem": "metric", "theme": "dark", "autoSaveSimulations": False, "highContrast3D": False, "emailAlerts": True}),
    },
    {
        "id": "usr-consultant-4",
        "name": "Ing. Sofía Morales",
        "email": "sofia.morales@climateresilient.tech",
        "role": "consultant",
        "avatar_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
        "organization": "Consultoría Agrotech Sostenible",
        "region": "Europa Sur",
        "preferences": _json.dumps({"unitSystem": "metric", "theme": "dark", "autoSaveSimulations": True, "highContrast3D": False, "emailAlerts": False}),
    },
]


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------
def list_fields() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT id, name, location_name, country, center_lat, center_lng,
                              area_hectares, altitude_meters, current_crop, soil_profile,
                              polygon, notes
                       FROM fields ORDER BY id"""
                )
            ).mappings().all()
        result = []
        for r in rows:
            d = dict(r)
            d["soilProfile"] = _parse_json(d.pop("soil_profile"), {})
            d["polygon"] = _parse_json(d.pop("polygon"), {"type": "Polygon", "coordinates": []})
            d["altitudeMeters"] = d.pop("altitude_meters")
            d["areaHectares"] = d.pop("area_hectares")
            d["centerLat"] = d.pop("center_lat")
            d["centerLng"] = d.pop("center_lng")
            d["locationName"] = d.pop("location_name")
            d["currentCrop"] = d.pop("current_crop")
            result.append(d)
        return result
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def _parse_json(raw: Any, fallback: Any) -> Any:
    if isinstance(raw, str):
        try:
            return _json.loads(raw)
        except (ValueError, TypeError):
            return fallback
    return raw or fallback


def list_soil_profiles() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM soil_profiles ORDER BY id")
            ).mappings().all()
        return [
            {
                "id": r["id"], "label": r["label"],
                "sandPercent": r["sand_percent"], "clayPercent": r["clay_percent"],
                "siltPercent": r["silt_percent"],
                "organicMatterPercent": r["organic_matter_percent"],
                "bulkDensity": r["bulk_density"], "fieldCapacity": r["field_capacity"],
                "wiltingPoint": r["wilting_point"], "saturation": r["saturation"],
                "saturatedConductivityKs": r["saturated_conductivity_ks"],
                "alphaVanGenuchten": r["alpha_van_genuchten"],
                "nVanGenuchten": r["n_van_genuchten"],
            }
            for r in rows
        ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def list_model_registry() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM model_registry ORDER BY trained_date DESC")
            ).mappings().all()
        return [
            {
                "version": r["version"], "name": r["name"], "architecture": r["architecture"],
                "trainedDate": r["trained_date"], "epochs": r["epochs"],
                "richardsWeightLambda": r["richards_weight_lambda"], "testR2": r["test_r2"],
                "testRmseKgHa": r["test_rmse_kg_ha"], "active": bool(r["active"]),
                "status": r["status"], "description": r["description"],
            }
            for r in rows
        ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def list_ingestion_pipelines() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM ingestion_pipelines ORDER BY id")
            ).mappings().all()
        return [
            {
                "id": r["id"], "name": r["name"], "source": r["source"],
                "frequency": r["frequency"], "lastSync": r["last_sync"],
                "status": r["status"], "recordsProcessed": r["records_processed"],
                "resolution": r["resolution"], "description": r["description"],
            }
            for r in rows
        ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def list_users() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM users ORDER BY id")
            ).mappings().all()
        return [
            {
                "id": r["id"], "name": r["name"], "email": r["email"], "role": r["role"],
                "avatarUrl": r["avatar_url"], "organization": r["organization"],
                "region": r["region"], "preferences": _parse_json(r["preferences"], {}),
            }
            for r in rows
        ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def list_scenarios() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("SELECT id, label, risk FROM scenarios ORDER BY id")
            ).mappings().all()
        return [dict(r) for r in rows]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def get_reports() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("SELECT id, title, generated_at, summary, payload FROM reports ORDER BY id")
            ).mappings().all()
        result = []
        for r in rows:
            import json

            d = dict(r)
            try:
                d["payload"] = json.loads(d["payload"])
            except (json.JSONDecodeError, TypeError):
                d["payload"] = {}
            result.append(d)
        return result
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def save_simulation(sim: Dict[str, Any]) -> None:
    """Persist a simulation result for later analysis (best effort)."""
    if not available():
        return
    try:
        with _connect() as conn:
            conn.execute(
                text(
                    """INSERT INTO simulations
                       (id, field_id, scenario, target_year, inference_mode,
                        projected_yield_kg_ha, payload, created_at)
                       VALUES (:id, :field_id, :scenario, :target_year, :inference_mode,
                               :projected_yield_kg_ha, :payload, :created_at)
                       ON CONFLICT (id) DO NOTHING"""
                ),
                {
                    "id": sim["id"],
                    "field_id": sim["field_id"],
                    "scenario": sim["scenario"],
                    "target_year": int(sim["target_year"]),
                    "inference_mode": sim["inference_mode"],
                    "projected_yield_kg_ha": float(sim["projected_yield_kg_ha"]),
                    "payload": sim.get("_payload_json", "{}"),
                    "created_at": now_utc(),
                },
            )
            conn.commit()
    except (SQLAlchemyError, DatabaseUnavailable):
        pass


def health() -> Optional[Dict[str, Any]]:
    """Return a live health payload, or None when the DB is unavailable."""
    if not available():
        return None
    try:
        with _connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
            postgis = conn.execute(
                text("SELECT postgis_version()")
            ).scalar()  # raises if PostGIS missing
        return {
            "database": "postgres",
            "postgis": postgis if isinstance(postgis, str) else "available",
            "status": "connected",
            "version": version[:60] if isinstance(version, str) else str(version),
        }
    except (SQLAlchemyError, DatabaseUnavailable):
        return None
