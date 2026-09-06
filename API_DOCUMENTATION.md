# CeresPINN API Documentation

This document describes the REST API endpoints for the CeresPINN climate-adaptive maize digital twin backend.

## Base URL

```
http://localhost:8000
```

The base URL can be configured via the `VITE_API_BASE_URL` environment variable in the frontend.

## Authentication

Currently, the API does not require authentication. Future versions may implement API key or OAuth-based authentication.

## Endpoints

### Health & Status

#### `GET /api/health`

Check the overall health of the API service.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /api/health/database`

Check the database connection status and PostGIS availability.

**Response:**
```json
{
  "database": "postgres",
  "postgis": "available",
  "status": "healthy",
  "connection_pool": "active"
}
```

### Master Data Endpoints

#### `GET /api/scenarios`

Retrieve available climate scenarios (CMIP6 SSP pathways).

**Response:**
```json
{
  "scenarios": [
    {
      "id": "ssp1-2.6",
      "name": "SSP1-2.6 (Sostenible)",
      "description": "Bajas emisiones, +1.5°C para 2100",
      "warming_degrees": 1.5,
      "co2_ppm": 450
    },
    {
      "id": "ssp2-4.5",
      "name": "SSP2-4.5 (Intermedio)",
      "description": "Emisiones moderadas, +2.5°C para 2100",
      "warming_degrees": 2.5,
      "co2_ppm": 650
    },
    {
      "id": "ssp5-8.5",
      "name": "SSP5-8.5 (Alto)",
      "description": "Altas emisiones, +4.4°C para 2100",
      "warming_degrees": 4.4,
      "co2_ppm": 950
    }
  ]
}
```

#### `GET /api/soil-profiles`

Retrieve available soil profile configurations.

**Response:**
```json
{
  "soil_profiles": [
    {
      "id": "clay-loam",
      "name": "Franco Arcilloso",
      "sand_fraction": 0.35,
      "clay_fraction": 0.35,
      "organic_matter": 0.025,
      "field_capacity": 0.35,
      "wilting_point": 0.15
    },
    {
      "id": "sandy-loam",
      "name": "Franco Arenoso",
      "sand_fraction": 0.60,
      "clay_fraction": 0.15,
      "organic_matter": 0.015,
      "field_capacity": 0.25,
      "wilting_point": 0.10
    }
  ]
}
```

#### `GET /api/model-registry`

Retrieve the registry of trained PINN models.

**Response:**
```json
{
  "models": [
    {
      "id": "pinn-v1",
      "name": "PINN Richards v1.0",
      "trained_on": "2024-01-15",
      "rmse": 0.12,
      "status": "production",
      "training_epochs": 5000
    },
    {
      "id": "pinn-v2",
      "name": "PINN Richards v2.0",
      "trained_on": "2024-06-20",
      "rmse": 0.08,
      "status": "production",
      "training_epochs": 10000
    }
  ]
}
```

#### `GET /api/users`

Retrieve user accounts and roles (RBAC).

**Response:**
```json
{
  "users": [
    {
      "id": "user-001",
      "name": "Dr. María González",
      "email": "maria.gonzalez@agro.edu",
      "role": "researcher",
      "institution": "Universidad Agronómica"
    },
    {
      "id": "user-002",
      "name": "Ing. Carlos Ruiz",
      "email": "carlos.ruiz@agrotech.com",
      "role": "operator",
      "institution": "AgroTech Solutions"
    }
  ]
}
```

### Simulation Endpoints

#### `POST /api/simulate`

Run a PINN simulation for a given field and configuration.

**Request Body:**
```json
{
  "field": {
    "id": "field-001",
    "name": "Campo Bajío Norte",
    "area_hectares": 50,
    "location": {
      "lat": 20.5,
      "lon": -101.2,
      "elevation_m": 1800
    }
  },
  "config": {
    "climate_scenario": "ssp2-4.5",
    "soil_profile_id": "clay-loam",
    "planting_date": 45,
    "planting_density": 75000,
    "irrigation_supplemental_mm": 50,
    "variety": "drought_resistant"
  }
}
```

**Response:**
```json
{
  "simulation_id": "sim-20240115-001",
  "summary_kpis": {
    "final_yield_kg_ha": 8200,
    "lai_max": 4.2,
    "cwsi_avg": 0.32,
    "water_use_efficiency_kg_mm": 18.5
  },
  "daily_records": [
    {
      "day": 1,
      "lai": 0.1,
      "soil_moisture_top": 0.35,
      "cwsi": 0.0,
      "stage": "Emergence",
      "stage_code": "VE"
    }
  ]
}
```

#### `GET /api/model/status`

Get the current status of the PINN model.

**Response:**
```json
{
  "model_id": "pinn-v2",
  "status": "ready",
  "last_training": "2024-06-20",
  "inference_count": 1523
}
```

### Validation Endpoints

#### `GET /api/validation`

Retrieve statistical validation metrics for the PINN model.

**Response:**
```json
{
  "hindcast_metrics": {
    "rmse_kg_ha": 385,
    "mae_kg_ha": 298,
    "r2_score": 0.942,
    "nrmse_percent": 4.8
  },
  "ks_test": {
    "statistic": 0.087,
    "p_value": 0.234,
    "null_rejected": false
  },
  "paired_t_test": {
    "t_statistic": -1.45,
    "p_value": 0.147,
    "significant": false
  },
  "sobol_sensitivity": {
    "first_order": {
      "temperature": 0.42,
      "precipitation": 0.31,
      "co2": 0.18
    },
    "total_order": {
      "temperature": 0.58,
      "precipitation": 0.45,
      "co2": 0.25
    }
  },
  "bootstrap_ci": {
    "yield_95_ci_lower": 7650,
    "yield_95_ci_upper": 8350,
    "n_bootstrap": 1000
  },
  "ensemble_uncertainty": {
    "mean_yield": 8000,
    "std_yield": 175,
    "ensemble_size": 32
  }
}
```

#### `GET /api/validation/hindcast`

Retrieve hindcast data (historical predictions vs observations).

**Response:**
```json
{
  "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
  "observed_yield": [8200, 7950, 8100, 7850, 8400, 8150, 8300, 8000, 8250, 8100],
  "predicted_yield": [8150, 8020, 8050, 7900, 8350, 8200, 8250, 8050, 8200, 8150],
  "residuals": [50, -70, 50, -50, 50, -50, 50, -50, 50, -50]
}
```

### Reports Endpoints

#### `GET /api/reports`

Retrieve available reports and summaries.

**Response:**
```json
{
  "title": "CeresPINN seasonal summary",
  "generated_at": "2024-01-15T10:30:00Z",
  "summary": "Yield outlook remains stable under moderate warming but degrades under severe drought stress.",
  "regions": [
    {
      "name": "Bajío",
      "yield_kg_ha": 7500
    },
    {
      "name": "Iowa",
      "yield_kg_ha": 8400
    },
    {
      "name": "Pampas",
      "yield_kg_ha": 7800
    }
  ]
}
```

### Data Pipelines Endpoints

#### `GET /api/pipelines`

List available data ingestion pipelines.

**Response:**
```json
{
  "pipelines": [
    {
      "id": "chirps-daily",
      "name": "CHIRPS Daily Precipitation",
      "source": "NASA/USGS",
      "frequency": "daily",
      "status": "active",
      "last_run": "2024-01-15T00:00:00Z"
    },
    {
      "id": "cmip6-downscale",
      "name": "CMIP6 Climate Downscaling",
      "source": "IPCC",
      "frequency": "monthly",
      "status": "active",
      "last_run": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### `POST /api/pipelines/{pipeline_id}/sync`

Trigger a manual sync for a specific pipeline.

**Response:**
```json
{
  "job_id": "job-20240115-001",
  "pipeline_id": "chirps-daily",
  "status": "started",
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

#### `GET /api/pipelines/jobs/{job_id}`

Get the status of a pipeline job.

**Response:**
```json
{
  "job_id": "job-20240115-001",
  "status": "completed",
  "records_processed": 365,
  "errors": 0,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:15Z"
}
```

#### `POST /api/pipelines/sync-all`

Trigger sync for all active pipelines.

**Response:**
```json
{
  "jobs_triggered": 3,
  "job_ids": ["job-001", "job-002", "job-003"],
  "status": "all_started"
}
```

### Field Management Endpoints

#### `GET /api/fields`

Retrieve all registered fields.

**Response:**
```json
{
  "fields": [
    {
      "id": "field-001",
      "name": "Campo Bajío Norte",
      "area_hectares": 50,
      "location": {
        "lat": 20.5,
        "lon": -101.2,
        "elevation_m": 1800
      },
      "soil_profile_id": "clay-loam"
    }
  ]
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "Database connection failed",
    "details": "Connection timeout after 30 seconds"
  }
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Frontend Integration

The React frontend (`src/services/api.ts`) includes fallback mechanisms for all endpoints. If the backend is unavailable or times out (4 seconds), the frontend will use local mock data to ensure the application remains functional.

### Environment Variables

- `VITE_API_BASE_URL`: Base URL for the API (default: `http://localhost:8000`)
- `DATABASE_URL`: PostgreSQL connection string (backend only)

## Rate Limiting

Currently, there are no rate limits enforced. Future versions may implement rate limiting based on user role or API key.

## Versioning

The API uses URI versioning. The current version is `v1`. Future versions will be released as `/api/v2/...`.

## Support

For issues or questions about the API, please refer to the main project repository or contact the development team.
