export type UserRole = 'admin' | 'researcher' | 'farmer' | 'consultant';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
  organization?: string;
  region: string;
  preferences: {
    unitSystem: 'metric' | 'imperial';
    theme: 'dark' | 'light';
    autoSaveSimulations: boolean;
    highContrast3D: boolean;
    emailAlerts: boolean;
  };
}

export interface SoilProfile {
  type: 'sandy_loam' | 'silty_clay' | 'clay_loam' | 'loam' | 'sandy_clay_loam';
  label: string;
  sandPercent: number;
  clayPercent: number;
  siltPercent: number;
  organicMatterPercent: number;
  bulkDensity: number; // g/cm³
  fieldCapacity: number; // cm³/cm³ (e.g. 0.28)
  wiltingPoint: number; // cm³/cm³ (e.g. 0.12)
  saturation: number; // cm³/cm³ (e.g. 0.44)
  saturatedConductivityKs: number; // mm/day
  alphaVanGenuchten: number; // 1/cm
  nVanGenuchten: number; // dimensionless
}

export interface FieldPolygon {
  type: 'Polygon';
  coordinates: [number, number][]; // [lat, lng][]
}

export interface Field {
  id: string;
  name: string;
  locationName: string;
  country: string;
  centerLat: number;
  centerLng: number;
  areaHectares: number;
  polygon: FieldPolygon;
  soilProfile: SoilProfile;
  altitudeMeters: number;
  currentCrop: string;
  notes?: string;
}

export type ClimateScenario = 'SSP1-2.6' | 'SSP3-7.0' | 'SSP5-8.5';
export type MaizeVariety = 'short_cycle' | 'medium_cycle' | 'long_cycle';
export type IrrigationStrategy = 'rainfed' | 'deficit_50' | 'optimal_100' | 'smart_sensor';

export interface SimulationConfig {
  id: string;
  fieldId: string;
  scenario: ClimateScenario;
  targetYear: number;
  plantingDate: string; // YYYY-MM-DD
  maizeVariety: MaizeVariety;
  irrigationStrategy: IrrigationStrategy;
  soilMoistureInitialPercent: number; // 0-100% of available water capacity
  nitrogenApplicationKgHa: number; // kg N / ha
  carbonDioxidePpm: number; // e.g. 440, 560, 680
  temperatureAnomalyC: number; // e.g. +1.2, +2.4
  precipitationAnomalyPercent: number; // e.g. -15%
}

export interface DailySimulationRecord {
  day: number; // Day of year (1-365)
  dap: number; // Days after planting (1-140)
  date: string; // YYYY-MM-DD
  gddAccumulated: number; // Growing Degree Days
  stage: 'Emergence' | 'V3' | 'V6' | 'V12' | 'VT (Tasseling)' | 'R1 (Silking)' | 'R3 (Milk)' | 'R6 (Maturity)';
  stageCode: 'VE' | 'V3' | 'V6' | 'V12' | 'VT' | 'R1' | 'R3' | 'R6';
  biomassKgHa: number;
  lai: number; // Leaf Area Index m²/m²
  rootDepthCm: number;
  canopyHeightM: number;
  
  // Soil Moisture at 3 depths (volumetric moisture θ cm³/cm³)
  soilMoistureTop: number; // 0-30 cm
  soilMoistureMid: number; // 30-60 cm
  soilMoistureDeep: number; // 60-100 cm
  soilMoistureAvg: number;
  
  // Water fluxes & ET
  etoMm: number; // Reference ET (Priestley-Taylor / Penman-Monteith)
  etcMm: number; // Crop ET
  transpirationMm: number;
  evaporationMm: number;
  precipitationMm: number;
  irrigationMm: number;
  runoffMm: number;
  deepDrainageMm: number;
  
  // Stress indices
  cwsi: number; // Crop Water Stress Index (0 = no stress, 1 = severe drought)
  thermalStressFactor: number; // 0-1
  dailyYieldLossPotentialKgHa: number;
  
  // Weather drivers
  tempMaxC: number;
  tempMinC: number;
  solarRadiationMjM2: number;
  vpdKpa: number; // Vapor pressure deficit
}

export interface SimulationResult {
  id: string;
  config: SimulationConfig;
  fieldName: string;
  fieldLocation: string;
  createdAt: string;
  
  summaryKPIs: {
    projectedYieldKgHa: number;
    potentialYieldKgHa: number;
    yieldLossDueToDroughtPercent: number;
    totalBiomassKgHa: number;
    totalWaterConsumedMm: number;
    waterProductivityKgM3: number; // kg grain per m³ water
    totalPrecipitationMm: number;
    totalIrrigationAppliedMm: number;
    peakWaterStressIndex: number;
    avgWaterStressIndex: number;
    criticalDroughtDaysCount: number;
    daysToMaturity: number;
    droughtResilienceScore: number; // 0 - 100
    economicReturnUsdHa: number;
  };
  
  dailyRecords: DailySimulationRecord[];
  
  soilDynamics: {
    fieldCapacity: number;
    wiltingPoint: number;
    saturation: number;
  };
  
  pinnValidationMetrics: {
    pdeResidualRichardsLoss: number;
    boundaryConditionLoss: number;
    empiricalNassLoss: number;
    totalLoss: number;
    inferenceTimeMs: number;
    physicsConservationErrorPercent: number;
    r2Score: number;
  };
  
  alerts: {
    id: string;
    level: 'info' | 'warning' | 'critical';
    title: string;
    description: string;
    timing: string;
    recommendedAction: string;
  }[];
  
  agronomicRecommendations: string[];
}

export interface WhatIfScenarioComparison {
  scenarioA: { name: string; config: SimulationConfig; result: SimulationResult };
  scenarioB: { name: string; config: SimulationConfig; result: SimulationResult };
  scenarioC: { name: string; config: SimulationConfig; result: SimulationResult };
}

export interface ModelRegistryEntry {
  version: string;
  name: string;
  architecture: string;
  trainedDate: string;
  epochs: number;
  richardsWeightLambda: number;
  testR2: number;
  testRmseKgHa: number;
  active: boolean;
  status: 'production' | 'staging' | 'archived';
  description: string;
}

export interface IngestionPipeline {
  id: string;
  name: string;
  source: string;
  frequency: string;
  lastSync: string;
  status: 'healthy' | 'running' | 'warning' | 'error';
  recordsProcessed: string;
  resolution: string;
  description: string;
}
