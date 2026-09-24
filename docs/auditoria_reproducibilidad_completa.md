# Auditoría técnica y de reproducibilidad de CeresPINN

Fecha de auditoría: 22 de septiembre de 2026
Repositorio examinado: `https://github.com/David42024/CeresPINN`
HEAD local examinado: `6c22e543b0fefbc498f5d811732974f48c1089c2` (`lucano`)

## Criterio de esta auditoría

- **VERIFICADO**: existe evidencia ejecutable o inspeccionable en el repositorio/entorno.
- **VERIFICADO CON SALVEDADES**: el hecho principal se comprobó, pero hay una limitación que impide una afirmación más fuerte.
- **NO VERIFICADO**: el repositorio actual no contiene la evidencia necesaria, el procedimiento no pudo ejecutarse desde cero o el resultado publicado no puede reconstruirse exactamente.

Los hallazgos numerados de esta auditoría describen el commit base `6c22e543...`. Después de esa fotografía se aplicó el cierre de reproducibilidad descrito a continuación; por eso, las observaciones históricas sobre archivos no rastreados deben interpretarse como el problema de origen y no como el estado final del paquete corregido.

## Estado posterior a la remediación

| Criterio | Estado actual | Evidencia ejecutable |
|---|---|---|
| B5.2 — datos, scripts y artefactos versionados | ✅ Cerrado | `data/cerespinn_training_iowa.csv`, `data/cerespinn_training_preprocessed.csv`, `scripts/generate_q1_revision_artifacts.py`, `scripts/generate_q1_extended_audit.py`, `docs/q1_artifacts/`, `reproducibility/manifest.json` |
| B5.3 — pipeline integral/CI | ✅ Cerrado | `python scripts/reproduce.py`; `.github/workflows/reproducibility.yml` |
| Licencia explícita | ✅ Cerrado | `LICENSE` (MIT) |
| Comandos desde clon limpio | ✅ Cerrado | sección “Reproduce the scientific results” de `README.md`; `requirements-repro.txt` |
| B3.1 — separación prospectiva | ✅ Diseño ejecutado, ⚠️ desempeño | entrenamiento 1990–2017 → prueba 2018–2025; diez semillas; `docs/q1_artifacts/temporal/` |

El comando integral verificó cuatro insumos mediante SHA-256 y conteos, regeneró
los artefactos Q1 básicos y extendidos, ejecutó la validación temporal y comprobó
ocho salidas obligatorias. La evaluación prospectiva no mostró buena
generalización: RMSE = 855.22 kg ha⁻¹, MAE = 683.62 kg ha⁻¹ y R² = −0.8318.
Por tanto, queda resuelta la ausencia metodológica de un corte temporal, pero no
se convierte en evidencia favorable ni sustituye una validación externa.

## Resumen ejecutivo

El backend sí carga el checkpoint PyTorch y `/api/simulate` lo consume. Sin embargo, la implementación entrenada no resuelve Richards ni optimiza un residuo PDE. Es una MLP de siete entradas con regularización de monotonicidad sobre la derivada del rendimiento respecto de temperatura y precipitación; su segunda cabeza, llamada `physics_head`, no tiene target observado y su única penalización efectiva de rango es cero por la activación sigmoide. El simulador diario posterior es un modelo de cubetas y reglas heurísticas; los efectos de cultivar, riego, nitrógeno y CO₂ sobre el rendimiento final se aplican mediante multiplicadores fijos.

El hindcast retenido tiene ocho años independientes. El checkpoint obtuvo RMSE = 712.126847 kg ha⁻¹, MAE = 604.187051 kg ha⁻¹ y R² = 0.825085. No supera a regresión lineal ni Ridge en ese split. Los IC bootstrap de sus diferencias frente a ambos incluyen cero. No existe validación externa espacial o de campo. La remediación añadió un corte prospectivo 1990–2017 → 2018–2025, cuyo R² negativo evidencia generalización temporal insuficiente. La reproducción completa sí queda empaquetada ahora mediante datasets procesados versionados, scripts Q1, artefactos, licencia MIT, dependencias fijadas, manifiesto de integridad, comando único y CI.

---

## Respuestas 1–22 — repositorio, entorno y formulación del modelo

### 1. Repositorio y versión exacta

**Respuesta concreta.** La URL es <https://github.com/David42024/CeresPINN>. Se comprobó acceso anónimo al branch `main`; `git ls-remote` devolvió `6c22e543b0fefbc498f5d811732974f48c1089c2 refs/heads/main`. El HEAD local auditado es el mismo hash, pero está en la rama local `lucano`. No hay tag apuntando a HEAD ni release identificado. Además, los nuevos scripts/CSV de auditoría están sin commit, por lo que **no existe un commit/release que corresponda exactamente a todos los resultados de este documento**.

- **Estado:** VERIFICADO para URL, acceso y hash; **NO VERIFICADO** para una release exacta del artículo.
- **Archivo/ruta:** `.git/config`; estado mediante Git.
- **Función/línea:** no aplica.
- **Comando:** `git remote -v; git rev-parse HEAD; git branch --show-current; git tag --points-at HEAD; git ls-remote https://github.com/David42024/CeresPINN.git refs/heads/main`
- **Salida:** origin público; HEAD `6c22e543...`; rama `lucano`; sin tag; remoto `main` en el mismo hash.
- **Cómo obtenerlo:** `git clone https://github.com/David42024/CeresPINN.git && cd CeresPINN && git checkout 6c22e543b0fefbc498f5d811732974f48c1089c2 && git rev-parse HEAD`.

### 2. Licencia del repositorio

**Respuesta concreta.** No existe `LICENSE`, `LICENSE.md`, `COPYING` ni una declaración equivalente rastreada. Por consiguiente, el código público no tiene una licencia de reutilización explícita.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** raíz del repositorio; archivo ausente.
- **Comando:** `git ls-files | rg '(^|/)(LICENSE|COPYING)(\.|$)'`
- **Salida:** sin coincidencias.
- **Artefacto:** ninguno; la ausencia es el resultado.

### 3. README de reproducción

**Respuesta concreta.** `README.md` documenta instalación del frontend, instalación/arranque del backend, variables de entorno, endpoints y despliegue. `backend/training/README.md` documenta configuración y comando básico de entrenamiento. No hay un recorrido verificable que prepare los datos reales, entrene, ejecute todos los baselines/estadísticas y genere todas las figuras desde un clon limpio. Tampoco fija el commit/dataset ni documenta los scripts Q1 nuevos, porque aún no están versionados.

- **Estado:** VERIFICADO CON SALVEDADES; README operativo, no README integral de reproducción científica.
- **Archivo/ruta:** `README.md` (aprox. líneas 32–114); `backend/training/README.md` (líneas 29–83); `docs/q1_artifacts/README.md` (local/no rastreado).
- **Comando:** `rg -n "install|train|baseline|figure|artifact|NASS_API_KEY|CERESPINN_DRY_RUN" README.md backend/training/README.md docs/q1_artifacts/README.md`
- **Salida:** instalación y entrenamiento parcial; no aparece una cadena completa clon→datos→paper.

### 4. Comando mínimo de reproducción

**Respuesta concreta.** No existe hoy un conjunto **verificado desde clon limpio** que reproduzca todo. La secuencia más cercana es:

```powershell
git clone https://github.com/David42024/CeresPINN.git
cd CeresPINN
git checkout 6c22e543b0fefbc498f5d811732974f48c1089c2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements-ml.txt
$env:NASS_API_KEY='<clave propia>'
$env:CERESPINN_DRY_RUN='0'
python -m backend.data.run_all
python -m backend.training.train
python scripts/generate_q1_revision_artifacts.py
python scripts/generate_q1_extended_audit.py
python -m pytest backend/tests -q
```

Esta receta falla como reproducción pública exacta porque el commit no incluye los dos scripts Q1 ni `data/cerespinn_training_iowa.csv`; además, el extractor no demuestra en una sola ejecución que produzca ese archivo exacto.

- **Estado:** **NO VERIFICADO** desde clon limpio.
- **Archivo/ruta:** `backend/data/run_all.py`, `backend/training/train.py`, scripts Q1 locales.
- **Salida observada:** los scripts funcionan en el workspace con el CSV local; no se validó el ciclo completo en clon limpio.

### 5. Pipeline automatizado

**Respuesta concreta.** Hay extractores (`backend/data/run_all.py`), entrenamiento (`backend/training/train.py`), Dockerfiles y dos generadores Q1 locales. No hay un único Makefile/notebook/workflow/script versionado que regenere datos, modelo, baselines, estadística y figuras. `ml_lab/docker-compose.yml` pertenece al laboratorio ML, no demuestra el pipeline íntegro del artículo.

- **Estado:** VERIFICADO; el pipeline único no existe.
- **Archivo/ruta:** `backend/data/run_all.py`, `backend/training/train.py`, `Dockerfile`, `ml_lab/Dockerfile`, `ml_lab/docker-compose.yml`, `scripts/generate_q1_*.py` (estos dos no rastreados).
- **Comando:** `rg --files | rg '(Makefile|Dockerfile|docker-compose|\.ipynb$|\.github/workflows|generate_q1)'`
- **Salida:** los archivos anteriores; sin Makefile, notebook integral ni workflow CI.

### 6. Docker

**Respuesta concreta.** Sí existe un `Dockerfile` raíz. Instala dependencias del backend, copia `backend/`, valida que exista el checkpoint y sirve FastAPI. No copia datasets ni scripts Q1; por tanto, no ejecuta el experimento. El intento `docker build --pull -t cerespinn-audit:6c22e54 .` falló porque el daemon Docker no estaba activo (`docker_engine` no encontrado). Funcionalidad desde cero: **NO VERIFICADA**.

- **Estado:** archivo VERIFICADO; build funcional **NO VERIFICADO**.
- **Archivo/ruta:** `Dockerfile` (completo); `ml_lab/Dockerfile`; `ml_lab/docker-compose.yml`.
- **Comando de imagen/API:** `docker build -t cerespinn-api:6c22e54 .` y `docker run --rm -p 8000:8000 cerespinn-api:6c22e54`.
- **Salida obtenida:** fallo de conexión al daemon; no se produjo imagen.
- **Comando de experimento:** no existe dentro del Dockerfile.

### 7. Dependencias y versiones

**Respuesta concreta.** Entorno usado en la auditoría: Python 3.12.14; PyTorch 2.6.0+cpu; NumPy 2.1.3; pandas 2.2.3; scikit-learn 1.9.1; SciPy 1.14.1; FastAPI 0.141.1; Pydantic 2.9.2; Uvicorn 0.30.6; SALib no instalada. El repositorio declara Python 3.12.6 en `runtime.txt`. PyTorch/NumPy/pandas/SciPy están fijados exactamente en `backend/requirements.txt`; FastAPI usa rango y `backend/requirements-ml.txt` usa mínimos (`>=`), por lo que el entorno no está completamente bloqueado.

- **Estado:** VERIFICADO para el entorno auditado; reproducibilidad exacta de todas las dependencias: **NO VERIFICADA**.
- **Archivo/ruta:** `runtime.txt`; `backend/requirements.txt`; `backend/requirements-ml.txt`.
- **Comando:** `python -c "import torch,numpy,pandas,sklearn,scipy,fastapi,pydantic,uvicorn; ..."`
- **Salida:** versiones listadas arriba; `importlib.util.find_spec('SALib')` → `None`.

### 8. Sistema operativo y hardware

**Respuesta concreta.** Benchmarks ejecutados en Windows 11 (`10.0.26200`, x64), Intel Core i5-12450H, 12 procesadores lógicos, 16,869,548,032 bytes de RAM (~15.71 GiB), CPU-only, PyTorch 2.6.0+cpu, ocho hilos PyTorch. No se usó CUDA. La identidad de una GPU instalada no pudo leerse por permisos, pero PyTorch fue compilado con `USE_CUDA=0`.

La nueva ejecución obtuvo 31.355816 s de entrenamiento, mediana 1.9984 ms y p95 5.658015 ms. Por ello, los valores narrados 31.8 s, 2.20 ms y 4.66 ms son plausibles como corrida previa, pero el p95 exacto no se reprodujo en esta corrida.

- **Estado:** hardware/entorno VERIFICADO; cifras exactas publicadas VERIFICADAS CON SALVEDADES.
- **Archivo/ruta:** `docs/q1_artifacts/q1_statistics.json`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py` y consulta de `os`, `torch.get_num_threads()`.
- **Salida:** 31.355816 s; 1.9984 ms mediana; 5.658015 ms p95; batch 1; CPU.

### 9. Semillas aleatorias

**Respuesta concreta.** Configuración principal: seed 42. `train()` fija `torch.manual_seed(42)` y `np.random.seed(42)`. El split usa `np.random.default_rng(42)`. No se fija `random.seed`, ni semillas CUDA. Los baselines auditados usan el mismo split; Random Forest usa `random_state=42`; regresión lineal y Ridge son deterministas; los modelos neuronales fijan NumPy/PyTorch. La corrida multi-seed usó `[0,1,2,3,4,5,6,7,8,42]`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/config.py:62`; `backend/training/train.py:46-47`; `backend/training/dataset.py:242-249`; `scripts/generate_q1_extended_audit.py`.
- **Comando:** `rg -n "seed|manual_seed|random_state|default_rng" backend/training scripts/generate_q1_*.py`
- **Salida:** no aparece `random.seed` ni `torch.use_deterministic_algorithms`.

### 10. Determinismo

**Respuesta concreta.** No se garantiza determinismo completo entre plataformas: `torch.use_deterministic_algorithms(True)` no está configurado y `random.seed` no se fija. En esta CPU, dos reentrenamientos seed 42 dieron diferencia máxima y media de predicción exactamente `0.0 bu/acre`.

- **Estado:** repetición local VERIFICADA; determinismo universal **NO VERIFICADO**.
- **Archivo/ruta:** `docs/q1_artifacts/extended/extended_audit.json`, clave `determinism_same_seed_repeat`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`
- **Salida:** `max_abs_prediction_difference_bu_acre=0.0`; `torch_deterministic_algorithms_enabled=false`.

### 11. Número exacto de épocas

**Respuesta concreta.** El valor por defecto y el guardado en metadatos es 300 épocas. El loop ejecuta `range(train_config.epochs)`. No hay early stopping y el checkpoint guardado corresponde al estado de la época final, no al mejor `test_mse`, aunque se calcula `best_test_mse`. Los resultados regenerados aquí usan 300 épocas.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/config.py:52`; `backend/training/train.py:81-112,152`.
- **Comando:** `rg -n "epochs|range\(train_config.epochs\)|early" backend/training backend/models/cerespinn_metadata.json`
- **Salida:** `epochs: 300`; sin parada temprana/restauración del mejor modelo.

### 12. Learning rate

**Respuesta concreta.** Adam usa `lr=0.001` constante. No existe scheduler ni cambio de tasa.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/config.py:51`; `backend/training/train.py:62-66`.
- **Comando:** `rg -n "learning_rate|scheduler|Adam" backend/training`
- **Salida:** `1e-3`; cero schedulers.

### 13. Batch size

**Respuesta concreta.** Batch real = 64. Con 84 filas de entrenamiento se producen dos minibatches por época (64 y 20); no es full-batch.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/config.py:53`; `backend/training/train.py:70-77`.
- **Comando:** `python -c "import math; print(math.ceil(84/64))"`
- **Salida:** `2` batches/época.

### 14. Weight decay y L2

**Respuesta concreta.** Hay dos regularizaciones L2 simultáneas: Adam `weight_decay=1e-5` y un término manual `1e-4 * Σθ²` sumado a la pérdida. El artículo debe reportar ambas; no debe llamar a `1e-4` el `weight_decay` del optimizador.

\[
L = L_{data} + L_{mono/range} + 10^{-4}\sum_j\theta_j^2,
\quad \text{Adam weight decay}=10^{-5}.
\]

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/config.py:54,59`; `backend/training/train.py:62-66,90-96`.
- **Comando:** `rg -n "weight_decay|loss_reg_weight|regul" backend/training`
- **Salida:** `1e-5` en Adam y `1e-4` manual.

### 15. Pérdida de monotonicidad (`physics_loss`)

**Respuesta concreta.** Se diferencia la salida de **rendimiento normalizado** respecto de las entradas **normalizadas** `temp_anomaly_c` y `seasonal_precip_mm`:

\[
L_{mono}=0.5\,\mathbb{E}[\max(0,\partial\hat y/\partial x_{temp})]
+0.5\,\mathbb{E}[\max(0,-\partial\hat y/\partial x_{precip})].
\]

Penaliza que el rendimiento aumente al subir la anomalía térmica y que disminuya al aumentar la precipitación estacional. No contiene ecuación de Richards, balance de agua ni derivadas de la cabeza hídrica. El docstring que dice “Jacobian of the physics head” contradice el código: se deriva `yield_pred`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/pinn.py:78-120`, función `physics_loss`.
- **Comando:** `Get-Content backend/training/pinn.py | Select-Object -Skip 77 -First 44`
- **Salida:** llamadas `autograd.grad(yield_pred.sum(), xg)` y ReLU descritas.

### 16. `L_range`

**Respuesta concreta.** Existe:

\[
L_{range}=0.5\{E[\max(0,h-1)]+E[\max(0,-h)]\}.
\]

Como `h=Sigmoid(·)`, `0≤h≤1` por construcción y el término es matemáticamente cero (salvo imposibles errores numéricos fuera del rango). En el checkpoint auditado: `physics_head_min_train=0.5`, `max=0.5`, `effective_range_penalty_train=0.0`. Conviene eliminarlo de la ecuación como “restricción aprendida” o describirlo como redundante; si se desea una penalización informativa, habría que retirar la sigmoide o supervisar/relacionar `h` con un balance físico.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/pinn.py:64-69,117-118`; `docs/q1_artifacts/extended/extended_audit.json`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`
- **Salida:** min=max=0.5; penalización=0.0.

### 17. Arquitectura exacta

**Respuesta concreta.** Siete entradas: `year`, `temp_anomaly_c`, `precip_anomaly_pct`, `co2_ppm`, `heatwave_risk`, `seasonal_precip_mm`, `seasonal_cdd`. Tronco: `7→128→128→128→128`, cada capa lineal seguida por Tanh y Dropout(0.05). Cabeza de rendimiento: `128→64(ReLU)→1` lineal. Cabeza física: `128→32(ReLU)→1(Sigmoid)`. No hay BatchNorm/LayerNorm; la normalización es externa z-score. Total = 63,042 parámetros, todos entrenables.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/config.py:41-84`; `backend/training/pinn.py:41-75`, clase `CeresPINN`; `docs/q1_artifacts/extended/hyperparameters.csv`.
- **Comando:** `python -c "...; print(sum(p.numel() for p in model.parameters()))"`
- **Salida:** `63042`.

### 18. Segunda cabeza de salida

**Respuesta concreta.** El código la denomina proxy de disponibilidad hídrica en `[0,1]`, pero no se entrena contra humedad/CWSI/agua observada ni participa en la monotonicidad. Solo entra a `L_range`, que es cero por la sigmoide, y sus pesos reciben L2/weight decay. En el checkpoint colapsó a 0.5 para todo el train. No debe presentarse como estado hídrico aprendido con significado físico validado.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/pinn.py:64-75,98-118`; `backend/training/train.py:84-96`.
- **Comando/artefacto:** `python scripts/generate_q1_extended_audit.py` → `extended_audit.json`.
- **Salida:** `physics_head_has_observed_target=false`; min=max=0.5.

### 19. Normalización

**Respuesta concreta.** Las siete entradas se estandarizan con media y desviación calculadas **solo en las 84 filas train**; el target usa min-max de train. Estadísticos, en orden de features:

| Variable | Media train | SD train |
|---|---:|---:|
| year | 2008.7857142857142 | 10.136064133631379 |
| temp_anomaly_c | 0.8557481166294651 | 2.0508371213083323 |
| precip_anomaly_pct | -0.12666666666666676 | 0.089938260421547 |
| co2_ppm | 481.6666666666667 | 30.641293861417076 |
| heatwave_risk | 0.4500000000000003 | 0.258069768011279 |
| seasonal_precip_mm | 374.82179252058165 | 139.78422607761186 |
| seasonal_cdd | 20.0 | 1e-8 |

Target: `y_min=78.0`, `y_max=210.10000001 bu/acre`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/train.py:49-58`; `backend/models/cerespinn_metadata.json`; `docs/q1_artifacts/extended/normalization_stats.csv`.
- **Comando:** `Get-Content docs/q1_artifacts/extended/normalization_stats.csv`
- **Salida:** tabla anterior.

### 20. Split temporal

**Respuesta concreta.** Train (28): 1990, 1993, 1994, 1995, 1996, 1997, 1999, 2000, 2002, 2005, 2006, 2007, 2008, 2009, 2010, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2025. Test (8): 1991, 1992, 1998, 2001, 2003, 2004, 2011, 2024. El algoritmo permuta años únicos con seed 42 y luego selecciona todas las filas cuyo año pertenece a cada partición; ninguna copia SSP de un año cruza particiones.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/dataset.py:239-258`; `backend/models/cerespinn_metadata.json`.
- **Comando:** `python -c "import json; d=json.load(open('backend/models/cerespinn_metadata.json')); print(d['data']['split'])"`
- **Salida:** listas anteriores, método `grouped-random-year-holdout`.

### 21. Construcción de 84/24 filas

**Respuesta concreta.** Se calcula una mediana de rendimiento por año y se replica cada uno de los 36 targets para tres escenarios: SSP1-2.6, SSP3-7.0 y SSP5-8.5. Por eso `36×3=108`, `28×3=84` train y `8×3=24` test.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/dataset.py:212-234`; `SCENARIO_TEMPLATE` en líneas 28-32.
- **Comando:** `python -c "print(36*3,28*3,8*3)"`
- **Salida:** `108 84 24`.

### 22. Unidad experimental

**Respuesta concreta.** Sí: las tres filas SSP de un año comparten exactamente el mismo `yield_bu_acre` porque `y=np.tile(annual['yield_bu_acre'], 3)`. Son observaciones condicionadas por escenario, no tres mediciones independientes. La unidad experimental para inferencia estadística es el año (`n=8` test), no la fila (`n=24`). Todas las pruebas de esta auditoría colapsan/promedian las tres predicciones por año antes de calcular métricas.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/dataset.py:232-234`; `scripts/generate_q1_revision_artifacts.py`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`
- **Salida:** `n_independent_years=8` en `q1_statistics.json`.

---

## Respuestas 23–42 — datos, simulador y escenarios de manejo

### 23. Origen de las 22,160 observaciones USDA-NASS

**Respuesta concreta.** El extractor consulta `https://quickstats.nass.usda.gov/api/api_GET/` en ventanas de tres años, 1990–2025, con filtros `source_desc=SURVEY`, `sector_desc=CROPS`, `commodity_desc=CORN`, `reference_period_desc=YEAR`, `statisticcat_desc=YIELD`, `agg_level_desc=COUNTY`, `unit_desc=BU / ACRE`. Si `NASS_STATE_ALPHA` está vacío consulta todos los estados; si existe, filtra ese estado. Conserva año, estado, condado, ANSI, valor, unidad y estadístico; elimina comas y paréntesis de `Value` y lo convierte a numérico.

El conteo 22,160 está guardado en metadatos/CSV expandido local, pero el CSV bruto actual fue sobrescrito por un dry-run y contiene solo encabezado (87 bytes, manifest 0 registros). Por ello no se pueden volver a enumerar los 22,160 originales desde el raw presente.

- **Estado:** consulta/código VERIFICADOS; contenido bruto exacto **NO VERIFICADO**.
- **Archivo/ruta:** `backend/data/nass.py:29-177`, `NASSProvider`; `backend/data/config.py:116-137`; `docs/q1_artifacts/extended/data_lineage_counts.csv`.
- **Comando:** `$env:NASS_API_KEY='...'; $env:CERESPINN_DRY_RUN='0'; python -m backend.data.nass`.
- **Salida actual:** `backend/data/raw/nass/usda-nass_manifest.json` declara `records:0,dry_run:true`.

### 24. Agregación a 36 años

**Respuesta concreta.** Tras limpiar, se calcula para cada año:

\[
y_t=\operatorname{mediana}\{Value_i:year_i=t\}.
\]

El código es `norm.groupby('year')['yield_bu_acre'].median()`. La tabla intermedia reconstruida tiene 36 filas 1990–2025 y está en `temporal_coverage.csv` con `year`, conteo y mediana. No obstante, se reconstruyó desde el CSV local expandido sin geografía, no desde el raw actualmente vacío.

- **Estado:** transformación/36 medianas VERIFICADAS; regeneración desde raw actual **NO VERIFICADA**.
- **Archivo/ruta:** `backend/training/dataset.py:64-72,212-218`; `docs/q1_artifacts/extended/temporal_coverage.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.
- **Salida:** 36 años; mediana 1990=124.9 y 2025=210.1 bu/ac.

### 25. Los 98 registros NEX-GDDP-CMIP6

**Respuesta concreta.** La configuración pretende leer SSP126/370/585, siete GCM por SSP, variables `pr,tasmax,tasmin,rsds,huss`, años 2015–2050 y bbox Bajío `[-102.0,19.5,-99.5,21.5]`; cada NetCDF anual se resume sobre la región muestreando hasta 12 días. Sin embargo, el archivo NEX actual tiene 2 bytes/0 filas y el manifest dry-run registra cero. No puede determinarse qué 98 combinaciones exactas generaron el checkpoint, ni si fueron descarga directa o preprocesado preservado.

- **Estado:** configuración VERIFICADA; procedencia de las 98 filas **NO VERIFICADA**.
- **Archivo/ruta:** `backend/data/config.py:86-113`; `backend/data/nex_gddp.py:45-210`; `backend/data/raw/nex-gddp/nex-gddp_manifest.json`.
- **Comando:** `Get-Content backend/data/raw/nex-gddp/nex-gddp_manifest.json`.
- **Salida:** `records=0`, dry-run, configuración anterior.

### 26. Valores faltantes de clima

**Respuesta concreta.** El código interpola linealmente por escenario entre años NEX disponibles y extiende extremos (`limit_direction='both'`) sobre 1990–2025; si no hay valor para `tasmax`/`pr`, conserva el template. Pero no registra, por celda, si el valor fue real, interpolado o predefinido. Con el resumen NEX original ausente no se puede generar la tabla solicitada de combinaciones.

- **Estado:** regla VERIFICADA; tabla exacta **NO VERIFICADA**.
- **Archivo/ruta:** `backend/training/dataset.py:86-140` (`_nex_year_lookup`) y `142-183` (`_blend_climate`).
- **Comando:** `rg -n "interpolate|limit_direction|Live NEX|template" backend/training/dataset.py`.
- **Salida:** interpolación implementada, sin columna de procedencia.

### 27. Valores +2.7 °C y −24%

**Respuesta concreta.** Son constantes manuales de `SCENARIO_TEMPLATE` para SSP5-8.5, junto con CO₂=520 ppm y `heatwave_risk=0.78`. El propio comentario las llama placeholders derivados del forcing del frontend. NEX puede reemplazar `temp_anomaly_c` y `seasonal_precip_mm`, pero no `precip_anomaly_pct`; en la llamada Iowa 2050 estos valores llegan directamente en el payload. No son valores NEX 2050 demostrados.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/dataset.py:25-32`; `backend/inference.py:106-132`.
- **Comando:** `rg -n "2.7|-0.24|520.0|0.78" backend src`.
- **Salida:** constantes de template.

### 28. CO₂

**Respuesta concreta.** No se carga una serie externa. Por escenario se asignan 445/480/520 ppm; después de 2026 se suma `1.5×(año−2026)` en `_blend_climate`. Como los años de entrenamiento llegan a 2025, el checkpoint fue entrenado con tres constantes de escenario, sin tendencia intraescenario. En inferencia, `build_features` toma `carbon_dioxide_ppm` del payload o template; el simulador aplica además un multiplicador separado de CO₂ al rendimiento.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/dataset.py:28-32,156-160`; `backend/inference.py:106-132,213-220`.
- **Comando:** `rg -n "co2_ppm|carbon_dioxide_ppm|years_from_base" backend/training/dataset.py backend/inference.py`.

### 29. `seasonal_cdd`

**Respuesta concreta.** En el checkpoint es constante 20.0; media 20 y desviación guardada `1e-8`, introducida para evitar división por cero. Quedó constante porque `years_from_base=max(0,year−2026)` y el train termina en 2025. No hay otra entrada con varianza cero; `seasonal_cdd` es la única correlación completamente NaN.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/dataset.py:181`; `backend/models/cerespinn_metadata.json`; `normalization_stats.csv`.
- **Comando:** `Get-Content docs/q1_artifacts/extended/normalization_stats.csv`.

### 30. `heatwave_risk`

**Respuesta concreta.** No se deriva de temperaturas diarias ni NEX. Es un valor predefinido por escenario: 0.15, 0.42 y 0.78. NEX no lo reemplaza.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/training/dataset.py:28-32`, `SCENARIO_TEMPLATE`.
- **Comando:** `rg -n "heatwave_risk" backend/training/dataset.py`.

### 31. Nombre `seasonal_precip_mm`

**Respuesta concreta.** El nombre correcto en todo el código ejecutable es `seasonal_precip_mm`. `seasonal_precio_mm` no aparece en el repositorio; es un error del manuscrito, no una variable implementada.

- **Estado:** VERIFICADO.
- **Comando:** `rg -n "seasonal_precip_mm|seasonal_precio_mm" . --glob '!node_modules/**'`.
- **Salida:** coincidencias solo para `seasonal_precip_mm`.

### 32. Simulador biofísico diario

**Respuesta concreta.** `PinnInference.run_full_simulation` realiza, por día:

1. clima sintético sinusoidal más anomalía; no lee una serie meteorológica diaria;
2. GDD con media térmica truncada a `[10,30]` y base 10;
3. etapa por umbrales GDD; LAI sinusoidal y senescencia; raíces lineales 15→120 cm;
4. ETo Priestley–Taylor simplificada y `ETc=ETo×Kc`;
5. lluvia determinista por senos y riego por umbral de humedad;
6. cubetas de 300/300/400 mm: entrada, transpiración, evaporación, drenajes 0.8/0.7/0.6 sobre FC y límites `[0.5WP,SAT]`;
7. `CWSI=clip(1−(θavg−WP)/(FC−WP),0.05,0.98)`;
8. estrés térmico `clip((Tmax−32)/10,0,1)`;
9. biomasa diaria heurística `220(LAI/LAImax)(1−0.65CWSI)(1−0.4 estrés térmico)n_mult`, mínimo 5 kg/ha/d.

- **Estado:** VERIFICADO como implementación; no está calibrado/validado físicamente.
- **Archivo/ruta:** `backend/inference.py:166-437`, método `run_full_simulation`.
- **Comando:** `Get-Content backend/inference.py | Select-Object -Skip 165 -First 275`.

### 33. Richards y residuo PDE

**Respuesta concreta.** **No.** No existe discretización numérica de Richards ni residuo PDE en el entrenamiento. La función llamada/comentada “Richards Layer Dynamics” es una actualización de depósitos por capa. La pérdida entrenada solo impone monotonicidad del rendimiento y rango de una salida sigmoide.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:363-387`; `backend/training/pinn.py:78-120`; `src/services/pinnEngine.ts:98-160`.
- **Comando:** `rg -n "autograd|Richards|pde|drain1|theta_top" backend src/services/pinnEngine.ts`.
- **Salida:** no hay derivadas espaciales/temporales de PDE ni residual en loss.

### 34. Variables falsas/legacy

**Respuesta concreta.** Siguen presentes. Backend devuelve constantes `pde_residual_richards_loss=0.0028`, `boundary_condition_loss=0.0019`, `physics_conservation_error_percent=0.85`; frontend las mapea con fallbacks 0.003/0.002/1.2; el simulador TypeScript local genera versiones aleatorias con `Math.random`; el PDF exporta `PINN PDE Richards Loss`. No fueron eliminadas.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:502-513`; `src/services/api.ts:180-187`; `src/services/pinnEngine.ts:510-517`; `src/components/ReportsModule.tsx:231`; `src/types/index.ts:152-160`.
- **Comando:** `rg -n "pde_residual|pdeResidual|boundary_condition|physics_conservation|physicsConservation" backend src`.

### 35. MLOps simulado

**Respuesta concreta.** `MLOpsDashboard.tsx` contiene seis puntos hard-coded de épocas 1,000–15,000 con total/PDE/data/boundary loss; no proceden del entrenamiento real de 300 épocas. El slider `lambdaPde` solo cambia UI. Registros históricos de `backend/db.py` contienen modelos seed de 8,000/12,000/15,000 épocas y métricas demo. Las métricas del modelo activo sí se leen de metadata. El PDF no exporta la curva, pero sí exporta el falso PDE loss de la simulación.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `src/components/MLOpsDashboard.tsx:37,81-86,123-170`; `backend/db.py:606-650`; `ReportsModule.tsx:231`.
- **Comando:** `rg -n "epoch:|pdeLoss|boundaryLoss|15000|12000|8000" src/components/MLOpsDashboard.tsx backend/db.py`.

### 36. Fecha de siembra y rendimiento

**Respuesta concreta.** `planting_date` no forma parte de las siete entradas de `build_features` ni de `bu_final`. Solo fija `curr_date`, día del año, clima sintético, fenología y balances diarios. Por eso adelantar 14 días cambia agua/estrés/fechas, pero el rendimiento final queda 13,331 kg/ha en ambos casos.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:106-147` (features), `206-223` (yield), `240-282` (calendario), `management_scenarios.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.
- **Salida:** baseline y early planting, ambos 13,331; CWSI 0.83 vs 0.95.

### 37. Suelo y rendimiento

**Respuesta concreta.** `field_id`, FC, WP, SAT y Ks tampoco son entradas de la red ni aparecen en la fórmula `bu_final`. Se resuelven después de calcular el rendimiento y solo modifican estados diarios. Así, cuatro suelos pueden compartir 13,331 kg/ha con igual clima/manejo.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:106-147,206-236`; `field_soil_constants.csv`.
- **Comando:** `rg -n "feature_values|soil_by_field|bu_final" backend/inference.py`.

### 38. Multiplicadores de manejo

**Respuesta concreta.** En orden multiplicativo sobre `bu_raw`:

- cultivar: corto 0.88, medio 1.00, largo 1.12;
- riego: secano 0.85, déficit50 0.96, déficit75 1.03, óptimo/full 1.08, sensor 1.06, desconocido 0.98;
- N si `<180`: `max(0.60,0.60+0.40N/180)`; si `≥180`: `min(1.08,1+0.0006(N−180))`;
- CO₂: `clip(1+0.00015(CO₂−420),0.96,1.08)`.

Luego `bu_final=max(40,producto)`, conversión `×62.77` a kg/ha y mínimo final 2,500 kg/ha. El CO₂ también modifica transpiración por `max(0.85,1−0.00025(CO₂−420))`, pero no vuelve a modificar el yield.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:188-223`.
- **Comando:** `Get-Content backend/inference.py | Select-Object -Skip 187 -First 38`.

### 39. Basal Iowa SSP5-8.5 2050

**Respuesta concreta.** Checkpoint: `217.9594268798828 bu/ac`. Configuración: ciclo medio 1.00; déficit50 0.96; N=180 →1.00; CO₂=520 → `1+(100×0.00015)=1.015`. Por tanto:

\[
217.9594268798828×1×0.96×1×1.015×62.77
=13331.0716067\;kg/ha\rightarrow13,331.
\]

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:188-223`; `management_scenarios.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 40. Riego al 75%

**Respuesta concreta.** La salida neuronal sigue en 217.9594269 bu/ac. Solo cambia riego 0.96→1.03:

\[
y=217.9594269×1.03×1.015×62.77=14303.1289\rightarrow14,303.
\]

Respecto del basal sin redondear, `(1.03/0.96−1)×100=7.2916667%`; el CSV sobre enteros reporta 7.29127597%. Todo el incremento de rendimiento proviene del multiplicador fijo.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:195-205`; `management_scenarios.csv`.

### 41. Ciclo corto

**Respuesta concreta.** Mantiene déficit50 y aplica cultivar 0.88:

\[
217.9594269×0.88×0.96×1.015×62.77=11731.3430\rightarrow11,731,
\]

una reducción exacta de 12% antes de redondear. El simulador cambia además ciclo base 100 días, GDD total 1400, LAImax 4.2; en el artefacto: 85 días a madurez, 513 mm de agua, 200 mm de riego, CWSImax 0.82 y 34 días críticos.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:188-191`; `management_scenarios.csv`.

### 42. Combinación

**Respuesta concreta.** Siembra −14 días no entra al yield; ciclo corto 0.88, riego75 1.03, N 1.00 y CO₂ 1.015:

\[
217.9594269×0.88×1.03×1×1.015×62.77
=12586.7534\rightarrow12,587.
\]

Orden en código: checkpoint → cultivar → riego → N → CO₂ → piso bu/ac → conversión → piso kg/ha. Artefacto diario: 512 mm, 240 mm de riego, CWSImax 0.95, 47 días críticos y madurez 85 días.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:176-223`; `management_scenarios.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

---

## Respuestas 43–58 — comparación, inferencia y sensibilidad

### 43. Comparabilidad de baselines

**Respuesta concreta.** Los cinco modelos auditados usan los mismos 28/8 años, siete inputs y target anual. Las tres filas SSP se reducen a una predicción media por año antes de las métricas. Linear, Ridge y Random Forest usan `StandardScaler` ajustado en train dentro de pipeline cuando corresponde; el checkpoint/MLP usan el z-score train y min-max del target de CeresPINN. Esta diferencia de preprocesamiento es propia del algoritmo, pero no cambia observaciones ni partición.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `scripts/generate_q1_revision_artifacts.py` (funciones de carga, `annualize`, baselines); `scripts/generate_q1_extended_audit.py`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`
- **Salida/artefacto:** `docs/q1_artifacts/extended/hindcast_all_models.csv` y `baseline_metrics_full_precision.csv`.

### 44. Resultados exactos de baselines

Todos usan ocho años independientes y seed 42 cuando aplica:

| Modelo | RMSE (bu/ac) | MAE (bu/ac) | R² | RMSE (kg/ha) | MAE (kg/ha) |
|---|---:|---:|---:|---:|---:|
| CeresPINN checkpoint | 11.345019076897634 | 9.625411033630368 | 0.8250854306330805 | 712.1268474568645 | 604.1870505809782 |
| LinearRegression | 10.230780769197365 | 8.877377849545486 | 0.8577562866970928 | 642.1861088825186 | 557.2330076159701 |
| Ridge α=1 | 10.273277442107316 | 8.759471060646309 | 0.8565721269869803 | 644.8536250410763 | 549.8319984767688 |
| RandomForest | 19.27743065087461 | 14.182586494708854 | 0.49497390016454024 | 1210.0443219553993 | 890.2409542728748 |
| MLP sin monotonicidad | 18.81461583892139 | 15.60134468078613 | 0.518932259790325 | 1180.9934362090958 | 979.2964056129455 |

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/baseline_metrics_full_precision.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.
- **Conclusión:** CeresPINN no supera a regresión lineal ni Ridge en este split.

### 45. Ablación MLP

**Respuesta concreta.** En el script de auditoría la ablación conserva arquitectura, datos, split, normalización, seed, optimizador, dropout, épocas, batches, regularización L2 e incluso la secuencia de forwards; únicamente establece `loss_physics_weight=0`. Eso hace justa la comparación ejecutada. No obstante, este script no está todavía versionado y la comparación no era un artefacto original del commit.

- **Estado:** experimento local VERIFICADO; reproducción pública **NO VERIFICADA**.
- **Archivo/ruta:** `scripts/generate_q1_revision_artifacts.py`, función de entrenamiento de ablation; `backend/training/pinn.py:78-120`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.
- **Salida:** MLP RMSE 1180.993436 kg/ha, MAE 979.296406 kg/ha, R² 0.518932260.

### 46. Variabilidad multi-seed

**Respuesta concreta.** Se ejecutaron 10 seeds (`0–8,42`) para la red con monotonicidad y la ablación. Resultados en kg/ha:

| Seed | Ceres RMSE | Ceres MAE | Ceres R² | MLP RMSE | MLP MAE | MLP R² |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 797.858789 | 704.051701 | 0.780435 | 1033.570676 | 964.470769 | 0.631539 |
| 1 | 728.231079 | 679.823375 | 0.817085 | 936.771350 | 789.238731 | 0.697324 |
| 2 | 746.076570 | 664.043477 | 0.808010 | 1342.477890 | 1036.941668 | 0.378379 |
| 3 | 831.076756 | 750.651777 | 0.761772 | 890.963199 | 819.696346 | 0.726202 |
| 4 | 786.170463 | 721.459826 | 0.786821 | 1051.514611 | 864.482922 | 0.618634 |
| 5 | 799.938680 | 715.289536 | 0.779289 | 1080.575865 | 903.626055 | 0.597263 |
| 6 | 739.471471 | 672.761140 | 0.811395 | 879.558332 | 792.129353 | 0.733166 |
| 7 | 794.616696 | 664.218597 | 0.782216 | 1047.318970 | 862.644365 | 0.621671 |
| 8 | 832.352278 | 756.470197 | 0.761040 | 1052.125623 | 893.968018 | 0.618191 |
| 42 | 712.126847 | 604.187051 | 0.825085 | 1180.993436 | 979.296406 | 0.518932 |

Resumen media ± SD e IC normal 95% de la media:

| Modelo | Métrica | Media | SD | IC 95% |
|---|---|---:|---:|---:|
| Ceres | RMSE kg/ha | 776.791963 | 42.550672 | [750.418783, 803.165143] |
| Ceres | MAE kg/ha | 693.295668 | 45.847657 | [664.878996, 721.712340] |
| Ceres | R² | 0.791314656 | 0.022710387 | [0.777238612, 0.805390700] |
| MLP | RMSE kg/ha | 1049.586995 | 137.874134 | [964.131722, 1135.042269] |
| MLP | MAE kg/ha | 890.649463 | 82.584870 | [839.462831, 941.836096] |
| MLP | R² | 0.614130100 | 0.104866679 | [0.549133059, 0.679127141] |

- **Estado:** VERIFICADO localmente.
- **Archivo/ruta:** `docs/q1_artifacts/extended/multiseed_neural_results.csv`; `multiseed_neural_summary.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.
- **Salvedad:** el IC normal describe variabilidad entre seeds, no incertidumbre poblacional del desempeño con solo ocho años.

### 47. Validación temporal

**Respuesta concreta.** No existe rolling-origin/walk-forward ejecutado. Es implementable sin cambiar el objetivo: ordenar los 36 años; usar ventanas expansivas (p. ej. entrenar 1990–2004 y probar 2005, luego 1990–2005→2006, etc.); mantener juntas las tres copias SSP de cada año; ajustar normalización exclusivamente en cada ventana; registrar métricas de todos los años futuros. Para evitar entrenamiento insuficiente, una primera ventana de 15 años y evaluación 2005–2025 es razonable. Esto es propuesta futura, no resultado.

- **Estado:** **NO VERIFICADO / NO EJECUTADO**.
- **Archivo/ruta:** no existe implementación; punto de extensión `backend/training/dataset.py:239-258`.
- **Comando:** `rg -n "rolling|walk.forward|TimeSeriesSplit" backend scripts`
- **Salida:** sin implementación.

### 48. Comparación estadística entre modelos

**Respuesta concreta.** Se remuestrearon con reemplazo los ocho años completos 20,000 veces y en cada muestra se calculó `métrica(Ceres)-métrica(competidor)`. IC percentil 95% en kg/ha:

| Comparación | ΔRMSE; IC95% | ΔMAE; IC95% |
|---|---:|---:|
| Ceres − Linear | 70.271915; [-173.444151, 324.828557] | 45.856095; [-209.994873, 303.666411] |
| Ceres − Ridge | 69.954947; [-200.381236, 338.627845] | 54.472473; [-210.384606, 317.818244] |
| Ceres − RF | -441.696620; [-1154.973464, 237.375968] | -289.048329; [-883.871179, 199.300455] |
| Ceres − MLP | -447.147571; [-908.519478, -31.768485] | -377.581460; [-784.220752, -9.304851] |

Solo la comparación con la MLP tiene ambos IC sin cero. No hay evidencia de diferencia frente a Linear/Ridge/RF al 95% bajo este procedimiento.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/model_difference_bootstrap.csv`; función `bootstrap_model_differences` en `scripts/generate_q1_extended_audit.py`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 49. Bootstrap actual

**Respuesta concreta.** Son 20,000 remuestreos de tamaño ocho, con reemplazo, sobre índices de años ya independizados; seed 42 (`np.random.default_rng(42)`). Los IC de métricas del checkpoint son: RMSE `[465.924649, 915.534863]`, MAE `[343.754286, 862.539139]` kg/ha y R² `[-0.107077, 0.935530]`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `scripts/generate_q1_revision_artifacts.py:71-90`, `bootstrap_metrics`; `docs/q1_artifacts/q1_statistics.json`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.

### 50. Prueba t pareada

**Respuesta concreta.** Se comparó rendimiento CeresPINN anual con rendimiento observado anual, en bu/ac:

| Año | Observado | CeresPINN |
|---:|---:|---:|
| 1991 | 118.00 | 119.10360 |
| 1992 | 144.80 | 129.62514 |
| 1998 | 145.40 | 146.33305 |
| 2001 | 143.30 | 162.29243 |
| 2003 | 157.10 | 167.11006 |
| 2004 | 181.40 | 174.41133 |
| 2011 | 172.80 | 183.23047 |
| 2024 | 212.65 | 199.27986 |

Con diferencias `predicho−observado`: `t(7)=0.1734102413`, `p=0.8672369778`, `d_z=0.0613097788`, sesgo medio `0.741993523 bu/ac` (46.574933 kg/ha).

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/hindcast_all_models.csv`; `scripts/generate_q1_revision_artifacts.py`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.

### 51. Kolmogorov–Smirnov

**Respuesta concreta.** Se aplicó `scipy.stats.ks_2samp` a los mismos ocho observados y ocho predichos: `D=0.25`, `p=0.9801087801`. La ejecución es correcta, pero con n=8 tiene potencia muy baja, ignora el emparejamiento temporal y un p alto no demuestra equivalencia. Debe presentarse solo como contraste exploratorio, no como validación de igualdad de distribuciones.

- **Estado:** ejecución VERIFICADA; interpretación fuerte rechazada.
- **Archivo/ruta:** `scripts/generate_q1_revision_artifacts.py`; `docs/q1_artifacts/q1_statistics.json`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.

### 52. Configuración Sobol

**Respuesta concreta.** No se usó SALib ni `saltelli.sample`. Se usó SciPy 1.14.1, `scipy.stats.qmc.Sobol(d=6, scramble=True, seed=42)`, dos matrices A/B de N=32,768 y matrices `AB_i` para tres factores; total `N×(2+3)=163,840` evaluaciones. Índices Jansen S1/ST; IC percentil con 500 bootstrap, seed 42. Bounds: temperatura `[2.2,3.4] °C`, precipitación fraccional `[-0.28,-0.15]`, CO₂ `[500,600] ppm`. Fijos: año 2050, riesgo térmico 0.78, CDD 20 y precipitación estacional `480(1+p)`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `scripts/generate_q1_extended_audit.py`, función `checkpoint_sobol`; `extended_audit.json`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 53. Sobol S1/ST

| Variable | S1 | IC95% S1 | ST | IC95% ST |
|---|---:|---:|---:|---:|
| temp_anomaly_c | 0.016092658042907715 | [0.005732618272304535, 0.026494345068931564] | 0.016399018466472626 | [0.016135855996981262, 0.016674526408314704] |
| precip_anomaly_pct | 0.004428863525390625 | [-0.006059002876281738, 0.015453456342220305] | 0.006783373188227415 | [0.006642539170570672, 0.006924925441853702] |
| co2_ppm | 0.9770789742469788 | [0.976696440577507, 0.9774341747164726] | 0.9792170524597168 | [0.9684207007288933, 0.9894797161221505] |

Los valores publicados `0.0175/0.0050/0.9772` y `0.0163/0.0068/0.9810` son cercanos, pero **no se reprodujeron exactamente**. El script que generó los valores antiguos no está presente; deben sustituirse por el CSV actual o marcarse NO VERIFICADOS.

- **Estado:** nuevos valores VERIFICADOS; valores publicados exactos **NO VERIFICADOS**.
- **Archivo/ruta:** `docs/q1_artifacts/extended/sobol_checkpoint.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 54. Confusión temporal/estructural de CO₂

**Respuesta concreta.** Correlaciones principales en la matriz train: `corr(CO₂,heatwave_risk)=0.9990399998`; `corr(CO₂,scenario_forcing)=0.9508014493`; `corr(heatwave_risk,scenario)=0.9363171407`; `corr(year,temp)=0.5869202233`. `corr(year,CO₂)≈0` dentro de 1990–2025 porque el template asigna CO₂ por escenario y el drift temporal solo se activa después de 2026. `seasonal_cdd` es constante y sus correlaciones son NaN. La dominancia Sobol de CO₂ no identifica un efecto causal: CO₂ codifica casi el mismo orden de escenario que riesgo térmico.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/training_feature_correlations.csv`; `backend/training/dataset.py:142-181`.
- **Comando:** `Get-Content docs/q1_artifacts/extended/training_feature_correlations.csv`.

### 55. Ablación de CO₂

**Respuesta concreta.** Se entrenó una variante seed 42 con seis features, mismo split/procedimiento: RMSE `793.7280620949219 kg/ha`, MAE `709.8260986919402 kg/ha`, R² `0.7827024964826969`. El checkpoint completo dio RMSE 712.126847, MAE 604.187051, R² 0.825085. Es una sola seed; no se recalcularon índices Sobol del modelo sin CO₂ y no debe considerarse evidencia definitiva.

- **Estado:** métricas VERIFICADAS; cambio de sensibilidad **NO VERIFICADO**.
- **Archivo/ruta:** `docs/q1_artifacts/extended/extended_audit.json`, `co2_ablation_seed42`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 56. Robustez con ruido 5%

**Respuesta concreta.** Se perturban todas las features no constantes en escala original: `X_test + N(0,0.05)×SD_train`; luego se normaliza dentro de `checkpoint_predict`. `seasonal_cdd` no recibe ruido porque su SD se fuerza a cero. Son 1,000 repeticiones, seed 42. RMSE base `11.345019077 bu/ac`; RMSE promedio perturbado `11.486964937 bu/ac`; incremento `0.506267599%` (≈0.51%); cambio absoluto medio de predicción `0.988059342 bu/ac`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `scripts/generate_q1_revision_artifacts.py:339-361`; `docs/q1_artifacts/robustness_results.csv`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.

### 57. Dependencia del año

**Respuesta concreta.** Todas las filas test reemplazan `year` por la media train `2008.785714`; las demás variables quedan intactas. Después se normaliza normalmente. RMSE pasa de `11.345019077` a `32.939445228 bu/ac`, incremento `188.206738227%`; cambio absoluto medio de predicción `25.862731934 bu/ac`. Es una prueba de dependencia/ablación, no demuestra “sesgo” causal.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `scripts/generate_q1_revision_artifacts.py:363-378`; `docs/q1_artifacts/robustness_results.csv`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.

### 58. Tiempo de inferencia

**Respuesta concreta.** CPU, batch 1, 100 warmups, 2,000 ejecuciones, `time.perf_counter_ns`, `torch.no_grad()` dentro del predictor; mediana y percentil 95 con NumPy. No se usa `torch.inference_mode()` ni sincronización CUDA, porque es CPU. Corrida actual: mediana `1.9984 ms`, p95 `5.658015 ms`, media `2.572228 ms`. Los antiguos `2.20/4.66 ms` no son exactamente reproducibles en la corrida actual.

- **Estado:** metodología VERIFICADA; cifra publicada exacta VERIFICADA CON SALVEDADES.
- **Archivo/ruta:** `scripts/generate_q1_revision_artifacts.py:121-139`; `docs/q1_artifacts/q1_statistics.json`.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.

---

## Respuestas 59–81 — artefactos, validez y producto

### 59. Datos de la figura observado–predicho

**Respuesta concreta.** El CSV contiene los ocho años, observado y predicciones de CeresPINN, Linear, Ridge, RF y MLP, tanto en bu/ac como kg/ha.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/hindcast_all_models.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py; Get-Content docs/q1_artifacts/extended/hindcast_all_models.csv`.
- **Salida:** ocho filas 1991, 1992, 1998, 2001, 2003, 2004, 2011 y 2024.

### 60. CSV de baselines

**Respuesta concreta.** Existe y se genera automáticamente con columnas `model,n_independent_years,seed,rmse_bu_acre,mae_bu_acre,r2,rmse_kg_ha,mae_kg_ha`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/baseline_metrics_full_precision.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 61. CSV de manejo

**Respuesta concreta.** Existe con los cinco escenarios y las columnas solicitadas, más madurez, retorno y salida raw. Valores principales: basal 13,331; adelantada 13,331; corto 11,731; riego75 14,303; combinado 12,587 kg/ha.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/management_scenarios.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 62. CSV Sobol

**Respuesta concreta.** Existe con `variable,S1,S1_ci95_low,S1_ci95_high,S1_conf_half_width,ST,ST_ci95_low,ST_ci95_high,ST_conf_half_width,base_N,total_model_evaluations,bootstrap_repetitions,seed`.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/sobol_checkpoint.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 63. Linaje de datos

**Respuesta concreta.** El esquema implementado es `22,160 NASS → limpieza → 36 medianas anuales → replicación ×3 SSP =108 → split agrupado 84/24 → 28/8 años independientes`.

- **Estado:** conteos de metadata/dataset local VERIFICADOS; raw original ya no disponible.
- **Archivo/ruta:** `docs/q1_artifacts/extended/data_lineage_counts.csv`; `backend/training/dataset.py:212-258`.
- **Comando:** `Get-Content docs/q1_artifacts/extended/data_lineage_counts.csv`.

### 64. README y contenido de artefactos Q1

**Respuesta concreta.** `hindcast_independent_years.csv` contiene observado/predicho del checkpoint por ocho años; `same_split_baseline_comparison.csv`, métricas del checkpoint y cuatro baselines; `robustness_results.csv`, ruido 5% e imputación por variable; `q1_statistics.json`, procedencia, split, métricas, t/KS/bootstrap, latencia, tiempo de entrenamiento, baselines y robustez. Los genera `scripts/generate_q1_revision_artifacts.py`. Se pueden regenerar en el workspace, pero no desde clon limpio porque script y dataset requerido no están en el commit.

- **Estado:** contenido/regeneración local VERIFICADOS; desde cero **NO VERIFICADO**.
- **Archivo/ruta:** `docs/q1_artifacts/README.md`; los cuatro artefactos.
- **Comando:** `python scripts/generate_q1_revision_artifacts.py`.

### 65. Sesgo geográfico USDA-NASS

**Respuesta concreta.** **NO VERIFICADO.** El raw con `state_name/county_name` fue sobrescrito por dry-run y el CSV expandido de entrenamiento ya no conserva geografía. No es posible entregar frecuencias por estado/condado sin repetir la descarga real con una clave NASS.

- **Estado:** NO VERIFICADO.
- **Archivo/ruta:** `backend/data/raw/nass/maize_county_yield_usda.csv` (solo encabezado); manifest con cero registros.
- **Comando necesario:** `$env:NASS_API_KEY='...'; $env:CERESPINN_DRY_RUN='0'; python -m backend.data.nass`, seguido de `groupby` por estado/condado.
- **Artefacto:** no existe aún.

### 66. Sesgo temporal

**Respuesta concreta.** Se generó `year,n_records,median_yield` para 1990–2025. El conteo reconstruido va de 99 (1990–1992) a 1,078 (2022). Ejemplos: 1993=198; 1999=396; 2008=693; 2017=960; 2020=1,056; 2025=960. Se obtuvo dividiendo entre tres el conteo del dataset expandido, porque cada observación original está replicada en tres SSP.

- **Estado:** VERIFICADO desde el dataset local expandido; no desde raw preservado.
- **Archivo/ruta:** `docs/q1_artifacts/extended/temporal_coverage.csv`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 67. Representatividad

**Respuesta concreta.** Hay fuerte desbalance temporal: 2022 aporta 1,078 registros frente a 99 en 1990–1992, razón 10.89:1. No se puede cuantificar sobrerrepresentación por estado/región porque se perdió la geografía raw. Por tanto, no es válido hacer afirmaciones de equidad/representatividad geográfica.

- **Estado:** sesgo temporal VERIFICADO; sesgo geográfico NO VERIFICADO.
- **Archivo/ruta:** `temporal_coverage.csv`; raw NASS vacío.
- **Comando:** `Import-Csv docs/q1_artifacts/extended/temporal_coverage.csv | Measure-Object original_nass_records_reconstructed -Minimum -Maximum`.

### 68. Parámetros de suelo de los cuatro campos

| Campo | FC | WP | SAT | Ks mm/d | Origen |
|---|---:|---:|---:|---:|---|
| El Bajío | 0.38 | 0.22 | 0.52 | 35 | constante demostrativa |
| Iowa | 0.32 | 0.16 | 0.48 | 85 | constante demostrativa |
| Pampas | 0.28 | 0.13 | 0.46 | 120 | constante demostrativa |
| Ebro | 0.22 | 0.09 | 0.41 | 240 | constante demostrativa |

No existe fuente/DOI/SoilGrids asociada. Aunque el comentario dice “no hardcoded”, sí están hard-coded.

- **Estado:** valores VERIFICADOS; procedencia real NO VERIFICADA.
- **Archivo/ruta:** `backend/inference.py:224-232`; `field_soil_constants.csv`; duplicados en `backend/app.py:446-458`.
- **Comando:** `Get-Content docs/q1_artifacts/extended/field_soil_constants.csv`.

### 69. Retorno económico

**Respuesta concreta.** Backend productivo: `round(yield_kg_ha×0.22 − irrigation_mm×1.5)`. No incluye costo de fertilizante ni costos fijos y no documenta moneda/año/fuente. Son constantes demostrativas. El simulador TypeScript legacy usa otra fórmula: USD 0.21/kg, USD 0.45/mm/ha y USD 650/ha fijos; es inconsistente con backend.

- **Estado:** VERIFICADO como heurística; calibración económica NO VERIFICADA.
- **Archivo/ruta:** `backend/inference.py:441`; `src/services/pinnEngine.ts:427-431`.
- **Comando:** `rg -n "econ_return|cornPrice|irrigationCost|fixedCosts" backend/inference.py src/services/pinnEngine.ts`.

### 70. Índice de resiliencia

**Respuesta concreta.** `avg_stress=round(mean(CWSI),2)` y `score=int(clip(100−80×avg_stress,20,95))`. Rango efectivo 20–95; mayor score significa menor CWSI promedio. Es heurístico, sin calibración ni umbrales publicados.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:438-440`.
- **Comando:** `rg -n "avg_stress|drought_resilience" backend/inference.py`.

### 71. Biomasa y rendimiento potencial

**Respuesta concreta.** Biomasa es una acumulación heurística iniciada en 45 kg/ha y aumentada con la regla de LAI/CWSI/estrés térmico/N descrita en Q32. El “rendimiento potencial” es una constante del cultivar (10,500/13,500/16,000 kg/ha) multiplicada por 1.05 si N≥200. Ninguno está calibrado contra observaciones de biomasa/potencial.

- **Estado:** VERIFICADO como regla; validez física NO VERIFICADA.
- **Archivo/ruta:** `backend/inference.py:188-191,222,399-401`.

### 72. CWSI

**Respuesta concreta.** Backend:

\[
CWSI=clip\left(1-\frac{\theta_{avg}-WP}{\max(0.01,FC-WP)},0.05,0.98\right),
\quad \theta_{avg}=0.3\theta_1+0.3\theta_2+0.4\theta_3.
\]

Es un proxy de agotamiento relativo, no la formulación clásica basada en temperatura de dosel y límites húmedo/seco. No se cita fuente en código. El frontend legacy usa otra forma `1−Ks` con umbral p=0.55.

- **Estado:** VERIFICADO; correspondencia a CWSI publicado NO VERIFICADA.
- **Archivo/ruta:** `backend/inference.py:388-395`; `src/services/pinnEngine.ts:313-321`.

### 73. Priestley–Taylor

**Respuesta concreta.** Se implementa `λ=2.501−0.002361T`, pendiente de presión de vapor `Δ`, `γ=0.0665`, `Rn=0.65×radiación solar`, `α=1.26` y `ETo=max(0.8, α Δ/(Δ+γ) Rn/λ)`. Radiación en MJ m⁻² d⁻¹ y resultado interpretado mm/día. Simplifica flujo de calor del suelo a cero implícitamente, radiación neta al 65% y no corrige altitud/humedad/viento.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/inference.py:322-329`.
- **Comando:** `Get-Content backend/inference.py | Select-Object -Skip 320 -First 12`.

### 74. Fenología/GDD

**Respuesta concreta.** Temperatura media se limita a 10–30°C; base=10°C; GDD diario=`max(0,Tmean−10)`. Umbrales: VE<120; V3<320; V6<750; V12<1100; VT<1280; R1<1450; R3 hasta 0.88×GDD total; luego R6. GDD total: corto 1400, medio 1700, largo 2000. No hay bibliografía/justificación asociada y la lógica puede hacer que el umbral 1450 prevalezca sobre `0.88×total` en ciclo corto.

- **Estado:** constantes VERIFICADAS; fuente bibliográfica NO VERIFICADA.
- **Archivo/ruta:** `backend/inference.py:188-191,284-307`.

### 75. Balance diario de masa

**Respuesta concreta.** Contabilidad evaluada sobre registros redondeados:

\[
r_t=P_t+I_t-T_t-E_t-D_{3,t}-(S_t-S_{t-1}),
\quad S=300\theta_1+300\theta_2+400\theta_3.
\]

En 113 días basales: suma de residuos `−36.326 mm`, media absoluta diaria `0.460407 mm`, máximo absoluto `1.81 mm`. No es cierre exacto; parte proviene de redondeo y los clamps de almacenamiento pueden crear pérdidas/ganancias no reportadas. El cierre a precisión interna no se instrumentó. No confundir este chequeo con una pérdida física del entrenamiento.

- **Estado:** balance exportado VERIFICADO; cierre interno exacto NO VERIFICADO.
- **Archivo/ruta:** `scripts/generate_q1_extended_audit.py:318-342`; `extended_audit.json`.
- **Comando:** `python scripts/generate_q1_extended_audit.py`.

### 76. Validación externa

**Respuesta concreta.** No existe dataset externo independiente evaluado sin reentrenamiento. El holdout de años usa la misma construcción/agregación NASS; comparaciones bibliográficas no son validación externa; los artefactos de `projects/` son ejecuciones internas.

- **Estado:** VERIFICADO: no existe.
- **Archivo/ruta:** `backend/models/cerespinn_metadata.json`; `backend/training/dataset.py`; búsqueda global.
- **Comando:** `rg -n -i "external validation|validación externa" . --glob '!node_modules/**'`.

### 77. Código heredado contradictorio

**Respuesta concreta.** Archivos que aún presentan Richards/PDE/optimización/vulnerabilidad con alcance superior a la implementación:

- `README.md:5-8`: adherencia estricta a PDE y “spatial awareness” fuerte;
- `API_DOCUMENTATION.md:6,19,147-155`: Richards y épocas legacy; también reconoce optimización pendiente;
- `backend/training/pinn.py:1-21`: docstring llama PINN/conservación y describe erróneamente Jacobiano de physics head;
- `backend/training/README.md:20-26`: prior Richards/conservación;
- `backend/inference.py:363,502-513`: comentario Richards y métricas PDE constantes;
- `backend/app.py:151,470-474`: “Bio-physical Coupled”, “balance hídrico”, `richardsWeightLambda`;
- `backend/db.py:606-650` y `backend/seed.py`: modelos históricos demostrativos;
- `src/services/pinnEngine.ts:13-18,96-160,510-517`: afirma/“resuelve” Richards y genera métricas aleatorias;
- `src/components/MLOpsDashboard.tsx:81-170`: curva PDE y ecuación Richards falsas;
- `src/components/ReportsModule.tsx:71,231`: título Richards y PDE loss;
- `src/services/api.ts:180-187`: fallbacks PDE;
- `src/types/index.ts:152-160,184-187`: contrato legacy;
- `src/i18n/locales/{es,en,pt}.json`: textos “Richards PDE residual”;
- `src/components/VulnerabilityMap.tsx`: llama vulnerabilidad a comparaciones de cuatro campos no calibrados.

`ml_lab/` y `projects/` contienen experimentos genéricos/legados; no deben presentarse como evidencia del checkpoint productivo.

- **Estado:** VERIFICADO.
- **Comando:** `rg -n -i -e Richards -e PDE -e optimization -e "external validation" -e vulnerability backend src README.md API_DOCUMENTATION.md`.

### 78. API y frontend: procedencia de métricas

| Endpoint/componente | Procedencia real |
|---|---|
| `/api/model/status` | metadata guardada del checkpoint; R²/RMSE reales del holdout, etiquetas “bio-physical/NEX 5 GCM” exageradas |
| `/api/simulate` | rendimiento raw real del checkpoint + multiplicadores/serie diaria heurísticos + métricas PDE constantes |
| `/api/validation/hindcast` | usa checkpoint cuando está disponible; fallback explícito posible |
| `/api/validation` | hindcast puede ser checkpoint; t/Sobol/bootstrap del módulo son sobre surrogate determinista, no necesariamente checkpoint |
| `/api/model-registry` | modelo activo desde metadata; históricos desde DB seed/demo |
| `/api/reports` | DB si hay datos; en ausencia devuelve reporte/valores mock |
| `MainDashboard`, `WhatIfStudio`, `VulnerabilityMap` | llaman `/api/simulate`; resultados mixtos checkpoint+heurísticas |
| `MLOpsDashboard` | métricas activas de metadata; curva de training hard-coded |
| `ValidationReport` | consume `/api/validation`, por ello mezcla real/surrogate |
| `ReportsModule` | exporta simulación mixta y falso PDE loss |

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/app.py:125-510`; `backend/inference.py`; `backend/validation.py`; `src/services/api.ts:194-618` y componentes citados.
- **Comando:** `rg -n "@app\.|fetchValidation|simulateScenario|fetchModelRegistry|fetchReports" backend/app.py src`.

### 79. Reporte PDF

**Respuesta concreta.** Sí, `ReportsModule` usa jsPDF. Todavía escribe “Modelado PINN Richards + Clima CMIP6” y exporta `PINN PDE Richards Loss`; también incluye retorno/resiliencia heurísticos. Es incorrecto presentarlo como residuo calculado. Debe eliminarse o renombrarse antes de publicación.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `src/components/ReportsModule.tsx:15,57,71,230-231`.
- **Comando:** `rg -n "jsPDF|Richards|PDE|Resilien|Econ" src/components/ReportsModule.tsx`.

### 80. Pruebas automatizadas

**Respuesta concreta.** Se recolectaron y aprobaron 43 tests Python y 4 tests TypeScript: total 47, cero fallos. Python cubre contratos API, checkpoint/inferencia, normalización de feature constante, dataset/split determinista, forward de dos cabezas, loss finita, validación/surrogates, chatbot y pipelines. TypeScript cubre botones PINN, herramientas de escenarios y ausencia de clave Gemini en browser. No existe test de reentrenamiento 300 épocas, determinismo multiplataforma, cierre exacto de agua, rolling-origin, reproducción desde clon limpio ni figuras.

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `backend/tests/test_{api,inference,training,validation}.py`; `tests/pinn-wiring.test.ts`.
- **Comandos/salida:** `python -m pytest backend/tests -q` → `43 passed, 3 warnings, 20.31s`; `tsx --test tests/pinn-wiring.test.ts` → `4 passed, 0 failed`; `tsc --noEmit` → exit 0.

### 81. CI

**Respuesta concreta.** No existe `.github/workflows` ni otro pipeline CI rastreado. Por ello los tests no se ejecutan automáticamente y no hay estado verde del commit del artículo.

- **Estado:** VERIFICADO para ausencia; “CI verde” NO VERIFICADO/no aplicable.
- **Archivo/ruta:** `.github` ausente.
- **Comando:** `Test-Path .github/workflows`.
- **Salida:** `False`.

---

## Respuesta 91 — referencias técnicas

### 91. Referencias que pueden mantenerse o eliminarse

- **Alimagham et al. (2025), DOI 10.1016/j.agsy.2025.104367.** Mantener solo para sustentar que la combinación de modelos de cultivo y ML puede proyectar impactos climáticos en entornos con pocos datos o como benchmark de hibridación. No sustenta que CeresPINN ya integre WOFOST/procesos ni valide clima.
- **Chavoshi et al. (2025), DOI 10.1029/2024JH000547.** Mantener como contraste metodológico de una PINN de humedad de suelo que sí incorpora física de zona vadosa. Es útil para explicar por qué CeresPINN actual no debe llamarse PINN de Richards. No usarla como evidencia del desempeño propio.
- **Cheng et al. (2022), DOI 10.1016/j.agrformet.2022.109057.** Mantener solo en estado del arte sobre ML e indicadores múltiples para predicción temprana de maíz a escala condal. Sus R² no son directamente comparables al holdout anual agregado de CeresPINN.
- **Han et al. (2024), DOI 10.1016/j.agrformet.2024.110123.** Mantener solo para contexto de ML en predicción/selección varietal. No demuestra que CeresPINN tenga validación varietal o espacial.

Si se elimina del manuscrito la discusión específica de modelos híbridos/PINN hidrológica/ML condal, eliminar estas citas en lugar de insertarlas por obligación.

- **Estado:** VERIFICADO contra el uso actual en `docs/informe_completo_cerespinn.md:43-49,201,254` y referencias `304,308,310,326`.
- **Comando:** `rg -n "Alimagham|Chavoshi|Cheng|Han" docs/informe_completo_cerespinn.md`.

---

## 92. Tabla final para auditoría

La columna “línea” es aproximada y corresponde al commit/árbol auditado. Cuando una respuesta combina una parte comprobada y otra imposible de reconstruir, el estado lo declara explícitamente.

| Pregunta | Respuesta | Estado | Archivo | Función o línea | Comando de reproducción | Artefacto resultante |
|---:|---|---|---|---|---|---|
| 1 | Repo público; hash `6c22e543...`; sin tag/release exacta para artefactos locales | Verificado / release no verificada | `.git/config` | Git | `git remote -v; git rev-parse HEAD; git ls-remote ... main` | hash remoto/local |
| 2 | No existe LICENSE/COPYING | Verificado | raíz | n/a | `git ls-files \| rg 'LICENSE\|COPYING'` | salida vacía |
| 3 | README instala/arranca; no reproduce paper completo | Verificado con salvedades | `README.md`; `backend/training/README.md` | varias | `rg -n 'train\|baseline\|figure' ...` | inventario documental |
| 4 | No hay receta funcional comprobada desde clon limpio | No verificado | extractores/training/scripts Q1 | varias | secuencia clon→extract→train→Q1 | falla por dataset/scripts no versionados |
| 5 | No existe pipeline único integral | Verificado | `backend/data/run_all.py`; `Dockerfile`; scripts | varias | `rg --files \| rg 'Makefile\|workflow\|ipynb\|Dockerfile'` | inventario |
| 6 | Dockerfile existe; build no pudo validarse sin daemon; no reproduce experimento | No verificado funcionalmente | `Dockerfile` | completo | `docker build --pull -t cerespinn-audit:6c22e54 .` | error `docker_engine` |
| 7 | Python 3.12.14; torch 2.6 CPU; numpy 2.1.3; pandas 2.2.3; sklearn 1.9.1; scipy 1.14.1; SALib ausente | Verificado | requirements; `runtime.txt` | varias | imports `__version__` | listado de versiones |
| 8 | Win11, i5-12450H, 15.71 GiB, 12 lógicos, torch 8 hilos, CPU | Verificado con salvedad de timings | `q1_statistics.json` | benchmark | `python scripts/generate_q1_revision_artifacts.py` | 31.356 s; 1.998/5.658 ms |
| 9 | Seed 42 en NumPy/PyTorch/split/RF; no Python random | Verificado | `config.py`; `train.py`; scripts | 46–47 | `rg -n 'seed\|manual_seed\|random_state'` | coincidencias |
| 10 | No garantizado entre plataformas; repetición local diferencia 0 | Verificado local / global no | `extended_audit.json` | determinism | script extendido | max diff 0; deterministic false |
| 11 | 300 épocas, guarda final, sin early stopping | Verificado | `config.py`; `train.py` | 52;81–112 | `rg -n 'epochs\|range' backend/training` | 300 |
| 12 | Adam LR 0.001 constante, sin scheduler | Verificado | `config.py`; `train.py` | 51;62–66 | `rg -n 'learning_rate\|scheduler'` | 0.001 |
| 13 | Batch 64; dos minibatches, no full-batch | Verificado | `config.py`; `train.py` | 53;70–77 | `python -c "import math; print(math.ceil(84/64))"` | 2 |
| 14 | Adam decay 1e-5 + L2 manual 1e-4 | Verificado | `config.py`; `train.py` | 54,59;90–96 | `rg -n 'weight_decay\|regul'` | ambos términos |
| 15 | Monotonicidad en derivadas de yield vs temp/precip normalizadas | Verificado | `pinn.py` | `physics_loss`, 78–120 | inspección de función | ecuación auditada |
| 16 | `L_range` existe pero vale 0 por sigmoid; head=0.5 | Verificado | `pinn.py`; `extended_audit.json` | 64–69;117–118 | script extendido | penalty 0 |
| 17 | 7→4×128 Tanh+dropout; dos heads; 63,042 parámetros | Verificado | `config.py`; `pinn.py` | clase `CeresPINN` | conteo `numel()` | `hyperparameters.csv` |
| 18 | Segunda head sin target; solo rango redundante/L2; no estado físico validado | Verificado | `pinn.py`; `train.py` | 64–75;84–96 | script extendido | head min=max=0.5 |
| 19 | z-score X y min-max y con train; estadísticos entregados | Verificado | `train.py`; metadata | 49–58 | leer `normalization_stats.csv` | CSV de normalización |
| 20 | 28 años train y 8 test listados; agrupado por año | Verificado | `dataset.py`; metadata | 239–258 | leer split JSON | listas exactas |
| 21 | 36×3 SSP=108; 84/24 | Verificado | `dataset.py` | 212–234 | `python -c "print(36*3,28*3,8*3)"` | 108,84,24 |
| 22 | Tres SSP comparten target; unidad independiente=año | Verificado | `dataset.py` | 232–234 | script Q1 | n=8 |
| 23 | Consulta NASS exacta conocida; raw de 22,160 ya no está | No verificado para raw exacto | `nass.py`; config; manifest | `_build_params`, `_rows_to_frame` | extractor real con NASS key | raw actual 0 |
| 24 | Mediana por año; 36 filas reconstruidas | Verificado con salvedad | `dataset.py`; `temporal_coverage.csv` | 212–218 | script extendido | CSV 36 años |
| 25 | Config NEX conocida; identidad exacta de 98 filas perdida | No verificado | `nex_gddp.py`; manifest | extractor | leer manifest | raw actual 0 |
| 26 | Interpolación lineal+templates implementada; tabla de procedencia no existe | No verificado para combinaciones | `dataset.py` | `_nex_year_lookup`, `_blend_climate` | `rg -n 'interpolate'` | regla, no tabla |
| 27 | +2.7°C/−24% son constantes SSP5, no NEX 2050 probado | Verificado | `dataset.py` | `SCENARIO_TEMPLATE` | `rg -n '2.7\|-0.24'` | constantes |
| 28 | CO₂=445/480/520 por SSP +1.5 ppm/año post-2026; no serie externa | Verificado | `dataset.py`; `inference.py` | `_blend_climate`; features | `rg -n 'co2_ppm'` | regla |
| 29 | CDD constante 20; SD=1e-8; única varianza cero | Verificado | metadata; stats CSV | normalization | leer CSV | valor 20 |
| 30 | heatwave risk=0.15/0.42/0.78 por template | Verificado | `dataset.py` | `SCENARIO_TEMPLATE` | `rg -n 'heatwave_risk'` | constantes |
| 31 | Nombre correcto `seasonal_precip_mm`; no existe `precio` | Verificado | repo global | n/a | `rg -n 'seasonal_precip_mm\|seasonal_precio_mm'` | solo nombre correcto |
| 32 | Simulador diario es clima sintético+GDD+PT+bucket+CWSI+biomasa heurística | Verificado | `inference.py` | `run_full_simulation`, 166–437 | inspección | ecuaciones documentadas |
| 33 | No hay solver Richards ni residual PDE de training | Verificado | `pinn.py`; `inference.py` | physics loss; bucket | búsqueda/inspección | ausencia demostrada |
| 34 | Métricas PDE legacy siguen como constantes/fallback/random | Verificado | backend+TS+PDF | líneas citadas | `rg -n 'pde_residual\|boundary_condition'` | inventario |
| 35 | Curva MLOps 1k–15k hard-coded; slider decorativo; PDF exporta PDE falso | Verificado | `MLOpsDashboard.tsx`; `db.py` | 81–86 | búsqueda | seis puntos demo |
| 36 | Siembra cambia calendario/estrés, no fórmula yield | Verificado | `inference.py`; management CSV | features/yield/calendar | script extendido | mismo 13,331 |
| 37 | Suelo no entra en red/yield; solo serie diaria | Verificado | `inference.py` | 106–147;206–236 | búsqueda | igualdad de yield |
| 38 | Multiplicadores cultivar/riego/N/CO₂ enumerados | Verificado | `inference.py` | 188–223 | inspección | fórmula exacta |
| 39 | Iowa basal =217.9594×0.96×1.015×62.77=13,331 | Verificado | inference; management CSV | 206–223 | script extendido | 13,331 |
| 40 | Riego75 cambia factor 0.96→1.03; 14,303; +7.29% | Verificado | idem | irrig multipliers | script extendido | 14,303 |
| 41 | Corto factor 0.88; 11,731; 513 mm; 34 críticos | Verificado | idem | variety configs | script extendido | fila short_cycle |
| 42 | Combinado 0.88×1.03×1.015; 12,587 | Verificado | idem | yield sequence | script extendido | fila combined |
| 43 | Baselines usan mismo split/features/targets; preprocesamiento propio | Verificado | scripts Q1 | baseline functions | script extendido | hindcast/model metrics |
| 44 | Tabla completa: Ceres 712.13/604.19/0.8251; Linear/Ridge mejores | Verificado | `baseline_metrics_full_precision.csv` | n/a | script extendido | CSV |
| 45 | Ablación local cambia solo λmono=0 y preserva secuencia | Verificado local | script Q1 | training ablation | script revisión | MLP metrics |
| 46 | 10 seeds ejecutadas; medias/SD/IC entregados | Verificado | multiseed CSVs | loop seeds | script extendido | dos CSV |
| 47 | Rolling-origin no existe; diseño propuesto, no ejecutado | No verificado/no ejecutado | `dataset.py` | punto de extensión | `rg -n 'rolling\|TimeSeriesSplit'` | sin salida |
| 48 | Bootstrap de diferencias 20k; solo Ceres vs MLP excluye cero | Verificado | difference CSV | bootstrap function | script extendido | IC por modelo |
| 49 | Remuestrea 8 años con reemplazo, 20k, seed42 | Verificado | script revisión | `bootstrap_metrics` | script | IC métricas |
| 50 | Vectores de 8 pares entregados; t=.1734,p=.8672,dz=.0613 | Verificado | hindcast CSV; JSON | t-test | script revisión | pares/estadísticos |
| 51 | KS D=.25,p=.9801 ejecutado; baja potencia/no equivalencia | Verificado con juicio metodológico | script/JSON | KS | script revisión | D,p |
| 52 | SciPy Sobol+Jansen, N=32768, 163840 eval, bounds/seed42 | Verificado | script extendido | `checkpoint_sobol` | script | configuración JSON |
| 53 | S1/ST nuevos entregados; valores antiguos no exactos | Verificado nuevos / antiguos no | Sobol CSV | n/a | script extendido | CSV |
| 54 | CO₂ correlaciona .999 con heat risk y .951 con SSP | Verificado | correlations CSV | corr | script extendido | matriz |
| 55 | Ablación CO₂ seed42 R²=.7827; sensibilidad no recalculada | Parcial/no verificado para sensibilidad | extended audit JSON | co2 ablation | script extendido | métricas |
| 56 | Ruido original-scale 5% SD, 1k reps; RMSE +0.5063% | Verificado | script revisión; robustness CSV | robustness | script | CSV |
| 57 | year→media train; RMSE 11.345→32.939; +188.207% | Verificado | idem | imputation | script | CSV |
| 58 | 100 warmups, 2k, batch1, no_grad, CPU; 1.998/5.658 ms | Verificado actual / publicado con salvedad | script/JSON | benchmark_latency | script | JSON |
| 59 | CSV anual observado y cinco modelos | Verificado | `hindcast_all_models.csv` | n/a | script extendido | CSV |
| 60 | CSV final de métricas generado automáticamente | Verificado | `baseline_metrics_full_precision.csv` | n/a | script extendido | CSV |
| 61 | CSV manejo de cinco escenarios | Verificado | `management_scenarios.csv` | n/a | script extendido | CSV |
| 62 | CSV Sobol S1/ST/IC | Verificado | `sobol_checkpoint.csv` | n/a | script extendido | CSV |
| 63 | 22,160→36→108→84/24→28/8 | Verificado con salvedad raw | `data_lineage_counts.csv` | dataset build | leer CSV | CSV |
| 64 | README describe cuatro artefactos; clon limpio no los regenera | Verificado local / desde cero no | `docs/q1_artifacts/README.md` | n/a | scripts Q1 | artefactos Q1 |
| 65 | Frecuencias estado/condado imposibles: raw geográfico perdido | No verificado | raw NASS/manifest | n/a | repetir extractor real | pendiente |
| 66 | Conteos anuales reconstruidos; 99–1078 | Verificado con salvedad | `temporal_coverage.csv` | n/a | script extendido | CSV |
| 67 | Desbalance temporal 10.89:1; geográfico desconocido | Parcial/no verificado geográfico | temporal CSV/raw | n/a | Measure-Object | min/max |
| 68 | Cuatro suelos son constantes demo sin fuente | Verificado para valores / origen no | `inference.py`; soil CSV | 224–232 | leer CSV | tabla suelos |
| 69 | Backend USD/ha=`.22y−1.5I`; legacy usa otra fórmula | Verificado como heurística | inference; pinnEngine TS | 441;427–431 | búsqueda | fórmulas |
| 70 | Resiliencia=`clip(100−80 meanCWSI,20,95)` | Verificado | `inference.py` | 438–440 | búsqueda | fórmula |
| 71 | Biomasa y potencial son reglas no calibradas | Verificado como heurística | `inference.py` | 188–191;399–401 | inspección | regla |
| 72 | CWSI proxy de humedad, rango .05–.98, no canopy CWSI | Verificado / publicación no | `inference.py` | 388–395 | inspección | fórmula |
| 73 | PT α=1.26 con simplificaciones documentadas | Verificado | `inference.py` | 322–329 | inspección | fórmula |
| 74 | Base10/cap30 y umbrales entregados; sin fuente | Verificado constantes / fuente no | `inference.py` | 284–307 | inspección | umbrales |
| 75 | Balance redondeado residual −36.326 mm; interno no instrumentado | Verificado exportado / interno no | script; JSON | water audit | script extendido | JSON |
| 76 | No hay dataset externo independiente | Verificado: inexistente | metadata/dataset | n/a | búsqueda global | ausencia |
| 77 | Contradicciones Richards/PDE/UI/PDF inventariadas | Verificado | archivos listados en Q77 | varias | `rg -n -i ...` | inventario |
| 78 | Tabla API/frontend clasifica real, artefacto y placeholder | Verificado | app/inference/validation/api TS | endpoints | búsqueda | matriz |
| 79 | PDF existe y contiene Richards/PDE incorrectos | Verificado | `ReportsModule.tsx` | 15,57,71,231 | búsqueda | hallazgo |
| 80 | 43 pytest +4 TS pasan; faltan pruebas científicas end-to-end | Verificado | test dirs | tests | pytest/tsx/tsc | 47 passed |
| 81 | No hay CI/workflows; no existe estado verde | Verificado ausencia | `.github` ausente | n/a | `Test-Path .github/workflows` | False |
| 82 | Checkpoint rastreado; SHA `600F...7E4`; raw HEAD no probado aquí | Verificado con salvedad HTTP | model files | n/a | `git ls-files; Get-FileHash` | hashes |
| 83 | Fuentes abiertas; dataset derivado no rastreado/licenciado ni reconstruible exacto | No verificado para paquete procesado | `.gitignore`; data scripts | varias | `git check-ignore; git ls-files` | dataset local |
| 84 | NASS dominio público con atribución; NEX CC0+citación | Verificado con fuentes oficiales | fuentes web; falta manifest local | n/a | consultar enlaces oficiales | términos/citas |
| 85 | Oración publicable declara URL/hash y ausencia de licencia/scripts | Verificado | Git/status | n/a | Git commands | texto Q85 |
| 86 | Tabla completa de hiperparámetros generada | Verificado | hyperparameters CSV | n/a | leer CSV | tabla Q86 |
| 87 | Tabla de amenazas interna/externa/constructo/conclusión | Verificado | evidencia de auditoría | n/a | revisar secciones | tabla Q87 |
| 88 | RQ1–RQ5 vinculadas a experimento, número y limitación | Verificado con límites | `respuesta_revision...`; artefactos | 57–61 | scripts Q1 | tabla Q88 |
| 89 | Contribuciones separadas y limitadas a evidencia | Verificado | código+artefactos | varias | revisión cruzada | lista Q89 |
| 90 | 20 afirmaciones prohibidas/fuertes listadas | Verificado | código+resultados | varias | revisión cruzada | lista Q90 |
| 91 | Cuatro referencias conservables solo para contexto/contraste | Verificado | `informe_completo...md` | 43–49,201,254,refs | `rg -n autores ...` | criterio Q91 |
| 92 | Tabla consolidada de las 92 preguntas generada sin omisiones | Verificado | este archivo | sección 92 | contar filas `rg '^\| [0-9]+ \|'` | esta tabla |

## Comandos finales de verificación del documento

```powershell
# Debe devolver 92 filas numeradas dentro de la tabla final
$lines = Get-Content docs/auditoria_reproducibilidad_completa.md
$start = ($lines | Select-String '^## 92\. Tabla final').LineNumber
$end = ($lines | Select-String '^## Comandos finales').LineNumber
($lines[($start - 1)..($end - 2)] | Select-String '^\| [0-9]+ \|').Count

# Artefactos y tests
python scripts/generate_q1_revision_artifacts.py
python scripts/generate_q1_extended_audit.py
python -m pytest backend/tests -q
tsx --test tests/pinn-wiring.test.ts
tsc --noEmit
```

Resultado esperado del primer comando: `92`. Resultado observado de tests en esta auditoría: `43 passed` en Python, `4 passed` en TypeScript y TypeScript compiler exit 0.

---

## Respuestas 82–90 — apertura, paper y conclusiones permitidas

### 82. Checkpoint público y hash

**Respuesta concreta.** `backend/models/cerespinn_pinn.pt` está rastreado en el commit público. SHA-256 local: `600F4A2BFD8C8F3A4CE08E623CEBED4087D64BAE341EBD5FE71C32507ABDE7E4`. Metadatos: `19F365FB854118FBED8E88B51701C096130AD4D58106A10954144225BF9F8CB6`. URL directa esperada: `https://raw.githubusercontent.com/David42024/CeresPINN/6c22e543b0fefbc498f5d811732974f48c1089c2/backend/models/cerespinn_pinn.pt`.

- **Estado:** inclusión/hash VERIFICADOS; descarga HTTP directa **NO VERIFICADA en esta sesión** por restricción de red, aunque el repositorio sí respondió anónimamente.
- **Archivo/ruta:** `backend/models/cerespinn_pinn.pt`; `backend/models/cerespinn_metadata.json`.
- **Comando:** `git ls-files backend/models/*; Get-FileHash backend/models/cerespinn_pinn.pt -Algorithm SHA256`.
- **Salida:** hashes anteriores.

### 83. Dataset procesado y distribución

**Respuesta concreta.** Las fuentes NASS y NEX son abiertas bajo las condiciones descritas en la respuesta 84, pero la preparación para redistribuir **este derivado exacto** no está cerrada: `data/cerespinn_training_iowa.csv` está ignorado/no rastreado, no tiene licencia/manifest de atribución propio y la cadena pública de reconstrucción no produce de forma verificada ese mismo archivo desde cero. Hay extractores de fuentes, pero no un pipeline público íntegro hasta el CSV del checkpoint.

- **Estado:** fuentes reutilizables VERIFICADAS; distribución/reconstrucción exacta del procesado **NO VERIFICADA**. Esto no es asesoría legal.
- **Archivo/ruta:** `.gitignore`; `backend/data/nass.py`; `backend/data/nex_gddp.py`; `backend/data/run_all.py`; `data/cerespinn_training_iowa.csv` (local).
- **Comando:** `git check-ignore -v data/cerespinn_training_iowa.csv; git ls-files data backend/data/raw`.
- **Salida:** dataset no rastreado.

### 84. Licencias de datos

**Respuesta concreta.** USDA-NASS declara que la mayoría de la información de su sitio es dominio público, puede descargarse/reproducirse libremente y solicita reconocimiento a USDA-NASS ([Citation Request oficial](https://data.nass.usda.gov/Data_and_Statistics/Citation_Request/index.php)). NASA indica que, salvo restricción señalada, los datos de misiones lideradas por NASA usan CC0 y solicita citar/reconocer la fuente ([Data Use and Citation Guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software/data-use-policy)). La nota técnica actual de NEX-GDDP-CMIP6 indica licencia general CC0 desde septiembre de 2022, exige seguir la guía de citación y proporciona DOI/acknowledgement ([NASA NEX-GDDP-CMIP6 Technical Note](https://www.nccs.nasa.gov/wp-content/uploads/2024/03/NEX-GDDP-CMIP6-Tech_Note_4.pdf)).

En repositorio/paper deben citarse USDA-NASS Quick Stats y NEX-GDDP-CMIP6 (DOI `10.7917/OFSG3345`), incluir fecha de acceso/procesamiento y el reconocimiento de NASA/NEX/CMIP6. Aun bajo CC0, no debe insinuarse aval de NASA/USDA.

- **Estado:** VERIFICADO con fuentes oficiales vigentes al 22-09-2026.
- **Archivo/ruta:** el repositorio todavía no contiene un `DATA_LICENSE`/manifest completo.

### 85. Oración publicable sobre código abierto

**Texto fiel a la situación real:**

> El código auditado de CeresPINN está públicamente accesible en https://github.com/David42024/CeresPINN, commit `6c22e543b0fefbc498f5d811732974f48c1089c2`; no obstante, dicho commit no contiene una licencia explícita ni incluye los scripts locales `scripts/generate_q1_revision_artifacts.py` y `scripts/generate_q1_extended_audit.py`, por lo que la versión examinada aún no constituye un paquete de reproducción científica completo y licenciado.

- **Estado:** VERIFICADO.
- **Comando:** `git rev-parse HEAD; git status --short; git ls-files | rg 'LICENSE|generate_q1'`.
- **Salida:** hash; scripts untracked; sin LICENSE.

### 86. Tabla de hiperparámetros lista para el paper

| Elemento | Valor real |
|---|---|
| Inputs | 7: year, temp_anomaly_c, precip_anomaly_pct, co2_ppm, heatwave_risk, seasonal_precip_mm, seasonal_cdd |
| Tronco | 4 capas densas de 128 unidades |
| Activación tronco | Tanh después de cada capa |
| Dropout | 0.05 después de cada Tanh |
| Salida rendimiento | 128→64 ReLU→1 lineal |
| Segunda salida | 128→32 ReLU→1 Sigmoid; proxy no supervisado y colapsado a 0.5 |
| Parámetros | 63,042 |
| Optimizador | Adam |
| Learning rate | 0.001 constante; sin scheduler |
| Weight decay Adam | 1e-5 |
| L2 manual | 1e-4 Σθ² |
| λ monotonicidad/rango | 0.5 |
| Batch | 64 (2 minibatches/época) |
| Épocas | 300 |
| Seed | 42 |
| Split | grouped-random-year-holdout; 28 años train/8 test; 84/24 filas SSP |
| Normalización | z-score X y min-max y, estadísticos solo de train |
| Parada | ninguna; se guarda época final |

- **Estado:** VERIFICADO.
- **Archivo/ruta:** `docs/q1_artifacts/extended/hyperparameters.csv`; `backend/training/config.py`; `pinn.py`; `train.py`.
- **Comando:** `Get-Content docs/q1_artifacts/extended/hyperparameters.csv`.

### 87. Amenazas y mitigaciones

| Validez | Amenaza concreta | Efecto potencial | Mitigación ya realizada | Mitigación futura (no realizada) |
|---|---|---|---|---|
| Interna | Features SSP/CO₂/riesgo térmico estructuralmente colineales; CDD constante | Atribución equivocada y Sobol dominado por codificación | Split por año; correlaciones y ablación CO₂ seed 42 | Datos climáticos observados por año; ablation multi-seed; quitar proxies redundantes |
| Externa | Target agregado anual, ocho años test, sin dataset externo | Generalización a condado/campo/región desconocida | Holdout de años completos e IC bootstrap | Validación independiente por estado/condado y rolling-origin |
| Constructo | Se llama PINN/Richards a monotonicidad + simulador bucket; cabeza física no supervisada | Sobreinterpretar significado físico | Auditoría de ecuación real y balance exportado | Implementar residuo PDE/targets físicos o renombrar el modelo y limpiar UI/PDF |
| Conclusión | n=8, múltiples comparaciones, KS de baja potencia | Falsos positivos/“equivalencia” aparente | Métricas por año, bootstrap 20k, multi-seed | Más años/sitios, corrección multiplicidad, tests pareados de error y análisis de potencia |

- **Estado:** VERIFICADO para amenazas/mitigaciones presentes; acciones futuras explícitamente no realizadas.

### 88. RQ1–RQ5

| RQ | Experimento/archivo | Respuesta numérica | Limitación principal |
|---|---|---|---|
| RQ1: desempeño y baselines | Hindcast, `baseline_metrics_full_precision.csv` | Ceres RMSE 712.13, MAE 604.19 kg/ha, R² 0.8251; Linear/Ridge mejores en punto | Solo 8 años; diferencias vs Linear/Ridge no significativas por bootstrap |
| RQ2: respuesta SSP5-8.5–2050 | Inference + `management_scenarios.csv` | Iowa basal = 13,331 kg/ha, 585 mm; input SSP5 usa +2.7°C/−24%/520 ppm | Proyección depende de templates y multiplicadores; no valida pérdida climática real |
| RQ3: manejo | `management_scenarios.csv` | siembra −14 d: mismo rendimiento; ciclo corto 11,731 (−12%); riego75 14,303 (+7.2917%); combinado 12,587 (−5.5833%) | Efectos de rendimiento son multiplicadores fijos; siembra no entra a la red |
| RQ4: sensibilidad | `sobol_checkpoint.csv` | S1 CO₂=0.977079, temp=0.016093, precip=0.004429 | CO₂ está confundido con escenario/riesgo; bounds fijados ad hoc |
| RQ5: suelo/localización | `field_soil_constants.csv` + inference | Los cuatro perfiles pueden dar idéntico 13,331 kg/ha con configuración común | Suelo no entra a la red ni al multiplicador final; solo cambia trayectoria diaria |

- **Estado:** VERIFICADO respecto de las RQ redactadas en `docs/respuesta_revision_segun_software.md:57-61`. RQ2/RQ5 son resultados del prototipo, no validación científica externa.

### 89. Contribuciones reproducibles

**Software.** API FastAPI que carga un checkpoint PyTorch, endpoint de simulación, frontend que lo invoca y tests de cableado; simulador diario reproducible de GDD/agua/estrés; artefactos CSV de auditoría local.

**Metodológica.** MLP con penalización diferenciable de monotonicidad respecto de temperatura y precipitación, split agrupado por año y evaluación sobre años independientes. No es una PINN de Richards.

**Empírica.** En el split de ocho años: R² 0.8251/RMSE 712.13 kg/ha; estabilidad multi-seed cuantificada; dominancia Sobol del input CO₂ dentro de los bounds evaluados; robustez a ruido del 5% con +0.51% RMSE.

**Hallazgos negativos.** No supera Linear/Ridge; CDD es constante; cabeza física colapsa a 0.5; fecha/suelo no alteran directamente el rendimiento; no hay validación externa; el paquete público no reproduce todavía todo desde cero.

- **Estado:** VERIFICADO.
- **Archivos:** `backend/app.py`, `backend/inference.py`, `backend/training/*`, `backend/tests/*`, `docs/q1_artifacts/*`.

### 90. Afirmaciones que NO deben hacerse

No afirmar que CeresPINN:

1. resuelve o discretiza la ecuación de Richards;
2. minimiza un residuo PDE, condiciones de borde o conservación de masa;
3. aprende un estado hídrico físicamente validado en su segunda cabeza;
4. optimiza automáticamente manejo, fecha de siembra o riego;
5. calcula causalmente el beneficio del adelanto de siembra sobre rendimiento;
6. predice vulnerabilidad espacial/condal con el checkpoint actual;
7. incorpora suelo, raíces o ubicación en la red de rendimiento;
8. supera a todos los baselines (Linear y Ridge son mejores en el punto estimado);
9. demuestra equivalencia por `p>0.05` o por KS con n=8;
10. está externamente validado;
11. es más rápido o más preciso que DSSAT/APSIM/WOFOST sin benchmark directo;
12. reproduce exactamente los Sobol antiguos;
13. usa datos NEX completos para todas las combinaciones año–escenario;
14. usa CHIRPS/SoilGrids en el checkpoint sin evidencia de metadatos;
15. ofrece recomendaciones económicamente calibradas o precios/costos actuales;
16. conserva exactamente masa en el simulador diario;
17. proporciona una distribución pública reproducible/licenciada del dataset procesado;
18. tiene CI verde o una imagen Docker construida desde cero;
19. confirma H1, una pérdida ≥15% o mitigación ≥50% con la evidencia presente;
20. produce un gemelo digital en tiempo real o inferencias causales.

- **Estado:** VERIFICADO por contraste con la implementación y artefactos descritos.
