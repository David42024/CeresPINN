import os
import re

file_path = "backend/training/dataset.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """    climate = _blend_climate(yy.astype(int), scenarios, None)
    X = climate[train_config.feature_names].to_numpy(dtype=float)"""

replacement = """    climate = _blend_climate(yy.astype(int), scenarios, None)
    
    # Map old features to new DataSchemaConfig features for synthetic
    if "season_temp_mean_c" not in climate.columns:
        climate["season_temp_mean_c"] = 14.0 + climate.get("temp_anomaly_c", 0.0)
    if "season_tmax_mean_c" not in climate.columns:
        climate["season_tmax_mean_c"] = climate["season_temp_mean_c"] + 8.0
    if "gdd" not in climate.columns:
        climate["gdd"] = (climate["season_temp_mean_c"] - 10) * 153
    if "cdd" not in climate.columns:
        climate["cdd"] = climate.get("seasonal_cdd", 20.0)
    if "heat_days_30c" not in climate.columns:
        climate["heat_days_30c"] = (climate.get("heatwave_risk", 0.0) * 30).astype(int)
    if "heat_days_35c" not in climate.columns:
        climate["heat_days_35c"] = (climate.get("heatwave_risk", 0.0) * 10).astype(int)
    if "vpd_mean_kpa" not in climate.columns:
        climate["vpd_mean_kpa"] = 1.2
        
    X = climate[train_config.feature_names].to_numpy(dtype=float)"""

target = target.replace('\n', '\r\n') if '\r\n' in content else target

if target in content:
    content = content.replace(target, replacement)
else:
    target = target.replace('\r\n', '\n')
    if target in content:
        content = content.replace(target, replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated synthetic dataset successfully")
