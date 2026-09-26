import os

file_path = "backend/training/dataset.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """    if "season_temp_mean_c" not in climate.columns:"""

replacement = """    if "season_precip_mm" not in climate.columns:
        climate["season_precip_mm"] = 400.0 * (1 + climate.get("precip_anomaly_percent", 0.0) / 100.0)
    if "season_temp_mean_c" not in climate.columns:"""

target = target.replace('\n', '\r\n') if '\r\n' in content else target

if target in content:
    content = content.replace(target, replacement)
else:
    target = target.replace('\r\n', '\n')
    if target in content:
        content = content.replace(target, replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated synthetic dataset precip successfully")
