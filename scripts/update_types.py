import os

file_path = "src/types/index.ts"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """export interface SimulationResult {
  id: string;
  inferenceMode: 'pinn' | 'local-fallback' | 'pinn-calibrated-surrogate' | 'unavailable';
  modelName?: string;
  modelDataSource?: string;
  modelUsesRealData?: boolean;
  scientificScope?: {"""

replacement = """export interface SimulationResult {
  id: string;
  inferenceMode: 'trained_ml' | 'pinn' | 'local-fallback' | 'pinn-calibrated-surrogate' | 'unavailable';
  modelName?: string;
  modelVersion?: string;
  modelVerified?: boolean;
  predictionScope?: string;
  datasetSha256?: string;
  predictionInterval90?: { lowerKgHa: number; upperKgHa: number };
  isExtrapolation?: boolean;
  extrapolatedFeatures?: string[];
  componentProvenance?: {
    yield: string;
    dailyRecords: string;
    economics: string;
    managementEffect: string;
  };
  modelDataSource?: string;
  modelUsesRealData?: boolean;
  scientificScope?: {"""

target = target.replace('\n', '\r\n') if '\r\n' in content else target

if target in content:
    content = content.replace(target, replacement)
else:
    target = target.replace('\r\n', '\n')
    if target in content:
        content = content.replace(target, replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated index.ts successfully")
