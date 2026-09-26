import os
import re

file_path = "src/services/api.ts"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """    id: response?.id ?? `sim-${Date.now()}`,
    inferenceMode: response?.inference_mode ?? 'unavailable',
    modelName: response?.model_name ?? 'CeresPINN',
    modelDataSource: response?.model_data_source,
    modelUsesRealData: response?.model_uses_real_data === true,
    scientificScope: response?.scientific_scope ? {"""

replacement = """    id: response?.id ?? `sim-${Date.now()}`,
    inferenceMode: response?.inference_mode ?? 'unavailable',
    modelName: response?.model_name ?? 'CeresPINN',
    modelVersion: response?.model_version,
    modelVerified: response?.model_verified,
    predictionScope: response?.prediction_scope,
    datasetSha256: response?.dataset_sha256,
    predictionInterval90: response?.prediction_interval_90 ? {
      lowerKgHa: response.prediction_interval_90.lower_kg_ha,
      upperKgHa: response.prediction_interval_90.upper_kg_ha,
    } : undefined,
    isExtrapolation: response?.is_extrapolation,
    extrapolatedFeatures: response?.extrapolated_features,
    componentProvenance: response?.component_provenance ? {
      yield: response.component_provenance.yield,
      dailyRecords: response.component_provenance.daily_records,
      economics: response.component_provenance.economics,
      managementEffect: response.component_provenance.management_effect,
    } : undefined,
    modelDataSource: response?.model_data_source,
    modelUsesRealData: response?.model_uses_real_data === true,
    scientificScope: response?.scientific_scope ? {"""

target = target.replace('\n', '\r\n') if '\r\n' in content else target

if target in content:
    content = content.replace(target, replacement)
else:
    target = target.replace('\r\n', '\n')
    if target in content:
        content = content.replace(target, replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated api.ts mappings successfully")
