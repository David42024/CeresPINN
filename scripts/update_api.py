import os
import re

file_path = "src/services/api.ts"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """const assertRemotePinnPayload = (payload: any) => {
  if (!REQUIRE_REMOTE_PINN) return;
  if (payload?.inference_mode !== 'pinn') {
    throw new Error(`Render returned inference_mode=${payload?.inference_mode ?? 'missing'}; trained PINN required.`);
  }
  if (payload?.model_uses_real_data !== true) {
    throw new Error(`Render returned data_source=${payload?.model_data_source ?? 'missing'}; USDA NASS + NASA NEX-GDDP checkpoint required.`);
  }
  if (
    payload?.scientific_scope?.use_classification !== 'exploratory_research_only'
    || payload?.scientific_scope?.territorial_prioritization_supported !== false
  ) {
    throw new Error('Render response is missing the required exploratory-use decision scope.');
  }
  const requiredNumbers = [
    'projected_yield_kg_ha',
    'potential_yield_kg_ha',
    'yield_loss_due_to_drought_percent',
    'total_biomass_kg_ha',
    'total_water_consumed_mm',
    'water_productivity_kg_m3',
    'total_precipitation_mm',
    'total_irrigation_applied_mm',
    'peak_water_stress_index',
    'avg_water_stress_index',
    'critical_drought_days_count',
    'days_to_maturity',
    'drought_resilience_score',
    'economic_return_usd_ha',
  ];
  const missing = requiredNumbers.filter(key => !Number.isFinite(Number(payload?.[key])));
  if (missing.length || !Array.isArray(payload?.daily_records) || payload.daily_records.length === 0) {
    throw new Error(`Incomplete PINN response from Render. Invalid fields: ${missing.join(', ') || 'daily_records'}.`);
  }
};"""

replacement = """const assertRemotePinnPayload = (payload: any) => {
  if (!REQUIRE_REMOTE_PINN) return;
  if (payload?.model_verified !== true) {
    throw new Error(`Render returned model_verified=${payload?.model_verified ?? 'missing'}; verified model required.`);
  }
  if (!payload?.model_version) {
    throw new Error('Render response is missing model_version.');
  }
  if (!payload?.prediction_interval_90) {
    throw new Error('Render response is missing prediction_interval_90.');
  }
  if (!payload?.component_provenance) {
    throw new Error('Render response is missing component_provenance.');
  }
  if (payload?.model_uses_real_data !== true) {
    throw new Error(`Render returned data_source=${payload?.model_data_source ?? 'missing'}; USDA NASS + NASA NEX-GDDP checkpoint required.`);
  }
  if (
    payload?.scientific_scope?.use_classification !== 'exploratory_research_only'
    || payload?.scientific_scope?.territorial_prioritization_supported !== false
  ) {
    throw new Error('Render response is missing the required exploratory-use decision scope.');
  }
  const requiredNumbers = [
    'projected_yield_kg_ha',
    'potential_yield_kg_ha',
    'yield_loss_due_to_drought_percent',
    'total_biomass_kg_ha',
    'total_water_consumed_mm',
    'water_productivity_kg_m3',
    'total_precipitation_mm',
    'total_irrigation_applied_mm',
    'peak_water_stress_index',
    'avg_water_stress_index',
    'critical_drought_days_count',
    'days_to_maturity',
    'drought_resilience_score',
    'economic_return_usd_ha',
  ];
  const missing = requiredNumbers.filter(key => !Number.isFinite(Number(payload?.[key])));
  if (missing.length || !Array.isArray(payload?.daily_records) || payload.daily_records.length === 0) {
    throw new Error(`Incomplete response from Render. Invalid fields: ${missing.join(', ') || 'daily_records'}.`);
  }
};"""

target = target.replace('\n', '\r\n') if '\r\n' in content else target

if target in content:
    content = content.replace(target, replacement)
else:
    # Try just removing \r just in case
    target = target.replace('\r\n', '\n')
    if target in content:
        content = content.replace(target, replacement)
    else:
        print("Target not found.")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated api.ts successfully")
