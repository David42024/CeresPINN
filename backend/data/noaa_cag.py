import os
import requests
import pandas as pd
import numpy as np
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.data.config import Settings

def fetch_noaa_cag_for_fips(state_alpha, fips_3, var, start_year=1990, end_year=2025):
    url = f"https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/county/time-series/{state_alpha}-{fips_3}/{var}/6/9/{start_year}-{end_year}.json"
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=10)
            if resp.ok:
                data = resp.json().get('data', {})
                return {int(k[:4]): float(v['value']) for k, v in data.items() if k.endswith('09')}
            elif resp.status_code == 404:
                return {}
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    return {}

def process_county(fips):
    fips_3 = fips[-3:]
    tavg = fetch_noaa_cag_for_fips("IA", fips_3, "tavg")
    tmax = fetch_noaa_cag_for_fips("IA", fips_3, "tmax")
    pcp = fetch_noaa_cag_for_fips("IA", fips_3, "pcp")
    cdd = fetch_noaa_cag_for_fips("IA", fips_3, "cdd")
    
    years = set(tavg.keys()) | set(tmax.keys()) | set(pcp.keys()) | set(cdd.keys())
    records = []
    for year in years:
        records.append({
            "year": year,
            "fips": fips,
            "season_temp_mean_f": tavg.get(year, None),
            "season_tmax_mean_f": tmax.get(year, None),
            "season_precip_in": pcp.get(year, None),
            "cdd_f": cdd.get(year, None)
        })
    return records

def main():
    settings = Settings()
    out_dir = settings.paths.processed
    
    nass_path = out_dir / "nass_clean.parquet"
    if not nass_path.exists():
        return
        
    df = pd.read_parquet(nass_path)
    fips_list = [f for f in df['fips'].unique() if f.startswith("19")]
    
    print(f"Fetching real NOAA climate data for {len(fips_list)} counties with threads...", flush=True)
    
    all_records = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_county, fips) for fips in fips_list]
        for idx, future in enumerate(as_completed(futures)):
            all_records.extend(future.result())
            if idx % 10 == 0:
                print(f"Progress: {idx}/{len(fips_list)}", flush=True)
                
    climate_df = pd.DataFrame(all_records).dropna().copy()
    
    climate_df['season_temp_mean_c'] = (climate_df['season_temp_mean_f'] - 32) * (5/9)
    climate_df['season_tmax_mean_c'] = (climate_df['season_tmax_mean_f'] - 32) * (5/9)
    climate_df['season_precip_mm'] = climate_df['season_precip_in'] * 25.4
    climate_df['cdd'] = climate_df['cdd_f'] * (5/9)
    
    climate_df['gdd'] = np.maximum(0, climate_df['season_temp_mean_c'] - 10) * 153
    climate_df['heat_days_30c'] = np.maximum(0, (climate_df['season_tmax_mean_c'] - 28) * 4).astype(int)
    climate_df['heat_days_35c'] = np.maximum(0, (climate_df['season_tmax_mean_c'] - 33) * 2).astype(int)
    climate_df['vpd_mean_kpa'] = 1.2 + (climate_df['season_temp_mean_c'] - 14) * 0.05
    
    climate_df = climate_df.drop(columns=['season_temp_mean_f', 'season_tmax_mean_f', 'season_precip_in', 'cdd_f'])
    
    out_path = out_dir / "noaa_climate.parquet"
    climate_df.to_parquet(out_path, index=False)
    print(f"Descargados {len(climate_df)} registros. Guardado en {out_path}", flush=True)

if __name__ == "__main__":
    main()
