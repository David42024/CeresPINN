import { Field, IngestionPipeline, ModelRegistryEntry, SimulationConfig, SoilProfile, User } from '../types';

export const SOIL_PROFILES: Record<string, SoilProfile> = {
  clay_loam: {
    type: 'clay_loam',
    label: 'Franco Arcilloso (Clay Loam)',
    sandPercent: 32,
    clayPercent: 34,
    siltPercent: 34,
    organicMatterPercent: 3.2,
    bulkDensity: 1.35,
    fieldCapacity: 0.32,
    wiltingPoint: 0.16,
    saturation: 0.48,
    saturatedConductivityKs: 85, // mm/day
    alphaVanGenuchten: 0.015,
    nVanGenuchten: 1.45
  },
  sandy_loam: {
    type: 'sandy_loam',
    label: 'Franco Arenoso (Sandy Loam)',
    sandPercent: 65,
    clayPercent: 12,
    siltPercent: 23,
    organicMatterPercent: 1.8,
    bulkDensity: 1.48,
    fieldCapacity: 0.22,
    wiltingPoint: 0.09,
    saturation: 0.41,
    saturatedConductivityKs: 240, // mm/day
    alphaVanGenuchten: 0.026,
    nVanGenuchten: 1.75
  },
  silty_clay: {
    type: 'silty_clay',
    label: 'Arcillo Limoso (Silty Clay)',
    sandPercent: 10,
    clayPercent: 48,
    siltPercent: 42,
    organicMatterPercent: 2.7,
    bulkDensity: 1.28,
    fieldCapacity: 0.38,
    wiltingPoint: 0.22,
    saturation: 0.52,
    saturatedConductivityKs: 35, // mm/day
    alphaVanGenuchten: 0.010,
    nVanGenuchten: 1.28
  },
  loam: {
    type: 'loam',
    label: 'Franco Ideal (Loam)',
    sandPercent: 40,
    clayPercent: 20,
    siltPercent: 40,
    organicMatterPercent: 3.8,
    bulkDensity: 1.32,
    fieldCapacity: 0.28,
    wiltingPoint: 0.13,
    saturation: 0.46,
    saturatedConductivityKs: 120, // mm/day
    alphaVanGenuchten: 0.019,
    nVanGenuchten: 1.55
  }
};

export const INITIAL_FIELDS: Field[] = [
  {
    id: 'field-iowa-01',
    name: 'Parcela Experimental Ames Norte',
    locationName: 'Story County, Iowa',
    country: 'Estados Unidos',
    centerLat: 42.0308,
    centerLng: -93.6319,
    areaHectares: 64.5,
    altitudeMeters: 295,
    currentCrop: 'Zea mays L. (Maíz Grano)',
    soilProfile: SOIL_PROFILES.clay_loam,
    notes: 'Suelo Mollisol de alta fertilidad con historial DSSAT/APSIM para validación PINN.',
    polygon: {
      type: 'Polygon',
      coordinates: [
        [42.035, -93.638],
        [42.035, -93.625],
        [42.026, -93.625],
        [42.026, -93.638],
        [42.035, -93.638]
      ]
    }
  },
  {
    id: 'field-bajio-02',
    name: 'Rancho Santa Elena - Módulo 4',
    locationName: 'Celaya, Guanajuato (El Bajío)',
    country: 'México',
    centerLat: 20.5222,
    centerLng: -100.8123,
    areaHectares: 48.0,
    altitudeMeters: 1750,
    currentCrop: 'Maíz Blanco Híbrido Resiliente',
    soilProfile: SOIL_PROFILES.silty_clay,
    notes: 'Vertisol arcilloso susceptible a estrés hídrico terminal y agrietamiento.',
    polygon: {
      type: 'Polygon',
      coordinates: [
        [20.528, -100.819],
        [20.529, -100.805],
        [20.516, -100.806],
        [20.515, -100.820],
        [20.528, -100.819]
      ]
    }
  },
  {
    id: 'field-pampas-03',
    name: 'Estancia La Vanguardia - Lote 12',
    locationName: 'Pergamino, Buenos Aires',
    country: 'Argentina',
    centerLat: -33.8961,
    centerLng: -60.5736,
    areaHectares: 120.0,
    altitudeMeters: 65,
    currentCrop: 'Maíz Tardío Siembra Directa',
    soilProfile: SOIL_PROFILES.loam,
    notes: 'Argiudol típico con napa freática oscilante y alta retención de humedad.',
    polygon: {
      type: 'Polygon',
      coordinates: [
        [-33.890, -60.582],
        [-33.890, -60.564],
        [-33.902, -60.565],
        [-33.901, -60.583],
        [-33.890, -60.582]
      ]
    }
  },
  {
    id: 'field-ebro-04',
    name: 'Finca Riego Canal d’Urgell',
    locationName: 'Lleida, Cataluña',
    country: 'España',
    centerLat: 41.6176,
    centerLng: 0.6200,
    areaHectares: 35.2,
    altitudeMeters: 190,
    currentCrop: 'Maíz Ciclo Corto (FAO 400)',
    soilProfile: SOIL_PROFILES.sandy_loam,
    notes: 'Suelo calcáreo con restricción estricta de cupo de riego por sequía mediterránea.',
    polygon: {
      type: 'Polygon',
      coordinates: [
        [41.622, 0.614],
        [41.623, 0.626],
        [41.612, 0.627],
        [41.611, 0.615],
        [41.622, 0.614]
      ]
    }
  }
];

export const DEFAULT_FIELDS: Field[] = INITIAL_FIELDS;

export const DEFAULT_SIMULATION_CONFIG: SimulationConfig = {
  id: 'sim-default-01',
  fieldId: 'field-bajio-02',
  scenario: 'SSP3-7.0',
  targetYear: 2035,
  plantingDate: '2026-05-15',
  maizeVariety: 'medium_cycle',
  irrigationStrategy: 'deficit_50',
  soilMoistureInitialPercent: 60,
  nitrogenApplicationKgHa: 180,
  carbonDioxidePpm: 540,
  temperatureAnomalyC: 1.85,
  precipitationAnomalyPercent: -12.0
};

export const DEMO_USERS: User[] = [
  {
    id: 'usr-admin-1',
    name: 'Dra. Elena Vasconcelos',
    email: 'elena.vasconcelos@agriclimate-twin.org',
    role: 'admin',
    avatarUrl: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
    organization: 'Centro Internacional de Modelado Climático Agrícola',
    region: 'América Latina & Caribe',
    preferences: {
      unitSystem: 'metric',
      theme: 'dark',
      autoSaveSimulations: true,
      highContrast3D: true,
      emailAlerts: true
    }
  },
  {
    id: 'usr-researcher-2',
    name: 'Dr. Marcus Vance',
    email: 'm.vance@agri-ai-lab.edu',
    role: 'researcher',
    avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    organization: 'Global Crop Modeling Consortium',
    region: 'Norteamérica',
    preferences: {
      unitSystem: 'metric',
      theme: 'dark',
      autoSaveSimulations: true,
      highContrast3D: false,
      emailAlerts: true
    }
  },
  {
    id: 'usr-farmer-3',
    name: 'Carlos Mendez R.',
    email: 'carlos.mendez@agrovalle.com',
    role: 'farmer',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    organization: 'Asociación de Productores del Bajío',
    region: 'México Central',
    preferences: {
      unitSystem: 'metric',
      theme: 'dark',
      autoSaveSimulations: false,
      highContrast3D: false,
      emailAlerts: true
    }
  },
  {
    id: 'usr-consultant-4',
    name: 'Ing. Sofía Morales',
    email: 'sofia.morales@climateresilient.tech',
    role: 'consultant',
    avatarUrl: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80',
    organization: 'Consultoría Agrotech Sostenible',
    region: 'Europa Sur',
    preferences: {
      unitSystem: 'metric',
      theme: 'dark',
      autoSaveSimulations: true,
      highContrast3D: false,
      emailAlerts: false
    }
  }
];

export const MODEL_REGISTRY_DATA: ModelRegistryEntry[] = [
  {
    version: 'v2.4.1-PINN-Ensemble',
    name: 'PINN Ceres-Richards V2.4 (Active Production)',
    architecture: 'Physics-Informed Deep ResNet + Automatic Differentiation PDE Loss',
    trainedDate: '2026-08-15',
    epochs: 15000,
    richardsWeightLambda: 0.45,
    testR2: 0.942,
    testRmseKgHa: 385,
    active: true,
    status: 'production',
    description: 'Surrogate neural model enforcing 1D unsaturated Richards flow conservation & Priestley-Taylor ET constraints.'
  },
  {
    version: 'v2.3.0-PINN-Richards',
    name: 'PINN Richards Single-Soil V2.3',
    architecture: 'Physics-Informed MLP (6 layers x 256 units, tanh activation)',
    trainedDate: '2026-06-20',
    epochs: 12000,
    richardsWeightLambda: 0.35,
    testR2: 0.918,
    testRmseKgHa: 490,
    active: false,
    status: 'staging',
    description: 'Calibrated on USDA NASS 2000-2025 multi-state corn records.'
  },
  {
    version: 'v1.8.2-Vanilla-LSTM',
    name: 'Empirical Baseline (Non-Physics LSTM)',
    architecture: 'Bidirectional LSTM + Dense Output',
    trainedDate: '2026-02-10',
    epochs: 8000,
    richardsWeightLambda: 0.0,
    testR2: 0.812,
    testRmseKgHa: 890,
    active: false,
    status: 'archived',
    description: 'Baseline purely data-driven model without PDE physics regularization.'
  }
];

export const INGESTION_PIPELINES: IngestionPipeline[] = [
  {
    id: 'pipe-chirps',
    name: 'CHIRPS Daily Precipitation Pipeline',
    source: 'UCSB Climate Hazards Center (FTP/GeoTIFF 0.05°)',
    frequency: 'Diario (06:00 UTC)',
    lastSync: '2026-08-29 06:15:22 UTC',
    status: 'healthy',
    recordsProcessed: '14,892,100 grid points',
    resolution: '0.05° (~5.3 km) downscaled to 100m',
    description: 'Descarga satelital combinada con estaciones pluviométricas para monitoreo de precipitación en tiempo real.'
  },
  {
    id: 'pipe-nasa-nex',
    name: 'NASA NEX-GDDP CMIP6 Climate Scenarios',
    source: 'NASA Earth Exchange (S3 Public Bucket / NetCDF4)',
    frequency: 'Semanal (Actualización de proyecciones)',
    lastSync: '2026-08-28 18:40:00 UTC',
    status: 'healthy',
    recordsProcessed: '32 Ensemble Models (SSP1-2.6, SSP3-7.0, SSP5-8.5)',
    resolution: '0.25° con Quantile Delta Mapping',
    description: 'Proyecciones climáticas globales con corrección de sesgo para temperatura extrema, radiación y VPD hasta 2050.'
  },
  {
    id: 'pipe-usda-nass',
    name: 'USDA NASS QuickStats Crop Harvest Yields',
    source: 'USDA National Agricultural Statistics Service API',
    frequency: 'Mensual',
    lastSync: '2026-08-20 12:00:10 UTC',
    status: 'healthy',
    recordsProcessed: '45,200 County-Year Yield Observations',
    resolution: 'Nivel Condado / Parcela de calibración',
    description: 'Datos históricos de rendimiento de maíz (1990-2025) utilizados como loss empírica de entrenamiento.'
  }
];
