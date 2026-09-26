# Plan de implementación para reentrenamiento y consumo de predicciones en CeresPinn

## Documento técnico de ejecución

Versión 1.0  
Fecha 25 de septiembre de 2026  
Repositorio evaluado cerespinn climate adaptive maize digital twin  
Commit de referencia 8bf6d695a9683231ef8710efa32bd149691bf78b

<!-- PAGEBREAK -->

# Decisión y propósito

CeresPinn puede reemplazar el modelo actual por un modelo supervisado convencional y mantener el mismo flujo React, FastAPI y artefacto de inferencia. La implementación recomendada no debe volver a entrenar otra red sobre la matriz actual de 108 filas y tratar el resultado como una predicción parcelaria. Debe reconstruir primero un panel histórico condado-año, entrenar modelos tabulares con validación temporal y geográfica, y separar las predicciones aprendidas de las variables generadas por el simulador determinista.

Este plan establece el trabajo necesario para producir un modelo de rendimiento anual condicionado por clima, integrarlo en el gemelo digital, cuantificar su incertidumbre y mostrar su alcance real en el frontend. También define una ruta provisional si no es posible recuperar inmediatamente los identificadores espaciales y las series climáticas históricas por condado.

El resultado esperado es un sistema en el que cada cifra indique si procede del modelo entrenado, del balance hídrico determinista o de un cálculo derivado. La promoción a producción dependerá de pruebas prospectivas. Un buen ajuste en una partición aleatoria no será suficiente.

# Resumen del estado actual

El archivo `data/cerespinn_training_iowa.csv` tiene 66 480 filas y nueve columnas, pero representa 22 160 rendimientos NASS repetidos para tres escenarios SSP. Solo contiene 36 años independientes, desde 1990 hasta 2025. El pipeline de entrenamiento calcula una mediana anual y replica el mismo objetivo para SSP1-2.6, SSP3-7.0 y SSP5-8.5. El modelo termina usando 84 filas de entrenamiento y 24 de prueba, equivalentes a 28 y 8 años independientes.

El dataset procesado no conserva estado, condado, FIPS ni coordenadas. Los tres escenarios tienen solo tres valores de CO2, precipitación anómala y riesgo de ola de calor. `seasonal_cdd` es constante. Por tanto, el modelo no puede distinguir localidades ni aprender una respuesta observada a los SSP futuros.

La validación prospectiva existente entrena con 1990 a 2017 y evalúa 2018 a 2025. El ensamble neuronal obtiene R2 negativo. Random Forest queda cerca de R2 cero y Ridge también obtiene R2 negativo. Estos resultados no invalidan las fuentes de datos, pero muestran que la representación actual no demuestra capacidad de pronóstico futuro.

| Elemento | Estado actual | Implicación |
| --- | --- | --- |
| Rendimiento observado | USDA NASS con 22 160 observaciones originales | La agregación actual descarta la variación espacial |
| Clima | Resumen regional NASA NEX GDDP y plantillas SSP | No existe emparejamiento histórico por condado en el CSV final |
| Unidades independientes | 36 años | Insuficiente para justificar una red profunda compleja |
| Escenarios | Tres copias del mismo rendimiento anual | No permiten aprender el efecto causal de SSP1 frente a SSP5 |
| Manejo | Sin targets observados de riego variedad o nitrógeno | Los efectos actuales son multiplicadores programados |
| Estados diarios | Sin observaciones de humedad LAI biomasa o CWSI | La serie diaria es una simulación determinista |
| Consumo frontend | Funcional mediante `/api/simulate` | El contrato exige actualmente `inference_mode=pinn` |

# Alcance del producto objetivo

## Capacidad que debe implementarse

La versión siguiente debe predecir rendimiento anual de maíz en kg por hectárea para una unidad espacial y un conjunto de variables climáticas compatibles con el entrenamiento. Debe devolver un intervalo predictivo, versión del modelo, procedencia del dataset, indicador de extrapolación y alcance geográfico.

Cuando el panel condado-año esté disponible, la unidad espacial será el condado. Mientras solo existan los archivos procesados actuales, la unidad será regional y la salida deberá etiquetarse como exploratoria.

## Capacidades que deben permanecer separadas

El balance hídrico de tres capas puede seguir generando humedad, evapotranspiración, drenaje y estrés diario, pero deberá identificarse como simulación determinista. No se debe afirmar que esos valores fueron aprendidos por el modelo de rendimiento.

Los efectos de variedad, riego y nitrógeno deben retirarse de la predicción aprendida hasta disponer de ensayos u observaciones que contengan esas variables y un rendimiento asociado. Pueden mantenerse como escenarios heurísticos si la interfaz los distingue de una recomendación agronómica validada.

La comparación territorial y la predicción parcelaria deberán permanecer deshabilitadas hasta completar una validación espacial independiente.

## Criterio de éxito

El proyecto estará listo para producción exploratoria cuando un modelo seleccionado supere baselines simples en evaluación temporal prospectiva, mantenga trazabilidad reproducible, detecte entradas fuera de dominio y sea consumido por React sin falsificar su tipo o procedencia. Si no supera el baseline, el pipeline debe conservar los resultados como investigación y no reemplazar el modelo activo.

<!-- PAGEBREAK -->

# Arquitectura objetivo

| Capa | Responsabilidad | Salida principal |
| --- | --- | --- |
| Ingesta | Descargar y versionar NASS clima histórico y proyecciones CMIP6 | Archivos crudos inmutables y manifiestos |
| Curación | Emparejar condado año clima suelo y rendimiento | Panel canónico validado |
| Entrenamiento | Comparar baselines modelos tabulares y MLP pequeña | Modelo candidato y métricas prospectivas |
| Registro | Guardar artefacto esquema hashes normalización y dominio | Paquete versionado de modelo |
| Inferencia FastAPI | Validar entradas predecir intervalo y detectar extrapolación | Respuesta JSON con procedencia |
| Simulador | Ejecutar balance hídrico y cálculos derivados | Serie diaria identificada como determinista |
| Frontend React | Mostrar resultado fuente incertidumbre y limitaciones | Interfaz auditable |

El servicio de inferencia debe exponer una interfaz neutral. El nombre `PinnInference` debe reemplazarse gradualmente por `YieldInferenceService`. El backend podrá cargar un artefacto de scikit-learn o PyTorch sin cambiar el contrato de negocio.

# Estrategias de implementación

## Ruta A con los archivos actuales

Esta ruta permite construir una versión regional en poco tiempo. El entrenamiento debe reducir el dataset a 36 observaciones anuales y eliminar la falsa multiplicación de unidades por escenario. Se compararán modelos simples y se informará que las proyecciones posteriores a 2025 son extrapolaciones.

La ruta A sirve para estabilizar el pipeline, el registro, la API, los tests y el frontend. No habilita predicción por condado, manejo agronómico aprendido ni priorización territorial.

## Ruta B recomendada con las fuentes actuales

Esta ruta vuelve a descargar o reconstruir los datos NASS preservando estado, condado y FIPS. Después agrega clima histórico por condado-año y, cuando sea posible, propiedades edáficas reales. Así se recuperan miles de unidades observacionales con variación espacial y temporal.

El modelo aprende la relación entre clima histórico y rendimiento observado. Las proyecciones futuras se obtienen aplicando exactamente la misma ingeniería de variables a cada miembro CMIP6. Los SSP no se usan como etiquetas de entrenamiento ni se replica el rendimiento histórico como si hubiera ocurrido bajo tres futuros distintos.

## Ruta C para un gemelo diario calibrado

Esta ruta requiere datasets adicionales de humedad del suelo, biomasa, LAI, fenología, riego, nitrógeno y rendimiento a nivel de parcela o ensayo. No forma parte del reentrenamiento inicial. Debe tratarse como una línea posterior de investigación y validación.

| Ruta | Resultado | Uso permitido | Recomendación |
| --- | --- | --- | --- |
| A | Rendimiento regional anual | Demostración e investigación | Ejecutar primero para estabilizar el sistema |
| B | Rendimiento por condado con clima histórico y CMIP6 | Exploración regional con validación espacial | Objetivo principal |
| C | Estados diarios y respuesta a manejo aprendida | Gemelo parcelario sujeto a datos y validación | Trabajo futuro |

# Fase 0 congelar y documentar la línea base

## Objetivo

Preservar el checkpoint, datasets, métricas y comportamiento actual para que toda mejora pueda compararse y revertirse.

## Actividades

1. Crear una etiqueta Git para la versión actual y registrar el commit de referencia.
2. Calcular SHA-256 de los CSV, checkpoint, metadata y artefactos Q1.
3. Guardar las respuestas de `/api/model/status` y `/api/simulate` para un conjunto fijo de casos.
4. Ejecutar la suite de tests Python y TypeScript y conservar sus resultados.
5. Registrar el rendimiento actual en holdout aleatorio y validación 2018 a 2025.
6. Crear un manifiesto de dependencias y semillas.

## Entregables

- `reproducibility/baseline_v2_manifest.json`
- Casos de inferencia dorados en `tests/fixtures/model_v2`
- Etiqueta o rama de respaldo de producción
- Informe comparativo inicial

## Criterios de aceptación

- El checkpoint actual puede restaurarse sin depender de archivos externos no versionados.
- Los hashes y métricas se reproducen en una ejecución limpia.
- Existe un procedimiento de rollback documentado.

# Fase 1 definir el contrato canónico de datos

## Objetivo

Establecer una fila observacional que conserve identidad espacial, tiempo, variables predictoras y target sin duplicación artificial.

## Esquema mínimo recomendado

| Campo | Tipo | Regla |
| --- | --- | --- |
| `year` | entero | Año de cosecha observado |
| `state_fips` | texto | Identificador estable del estado |
| `county_fips` | texto | Identificador estable del condado |
| `state_name` | texto | Etiqueta informativa |
| `county_name` | texto | Etiqueta informativa |
| `latitude` `longitude` | decimal | Centroide o geometría de referencia documentada |
| `yield_bu_acre` | decimal | Target NASS limpio |
| `season_temp_mean_c` | decimal | Clima histórico de la estación agrícola |
| `season_tmax_mean_c` | decimal | Máxima media estacional |
| `season_precip_mm` | decimal | Precipitación acumulada |
| `gdd` | decimal | Grados día con fórmula versionada |
| `cdd` | decimal | Días secos consecutivos con umbral versionado |
| `heat_days_30c` | entero | Días sobre 30 grados Celsius |
| `heat_days_35c` | entero | Días sobre 35 grados Celsius |
| `vpd_mean_kpa` | decimal | Si la fuente permite calcularlo |
| `soil_source` | texto | Fuente del perfil edáfico cuando exista |
| `data_quality_flags` | texto | Ausencias interpolación y anomalías |

## Reglas obligatorias

- Una observación histórica tendrá un único target.
- Los SSP futuros no duplicarán targets históricos.
- Toda imputación incluirá una bandera.
- Las unidades se convertirán en una sola etapa reproducible.
- Los límites de la estación agrícola se definirán por región o mediante una regla documentada.
- Las columnas categóricas usarán códigos estables además de nombres.

## Archivos que deben cambiar

- `backend/training/dataset.py` para abandonar la mediana anual como dataset principal.
- `backend/training/config.py` para declarar esquema, columnas y versiones.
- `backend/data/nass.py` para preservar FIPS y atributos espaciales.
- `backend/data/nex_gddp.py` y `backend/data/chirps.py` para producir agregados por unidad espacial.

## Criterios de aceptación

- Una prueba detecta duplicación del mismo target bajo SSP distintos.
- Cada fila puede trazarse hasta un registro NASS y archivos climáticos concretos.
- El panel incluye un diccionario de datos y un reporte de calidad.

# Fase 2 reconstruir el panel histórico

## Paso 1 recuperar rendimiento NASS

Ejecutar el extractor en modo real con una clave NASS válida y `CERESPINN_DRY_RUN=0`. La descarga debe preservar año, estado, condado, FIPS, unidad, descripción de la variable y valor original. Los registros deben almacenarse como artefactos crudos inmutables antes de la limpieza.

## Paso 2 normalizar rendimiento

Convertir valores a numérico, resolver símbolos de supresión, unificar unidades y eliminar duplicados exactos. No se deben combinar condados hasta después de crear el panel. Los outliers no deben eliminarse automáticamente; se marcarán para revisión y se compararán reglas robustas.

## Paso 3 construir clima histórico

Para el periodo observado se debe utilizar clima histórico, no plantillas SSP. Agregar temperatura, precipitación, GDD, CDD y extremos para la estación de cultivo de cada condado-año. Si NEX-GDDP histórico no cubre todos los años con calidad suficiente, se debe incorporar una fuente observacional o de reanálisis compatible y documentar el cambio.

## Paso 4 incorporar proyecciones

Procesar CMIP6 por escenario, modelo climático, condado y año futuro. Conservar el identificador del GCM. No resumir todos los modelos antes de inferencia. La distribución entre miembros se utilizará para cuantificar incertidumbre climática.

## Paso 5 incorporar suelo cuando sea verificable

No usar los cuatro perfiles codificados del frontend como evidencia espacial. Si se incorpora suelo, cada condado o geometría debe enlazarse a una fuente externa documentada y a variables que tengan cobertura consistente. La primera versión puede excluir suelo si la cobertura no es adecuada.

## Paso 6 producir el panel canónico

Guardar el panel en Parquet para preservar tipos y reducir tamaño. Crear además una muestra CSV legible y un manifiesto JSON con hashes, fuentes, periodo, número de condados, años, porcentaje de datos faltantes y transformaciones.

## Criterios de aceptación

- No existen filas con el mismo condado, año y target repetidas por escenario.
- La cobertura temporal y espacial se publica por variable.
- Se identifican explícitamente años y condados sin clima suficiente.
- Las proyecciones CMIP6 se almacenan separadas del dataset histórico de entrenamiento.

# Fase 3 ingeniería de variables

## Variables permitidas para el primer modelo

El primer modelo utilizará solo variables disponibles tanto en el entrenamiento histórico como en la inferencia futura. Se priorizarán acumulados y extremos estacionales. El año podrá incluirse como tendencia tecnológica, pero deberá compararse contra un modelo sin año para medir cuánto desempeño procede de la tendencia y cuánto del clima.

## Variables que deben excluirse inicialmente

- Etiqueta SSP como predictor directo.
- CO2 si solo tiene tres valores de plantilla y no una serie histórica coherente.
- Riesgo de ola de calor codificado por escenario.
- `seasonal_cdd` constante.
- Variables de manejo sin observaciones asociadas.
- Identificadores textuales de condado sin una estrategia validada de codificación.

## Prevención de fuga de información

Las estadísticas de normalización, imputación, selección de variables y codificación se ajustarán solo con el conjunto de entrenamiento dentro de cada fold. Las transformaciones deben formar parte de un `Pipeline` de scikit-learn o equivalente para evitar aplicar información del periodo de prueba.

## Diagnósticos requeridos

- Distribución y cobertura por variable.
- Matriz de correlaciones y varianza.
- Dependencia con el año.
- Comparación de clima histórico y clima futuro para detectar extrapolación.
- Importancia por permutación calculada solo en validación.
- Pruebas de estabilidad ante exclusión de una variable.

# Fase 4 diseñar la validación

## División temporal principal

La evaluación principal debe simular el uso futuro. Un diseño inicial conservará 1990 a 2017 para entrenamiento y 2018 a 2025 para prueba final. Durante desarrollo se utilizará validación rolling-origin dentro de 1990 a 2017.

## Validación espacial

Cuando exista el panel condado-año, se reservarán estados o grupos de condados completos. El modelo no debe ver la misma unidad espacial en entrenamiento y prueba para la evaluación espacial. Se reportarán por separado desempeño temporal, espacial y espacio-temporal.

## Baselines obligatorios

1. Media histórica de entrenamiento.
2. Rendimiento del año anterior cuando esté disponible.
3. Tendencia lineal por año.
4. Ridge con variables climáticas.
5. Random Forest o HistGradientBoosting regularizado.

Un modelo neuronal solo podrá seleccionarse si mejora consistentemente estos baselines en los periodos y territorios reservados.

## Métricas

| Métrica | Uso |
| --- | --- |
| MAE kg por hectárea | Error típico interpretable |
| RMSE kg por hectárea | Penalización de errores grandes |
| R2 | Comparación con variabilidad del conjunto de prueba |
| Sesgo medio | Tendencia a sobreestimar o subestimar |
| Cobertura del intervalo | Proporción dentro del intervalo predictivo |
| Anchura del intervalo | Utilidad de la incertidumbre reportada |
| Error por región y cuantil | Equidad y estabilidad geográfica |

## Regla de promoción

El candidato debe mejorar el baseline operativo en MAE y RMSE sobre el holdout temporal y no degradarse de forma material en la validación espacial. El R2 prospectivo debe ser positivo para declarar habilidad predictiva frente a una referencia constante. Si no cumple, el sistema conservará el modelo como experimental y mostrará esa clasificación.

No se debe ajustar el modelo después de observar repetidamente el conjunto 2018 a 2025. Si se usa para decisiones de arquitectura, será necesario reservar un nuevo conjunto final o aplicar validación anidada.

# Fase 5 entrenar y seleccionar modelos

## Experimento A modelos simples

Entrenar regresión lineal, Ridge y Elastic Net con un pipeline completo de imputación, escalado y estimación. Estos modelos establecen una referencia interpretable y permiten detectar si la señal principal es solo tendencia temporal.

## Experimento B modelos de árboles

Entrenar Random Forest, Extra Trees y HistGradientBoosting con límites de profundidad, tamaño mínimo de hoja y búsqueda de hiperparámetros dentro de los folds temporales. Los árboles no deben validarse mediante KFold aleatorio sobre filas mezcladas.

## Experimento C red neuronal pequeña

Entrenar una MLP pequeña solo después de establecer baselines. La arquitectura debe ser proporcional al número de unidades independientes. Se probarán dropout, weight decay y early stopping. La regularización monotónica puede conservarse como experimento, pero deberá describirse como restricción de forma y no como residual físico.

## Selección

La selección se realizará por una tabla predefinida que combine MAE temporal, RMSE temporal, sesgo, estabilidad entre seeds, desempeño espacial y cobertura de intervalos. El nombre del modelo no tendrá peso en la decisión.

## Reproducibilidad

Cada corrida registrará commit, hash del dataset, seed, versiones de dependencias, hiperparámetros, duración, métricas por fold y ruta del artefacto. Las mejores corridas se guardarán en un registro de modelos inmutable.

## Entregables

- `backend/training_v3` o refactor equivalente
- Tabla comparativa de modelos
- Predicciones out of fold
- Reporte de errores por año y región
- Artefacto candidato no promovido

# Fase 6 incertidumbre y detección de extrapolación

## Incertidumbre del modelo

Calibrar intervalos sobre predicciones out of fold. Puede utilizarse conformal prediction o un ensamble de seeds si se demuestra cobertura adecuada. El intervalo debe reflejar incertidumbre del modelo y no confundirse con dispersión climática.

## Incertidumbre climática

Ejecutar inferencia para cada miembro GCM y escenario disponible. Reportar mediana, cuartiles y rango del ensamble real. El frontend no debe mostrar “32 modelos” si no existen 32 artefactos procesados en la solicitud.

## Fuera de dominio

Guardar en metadata mínimos, máximos, cuantiles y distribución de cada variable de entrenamiento. La inferencia marcará una entrada como extrapolación cuando exceda el dominio configurado. También se evaluará distancia multivariable mediante un método sencillo y reproducible.

## Respuesta esperada

Una respuesta futura debe distinguir:

- Intervalo por incertidumbre del modelo.
- Dispersión entre GCM.
- Bandera de extrapolación.
- Alcance espacial y temporal validado.

# Fase 7 empaquetar el modelo

## Contenido del paquete

El artefacto de producción incluirá el estimador, pipeline de transformación, esquema de entrada, metadata, hashes, métricas, dominio de variables y ejemplos dorados. Para scikit-learn puede utilizarse `joblib` con versiones fijadas. Para PyTorch se conservarán pesos y configuración explícita.

## Metadata mínima

| Campo | Contenido |
| --- | --- |
| `model_name` | Nombre neutral sin afirmar PINN |
| `model_version` | Versión semántica |
| `framework` | scikit-learn o PyTorch |
| `dataset_sha256` | Hash del panel de entrenamiento |
| `feature_schema_version` | Versión del contrato |
| `train_period` | Periodo usado para ajuste |
| `validation_period` | Periodo prospectivo |
| `geographic_scope` | Región o condados cubiertos |
| `metrics` | Temporal espacial e intervalos |
| `training_commit` | Commit de código |
| `created_at` | Fecha UTC |
| `limitations` | Restricciones de uso |

## Promoción atómica

El modelo nuevo se guardará con un nombre versionado. Un alias o archivo de manifiesto señalará la versión activa. La promoción cambiará el alias solo después de superar tests. El checkpoint anterior permanecerá disponible para rollback.

# Fase 8 integrar FastAPI

## Refactor del servicio

Crear una interfaz `YieldModelAdapter` con métodos para cargar, validar esquema, predecir y devolver incertidumbre. Implementar adaptadores separados para el checkpoint actual y el nuevo modelo. `YieldInferenceService` seleccionará el adaptador desde configuración.

## Cambios en el endpoint

`POST /api/simulate` continuará componiendo la predicción anual con el simulador diario. La respuesta separará cada procedencia. No se reutilizará `inference_mode=pinn` para un modelo que no sea PINN.

## Contrato propuesto

```json
{
  "inference_mode": "trained_ml",
  "model_name": "CeresYield",
  "model_version": "3.0.0",
  "model_verified": true,
  "prediction_scope": "county_annual",
  "model_data_source": "USDA NASS plus historical climate",
  "dataset_sha256": "hash",
  "projected_yield_kg_ha": 9200,
  "prediction_interval_90": {
    "lower_kg_ha": 7800,
    "upper_kg_ha": 10600
  },
  "is_extrapolation": false,
  "extrapolated_features": [],
  "component_provenance": {
    "yield": "trained_model",
    "daily_records": "deterministic_water_balance",
    "economics": "derived_formula",
    "management_effect": "not_learned"
  },
  "daily_records": []
}
```

## Validación de entrada

El backend rechazará combinaciones imposibles, valores faltantes y unidades incorrectas. Para datos fuera del dominio podrá responder con predicción marcada como extrapolación o rechazarla según la severidad. La decisión deberá ser configurable y quedar registrada.

## Compatibilidad

Durante la transición se mantendrá el adaptador v2 y se agregará un parámetro interno para ejecutar v2 y v3 en paralelo. El frontend recibirá v3 solo cuando el contrato esté completo. No se ejecutará fallback sintético silencioso en producción.

# Fase 9 integrar React

## Cambios en el cliente API

Modificar `src/services/api.ts` para validar `model_verified`, `model_version`, alcance, intervalo y procedencia, en vez de exigir `inference_mode === pinn`. La producción seguirá rechazando respuestas incompletas o no verificadas.

## Cambios de presentación

El Dashboard identificará el rendimiento como salida del modelo entrenado. Humedad, biomasa, CWSI y economía llevarán etiquetas de simulación o cálculo derivado. La interfaz mostrará intervalo predictivo y advertencia de extrapolación cerca del rendimiento, no en una nota separada.

## Cambios de configuración

Crear una sola fuente de forzamiento climático compartida por configuración, API y simulador. Al cambiar escenario o año se actualizarán los valores enviados. El frontend no mostrará variables que no coincidan con el request efectivo.

## Módulos que deben ajustarse

- Dashboard: retirar el ensamble GCM fijo y leer intervalos reales.
- What-if: comparar respuestas verificadas sin declarar un ganador prescriptivo.
- Adaptación: fusionar con What-if y marcar efectos no aprendidos.
- MLOps: mostrar metadata del modelo v3.
- Validación: leer artefactos del modelo activo y no sustitutos heredados.
- Comparación de campos: habilitar solo si el alcance espacial está validado.
- Reportes: exportar versión, hash, intervalo y procedencia.

# Fase 10 pruebas

## Pruebas de datos

- Esquema, tipos, unidades y rangos.
- Unicidad condado-año.
- Ausencia de targets duplicados por SSP.
- Cobertura temporal y espacial mínima.
- Detección de cambios de distribución.
- Hash reproducible del dataset.

## Pruebas de entrenamiento

- Separación temporal sin solapamiento.
- Transformaciones ajustadas solo con entrenamiento.
- Reproducibilidad con seed fija.
- Comparación automática contra baselines.
- Validación de metadata y dominio.
- Fallo obligatorio cuando solo está disponible el fallback sintético para una corrida de producción.

## Pruebas de inferencia

- Carga del artefacto exacto.
- Igualdad entre predicción offline y API.
- Unidades correctas.
- Intervalos ordenados y finitos.
- Detección de extrapolación.
- Rechazo de features faltantes.
- Pruebas doradas de regresión.

## Pruebas de integración

- React envía exactamente los forzantes mostrados.
- Producción no acepta fallback local.
- El badge presenta modelo versión y fuente correctos.
- PDF y XLSX incluyen procedencia.
- La validación usa el modelo activo.
- Rollback restaura v2 sin migraciones destructivas.

## Pruebas científicas

- Métricas temporales y espaciales calculadas sobre unidades independientes.
- Comparación de predicciones contra observaciones por año y región.
- Sensibilidad coherente con las features reales del modelo.
- Intervalos evaluados por cobertura.
- Escenarios futuros ejecutados por miembro GCM real.

# Fase 11 despliegue progresivo

## Etapa de sombra

Ejecutar v2 y v3 para las mismas solicitudes sin mostrar v3 al usuario. Registrar diferencias, tiempos, errores, extrapolaciones y disponibilidad. No guardar información personal ni entradas sensibles en logs.

## Etapa de revisión

Revisar una muestra de resultados con perfiles científicos y de ingeniería. Verificar que los cambios se explican por features y no por errores de unidades o transformación.

## Etapa canaria

Habilitar v3 para una fracción controlada de tráfico o mediante una bandera interna. Mantener monitoreo de errores, latencia y porcentaje de extrapolaciones.

## Promoción

Cambiar el alias del modelo activo cuando se cumplan los criterios técnicos y científicos. Conservar v2 durante una ventana de rollback. La UI y los reportes deberán mostrar inmediatamente la versión activa.

## Monitoreo

- Disponibilidad y latencia de inferencia.
- Distribución de variables de entrada.
- Porcentaje de solicitudes fuera de dominio.
- Distribución de predicciones por región y escenario.
- Errores de esquema.
- Deriva cuando se incorporen nuevos rendimientos observados.

# Cambios propuestos por archivo

| Ruta | Cambio principal |
| --- | --- |
| `backend/data/nass.py` | Preservar FIPS estado condado unidad y trazabilidad |
| `backend/data/nex_gddp.py` | Agregar clima por geografía año escenario GCM y variable |
| `backend/data/chirps.py` | Generar precipitación histórica por unidad espacial |
| `backend/training/dataset.py` | Sustituir expansión SSP por panel histórico canónico |
| `backend/training/config.py` | Versionar features esquema splits y rutas |
| `backend/training/train.py` | Entrenar pipeline v3 registrar baselines e incertidumbre |
| `backend/training/pinn.py` | Mantener solo para compatibilidad o renombrar el modelo experimental |
| `backend/inference.py` | Separar adaptador de modelo y simulador determinista |
| `backend/app.py` | Exponer contrato neutral y metadata completa |
| `backend/validation.py` | Leer artefactos del modelo activo y retirar sustitutos |
| `src/services/api.ts` | Validar modelo verificado en vez de exigir PINN |
| `src/components/MainDashboard.tsx` | Mostrar intervalo procedencia y extrapolación |
| `src/components/SimulationConfig.tsx` | Sincronizar escenario año y forzantes enviados |
| `src/components/MLOpsDashboard.tsx` | Mostrar dataset hash alcance y métricas prospectivas |
| `src/components/ValidationReport.tsx` | Presentar validación temporal espacial y cobertura reales |
| `tests` | Agregar pruebas de datos modelo API frontend y rollback |

# Plan de trabajo indicativo

La duración depende del acceso a APIs, cobertura climática y recursos de cómputo. El siguiente orden es más importante que las fechas.

| Bloque | Trabajo | Duración indicativa | Dependencia |
| --- | --- | --- | --- |
| 1 | Línea base contratos y pruebas | 1 semana | Ninguna |
| 2 | Ruta A regional y API neutral | 1 a 2 semanas | Bloque 1 |
| 3 | Reextracción NASS y clima espacial | 2 a 4 semanas | Acceso a fuentes |
| 4 | Panel canónico y QA | 1 a 2 semanas | Bloque 3 |
| 5 | Modelos validación e incertidumbre | 2 a 3 semanas | Bloque 4 |
| 6 | Integración backend y frontend | 1 a 2 semanas | Bloque 5 |
| 7 | Sombra revisión y promoción | 1 a 2 semanas | Bloque 6 |

Con trabajo secuencial, la ruta B requiere aproximadamente ocho a doce semanas. La ruta A puede quedar integrada antes, siempre que se mantenga su clasificación regional exploratoria.

# Roles requeridos

| Rol | Responsabilidad |
| --- | --- |
| Ingeniería de datos | Extracción geográfica panel calidad y manifiestos |
| Ciencia de datos | Features modelos validación incertidumbre y errores |
| Revisión científica | Alcance agronómico diseño de variables y afirmaciones |
| Backend | Adaptadores contratos registro despliegue y observabilidad |
| Frontend | Procedencia incertidumbre configuración y módulos |
| Calidad | Tests reproducibilidad seguridad y criterios de promoción |

# Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Clima histórico sin cobertura consistente | El panel no puede entrenarse de forma homogénea | Definir una fuente observacional alternativa y documentar el cambio |
| Pocos años independientes | Alta varianza y extrapolación | Usar panel espacial modelos simples regularización e intervalos |
| Fuga por filas repetidas | Métricas infladas | Dividir por año y geografía antes de cualquier transformación |
| SSP correlacionado con CO2 y riesgo | Efectos no identificables | No entrenar con etiquetas SSP replicadas |
| Diferencias de unidades | Predicciones físicamente absurdas | Esquema tipado validaciones y tests dorados |
| Intervalos demasiado estrechos | Falsa confianza | Evaluar cobertura prospectiva y mostrar anchura |
| Deriva futura | Degradación silenciosa | OOD monitoreo y reentrenamiento versionado |
| Frontend mezcla procedencias | El usuario interpreta simulación como ML | Etiquetas por componente y contrato obligatorio |
| Promoción de un modelo peor | Regresión científica | Baselines gates etapa sombra y rollback atómico |

# Criterios de terminado

El trabajo estará terminado cuando se cumplan todos los puntos siguientes:

1. Existe un panel histórico versionado sin replicación de targets por SSP.
2. La unidad espacial y temporal es explícita y trazable.
3. El modelo activo supera el baseline acordado en validación prospectiva o permanece marcado como experimental.
4. La evaluación espacial se reporta antes de habilitar comparaciones territoriales.
5. Cada predicción incluye intervalo, versión, hash, alcance y bandera de extrapolación.
6. FastAPI carga el artefacto versionado y reproduce las predicciones offline.
7. React acepta un modelo ML verificado sin llamarlo PINN.
8. El frontend distingue salida aprendida, simulación determinista y cálculo derivado.
9. Producción no utiliza fallback sintético o local de manera silenciosa.
10. Los reportes y la pantalla de validación leen métricas del modelo activo.
11. Las pruebas de datos entrenamiento inferencia integración y rollback pasan.
12. El modelo anterior puede restaurarse mediante un cambio de alias documentado.

# Primera iteración recomendada

La primera iteración debe completar Fase 0 y Ruta A sin reemplazar todavía el modelo de producción. Su objetivo será construir la interfaz neutral de inferencia, corregir la validación temporal, eliminar la replicación SSP y comparar Ridge Random Forest HistGradientBoosting y una MLP pequeña sobre las 36 unidades anuales.

En paralelo debe iniciarse la Ruta B, comenzando por preservar FIPS en NASS y producir clima histórico por condado-año. El modelo v3 solo se promoverá cuando esa ruta demuestre habilidad prospectiva y, para funciones territoriales, validación espacial independiente.

# Referencias internas

- `data/README.md`
- `backend/training/dataset.py`
- `backend/training/config.py`
- `backend/training/train.py`
- `backend/training/pinn.py`
- `backend/inference.py`
- `backend/app.py`
- `docs/q1_artifacts/temporal/temporal_validation_1990_2017_to_2018_2025.json`
- `docs/q1_artifacts/same_split_baseline_comparison.csv`
- `docs/auditoria_modelo_y_modulos_frontend_2026-09-25.md`
