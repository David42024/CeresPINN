# Auditoría científica de la revisión del 26 de octubre de 2026

Las correcciones nuevas están separadas del checkpoint histórico. El modelo activo y sus datos originales no se reemplazan.

## Reproducción

```bash
python -m venv .venv-revision
# Activar el entorno según el sistema operativo.
python -m pip install -r requirements-revision.txt
python scripts/revision_scientific_audit.py
```

El script guarda resultados en este directorio y utiliza un solo hilo de PyTorch y algoritmos deterministas sobre CPU. El CSV regional congelado evita la necesidad de pyarrow durante la reproducción. Las versiones exactas se registran en audit.json; una versión numérica distinta puede cambiar los reentrenamientos.

Antes de generar las figuras y el Word, ejecutar la extensión Bushland como se describe en `docs/q1_artifacts/bushland/README.md`. Los generadores son `python scripts/revision_figures.py` y `python scripts/build_revised_article.py`. El ZIP incluye el original como `manuscript_source.docx`, que el generador conserva. Para las 24 pruebas Python se usa `requirements-revision-test.txt` y los siete archivos de pruebas Python incluidos en el paquete.

## Archivos principales

- `audit.json`: protocolos, métricas, intervalos, contrastes ajustados, versiones y hashes.
- `rolling_origin_predictions.csv`: predicción anual por modelo y bloque temporal; 20 años únicos.
- `held_county_future_predictions.csv`: predicciones de tres baselines en condados excluidos durante el ajuste; 696 observaciones por modelo.
- `correlations_initial_training_only.csv`: correlaciones calculadas antes de los años de prueba.
- `vif_initial_training_only.csv`: constantes y dependencias exactas indicadas explícitamente; un VIF vacío con estado de rango deficiente representa infinito, no un valor desconocido.
- `vif_reduced_initial_training_only.csv`: diagnóstico del diseño de dos variables climáticas.
- `reference_verification.csv`: disposición de las 41 referencias originales y correspondencia con las 31 entradas finales.
- `manuscript_integrity.json`: hashes de original y copia revisada, número de figuras/tablas y renumeración bibliográfica.
- `figures/`: PNG y SVG obtenidos de datos numéricos mediante `scripts/revision_figures.py`.

La evaluación temporal nacional es retrospectiva e interna. La evaluación por condado corresponde a baselines regionales y no al checkpoint neuronal nacional. Una extensión separada de procesos usa datos públicos de campo de Bushland: cuatro campañas para calibrar y dos para evaluar. Su RMSE de grano es 3.248,07 kg/ha frente a 1.604,19 para Ridge; no valida el checkpoint nacional ni los efectos causales del manejo. Los protocolos, datos originales y resultados están incluidos en el paquete. No se ha publicado una release con DOI.


La recuperación actual de USDA/NOAA y la prueba por nueve distritos están en `docs/q1_artifacts/reacquired_20261026/README.md`. Se conservan los valores congelados; el control estricto detecta y documenta diferencias climáticas de 2025. La reproducción del análisis nuevo usa `python scripts/audit_reacquired_county.py` y `python scripts/audit_geographic_districts.py`.
