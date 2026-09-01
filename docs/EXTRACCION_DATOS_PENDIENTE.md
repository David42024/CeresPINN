# Extracción de Datos Climatológicos — Estado y Pendientes

> **Documento de trabajo para retomar la descarga de datos reales cuando haya mejor conexión a internet.**
> Última actualización: 2026-09 (sesión de diseño ya completada).

---

## 1. Resumen ejecutivo

El sistema CeresPINN requiere **3 fuentes de datos reales** para entrenar el PINN y hacer la validación estadística (hindcast vs. USDA NASS):

| Fuente | Qué aporta | API Key | Estado |
|---|---|---|---|
| **CHIRPS** (UCSB) | Precipitación histórica | No | 🔴 Suspendida (404 por ahora) |
| **USDA NASS** | Rendimiento real de maíz por condado (ground truth) | **Sí** | 🔴 Suspendida (límite 50k filas) |
| **NASA NEX-GDDP-CMIP6** | Proyecciones climáticas downscaled 0.25° | No | 🔴 Suspendida (red muy lenta) |

**Hasta ahora NO se descargó ningún dato real.** Todo lo que hay en `backend/data/raw/` son **manifests de dry-run** (archivos de planificación offline, cero bytes útiles). Los datos que hoy usa la aplicación son mocks/frontend/BD, no extracciones reales.

---

## 2. Estado del código (ya corregido, listo para usar)

Durante la sesión se **corrigieron bugs** en los extractores para que funcionen contra las fuentes reales. **Estos cambios NO están commiteados aún** en el momento de escribir esto.

### 2.1 `backend/data/nex_gddp.py` — CORREGIDO ✅
El bucket real de NASA usa un esquema diferente al que tenía el código:

- **Host correcto** (obligatorio): `https://nex-gddp-cmip6.s3-us-west-2.amazonaws.com`
  - El host `nex-gddp-cmip6.s3.amazonaws.com` (sin región) responde **`PermanentRedirect`** a `us-west-2`; los lectores de red/NetCDF no lo siguen → el código viejo siempre daba 404.
- **Estructura real del bucket**:
  ```
  NEX-GDDP-CMIP6/{model}/{scenario}/r1i1p1f1/{variable}/
    {variable}_day_{model}_{scenario}_r1i1p1f1_gn_{year}_v2.0.nc
  ```
  - Archivos **ANUALES** (un NetCDF por año, ~200 MB global), NO mensuales.
  - Versión `_v2.0` de NASA. Ejemplo verificado:
    `pr_day_MRI-ESM2-0_ssp585_r1i1p1f1_gn_2015_v2.0.nc`
- **Variables disponibles**: `pr`, `tasmax`, `tasmin`, `rsds`, `huss`.
- **Nuevo método `_regional_summary()`**: lee **solo el bbox del Bajío** (lat 19.5–21.5, lon -102..-99.5) mediante `fsspec` + `h5py` con **byte-range requests** sobre S3, **sin descargar** el archivo global completo. Uso `lon % 360` (NEX-GDDP usa lon 0-360).
- Nueva variable: `CERESPINN_NEX_YEAR_STEP` (default `1`) para espaciar años y reducir descargas.

### 2.2 `backend/data/nass.py` — CORREGIDO (parcial) ⚠️
- La API NASS responde `413 exceeds limit=50000` si se pide todo EE.UU. 1990-2025 en una sola llamada.
- Se implementó **división en ventanas de años** por request (`window_size = 3`).
- **AÚN INCOMPLETO**: 3 años todavía excedió el límite (se probó 1990-1992 → 413). (El `state_alpha` de Iowa 1990 devolvió vacío/sin respuesta en el test.) Hay que terminarlo, ver sección 4.

### 2.3 `backend/data/.env.example` — NUEVO ✅
Plantilla para credenciales locales:
```
NASS_API_KEY=tu-key-aqui
```
Copiar a `backend/data/.env` (que está en `.gitignore`, **no se commitea**).

### 2.4 `extract_all.ps1` — NUEVO (script de disparo) ✅
Script PowerShell en la raíz que:
1. Lee `NASS_API_KEY` desde argumento, `.env` o entorno.
2. Fuerza `CERESPINN_DRY_RUN=0` (LIVE).
3. Lanza `python -m backend.data.extractors all`.

Uso:
```powershell
powershell -ExecutionPolicy Bypass -File extract_all.ps1 -NassKey "TU-KEY"
# o deja la key en backend/data/.env y:
powershell -ExecutionPolicy Bypass -File extract_all.ps1
```

---

## 3. Credenciales / Configuración

| Variable | Dónde | Secreto |
|---|---|---|
| `NASS_API_KEY` | `backend/data/.env` (local, git-ignored) | Sí — tratar como secreto |
| `CERESPINN_DRY_RUN` | default `1` (offline). Se fuerza `0` en el script | — |
| `CERESPINN_NEX_YEAR_STEP` | opcional, espacia años NEX-GDDP | — |
| `DATABASE_URL` (Supabase) | En el dashboard de Render (no en repo) | **Sí — ROTAR contraseña** (expuesta antes en chat) |

**NASS key actual**: registrada con el correo del usuario. **YA NO pegarla en el chat.**

---

## 4. Pendientes — Plan de acción para la próxima sesión (con mejor internet)

### Paso 1 — Terminar `nass.py` (declaran correcto)
1. **Probar reducir aún más la query** hasta pasar el límite:
   ```powershell
   $env:NASS_API_KEY="<tu-key>"; $env:CERESPINN_DRY_RUN="0"
   .venv\Scripts\python.exe -m backend.data.extractors nass
   ```
2. Si sigue 413: **filtrar por estados del Midwest** (protocolo: "condados productores de maíz del Midwest"):
   - NASS admite `state_alpha` (un solo estado por query).
   - Estados clave maíz: `IA, IL, IN, OH, NE, MN, MO, SD, KS, WI, MI, KY, ND, PA, TN, TX, NY, MS`.
   - Añadir encolado por estado en `nass.py` (bucle sobre lista de estados + ventanas de años).
   - O añadir parámetro `NASS_STATE_ALPHA` ya soportado en config → pasar `"IA"` (Iowa).
3. **Verificar** que `maize_county_yield_usda.csv` quede con miles de filas:
   ```powershell
   (Get-Content backend/data/raw/nass/maize_county_yield_usda.csv).Count
   ```
   Debe ser > 1000; el `info["source"]` de `build_dataset` debe pasar a `"nass+nex-gddp"` en vez de `synthetic-fallback`.

### Paso 2 — Verificar CHIRPS
- El código descarga los últimos 5 días (`days_back=5`) de `https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05/{year}/`.
- En la prueba devolvió 404 (la ventana de 5 días quizá aún no publicada, o la fecha del sistema 2026-09-01 no tiene datos).
- **Pendiente**: confirmar el path correcto de CHIRPS-2.0 daily `.tif` y, si hace falta, ampliar ventana o cambiar a la integración mensual.

### Paso 3 — Ejecutar NEX-GDDP (muestreo ligero)
- Es el más lento por tu conexión (medido **~0.41 MB/s** hacia el bucket → ~200 MB/archivo ≈ 8 min/archivo si se bajara completo).
- Con `_regional_summary()` (range reads) se evita bajar el archivo completo; leer 1 año/región tomó ~47 s en el test.
- Comando con espaciado para mantener el volumen bajo:
  ```powershell
  $env:CERESPINN_NEX_YEAR_STEP="5"   # 2015, 2020, 2025, ... 2050
  .venv\Scripts\python.exe -m backend.data.extractors nex
  ```
- **Meta**: poblar `nex_gddp_region_summary.csv` con filas (scenario, model, variable, year, region_mean/min/max) que ya consume `dataset.py::_blend_climate`.

### Paso 4 — Entrenar el PINN con datos reales
```powershell
$env:CERESPINN_DRY_RUN="0"
.venv\Scripts\python.exe -m backend.training.train
```
- Requisito local: `torch` (ya instalado en `.venv`; **no** está en `requirements.txt` para no inflar Render).
- Output: `backend/models/cerespinn_pinn.pt` + `cerespinn_metadata.json`.
- Verificar que `inference_mode` pase a `"pinn"` en `/api/simulate`.

### Paso 5 — Subir datos/modelo a producción
- Los CSV/NetCDF están en `backend/data/raw/` (**git-ignored** — no subir al repo; son gigabytes).
- El repo solo guarda código + `.env.example`. Los datos reales viven en disco local o en un bucket (futuro).
- Para Render: pensar si se transfiere el checkpoint modelo (~MB) o se entrena en CI.

---

## 5. Cómo verificar el éxito al final

| Chequeo | Criterio |
|---|---|
| `maize_county_yield_usda.csv` | ›1000 filas, con `year/state_name/county_name/Value` |
| `build_dataset` | `info["source"] == "nass+nex-gddp"` (no `synthetic-fallback`) |
| `nex_gddp_region_summary.csv` | filas por scenario/model/variable/year con `region_mean` |
| `backend/models/cerespinn_pinn.pt` | existe (trained) |
| `/api/validation` hindcast | `reference_source == "usda-nass"` y RMSE/R² sensatos |
| `/api/simulate` | `inference_mode == "pinn"` |

---

## 6. Archivos relevantes (rutas)

- `backend/data/nex_gddp.py` — extractor NEX-GDDP (corregido)
- `backend/data/nass.py` — extractor NASS (corregido parcialmente)
- `backend/data/chirps.py` — extractor CHIRPS
- `backend/data/extractors.py` — CLI `python -m backend.data.extractors [all|chirps|nass|nex]`
- `backend/data/config.py` — configuración (StudyArea, TimeConfig, NASSConfig, ensemble_members)
- `backend/training/dataset.py` — `build_dataset` (consume NASS CSV + nex summary)
- `backend/training/train.py` — entrenamiento (guarda `.pt` + metadata)
- `extract_all.ps1` — script disparador PowerShell (LIVE)
- `backend/data/.env.example` — plantilla de credenciales