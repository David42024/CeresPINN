#!/usr/bin/env python3
"""CeresPINN - Script de Seedeo de Base de Datos.

Uso desde la raiz del proyecto:
    python -m backend.seed

O desde dentro de backend/:
    python seed.py
"""
from __future__ import annotations
import sys, os

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

from backend.db import (
    get_engine, init_db, available, _connect,
    _USERS_SEED, _FIELDS_SEED, _SCENARIOS_SEED, _REPORTS_SEED,
    _INGESTION_PIPELINES_SEED, _SOIL_PROFILES_SEED,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


def _is_sqlite():
    e = get_engine()
    return e is not None and "sqlite" in str(e.url)


def _sqlite_or_pg(conn, sqlite_sql, pg_sql, rows):
    stmt = text(sqlite_sql if _is_sqlite() else pg_sql)
    for row in rows:
        conn.execute(stmt, row)
    return len(rows)


def run_seed():
    print("=" * 60)
    print("  CeresPINN - Seedeo de Base de Datos")
    print("=" * 60)

    if not available():
        print("\n  BD no disponible. Verifica DATABASE_URL.")
        sys.exit(1)

    engine = get_engine()
    db_type = "SQLite" if "sqlite" in str(engine.url) else "PostgreSQL"
    print(f"\nConectado a: {db_type}")
    if "sqlite" in str(engine.url):
        print(f"Archivo: {str(engine.url).replace('sqlite:///', '')}")
    print()

    print("Inicializando esquema de tablas...")
    init_db()
    print("Tablas OK\n")

    totals = {}
    with _connect() as conn:
        try:
            # Soil profiles
            totals["soil_profiles"] = _sqlite_or_pg(conn,
                """INSERT OR REPLACE INTO soil_profiles
                   (id,label,sand_percent,clay_percent,silt_percent,organic_matter_percent,
                    bulk_density,field_capacity,wilting_point,saturation,
                    saturated_conductivity_ks,alpha_van_genuchten,n_van_genuchten)
                   VALUES(:id,:label,:sand_percent,:clay_percent,:silt_percent,
                    :organic_matter_percent,:bulk_density,:field_capacity,:wilting_point,
                    :saturation,:saturated_conductivity_ks,:alpha_van_genuchten,:n_van_genuchten)""",
                """INSERT INTO soil_profiles
                   (id,label,sand_percent,clay_percent,silt_percent,organic_matter_percent,
                    bulk_density,field_capacity,wilting_point,saturation,
                    saturated_conductivity_ks,alpha_van_genuchten,n_van_genuchten)
                   VALUES(:id,:label,:sand_percent,:clay_percent,:silt_percent,
                    :organic_matter_percent,:bulk_density,:field_capacity,:wilting_point,
                    :saturation,:saturated_conductivity_ks,:alpha_van_genuchten,:n_van_genuchten)
                   ON CONFLICT(id) DO NOTHING""",
                _SOIL_PROFILES_SEED)

            # Fields
            totals["fields"] = _sqlite_or_pg(conn,
                """INSERT OR REPLACE INTO fields
                   (id,name,location_name,country,center_lat,center_lng,
                    area_hectares,altitude_meters,current_crop,soil_profile,polygon,notes)
                   VALUES(:id,:name,:location_name,:country,:center_lat,:center_lng,
                    :area_hectares,:altitude_meters,:current_crop,:soil_profile,:polygon,:notes)""",
                """INSERT INTO fields
                   (id,name,location_name,country,center_lat,center_lng,
                    area_hectares,altitude_meters,current_crop,soil_profile,polygon,notes)
                   VALUES(:id,:name,:location_name,:country,:center_lat,:center_lng,
                    :area_hectares,:altitude_meters,:current_crop,:soil_profile,:polygon,:notes)
                   ON CONFLICT(id) DO UPDATE SET
                    name=EXCLUDED.name,current_crop=EXCLUDED.current_crop""",
                _FIELDS_SEED)

            # Scenarios
            totals["scenarios"] = _sqlite_or_pg(conn,
                "INSERT OR REPLACE INTO scenarios (id,label,risk) VALUES(:id,:label,:risk)",
                """INSERT INTO scenarios (id,label,risk) VALUES(:id,:label,:risk)
                   ON CONFLICT(id) DO UPDATE SET label=EXCLUDED.label,risk=EXCLUDED.risk""",
                _SCENARIOS_SEED)

            # Reports
            stmt_r = text(
                "INSERT OR REPLACE INTO reports (id,title,generated_at,summary,payload) VALUES(:id,:title,:generated_at,:summary,:payload)"
                if _is_sqlite() else
                """INSERT INTO reports (id,title,generated_at,summary,payload)
                   VALUES(:id,:title,:generated_at,:summary,:payload) ON CONFLICT(id) DO NOTHING"""
            )
            conn.execute(stmt_r, _REPORTS_SEED)
            totals["reports"] = 1

            # Pipelines
            totals["ingestion_pipelines"] = _sqlite_or_pg(conn,
                """INSERT OR REPLACE INTO ingestion_pipelines
                   (id,name,source,frequency,last_sync,status,records_processed,resolution,description)
                   VALUES(:id,:name,:source,:frequency,:last_sync,:status,:records_processed,:resolution,:description)""",
                """INSERT INTO ingestion_pipelines
                   (id,name,source,frequency,last_sync,status,records_processed,resolution,description)
                   VALUES(:id,:name,:source,:frequency,:last_sync,:status,:records_processed,:resolution,:description)
                   ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,last_sync=EXCLUDED.last_sync""",
                _INGESTION_PIPELINES_SEED)

            # Users
            totals["users"] = _sqlite_or_pg(conn,
                """INSERT OR REPLACE INTO users
                   (id,name,email,role,avatar_url,organization,region,preferences)
                   VALUES(:id,:name,:email,:role,:avatar_url,:organization,:region,:preferences)""",
                """INSERT INTO users
                   (id,name,email,role,avatar_url,organization,region,preferences)
                   VALUES(:id,:name,:email,:role,:avatar_url,:organization,:region,:preferences)
                   ON CONFLICT(id) DO UPDATE SET
                    name=EXCLUDED.name,email=EXCLUDED.email,role=EXCLUDED.role,
                    organization=EXCLUDED.organization,region=EXCLUDED.region""",
                _USERS_SEED)

            conn.commit()
        except SQLAlchemyError as exc:
            conn.rollback()
            print(f"Error durante seed: {exc}")
            sys.exit(1)

    print("Datos insertados/actualizados:")
    for table, count in totals.items():
        print(f"  {table:<25} {count:>3} registro(s)")

    print()
    print("=" * 60)
    print("  Credenciales de Login (todas con password: Ceres2026!)")
    print("=" * 60)
    creds = [
        ("admin",      "admin@agri.com"),
        ("researcher", "m.vance@agri-ai-lab.edu"),
        ("farmer",     "carlos.mendez@agrovalle.com"),
        ("consultant", "sofia.morales@climateresilient.tech"),
    ]
    for role, email in creds:
        print(f"  [{role:>12}]  {email}")
    print()
    print("NOTA: El login es FRONTEND-ONLY.")
    print("      Credenciales en: src/components/LoginScreen.tsx -> DEMO_CREDENTIALS")
    print()
    print("Seed completado exitosamente.")


if __name__ == "__main__":
    run_seed()
