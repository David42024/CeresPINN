import pandas as pd
import json
from pathlib import Path
from backend.data.config import Settings

def main():
    print("Iniciando construcción del panel canónico con CLIMA REAL (Paso 3 a 6)...")
    settings = Settings()
    
    nass_path = settings.paths.processed / "nass_clean.parquet"
    noaa_path = settings.paths.processed / "noaa_climate.parquet"
    
    if not nass_path.exists() or not noaa_path.exists():
        print("Error: Ejecuta clean_nass.py y noaa_cag.py primero.")
        return
        
    nass_df = pd.read_parquet(nass_path)
    climate_df = pd.read_parquet(noaa_path)
    
    # Paso 6: Producir el panel canónico
    panel = pd.merge(nass_df, climate_df, on=["year", "fips"], how="inner")
    
    out_dir = settings.paths.processed
    panel_path = out_dir / "canonical_panel.parquet"
    panel.to_parquet(panel_path, index=False)
    
    # Save CSV for humans
    csv_path = out_dir / "canonical_panel_sample.csv"
    panel.sample(min(100, len(panel))).to_csv(csv_path, index=False)
    
    import hashlib
    h = hashlib.sha256(panel.to_csv(index=False).encode('utf-8')).hexdigest()
    
    manifest = {
        "dataset_name": "CeresPINN Canonical Historical Panel",
        "rows": len(panel),
        "years": sorted([int(y) for y in panel['year'].unique()]),
        "counties": len(panel['fips'].unique()),
        "missing_values_percent": round(panel.isna().mean().mean() * 100, 2),
        "sha256": h,
        "sources": {
            "yield": "USDA NASS QuickStats (Real)",
            "climate": "NOAA NCEI Climate at a Glance API (Real Observacional)",
            "soil": "Excluded (Fase 2 Paso 5)"
        }
    }
    manifest_path = out_dir / "canonical_panel_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    print(f"Panel canónico guardado en {panel_path}")
    print(f"Filas totales (Matching yields + clima real): {len(panel)}")

if __name__ == "__main__":
    main()
