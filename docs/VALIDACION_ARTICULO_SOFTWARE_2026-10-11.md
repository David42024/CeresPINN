# Validación del artículo CeresPINN frente al software

Fecha: 11 de octubre de 2026.

El artículo describe razonablemente el checkpoint histórico CeresPINN-maize-v2.5, pero necesita una revisión mayor antes de enviarse. La aplicación carga ese checkpoint; el entrenamiento actual y varios artefactos posteriores ya no corresponden exactamente al experimento descrito. La capacidad de extrapolación temporal no está demostrada. No se modificaron el manuscrito ni los archivos de implementación para esta revisión.

## Alcance y evidencia

Se revisó el DOCX indicado por el autor, incluyendo texto dentro de controles de contenido de Word mediante XML, el código de entrenamiento e inferencia, los metadatos del checkpoint, los scripts de reproducción y las tablas científicas guardadas. Se ejecutaron comprobaciones de integridad, TypeScript, tests del frontend, tests del modelo y siete simulaciones directas con el checkpoint local. Las métricas temporales y multi-seed que siguen son las de los artefactos actuales: no se reentrenaron sus experimentos completos durante esta revisión.

La lectura simple con python-docx omitía algunos controles de contenido; se contrastaron los párrafos relevantes contra el XML completo para no confundir ese problema de extracción con texto ausente. No se certifica la maquetación final: el renderer empaquetado no encontró LibreOffice. Tampoco se verificó el despliegue remoto ni el origen de cada archivo climático bruto.

## Qué sí coincide

- Metadatos: siete entradas, cuatro capas de 128 unidades, 84 filas de entrenamiento y 24 de prueba; objetivos agregados en 36 años y ocho años independientes de evaluación.
- Los años de prueba históricos coinciden con el artículo: 1991, 1992, 1998, 2001, 2003, 2004, 2011 y 2024.
- Al recalcular a partir de las muestras guardadas, promediando por año: RMSE 712.126 kg/ha, MAE 604.186 kg/ha y R² 0.825086. Son las cifras centrales del manuscrito.
- El software aplica multiplicadores de manejo. La razón 1.03/0.96 implica +7.2917 % para deficit_75 frente a deficit_50; no es un beneficio estimado con observaciones de riego.
- La siembra y el suelo cambian las trayectorias diarias, pero no el rendimiento neuronal. El texto reconoce correctamente este desacoplamiento.
- El modelo no resuelve Richards. La descripción como red regularizada por monotonía es más precisa que una afirmación de solución de PDE.

## Correcciones prioritarias en el artículo

### Incluir la validación temporal posterior

El archivo `docs/q1_artifacts/temporal/temporal_validation_1990_2017_to_2018_2025.json` registra entrenamiento en 1990–2017 y prueba en 2018–2025. Para el ensamble de diez semillas informa:

| Modelo | RMSE kg/ha | MAE kg/ha | R² |
|---|---:|---:|---:|
| CeresPINN ensamble | 804.54 | 616.72 | -0.6211 |
| Regresión lineal | 718.37 | 509.48 | -0.2925 |
| Ridge | 701.15 | 486.14 | -0.2313 |
| Random Forest | 637.05 | 494.20 | -0.0164 |

El IC bootstrap del R² del ensamble es [-4.0469, 0.2039]. El promedio del RMSE de las semillas es 824.81 ± 229.54 kg/ha; no debe confundirse con el RMSE de la predicción promedio del ensamble. El README contiene cifras distintas (855.22, 683.62 y -0.8318), de modo que también debe actualizarse.

Añadir este experimento en métodos, resultados, resumen y conclusiones. Un R² negativo indica que, sobre estos años de prueba y con la definición habitual de R², el predictor supera en error cuadrático a la referencia constante basada en la media de los objetivos de prueba. La evaluación histórica aleatoria no justifica eficacia predictiva en 2050. Las salidas futuras deben presentarse como exploraciones fuera del dominio evaluado.

### Sincronizar todas las cifras con una versión científica congelada

| Resultado | Artículo | Artefacto actual |
|---|---|---|
| MLP sin monotonía, RMSE | 1180.99 | 1221.51 kg/ha |
| MLP sin monotonía, MAE | 979.30 | 1069.94 kg/ha |
| MLP sin monotonía, R² | 0.5189 | 0.4854 |
| CeresPINN multi-seed, RMSE medio ± DE | 776.79 ± 42.55 | 813.54 ± 53.00 kg/ha |
| CeresPINN multi-seed, R² medio ± DE | 0.7913 ± 0.0227 | 0.7708 ± 0.0306 |
| MLP multi-seed, RMSE medio ± DE | 1049.59 ± 137.87 | 1034.08 ± 103.67 kg/ha |
| MLP multi-seed, R² medio ± DE | 0.6141 ± 0.1049 | 0.6278 ± 0.0751 |
| Tiempo de entrenamiento | 31.36 s | 5.84 s |
| Latencia mediana / p95 | 2.00 / 5.66 ms | 0.2102 / 0.7354 ms |
| Caso base de manejo | 13331 kg/ha | CSV: 9625; ejecución directa: 13310 |
| Riego 75 % | 14303 kg/ha | CSV: 10326; ejecución directa: 14281 |

Las diferencias de tiempo pueden proceder de entornos y ejecuciones distintos, no necesariamente de errores. Se necesita un identificador de ejecución y su entorno para cada tabla. En el CSV actual de manejo, `raw_checkpoint_bu_acre` está vacío; no se debe asumir que provino de la misma inferencia neuronal que el manuscrito. La ejecución directa usó el payload del script extendido: Iowa, SSP5-8.5, 2050, 520 ppm, +2.7 °C, -24 % precipitación, humedad inicial 60 %, N=180 y cultivar medio.

No basta sustituir números: corregir primero los scripts de auditoría y regenerar conjuntamente tablas, figuras, intervalos y conclusiones sobre ablaciones.

### Delimitar el significado del prototipo

Mantener las advertencias ya presentes sobre manejo heurístico, falta de validación espacial y ausencia de Richards. Reemplazar «no resuelve del todo la ecuación de Richards» por «no resuelve la ecuación de Richards». Suavizar «excelente viabilidad» y el alcance de «Drought-Resilient»: no se ha validado resiliencia del rendimiento con observaciones independientes.

Definir qué hace que el sistema sea un prototipo de gemelo digital. Si no hay sincronización periódica con observaciones de una parcela ni asimilación de datos, describirlo explícitamente como plataforma de simulación híbrida o prototipo orientado a gemelo digital. Evitar que el título implique una validación agronómica que no existe.

Añadir la fórmula exacta de la pérdida de monotonía, su peso 0.5 y las columnas sobre las que se diferencia. El texto habla de monotonía de precipitación «dentro del régimen de déficit», pero la función actual aplica la penalización a todo el lote y no contiene una máscara de déficit. Cambiar esa descripción o implementar y validar dicha condición.

### Mejorar metodología y discusión

- Tratar los escenarios replicados como un artificio del diseño histórico; no como observaciones de respuestas distintas a SSP. El artículo reconoce n=36, pero la replicación tampoco valida el efecto de escenario.
- Separar interpolación de años históricos, extrapolación temporal, generalización geográfica y respuesta al manejo.
- El año puede representar tendencia tecnológica, variedades y manejo omitidos. Añadir una referencia con solo año y comparar anomalías de rendimiento o tendencias estimadas únicamente en entrenamiento.
- El Sobol calculado variando CO₂ y otros parámetros independientemente explora combinaciones que pueden no corresponder a escenarios coherentes. Documentar rangos y distribución, evaluar dependencias y separar sensibilidad matemática de interpretación fisiológica.
- Las diez semillas evalúan variabilidad de inicialización, no diez muestras independientes de campo. No aumentan los ocho años de prueba.
- Mantener que ausencia de significancia no demuestra equivalencia. Reportar la gran incertidumbre de R² y evitar presentar los p-values de sesgo/KS como validación de precisión.
- Explicitar lluvia, temperatura y radiación diarias sintéticas del simulador. No son series diarias NEX extraídas para la parcela.
- El indicador llamado CWSI se calcula con humedad media del suelo; precisar que es un índice heurístico de estrés, sin afirmar una medición térmica del dosel.

### Preparar el manuscrito para la revista

La revista exige inglés en todo el manuscrito y referencias, plantilla oficial y 12–20 páginas. El archivo está mayormente en español. Traducir después de corregir la evidencia para evitar rehacer el texto. Verificar el número de páginas en la exportación final; no se contó mediante render durante esta auditoría.

Corregir errores concretos: «no ueron», «darlen», «natuiraleza», «huamana», «identificas», «CO₂Como», «20502» y referencias concatenadas como `[10]Raissi` y `[20]Granella`. Completar títulos bibliográficos, DOI, volumen y páginas donde falten; no se verificaron una por una todas las referencias. Reconstruir potencias y sumatorias como ecuaciones editables y revisar la continuidad de la Tabla 1. El texto del XML conserva contenido que algunas lecturas simples omitían, por lo que cualquier aparente truncamiento debe comprobarse visualmente antes de editarlo.

## Correcciones prioritarias en el software

### Contrato único de variables y versión científica

`backend/training/config.py` define ocho variables; el checkpoint y el artículo usan siete. `backend/training/dataset.py` conserva observaciones individuales y elimina la expansión SSP, mientras el modelo histórico se entrenó con medianas por año y escenario. Un entrenamiento nuevo puede reemplazar los mismos nombres de archivos con un modelo distinto.

Separar explícitamente la reproducción v2.5 de los experimentos nuevos. Versionar checkpoint, esquema, normalización, split, entorno y commit. En inferencia, cargar arquitectura y columnas desde metadatos validados, rechazar variables ausentes y prohibir completarlas silenciosamente con cero.

El laboratorio ML también conserva un experimento diferente en `ml_lab/artifacts/common_benchmark.json`: siete variables de otro esquema, 50 épocas, un hash distinto y particiones entrenamiento/validación/prueba. Su código selecciona por validación, una mejora respecto a elegir con test. No se pueden mezclar sus cifras con las del checkpoint de producción ni trasladar al artículo su modelo ganador sin describir un experimento nuevo. Unificar el registro de modelos entre laboratorio, servicio y manuscrito.

### Penalizaciones de auditoría sobre columnas incorrectas

`scripts/generate_q1_revision_artifacts.py` construye configuraciones en `benchmark_training` y `train_unconstrained_mlp` sin fijar `feature_names=FEATURES`, pese a alimentar matrices de siete columnas. La configuración por defecto actual selecciona temperatura en índice 1 y precipitación en índice 2; en la matriz histórica el índice 2 es anomalía de precipitación, mientras la precipitación estacional está en índice 5. La penalización puede ejecutarse y pasar tests aun actuando sobre la variable equivocada.

Fijar el esquema en cada configuración y comprobar que número, nombres y orden coinciden con la matriz. El script temporal y el ajuste multi-seed extendido sí fijan sus nombres; no atribuir este defecto indiscriminadamente a todos los experimentos.

### Errores en dataset y evaluación del entrenamiento actual

- `season_precip_mm` se reconstruye desde `precip_anomaly_percent`, nombre ausente en el clima generado, y cae a 400 mm; no copia `seasonal_precip_mm` disponible. Unificar nombres y unidades.
- `_blend_climate` interpola bidireccionalmente antes de la división temporal. Evitar que datos posteriores al corte contribuyan a transformar el entrenamiento; distinguir este riesgo de la validación temporal sobre CSV ya congelado.
- Cuando NASS existe pero queda vacío tras limpieza, `build_dataset` devuelve solo una matriz en lugar de sus cinco salidas contractuales. Fallar con diagnóstico o devolver una tupla completa.
- `train.py` guarda `features[0]` como año, pero la configuración actual comienza por temperatura. Pasar el año como identificador separado.
- En `train_v4_spatial.py` se elige el modelo por RMSE de 2018–2025: esos años sirven entonces para selección, no para prueba final independiente. Usar validación interna temporal y reservar un test final. Reportar RMSE por condado dentro del mismo test temporal no prueba generalización a condados excluidos.

### Disponibilidad, trazabilidad y extrapolación reales

`PinnAdapter.available` y `load` comprueban existencia de archivos; no una inferencia válida. El servicio debe validar pesos, dimensiones, normalización y una predicción finita al arrancar. El endpoint de salud tampoco debería omitir la exigencia de datos reales mediante `True or ...`.

La ejecución directa devolvió `CeresYield`, versión `3.0.0`, hash literal `hash`, ámbito `county_annual` y `model_verified=true`, aunque el checkpoint es v2.5 de medianas nacionales. Derivar estos campos de metadatos comprobados; no usar valores afirmativos por defecto, tampoco en el fallback.

`PinnAdapter.check_extrapolation` devuelve siempre falso: 2050 quedó marcado dentro de dominio aunque el entrenamiento termina en 2025. Guardar rangos y detectar extrapolación temporal y de covariables; añadir una advertencia visible.

### Inferencia coherente y rápida

La correspondencia de heatwave_risk difiere entre entrenamiento (0.15, 0.42, 0.78) e inferencia PINN (0.15, 0.60, 0.85 para los escenarios coincidentes). Los adaptadores usan reglas diferentes. Centralizar transformación y verificar paridad entrenamiento–servicio.

La ruta actual vuelve a cargar pesos y reconstruir la red en cada predicción. Cachear el modelo tras validarlo. La medición de latencia de un forward sobre una red ya cargada no representa automáticamente `/api/simulate`, que incluye carga, simulación y serialización.

### Balance hídrico y parámetros inactivos

Ksat se lee pero no se utiliza en los flujos. Las pruebas con Ksat=1 y Ksat=1000 dieron iguales indicadores. Implementar su efecto con unidades explícitas o retirarlo del formulario y de las afirmaciones metodológicas.

Los contenidos de agua se recortan a mínimos y saturación sin registrar toda la corrección en flujos; runoff se fija a cero. A partir de las salidas redondeadas del caso Iowa se obtuvo un residuo acumulado de balance de aproximadamente +36.33 mm y un máximo diario de 1.81 mm. El diagnóstico requiere confirmar el balance internamente antes del redondeo; no permite afirmar conservación de masa.

Publicar almacenamiento inicial/final y verificar por paso: cambio de almacenamiento = lluvia + riego − evapotranspiración − drenaje − escorrentía. No afirmar efectos hidráulicos de una variable solo porque se acepta como entrada.

### Incertidumbre, manejo y métricas del API

La banda PINN es ±15 % del rendimiento bruto, no un intervalo calibrado del rendimiento ajustado; en cultivar corto queda centrada alrededor de una cantidad distinta a la salida mostrada. Describirla como banda heurística, corregir el centro y no usar «90» como promesa de cobertura. Calibrar intervalos posteriormente sobre validación independiente y comprobar cobertura.

El CO₂ interviene en la red y vuelve a multiplicar el rendimiento después. Documentar esta duplicación y validarla antes de atribuirla a fisiología. Para manejo y suelo, el acoplamiento con rendimiento requerirá calibración de un mecanismo y validación independiente; añadir un multiplicador de estrés sin datos no resuelve el problema científico.

`backend/validation.py` busca `rmse`, aunque el checkpoint histórico almacena `mse`, y mezcla posibles unidades de MAE. Emitir nombres con unidades, protocolo y unidad experimental; hacer sqrt(MSE) y la conversión cuando corresponda. Evitar mostrar métricas históricas de 24 filas como si fueran las métricas de ocho años o la validación temporal posterior.

## Verificación ejecutada y límites

- Integridad: cuatro entradas verificadas contra el manifiesto; ocho salidas esperadas presentes. Esta comprobación no garantiza corrección estadística ni que los artefactos se generaran con el código actual.
- TypeScript: `tsc --noEmit` pasó.
- Frontend: siete tests de conexión pasaron; son mayormente comprobaciones de código fuente, no de calidad predictiva.
- Modelo: 14 tests de entrenamiento, monotonía e inferencia pasaron.
- Suite backend completa: en `.venv-mllab` falló la recolección por dependencias httpx/httpx2 ausentes. El intento alternativo en `.venv-langchain` no produjo resultados durante varios minutos y se interrumpió; no se declara aprobada la suite completa.
- El entorno `.venv` falló al importar extensiones de NumPy. La inferencia directa se ejecutó en `.venv-mllab`, con PyTorch 2.14.0+cpu y NumPy 2.3.5, distintos del entorno declarado en el artículo.
- Build: pasó fuera de aislamiento (2554 módulos; 1 min 28 s), con advertencia por un bundle principal de 2.16 MB. El primer intento bajo aislamiento falló por EPERM al resolver un archivo, no por un error de TypeScript.
- Evidencia ejecutable: `.audit/probe_article.py`; resultados: `.audit/probe_results.json`. Los artefactos históricos no fueron sobrescritos.

## Orden recomendado

1. Congelar versión científica y corregir contratos, penalizaciones, trazabilidad y detección de extrapolación.
2. Regenerar auditorías en un entorno documentado y fallar si el escenario usa fallback.
3. Sincronizar todas las cifras del manuscrito y README; incluir el resultado temporal negativo.
4. Corregir alcance, ecuaciones y referencias; traducir y verificar plantilla y páginas.
5. Para una contribución predictiva más fuerte, desarrollar datos condado-año con clima observado alineado y pruebas temporales/geográficas independientes; después calibrar efectos de suelo y manejo.

Texto sugerido para la conclusión: «La regularización de monotonía mejoró el desempeño frente al MLP equivalente en la partición histórica agrupada por año. Sin embargo, la evaluación prospectiva 2018–2025 produjo R² negativo, por lo que no se demostró capacidad de extrapolación temporal. Las respuestas de manejo y suelo se interpretan como exploraciones deterministas de un prototipo, sin validación causal ni espacial del rendimiento».

## Fuentes externas verificadas

- [Instrucciones oficiales de envío de Acta Polytechnica Hungarica](https://acta.uni-obuda.hu/Paper_Submission.htm).
- [Política editorial de la revista](https://acta.uni-obuda.hu/EditPolicy.htm).
- [Thrasher et al. 2022 sobre NEX-GDDP-CMIP6](https://www.nature.com/articles/s41597-022-01393-4): respalda la descripción del producto general, no la trazabilidad de los resúmenes específicos del proyecto.
