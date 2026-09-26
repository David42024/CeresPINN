import os
import pandas as pd
import numpy as np
from pathlib import Path
import json
from backend.data.config import Settings

def main():
    print("Iniciando normalización de NASS (Paso 2)...")
    settings = Settings()
    
    raw_path = settings.paths.nass / "maize_county_yield_usda.csv"
    if not raw_path.exists():
        print(f"Error: No se encontró el dataset en {raw_path}")
        return
        
    df = pd.read_csv(raw_path)
    print(f"Filas originales: {len(df)}")
    
    # 1. Eliminar duplicados exactos
    df = df.drop_duplicates().copy()
    print(f"Filas tras eliminar duplicados: {len(df)}")
    
    # 2. Convertir 'Value' a numérico, resolver símbolos (e.g., (D))
    # coerces invalid parsing to NaN
    df['Value'] = pd.to_numeric(df['Value'].astype(str).str.replace(',', ''), errors='coerce')
    
    # 3. Unificar unidades (BU / ACRE -> kg/ha)
    # 1 bushel of maize per acre = 62.77 kg / ha
    df['yield_kg_ha'] = df['Value'] * 62.77
    
    # Drop rows where yield couldn't be parsed
    df = df.dropna(subset=['yield_kg_ha']).copy()
    
    # 4. Marcar outliers (e.g., valores extremos) sin eliminarlos
    # Using simple interquartile range across the whole state as a robust rule, or just fixed thresholds.
    # We will use fixed thresholds for corn in Iowa to flag them for review.
    # Historical ranges usually between 30 and 250 bu/acre (approx 1800 to 15600 kg/ha).
    upper_bound = 250 * 62.77
    lower_bound = 15 * 62.77
    df['is_outlier'] = (df['yield_kg_ha'] > upper_bound) | (df['yield_kg_ha'] < lower_bound)
    
    # Create the 'FIPS' code standardized
    # state_fips and county_fips might be parsed as floats or integers. We want a 5-digit string.
    # Note: earlier output showed 'state_fips' and 'county_fips'.
    if 'state_fips' in df.columns and 'county_fips' in df.columns:
        df['state_fips_str'] = df['state_fips'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(2)
        df['county_fips_str'] = df['county_fips'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3)
        df['fips'] = df['state_fips_str'] + df['county_fips_str']
    else:
        df['fips'] = "UNKNOWN"
        
    # Reordenar y limpiar columnas
    clean_df = df[['year', 'fips', 'state_alpha', 'county_name', 'yield_kg_ha', 'is_outlier']].copy()
    clean_df = clean_df.sort_values(by=['year', 'fips'])
    
    # 5. Guardar en Parquet (Paso 6 requiere Parquet para el panel final, guardamos este paso también en Parquet)
    out_dir = settings.paths.processed
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "nass_clean.parquet"
    clean_df.to_parquet(out_path, index=False)
    
    # Manifiesto
    manifest = {
        "source": "USDA NASS QuickStats",
        "rows_raw": len(pd.read_csv(raw_path)),
        "rows_clean": len(clean_df),
        "outliers_flagged": int(clean_df['is_outlier'].sum()),
        "years": clean_df['year'].unique().tolist(),
        "counties_unique": len(clean_df['fips'].unique())
    }
    manifest_path = out_dir / "nass_clean_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    print(f"Normalización completada. Archivo guardado en {out_path}")
    print(f"Outliers marcados: {manifest['outliers_flagged']}")

if __name__ == "__main__":
    main()
