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
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    location_name TEXT NOT NULL,
    country       TEXT NOT NULL,
    center_lat    DOUBLE PRECISION NOT NULL,
    center_lng    DOUBLE PRECISION NOT NULL,
    area_hectares DOUBLE PRECISION NOT NULL,
    current_crop  TEXT NOT NULL
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
    """Create tables if the database is configured. Never raises."""
    if not available():
        return
    try:
        with _connect() as conn:
            conn.execute(text(_SCHEMA))
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
            scenarios_count = conn.execute(text("SELECT count(*) FROM scenarios")).scalar() or 0
            reports_count = conn.execute(text("SELECT count(*) FROM reports")).scalar() or 0

            if fields_count == 0:
                INSERT = text(
                    """INSERT INTO fields
                       (id, name, location_name, country, center_lat, center_lng,
                        area_hectares, current_crop)
                       VALUES (:id, :name, :location_name, :country, :center_lat,
                               :center_lng, :area_hectares, :current_crop)"""
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

            conn.commit()
    except (SQLAlchemyError, DatabaseUnavailable):
        pass


# Seed data (keep in sync with the mocks in app.py)
_FIELDS_SEED: List[Dict[str, Any]] = [
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


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------
def list_fields() -> Optional[List[Dict[str, Any]]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT id, name, location_name, country, center_lat, center_lng,
                              area_hectares, current_crop
                       FROM fields ORDER BY id"""
                )
            ).mappings().all()
        return [dict(r) for r in rows]
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
