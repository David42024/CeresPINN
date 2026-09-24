# Artefactos de auditoría Q1

## Regeneración

Desde la raíz del repositorio y con las dependencias Python instaladas:

```powershell
python -m pip install --requirement requirements-repro.txt
python scripts/reproduce.py
```

El pipeline verifica primero los hashes y conteos del dataset, metadatos y
checkpoint versionados. Después ejecuta ambos generadores Q1 y la validación
temporal prospectiva. No requiere credenciales ni acceso de red.

## Artefactos básicos

- `hindcast_independent_years.csv`: ocho años independientes, observado y predicho
  por el checkpoint, en bu/acre y kg/ha.
- `same_split_baseline_comparison.csv`: métricas anuales del checkpoint y baselines.
- `robustness_results.csv`: ruido gaussiano al 5 % e imputación de una variable.
- `q1_statistics.json`: procedencia, métricas, t-test, KS, bootstrap, latencia,
  entrenamiento y robustez.

## Artefactos extendidos

- `extended/multiseed_neural_results.csv`: 10 semillas por modelo para CeresPINN y
  el MLP sin monotonicidad.
- `extended/multiseed_neural_summary.csv`: media, desviación estándar e IC 95 %.
- `extended/baseline_metrics_full_precision.csv`: RMSE, MAE y R² sin redondeo.
- `extended/hindcast_all_models.csv`: predicciones anuales de todos los modelos.
- `extended/model_difference_bootstrap.csv`: diferencias CeresPINN–baseline mediante
  20,000 remuestreos de los ocho años.
- `extended/sobol_checkpoint.csv`: S1/ST e intervalos para temperatura,
  precipitación y CO₂ calculados sobre el checkpoint.
- `extended/management_scenarios.csv`: escenarios de manejo del caso Iowa 2050.
- `extended/training_feature_correlations.csv`: matriz de correlación de entradas.
- `extended/temporal_coverage.csv`: registros por año y mediana anual.
- `extended/normalization_stats.csv`: media y desviación de entrenamiento.
- `extended/data_lineage_counts.csv`: conteos de cada transformación de datos.
- `extended/hyperparameters.csv`: configuración exacta del modelo evaluado.
- `extended/field_soil_constants.csv`: perfiles edáficos demostrativos codificados.
- `extended/extended_audit.json`: determinismo, ablación de CO₂, arquitectura,
  balance de agua aproximado y configuración Sobol.

## Validación temporal prospectiva

- `temporal/temporal_validation_1990_2017_to_2018_2025.json`: protocolo completo,
  hashes, versiones, métricas del ensamble de diez semillas, intervalos bootstrap
  y baselines.
- `temporal/temporal_predictions_2018_2025.csv`: observado y predicciones anuales.
- `temporal/temporal_seed_metrics.csv`: métricas individuales de las diez semillas.

El corte es estrictamente cronológico: entrenamiento 1990–2017 y prueba
2018–2025. Las transformaciones se ajustan solo en entrenamiento. El ensamble
obtuvo RMSE 855.22 kg ha⁻¹, MAE 683.62 kg ha⁻¹ y R² −0.8318. Por tanto, el
experimento cierra la ausencia de evaluación prospectiva, pero evidencia una
generalización temporal insuficiente y no reemplaza una validación externa.

Todos estos artefactos, sus generadores y el dataset procesado forman parte del
paquete reproducible del repositorio. GitHub Actions vuelve a generarlos en cada
push y pull request.
