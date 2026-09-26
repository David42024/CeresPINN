import os

file_path = "backend/training/dataset.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target1 = """    # Deterministic county-aggregate: median yield per year (keeps frame small/loss calm).
    annual = (
        norm.groupby("year")["yield_bu_acre"]
        .median()
        .reset_index()
    )"""

replacement1 = """    # Instead of median aggregate, we use the raw county observations for the panel.
    annual = norm.copy()"""

target2 = """    # Scenario expansion: every county-year row is replicated across the SSP scenarios
    # because a projected twin is scenario-conditional.
    scenarios = np.array([s for s in SCENARIO_TEMPLATE for _ in annual.index])
    years = np.tile(annual["year"].to_numpy(), len(SCENARIO_TEMPLATE))
    y = np.tile(annual["yield_bu_acre"].to_numpy(), len(SCENARIO_TEMPLATE))

    climate = _blend_climate(years.astype(int), scenarios, nex_summary)
    X = climate[train_config.feature_names].to_numpy(dtype=float)"""

replacement2 = """    # Stop expanding historical scenarios across SSPs!
    # A historical observation belongs to the historical climate.
    years = annual["year"].to_numpy(dtype=int)
    scenarios = np.array(["historical"] * len(years))
    y = annual["yield_bu_acre"].to_numpy()

    climate = _blend_climate(years, scenarios, nex_summary)
    
    # Map old features to new DataSchemaConfig features
    if "season_temp_mean_c" not in climate.columns:
        climate["season_temp_mean_c"] = 14.0 + climate.get("temp_anomaly_c", 0.0)
    if "season_tmax_mean_c" not in climate.columns:
        climate["season_tmax_mean_c"] = climate["season_temp_mean_c"] + 8.0
    if "gdd" not in climate.columns:
        climate["gdd"] = np.maximum(0, climate["season_temp_mean_c"] - 10) * 153
    if "cdd" not in climate.columns:
        climate["cdd"] = climate.get("seasonal_cdd", 20.0)
    if "heat_days_30c" not in climate.columns:
        climate["heat_days_30c"] = (climate.get("heatwave_risk", 0.0) * 30).astype(int)
    if "heat_days_35c" not in climate.columns:
        climate["heat_days_35c"] = (climate.get("heatwave_risk", 0.0) * 10).astype(int)
    if "vpd_mean_kpa" not in climate.columns:
        climate["vpd_mean_kpa"] = 1.2
        
    X = climate[train_config.feature_names].to_numpy(dtype=float)"""

# In case of CRLF
target1 = target1.replace("\n", "\r\n") if "\r\n" in content else target1
target2 = target2.replace("\n", "\r\n") if "\r\n" in content else target2

content = content.replace(target1, replacement1)
content = content.replace(target2, replacement2)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated dataset.py successfully")
