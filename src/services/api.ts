import type { DailySimulationRecord, Field, SimulationConfig, SimulationResult } from '../types';
import { runPINNSimulation } from './pinnEngine';
import { DEFAULT_FIELDS, SOIL_PROFILES } from '../data/mockData';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';

const safeNumber = (value: unknown, fallback: number) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
};

const mapStage = (value: unknown): DailySimulationRecord['stage'] => {
  const stage = String(value ?? 'Emergence');
  const validStages: DailySimulationRecord['stage'][] = [
    'Emergence',
    'V3',
    'V6',
    'V12',
    'VT (Tasseling)',
    'R1 (Silking)',
    'R3 (Milk)',
    'R6 (Maturity)',
  ];

  return validStages.includes(stage as DailySimulationRecord['stage'])
    ? (stage as DailySimulationRecord['stage'])
    : 'Emergence';
};

const mapStageCode = (value: unknown): DailySimulationRecord['stageCode'] => {
  const stageCode = String(value ?? 'VE');
  const validCodes: DailySimulationRecord['stageCode'][] = ['VE', 'V3', 'V6', 'V12', 'VT', 'R1', 'R3', 'R6'];

  return validCodes.includes(stageCode as DailySimulationRecord['stageCode'])
    ? (stageCode as DailySimulationRecord['stageCode'])
    : 'VE';
};

const mapBackendSimulation = (field: Field, config: SimulationConfig, response: any): SimulationResult => {
  const dailyRecords = Array.isArray(response?.daily_records) ? response.daily_records : [];

  return {
    id: response?.id ?? `sim-${Date.now()}`,
    config,
    fieldName: field.name,
    fieldLocation: `${field.locationName}, ${field.country}`,
    createdAt: new Date().toISOString(),
    summaryKPIs: {
      projectedYieldKgHa: safeNumber(response?.projected_yield_kg_ha, runPINNSimulation(field, config).summaryKPIs.projectedYieldKgHa),
      potentialYieldKgHa: safeNumber(response?.potential_yield_kg_ha, runPINNSimulation(field, config).summaryKPIs.potentialYieldKgHa),
      yieldLossDueToDroughtPercent: safeNumber(response?.yield_loss_due_to_drought_percent, runPINNSimulation(field, config).summaryKPIs.yieldLossDueToDroughtPercent),
      totalBiomassKgHa: safeNumber(response?.total_biomass_kg_ha, runPINNSimulation(field, config).summaryKPIs.totalBiomassKgHa),
      totalWaterConsumedMm: safeNumber(response?.total_water_consumed_mm, runPINNSimulation(field, config).summaryKPIs.totalWaterConsumedMm),
      waterProductivityKgM3: safeNumber(response?.water_productivity_kg_m3, runPINNSimulation(field, config).summaryKPIs.waterProductivityKgM3),
      totalPrecipitationMm: safeNumber(response?.total_precipitation_mm, runPINNSimulation(field, config).summaryKPIs.totalPrecipitationMm),
      totalIrrigationAppliedMm: safeNumber(response?.total_irrigation_applied_mm, runPINNSimulation(field, config).summaryKPIs.totalIrrigationAppliedMm),
      peakWaterStressIndex: safeNumber(response?.peak_water_stress_index, runPINNSimulation(field, config).summaryKPIs.peakWaterStressIndex),
      avgWaterStressIndex: safeNumber(response?.avg_water_stress_index, runPINNSimulation(field, config).summaryKPIs.avgWaterStressIndex),
      criticalDroughtDaysCount: safeNumber(response?.critical_drought_days_count, runPINNSimulation(field, config).summaryKPIs.criticalDroughtDaysCount),
      daysToMaturity: safeNumber(response?.days_to_maturity, runPINNSimulation(field, config).summaryKPIs.daysToMaturity),
      droughtResilienceScore: safeNumber(response?.drought_resilience_score, runPINNSimulation(field, config).summaryKPIs.droughtResilienceScore),
      economicReturnUsdHa: safeNumber(response?.economic_return_usd_ha, runPINNSimulation(field, config).summaryKPIs.economicReturnUsdHa),
    },
    dailyRecords: dailyRecords.map((record: any, index: number) => ({
      day: safeNumber(record?.day, index + 1),
      dap: safeNumber(record?.dap, index + 1),
      date: record?.date ?? new Date(Date.now() + index * 86400000).toISOString().slice(0, 10),
      gddAccumulated: safeNumber(record?.gdd_accumulated, 0),
      stage: mapStage(record?.stage),
      stageCode: mapStageCode(record?.stage_code ?? record?.stageCode),
      biomassKgHa: safeNumber(record?.biomass_kg_ha, 0),
      lai: safeNumber(record?.lai, 0.1),
      rootDepthCm: safeNumber(record?.root_depth_cm, 15),
      canopyHeightM: safeNumber(record?.canopy_height_m, 0.2),
      soilMoistureTop: safeNumber(record?.soil_moisture_top, 0.2),
      soilMoistureMid: safeNumber(record?.soil_moisture_mid, 0.2),
      soilMoistureDeep: safeNumber(record?.soil_moisture_deep, 0.18),
      soilMoistureAvg: safeNumber(record?.soil_moisture_avg, 0.2),
      etoMm: safeNumber(record?.eto_mm, 3),
      etcMm: safeNumber(record?.etc_mm, 2.5),
      transpirationMm: safeNumber(record?.transpiration_mm, 1.8),
      evaporationMm: safeNumber(record?.evaporation_mm, 0.9),
      precipitationMm: safeNumber(record?.precipitation_mm, 0),
      irrigationMm: safeNumber(record?.irrigation_mm, 0),
      runoffMm: safeNumber(record?.runoff_mm, 0),
      deepDrainageMm: safeNumber(record?.deep_drainage_mm, 0),
      cwsi: safeNumber(record?.cwsi, 0.2),
      thermalStressFactor: safeNumber(record?.thermal_stress_factor, 0.1),
      dailyYieldLossPotentialKgHa: safeNumber(record?.daily_yield_loss_potential_kg_ha, 0),
      tempMaxC: safeNumber(record?.temp_max_c, 28),
      tempMinC: safeNumber(record?.temp_min_c, 16),
      solarRadiationMjM2: safeNumber(record?.solar_radiation_mj_m2, 18),
      vpdKpa: safeNumber(record?.vpd_kpa, 1.2),
    })),
    soilDynamics: {
      fieldCapacity: field.soilProfile.fieldCapacity,
      wiltingPoint: field.soilProfile.wiltingPoint,
      saturation: field.soilProfile.saturation,
    },
    pinnValidationMetrics: {
      pdeResidualRichardsLoss: safeNumber(response?.pinn_validation_metrics?.pde_residual_richards_loss, 0.003),
      boundaryConditionLoss: safeNumber(response?.pinn_validation_metrics?.boundary_condition_loss, 0.002),
      empiricalNassLoss: safeNumber(response?.pinn_validation_metrics?.empirical_nass_loss, 0.021),
      totalLoss: safeNumber(response?.pinn_validation_metrics?.total_loss, 0.028),
      inferenceTimeMs: safeNumber(response?.pinn_validation_metrics?.inference_time_ms, 420),
      physicsConservationErrorPercent: safeNumber(response?.pinn_validation_metrics?.physics_conservation_error_percent, 1.2),
      r2Score: safeNumber(response?.pinn_validation_metrics?.r2_score, 0.91),
    },
    alerts: Array.isArray(response?.alerts) ? response.alerts : [],
    agronomicRecommendations: Array.isArray(response?.agronomic_recommendations) ? response.agronomic_recommendations : [],
  };
};

export async function simulateScenario(field: Field, config: SimulationConfig): Promise<SimulationResult> {
  const fallback = runPINNSimulation(field, config);

  try {
    const response = await fetch(`${API_BASE}/api/simulate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        field_id: field.id,
        scenario: config.scenario,
        target_year: config.targetYear,
        planting_date: config.plantingDate,
        maize_variety: config.maizeVariety,
        irrigation_strategy: config.irrigationStrategy,
        soil_moisture_initial_percent: config.soilMoistureInitialPercent,
        nitrogen_application_kg_ha: config.nitrogenApplicationKgHa,
        carbon_dioxide_ppm: config.carbonDioxidePpm,
        temperature_anomaly_c: config.temperatureAnomalyC,
        precipitation_anomaly_percent: config.precipitationAnomalyPercent,
      }),
    });

    if (!response.ok) {
      throw new Error(`Simulation API returned ${response.status}`);
    }

    const payload = await response.json();
    return mapBackendSimulation(field, config, payload);
  } catch (error) {
    console.warn('FastAPI simulation backend unavailable; falling back to local PINN engine.', error);
    return fallback;
  }
}

export async function getModelStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/model/status`);
    if (!response.ok) {
      throw new Error(`Model status API returned ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.warn('Model status endpoint unavailable.', error);
    return {
      model_name: 'CeresPINN-maize-v2.5',
      status: 'local-fallback',
      backend: 'FastAPI-ready',
    };
  }
}

// ---------------------------------------------------------------------------
// Data pipelines (CHIRPS / NASA NEX-GDDP / USDA NASS)
//
// All pipeline functions implement a *rigorous fallback* contract:
//   - They attempt the live backend first.
//   - On any network/HTTP error they return an explicit, typed local-fallback
//     snapshot (never a throw), so the UI can render deterministic state.
//   - The fallback carries `fallback: true` so callers can surface that the data
//     is local/mock and not live, instead of silently pretending it is real.
// ---------------------------------------------------------------------------

export interface PipelineSyncResult {
  ok: boolean;
  fallback: boolean;
  jobId?: string;
  message: string;
}

const FALLBACK_TIMEOUT_MS = 4000;

async function fetchWithTimeout(url: string, init: RequestInit, ms: number) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export async function listPipelines(): Promise<any> {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/pipelines`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Pipelines API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, pipelines: payload.pipelines };
  } catch (error) {
    console.warn('Pipelines list endpoint unavailable; returning local fallback.', error);
    return { fallback: true };
  }
}

export async function triggerPipelineSync(pipelineId: string): Promise<PipelineSyncResult> {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/pipelines/${pipelineId}/sync`,
      { method: 'POST' },
      FALLBACK_TIMEOUT_MS,
    );
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload?.detail ?? `Pipelines API returned ${response.status}`);
    }
    return {
      ok: true,
      fallback: false,
      jobId: payload?.job_id,
      message: payload?.message ?? 'Sync enqueued.',
    };
  } catch (error) {
    console.warn('Pipeline sync endpoint unavailable; using local (cosmetic) fallback.', error);
    return {
      ok: false,
      fallback: true,
      message: 'Backend no disponible: la sincronización local simuló el procesamiento.',
    };
  }
}

export interface PipelineJobStatus {
  status: string;
  stage?: string;
  step?: number;
  total?: number;
  percent?: number;
  message?: string;
  error?: string | null;
}

export async function getPipelineJob(jobId: string): Promise<PipelineJobStatus | null> {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/pipelines/jobs/${jobId}`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Job API returned ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.warn('Pipeline job status endpoint unavailable.', error);
    return null;
  }
}

export async function triggerAllPipelinesSync(): Promise<PipelineSyncResult> {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/pipelines/sync-all`,
      { method: 'POST' },
      FALLBACK_TIMEOUT_MS,
    );
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload?.detail ?? `Pipelines API returned ${response.status}`);
    }
    return {
      ok: true,
      fallback: false,
      jobId: payload?.job_id,
      message: payload?.message ?? 'Sync de todos los pipelines encolado.',
    };
  } catch (error) {
    console.warn('Pipelines sync-all endpoint unavailable; using local fallback.', error);
    return { ok: false, fallback: true, message: 'Backend no disponible: sincronización local simulada.' };
  }
}

// ---------------------------------------------------------------------------
// Master Data Endpoints (Scenarios, Soil Profiles, Model Registry, Users)
// ---------------------------------------------------------------------------

export async function fetchScenarios() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/scenarios`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Scenarios API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, scenarios: payload };
  } catch (error) {
    console.warn('Scenarios endpoint unavailable; returning local fallback.', error);
    return { 
      fallback: true, 
      scenarios: [
        { id: 'SSP1-2.6', label: 'Sustainable pathway', risk: 'low' },
        { id: 'SSP3-7.0', label: 'Regional rivalry', risk: 'medium' },
        { id: 'SSP5-8.5', label: 'Fossil-fueled development', risk: 'high' },
      ]
    };
  }
}

export async function fetchFields(): Promise<{ fallback: boolean; fields: Field[] }> {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/fields`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Fields API returned ${response.status}`);
    }
    const payload = await response.json();
    if (Array.isArray(payload) && payload.length > 0) {
      const fields: Field[] = payload.map((item: any) => {
        const defaultField = DEFAULT_FIELDS.find(f => f.id === item.id) || DEFAULT_FIELDS[0];
        return {
          id: item.id || defaultField.id,
          name: item.name || defaultField.name,
          locationName: item.location_name || item.locationName || defaultField.locationName,
          country: item.country || defaultField.country,
          centerLat: item.center_lat ?? item.centerLat ?? defaultField.centerLat,
          centerLng: item.center_lng ?? item.centerLng ?? defaultField.centerLng,
          areaHectares: item.area_hectares ?? item.areaHectares ?? defaultField.areaHectares,
          altitudeMeters: item.altitude_meters ?? item.altitudeMeters ?? defaultField.altitudeMeters,
          currentCrop: item.current_crop || item.currentCrop || defaultField.currentCrop,
          soilProfile: defaultField.soilProfile || SOIL_PROFILES.clay_loam,
          notes: item.notes || defaultField.notes,
          polygon: defaultField.polygon,
        };
      });
      return { fallback: false, fields };
    }
    return { fallback: true, fields: DEFAULT_FIELDS };
  } catch (error) {
    console.warn('Fields endpoint unavailable; returning local fallback.', error);
    return { fallback: true, fields: DEFAULT_FIELDS };
  }
}

export async function fetchSoilProfiles() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/soil-profiles`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Soil profiles API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, soilProfiles: payload };
  } catch (error) {
    console.warn('Soil profiles endpoint unavailable; returning local fallback.', error);
    return { fallback: true };
  }
}

export async function fetchModelRegistry() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/model-registry`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Model registry API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, models: payload };
  } catch (error) {
    console.warn('Model registry endpoint unavailable; returning local fallback.', error);
    return { fallback: true };
  }
}

export async function fetchUsers() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/users`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Users API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, users: payload };
  } catch (error) {
    console.warn('Users endpoint unavailable; returning local fallback.', error);
    return { fallback: true };
  }
}

// ---------------------------------------------------------------------------
// Validation Endpoints (Hindcast, KS test, t-test, Sobol, bootstrap)
// ---------------------------------------------------------------------------

export async function fetchValidationReport() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/validation`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Validation API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, report: payload };
  } catch (error) {
    console.warn('Validation endpoint unavailable; returning local fallback.', error);
    return { 
      fallback: true,
      report: {
        hindcast_metrics: {
          rmse_kg_ha: 385,
          mae_kg_ha: 298,
          r2_score: 0.942,
          nrmse_percent: 4.8
        },
        ks_test: {
          statistic: 0.087,
          p_value: 0.234,
          null_rejected: false
        },
        paired_t_test: {
          t_statistic: -1.45,
          p_value: 0.147,
          significant: false
        },
        sobol_sensitivity: {
          first_order: { temperature: 0.42, precipitation: 0.31, co2: 0.18 },
          total_order: { temperature: 0.58, precipitation: 0.45, co2: 0.25 }
        },
        bootstrap_ci: {
          yield_95_ci_lower: 7650,
          yield_95_ci_upper: 8350,
          n_bootstrap: 1000
        },
        ensemble_uncertainty: {
          mean_yield: 8000,
          std_yield: 175,
          ensemble_size: 32
        }
      }
    };
  }
}

export async function fetchHindcastData() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/validation/hindcast`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Hindcast API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, hindcast: payload };
  } catch (error) {
    console.warn('Hindcast endpoint unavailable; returning local fallback.', error);
    return { 
      fallback: true,
      hindcast: {
        years: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        observed_yield: [8200, 7950, 8100, 7850, 8400, 8150, 8300, 8000, 8250, 8100],
        predicted_yield: [8150, 8020, 8050, 7900, 8350, 8200, 8250, 8050, 8200, 8150],
        residuals: [50, -70, 50, -50, 50, -50, 50, -50, 50, -50]
      }
    };
  }
}

// ---------------------------------------------------------------------------
// Reports and Database Health Endpoints
// ---------------------------------------------------------------------------

export async function fetchReports() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/reports`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Reports API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, reports: payload };
  } catch (error) {
    console.warn('Reports endpoint unavailable; returning local fallback.', error);
    return { 
      fallback: true,
      reports: {
        title: "CeresPINN seasonal summary",
        generated_at: new Date().toISOString(),
        summary: "Yield outlook remains stable under moderate warming but degrades under severe drought stress.",
        regions: [
          { name: "Bajío", yield_kg_ha: 7500 },
          { name: "Iowa", yield_kg_ha: 8400 },
          { name: "Pampas", yield_kg_ha: 7800 },
        ]
      }
    };
  }
}

export async function fetchDatabaseHealth() {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE}/api/health/database`,
      { method: 'GET' },
      FALLBACK_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(`Database health API returned ${response.status}`);
    }
    const payload = await response.json();
    return { fallback: false, health: payload };
  } catch (error) {
    console.warn('Database health endpoint unavailable; returning local fallback.', error);
    return { 
      fallback: true,
      health: {
        database: "postgres",
        postgis: "available",
        status: "mock-or-live",
        note: "DATABASE_URL no configurada o BD inalcanzable: se usa el mock."
      }
    };
  }
}
