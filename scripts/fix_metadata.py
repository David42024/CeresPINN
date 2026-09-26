import re

# Fix db.py pipelines
db_file = "backend/db.py"
with open(db_file, "r", encoding="utf-8") as f:
    content = f.read()

start_str = "_INGESTION_PIPELINES_SEED: List[Dict[str, Any]] = ["
end_str = "_USERS_SEED: List[Dict[str, Any]] = ["

start_idx = content.find(start_str)
end_idx = content.find(end_str)

new_pipelines = """_INGESTION_PIPELINES_SEED: List[Dict[str, Any]] = [
    {
        "id": "pipe-noaa-cag",
        "name": "NOAA NCEI Climate at a Glance",
        "source": "NOAA (API Observacional Real)",
        "frequency": "Mensual",
        "last_sync": "2026-09-25",
        "status": "healthy",
        "records_processed": "3,564 registros (Iowa)",
        "resolution": "Nivel Condado",
        "description": "Temperatura máxima, media, precipitaciones estacionales y CDD por condado para Iowa (1990-2025).",
    },
    {
        "id": "pipe-usda-nass",
        "name": "USDA NASS QuickStats",
        "source": "USDA NASS API (Real)",
        "frequency": "Mensual",
        "last_sync": "2026-09-25",
        "status": "healthy",
        "records_processed": "3,476 observaciones de rendimiento",
        "resolution": "Nivel Condado",
        "description": "Datos históricos de rendimiento de maíz observados en Iowa.",
    }
]

"""

content = content[:start_idx] + new_pipelines + content[end_idx:]
with open(db_file, "w", encoding="utf-8") as f:
    f.write(content)

# Fix app.py health database
app_file = "backend/app.py"
with open(app_file, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"database": "postgresql+postgis"', '"database": "sqlite3"')
content = content.replace('"database": "PostgreSQL/PostGIS"', '"database": "SQLite Local"')
with open(app_file, "w", encoding="utf-8") as f:
    f.write(content)

print("DB and App patched")
