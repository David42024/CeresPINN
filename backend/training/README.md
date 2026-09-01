# CeresPINN — Entrenamiento del modelo (PINN de maíz)

Este módulo (`backend/training/`) construye el PINN que aprende rendimiento de maíz
resiliente a sequía, condicionado a escenarios climáticos CMIP6 (SSP1-2.6, SSP3-7.0,
SSP5-8.5), usando los datasets públicos extraídos por `backend/data/`.

## Arquitectura

```
backend/training/
├── config.py     # Hiperparámetros + rutas (todo sobreescribible por env)
├── dataset.py    # Asimila NASS (yield) + CHIRPS/NEX-GDDP (clima) -> feature/target
├── pinn.py       # CeresPINN (red 2 heads) + pérdida física (conservación de agua)
├── train.py      # Loop de entrenamiento + persistence (.pt + metadata.json)
└── README.md
```

- **Modelo** `CeresPINN`: MLP multicapa con dos salidas:
  - `yield_head` → rendimiento predicho (bu/acre)
  - `physics_head` → proxy de disponibilidad hídrica en [0,1] (via sigmoid)
- **Pérdida física** (`physics_loss`): además del MSE de datos, penaliza
  - que el rendimiento aumente con la anomalía térmica (no físico),
  - que el rendimiento disminuya con más precipitación,
  - disponibilidad hídrica fuera de [0,1].
  → Incorpora el **Richards/agua-suelo** como prior de conservación simple; un bucle
  completo de residuos PDE es una extensión directa de esta función.

## Configuración del entorno

```bash
# 1. Entorno Python (3.10+)
python -m venv .venv

# 2. Dependencias de entrenamiento (PyTorch, sklearn, etc.)
.venv\Scripts\pip install -r backend/requirements-ml.txt
#   Para GPU (Windows/CUDA), instala torch primero:
#   .venv\Scripts\pip install torch --index-url https://download.pytorch.org/whl/cu121
#   luego el resto.

# 3. (Opcional) Extraer datos reales
.venv\Scripts\python -m backend.data.extractors all        # dry-run por defecto
.venv\Scripts\python -m backend.data.extractors all        # con NASS_API_KEY + DRY_RUN=0
```

## Ejecutar el entrenamiento

```bash
# Entrenamiento (usa datos extraídos si existen, si no usa fallback sintético)
.venv\Scripts\python -m backend.training.train
```

Hiperparámetros por variables de entorno:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CERESPINN_EPOCHS` | 300 | épocas |
| `CERESPINN_LR` | 1e-3 | learning rate |
| `CERESPINN_BATCH_SIZE` | 64 | batch |
| `CERESPINN_HIDDEN_LAYERS` | 4 | capas ocultas |
| `CERESPINN_HIDDEN_UNITS` | 128 | unidades por capa |
| `CERESPINN_LOSS_PHYSICS` | 0.5 | peso de la pérdida física |
| `CERESPINN_SEED` | 42 | semilla (reproducibilidad) |
| `CERESPINN_DEVICE` | auto | `auto`/`cpu`/`cuda` |

## Artefactos

Se guardan en `backend/models/`:

- `cerespinn_pinn.pt` — pesos entrenados (`state_dict` de PyTorch)
- `cerespinn_metadata.json` — métricas, features, normalización, device, data_source

> `backend/models/` está en `.gitignore` (los pesos son reproducibles vía entrenamiento).

## Fuente de datos

- `data_source` en la metadata te dice qué datos alimentaron el modelo:
  - `"nass+nex-gddp"` → datos reales extraídos (requiere NASS_API_KEY)
  - `"synthetic-fallback"` → datos sintéticos deterministas (para smoke-test antes
    de un harvest real)

## Consumo en el backend de inferencia

La inferencia del PINN entrenado se sirve desde el backend FastAPI (`/api/simulate`),
que carga `cerespinn_pinn.pt`. Ese runtime usa `backend/requirements.txt` (ligero),
no el stack ML completo.
