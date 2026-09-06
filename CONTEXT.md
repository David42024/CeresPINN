# CeresPINN - Contexto del Sistema

## Resumen del Proyecto

**Nombre:** Climate-Adaptive Digital Twin for Drought-Resilient Maize Production

**Objetivo:** Construir un gemelo digital que acople proyecciones climáticas descendentes (CMIP6, bias-corrected) con un PINN (Physics-Informed Neural Network) de crecimiento de maíz, permitiendo simular rendimiento bajo 4 escenarios SSP y prescribir adaptaciones (variedad, fecha de siembra, riego suplementario).

## Problema

Los modelos de cultivo actuales (APSIM, DSSAT) usan series climáticas históricas como entrada, tratando el clima como estacionario. No incorporan proyecciones de cambio climático, limitando la capacidad de adaptación proactiva. Los gemelos digitales tampoco han integrado CMIP6.

## Hipótesis

- **H0:** El twin climático no predice diferencias significativas de rendimiento entre SSP2-4.5 y SSP5-8.5 para 2050.
- **H1:** El twin predice reducción del rendimiento en ≥15% bajo SSP5-8.5 vs. baseline histórico, con identificación de ventanas de siembra óptimas que mitigan ≥50% de la pérdida.

---

## Arquitectura del Sistema

### Stack Tecnológico

**Frontend:**
- React + Vite + TypeScript
- TailwindCSS para estilos
- Recharts para visualización
- Lucide React para iconos
- Puerto: 3000

**Backend:**
- FastAPI (Python)
- PostgreSQL con PostGIS
- PyTorch para PINN
- Puerto: 8000

**Data Sources:**
- CHIRPS (precipitación histórica)
- CHIRTS (temperatura histórica)
- USDA NASS QuickStats (rendimiento por condado, ground truth)
- CMIP6 NASA NEX-GDDP (5 modelos GCM, downscaled a 0.25°)
- SoilGrids 2.0 (suelo)

---

## Módulos del Sistema

### Módulo 1: Datos (Data Extraction)

**Estado Actual:**
- ✅ `backend/data/chirps.py` - Extracción de CHIRPS daily precipitation GeoTIFFs
- ✅ `backend/data/nex_gddp.py` - Extracción de NASA NEX-GDDP CMIP6 climate projections
- ✅ `backend/data/nass.py` - Extracción de USDA NASS QuickStats county-level maize yield
- ✅ `backend/data/config.py` - Configuración centralizada de pipelines de datos
- ✅ `backend/training/dataset.py` - Ensamblaje de dataset para PINN training

**Funcionalidad Esperada (FICHA 5):**
- Integración de CHIRTS para temperatura histórica
- Integración completa de SoilGrids 2.0
- Downscaling bias-corrected de CMIP6
- Validación de calidad de datos

**Faltante:**
- ❌ CHIRTS integration
- ❌ SoilGrids 2.0 integration
- ❌ Bias correction pipeline para CMIP6
- ❌ Data quality validation

### Módulo 2: Arquitectura PINN

**Estado Actual:**
- ✅ `backend/training/pinn.py` - CeresPINN model con physics-informed loss
- ✅ `backend/training/train.py` - Training loop con physics loss
- ✅ `backend/services/pinnEngine.ts` - Frontend PINN engine mock
- ✅ Physics loss: monotonicity y range feasibility

**Funcionalidad Esperada (FICHA 5):**
- Ecuaciones de crecimiento de cultivo como términos de pérdida física:
  - Acumulación de biomasa
  - Desarrollo fenológico
  - Balance hídrico (Richards equation)
- Entrada: Tmax, Tmin, precipitación, radiación solar (downscaled)
- Salida: rendimiento, fecha de floración, fecha de madurez, ET acumulada
- Capa de adaptación: optimización de fecha de siembra y variedad mediante búsqueda bayesiana

**Faltante:**
- ❌ Ecuaciones PDE completas de crecimiento de cultivo
- ❌ Richards equation completa en physics loss
- ❌ Búsqueda bayesiana para optimización de adaptación
- ❌ Output de fechas fenológicas y ET acumulada

### Módulo 3: Validación

**Estado Actual:**
- ✅ `backend/validation.py` - Implementación de validación estadística
- ✅ KS test para distribución de rendimiento
- ✅ Paired t-test para comparación SSP scenarios
- ✅ Sobol sensitivity analysis
- ✅ Bootstrap para ensemble uncertainty
- ✅ Hindcast validation pipeline

**Funcionalidad Esperada (FICHA 5):**
- Validación histórica (hindcast): simular 1990-2020 con datos climáticos históricos y comparar con USDA NASS
- Validación de proyecciones: comparación con ensayos de trigo/maíz en ambientes controlados de temperatura elevada (literatura)
- Métricas: RMSE, MAE, R² para hindcast
- Intervalo de incertidumbre del ensemble (rango intercuartílico)

**Faltante:**
- ❌ Integración de validación de proyecciones con literatura
- ❌ Frontend para visualizar resultados de validación
- ❌ Reportes automatizados de validación

### Módulo 4: Escenarios

**Estado Actual:**
- ✅ Backend endpoint `/api/scenarios` - SSP scenarios
- ✅ Frontend `SimulationConfig.tsx` - Configuración de escenarios
- ✅ Escenarios: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5
- ✅ Horizonte temporal: 2026-2050
- ✅ Intervenciones: variedad, fecha de siembra, riego

**Funcionalidad Esperada (FICHA 5):**
- Escenarios: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5 para 2030, 2050, 2070
- Intervenciones específicas:
  - (a) adelanto de siembra 15 días
  - (b) cambio a variedad de ciclo más corto
  - (c) riego suplementario de 50mm en floración

**Faltante:**
- ❌ Escenario SSP2-4.5 en frontend
- ❌ Horizonte 2070
- ❌ Implementación específica de intervenciones adaptativas

### Módulo 5: Impacto

**Estado Actual:**
- ✅ Frontend `MainDashboard.tsx` - KPIs y time-series charts
- ✅ Backend endpoint `/api/reports` - Report generation
- ✅ Visualización de resultados de simulación

**Funcionalidad Esperada (FICHA 5):**
- Mapa de vulnerabilidad por condado
- Ganancia/pérdida de rendimiento
- Recomendaciones de política de adaptación
- Análisis de incertidumbre de ensemble GCM

**Faltante:**
- ❌ Mapas geoespaciales de vulnerabilidad
- ❌ Análisis de impacto por condado
- ❌ Sistema de recomendaciones de adaptación
- ❌ Visualización de incertidumbre ensemble

---

## Frontend - Estado Actual

### Componentes Implementados

**Main Components:**
- ✅ `App.tsx` - Main application, state management, tab navigation
- ✅ `MainDashboard.tsx` - KPIs y time-series charts
- ✅ `SimulationConfig.tsx` - Configuración de simulación (clima, cultivo, riego, suelo)
- ✅ `MLOpsDashboard.tsx` - Gestión de modelos PINN y retraining
- ✅ `UserManagement.tsx` - Gestión de usuarios y roles (RBAC)
- ✅ `ThreeFieldViewer.tsx` - Visualización 3D de campos

**API Integration (Etapa 1 - Completado):**
- ✅ `api.ts` - `fetchScenarios()` - Consume `/api/scenarios`
- ✅ `api.ts` - `fetchSoilProfiles()` - Consume `/api/soil-profiles`
- ✅ `api.ts` - `fetchModelRegistry()` - Consume `/api/model-registry`
- ✅ `api.ts` - `fetchUsers()` - Consume `/api/users`
- ✅ Fallbacks a datos mock cuando backend no disponible

**Data:**
- ✅ `mockData.ts` - Datos mock para fallbacks
- ✅ `types.ts` - TypeScript interfaces

### Faltante en Frontend

- ❌ Tab de validación histórica (hindcast results)
- ❌ Visualización de mapas de vulnerabilidad
- ❌ Panel de análisis de sensibilidad (Sobol)
- ❌ Panel de recomendaciones de adaptación
- ❌ Visualización de incertidumbre ensemble
- ❌ Reportes de validación estadística

---

## Backend - Estado Actual

### Endpoints Implementados

- ✅ `/api/health` - Health check
- ✅ `/api/model/status` - Status del modelo PINN
- ✅ `/api/fields` - Lista de campos
- ✅ `/api/scenarios` - Escenarios CMIP6
- ✅ `/api/simulate` - Ejecutar simulación
- ✅ `/api/reports` - Generación de reportes
- ✅ `/api/soil-profiles` - Perfiles de suelo
- ✅ `/api/model-registry` - Registro de modelos
- ✅ `/api/users` - Gestión de usuarios
- ✅ `/api/validation` - Validación estadística
- ✅ `/api/pipelines/*` - Gestión de pipelines de datos

### Faltante en Backend

- ❌ Endpoint para optimización bayesiana de adaptación
- ❌ Endpoint para mapas de vulnerabilidad
- ❌ Endpoint para análisis de sensibilidad
- ❌ Endpoint para recomendaciones de adaptación
- ❌ Integración de CHIRTS
- ❌ Integración de SoilGrids

---

## Protocolo de Investigación

**Tipo:** Simulación basada en modelos con validación histórica (hindcast)

**DAG:** Emisiones → Forzante radiativo → Tmax + Precip → Desarrollo fenológico → Rendimiento. Intervención: adaptación de manejo.

**Población:** Condados productores de maíz del Midwest de EE.UU.

**Inclusión:** Condados con datos USDA NASS ≥20 años, cobertura de CMIP6 completa.

**Exclusión:** Condados con >50% de área de riego (irrigated).

**Pre-registro:** OSF.

**Ética:** Datos públicos. Consideración de impacto en seguridad alimentaria y equidad (condados con menor capacidad de adaptación).

**Timeline:**
- Meses 1–3: revisión + datos CMIP6
- Meses 4–6: downscaling + preprocesamiento
- Meses 7–10: PINN + calibración
- Meses 11–14: proyecciones + adaptación
- Meses 15–17: redacción

---

## Pruebas Estadísticas

### Implementadas
- ✅ KS test - Validar distribución de rendimiento simulado (hindcast) vs. observado (USDA NASS)
- ✅ Paired t-test - Comparación de rendimiento proyectado (SSP5-8.5 vs. histórico) por condado
- ✅ Sobol sensitivity - Identificar qué variable climática explica más varianza en pérdida de rendimiento
- ✅ Bootstrap - IC 95% para rendimiento proyectado mediante bootstrap de ensemble GCM
- ✅ RMSE, MAE, R² - Métricas predictivas para hindcast

### Faltante
- ❌ Integración con frontend para visualización
- ❌ Reportes automatizados

---

## Revistas Objetivo

- European Journal of Agronomy (CiteScore ~8.0, afinidad: modelos de cultivo + clima)
- Agricultural Systems (CiteScore ~9.0, afinidad: sistemas + adaptación)
- Science of the Total Environment (CiteScore ~12.5, afinidad: cambio climático + impacto ambiental)

---

## Estado de Implementación

### Completado
- ✅ Etapa 1: Integración de Endpoints de Datos Maestros (Frontend)
- ✅ Backend API básico
- ✅ Frontend UI principal
- ✅ PINN model básico
- ✅ Validación estadística backend
- ✅ Data extraction pipelines (CHIRPS, NEX-GDDP, NASS)

### En Progreso
- 🔄 Etapa 2: Integración de Endpoints de Validación y Reportes
- 🔄 Mejora del PINN con ecuaciones físicas completas

### Pendiente
- ❌ CHIRTS integration
- ❌ SoilGrids integration
- ❌ Bias correction pipeline
- ❌ Búsqueda bayesiana para adaptación
- ❌ Mapas de vulnerabilidad
- ❌ Sistema de recomendaciones
- ❌ Frontend de validación
- ❌ Visualización de incertidumbre ensemble

---

## Configuración Local

**Frontend:**
```bash
npm install
npm run dev  # Puerto 3000
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

**Variables de Entorno:**
- `API_BASE`: http://localhost:8000 (default)
- `NASS_API_KEY`: Requerido para USDA NASS QuickStats
