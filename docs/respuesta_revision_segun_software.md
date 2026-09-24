# Respuesta técnica a las observaciones, basada en el software ejecutable

## Alcance de la respuesta

La respuesta se preparó contrastando el manuscrito con el *checkpoint* `backend/models/cerespinn_pinn.pt`, sus metadatos, el código de entrenamiento, el motor de inferencia y los datos reconstruibles del experimento. Las métricas nuevas se obtuvieron con `scripts/generate_q1_revision_artifacts.py`, usando el mismo *split* agrupado por año almacenado con el modelo: 28 años de entrenamiento y ocho años independientes de prueba. No se atribuyen al sistema procesos, métricas o capacidades que no estén implementados.

## Qué hace realmente el software

El flujo decisional actual tiene cinco pasos:

1. La red recibe siete variables: año, anomalía térmica, anomalía de precipitación, CO₂, riesgo de ola de calor, precipitación estacional y días secos consecutivos.
2. Un perceptrón multicapa de cuatro capas ocultas y dos cabezas genera un rendimiento basal y un indicador hídrico auxiliar. La pérdida de entrenamiento impone error supervisado, regularización L2 y monotonicidad respecto de temperatura y precipitación.
3. El rendimiento basal se modifica mediante multiplicadores fijos de variedad, riego, nitrógeno y CO₂. Esas reglas permiten comparar escenarios, pero no constituyen una optimización aprendida.
4. Un simulador diario posterior calcula fenología, evapotranspiración, estrés y almacenamiento hídrico en tres reservorios de suelo. Este módulo no es diferenciable respecto de la red y no resuelve la ecuación de Richards.
5. La fecha de siembra y el perfil edáfico modifican las trayectorias diarias, pero no retroalimentan el rendimiento basal de la red. Por ello, el sistema sirve actualmente para exploración *what-if*, no para prescripción agronómica autónoma.

---

## 1. Naturaleza real de la PINN y ecuación de pérdida

**Respuesta al evaluador.** Aceptamos la observación. La versión evaluada no es una PINN de Richards en sentido estricto, sino una red neuronal físicamente regularizada incorporada en un gemelo digital híbrido. La función `physics_loss` solamente penaliza dos violaciones de monotonicidad: que el rendimiento aumente con la anomalía térmica y que disminuya al aumentar la precipitación estacional. El término de rango del indicador hídrico es nulo por construcción porque la cabeza correspondiente termina en una activación sigmoidal. La regularización L2 se añade en el ciclo de entrenamiento. No existen términos de residuo de Richards ni de condiciones de frontera en la función de pérdida ejecutada.

La formulación que debe permanecer en el manuscrito es:

\[
\mathcal{L}_{total}=\mathcal{L}_{data}+\lambda_{mono}\mathcal{L}_{mono}+\lambda_{reg}\lVert\theta\rVert_2^2,
\]

\[
\mathcal{L}_{data}=\frac{1}{N}\sum_{i=1}^{N}(y_i-\hat y_i)^2,
\]

\[
\mathcal{L}_{mono}=\mathbb{E}\left[\operatorname{ReLU}\left(\frac{\partial \hat y}{\partial \Delta T}\right)\right]
+\mathbb{E}\left[\operatorname{ReLU}\left(-\frac{\partial \hat y}{\partial P_s}\right)\right]+\mathcal{L}_{range},
\]

con \(\lambda_{mono}=0.5\) y \(\lambda_{reg}=10^{-4}\). Aquí, \(P_s\) es la precipitación estacional.

**Decisión editorial.** Se eliminan las expresiones \(\mathcal{L}_{Richards}\), \(\mathcal{L}_{boundary}\), “pérdida residual de la PDE” y “conservación física de masa” como resultados del modelo entrenado. El balance hídrico diario se describirá como un balance estratificado de reservorios inspirado en procesos hidrológicos, no como una solución de Richards.

**Hallazgo que todavía debe corregirse en el producto.** El backend aún devuelve valores constantes con los nombres `pde_residual_richards_loss`, `boundary_condition_loss` y `physics_conservation_error_percent`; el frontend además conserva curvas MLOps simuladas. Esos valores son marcadores de demostración, no mediciones. Deben retirarse de la API, del reporte PDF y del tablero antes de afirmar que la contradicción quedó resuelta también en el software.

## 2. Métricas de 24 filas frente a ocho años independientes

**Respuesta al evaluador.** Aceptamos la observación. Las 24 filas corresponden a las ocho anualidades retenidas replicadas en tres escenarios. Como las tres filas de cada año comparten el mismo rendimiento observado, la unidad experimental independiente es el año. Se reportarán ambos niveles y se identificará cuál constituye el resultado principal.

- Sobre 24 filas año–escenario: RMSE = 717.4 kg ha⁻¹, MAE = 618.3 kg ha⁻¹ y R² = 0.8225.
- Tras promediar las tres predicciones de cada uno de los ocho años: RMSE = 712.1 kg ha⁻¹, MAE = 604.2 kg ha⁻¹ y R² = 0.8251.

**Texto corregido para el resumen.** “Al agregar por año las predicciones correspondientes a los ocho años independientes reservados para prueba, CeresPINN alcanzó RMSE = 712.1 kg ha⁻¹, MAE = 604.2 kg ha⁻¹ y R² = 0.8251; sobre las 24 filas año–escenario sin agregación, los valores fueron 717.4 kg ha⁻¹, 618.3 kg ha⁻¹ y 0.8225, respectivamente.”

## 3. Preguntas de investigación e hipótesis

**Respuesta al evaluador.** Aceptamos la observación. Las hipótesis no se redefinirán como preguntas. Se incorporan las siguientes preguntas explícitas:

- **RQ1.** ¿Qué capacidad predictiva presenta CeresPINN sobre años no utilizados durante el entrenamiento y cómo se compara con líneas base evaluadas sobre el mismo *split*?
- **RQ2.** ¿Cómo responde el prototipo ante el forzamiento parametrizado como SSP5-8.5 hacia 2050?
- **RQ3.** ¿Cómo modifican la fecha de siembra, la duración del cultivar y el régimen de riego las salidas del gemelo digital?
- **RQ4.** ¿Qué variables dominan la sensibilidad global de la salida de rendimiento dentro de los rangos evaluados?
- **RQ5.** ¿En qué medida la implementación actual representa diferencias debidas a perfiles edáficos y localización?

H0 y H1 se mantienen como hipótesis del protocolo original, pero se separan y se declaran no contrastadas adecuadamente: SSP2-4.5 no formó parte del entrenamiento y la adaptación se implementó mediante multiplicadores deterministas.

## 4. Baseline experimental y ablación de la regularización física

**Respuesta al evaluador.** Aceptamos la observación y ejecutamos líneas base con exactamente los mismos 28 años de entrenamiento, ocho años de prueba y semilla 42. También se ejecutó una ablación con la misma arquitectura neuronal, pero con \(\lambda_{mono}=0\).

| Modelo | RMSE (kg ha⁻¹) | MAE (kg ha⁻¹) | R² |
|---|---:|---:|---:|
| Regresión lineal | **642.2** | 557.2 | **0.8578** |
| Ridge, α = 1 | 644.9 | **549.8** | 0.8566 |
| CeresPINN | 712.1 | 604.2 | 0.8251 |
| MLP idéntico, sin pérdida física | 984.0 | 817.7 | 0.6661 |
| Random Forest | 1,210.0 | 890.2 | 0.4950 |

**Interpretación.** La regularización de monotonicidad mejoró el MLP de la misma arquitectura: redujo el RMSE 27.6 % y elevó R² en 0.1590. Sin embargo, CeresPINN no superó a la regresión lineal ni a Ridge en este conjunto pequeño y fuertemente temporal. Por tanto, los resultados sugieren utilidad estabilizadora de la restricción dentro de la familia neuronal, pero no demuestran superioridad predictiva global. La inferencia causal sobre el aporte físico sigue limitada por una sola partición y una sola semilla; una versión posterior deberá repetir la ablación con múltiples semillas y validación temporal anidada.

## 5. “Optimización” frente a evaluación de escenarios

**Respuesta al evaluador.** Aceptamos la observación. El módulo no busca un óptimo, no estima una función objetivo y no utiliza búsqueda bayesiana, gradientes de decisión ni programación multiobjetivo. Evalúa configuraciones discretas mediante multiplicadores fijos: variedad 0.88/1.00/1.12 y riego 0.85/0.96/1.03/1.08/1.06, además de respuestas acotadas a nitrógeno y CO₂.

**Decisión editorial.** El título se cambia a **“3.3.4. Módulo de simulación de escenarios de manejo”**. En Resultados se hablará de comparación *what-if* y no de estrategia óptima. Las recomendaciones de manejo se describirán como heurísticas del prototipo, no como decisiones calibradas experimentalmente.

## 6. Eficiencia computacional

**Respuesta al evaluador.** Aceptamos la observación y eliminamos cualquier afirmación de aceleración en “órdenes de magnitud” frente a DSSAT o APSIM. En el equipo de desarrollo Windows 11, CPU, PyTorch con ocho hilos, un entrenamiento de 300 épocas sobre 84 filas tomó 31.8 s. En 2,000 inferencias escalares, después de calentamiento, la mediana fue 2.20 ms y el percentil 95 fue 4.66 ms. Estas mediciones prueban que la red es apta para interacción, pero no constituyen un benchmark contra modelos de procesos.

**Texto corregido.** “La inferencia escalar del *checkpoint* presentó una mediana de 2.20 ms en CPU y el entrenamiento de 300 épocas tomó 31.8 s en el entorno de desarrollo. Estas cifras demuestran viabilidad interactiva. No se realizó una comparación controlada con DSSAT, APSIM o AquaCrop; por tanto, no se afirma superioridad computacional frente a esos modelos.”

## 7. Prueba t, KS, bootstrap, Sobol y robustez

**Respuesta al evaluador.** Aceptamos la observación y reportamos todos los análisis que permanecen en Métodos. Sobre los ocho años independientes:

- Prueba *t* pareada entre rendimiento predicho y observado: \(t(7)=0.1734\), \(p=0.8672\).
- Sesgo medio: +46.6 kg ha⁻¹; tamaño del efecto pareado \(d_z=0.0613\).
- Kolmogorov–Smirnov: \(D=0.25\), \(p=0.9801\).
- IC bootstrap 95 % con 20,000 remuestreos: RMSE [465.9, 915.5] kg ha⁻¹; MAE [343.8, 862.5] kg ha⁻¹; R² [−0.1071, 0.9355].

El intervalo amplio de R² y el valor inferior negativo evidencian la incertidumbre causada por \(n=8\); un p-valor no significativo no demuestra equivalencia entre predicciones y observaciones.

El análisis Sobol auditado para temperatura, precipitación y CO₂ produjo índices de primer orden de 0.0175, 0.0050 y 0.9772, e índices totales de 0.0163, 0.0068 y 0.9810, respectivamente. La dominancia de CO₂ se interpreta como posible confusión entre CO₂, año y tendencia tecnológica. No se reporta un índice Sobol para CDD porque `seasonal_cdd` fue constante en el conjunto de entrenamiento del *checkpoint*.

Como prueba de robustez, ruido gaussiano con desviación estándar igual al 5 % de la desviación de entrenamiento aumentó el RMSE de las 24 filas solamente 0.51 % en 1,000 repeticiones. En contraste, imputar el año por su media elevó el RMSE 188.2 %, lo que confirma una dependencia temporal fuerte y limita la extrapolación causal.

## 8. IA generativa, conflictos, financiamiento, ética y disponibilidad

**Respuesta al evaluador.** Aceptamos la observación. Se sustituirán todos los marcadores por declaraciones completas. El siguiente texto puede utilizarse si refleja la situación de todos los autores:

### Declaración de uso de IA generativa

“Durante la preparación de este manuscrito se utilizó OpenAI Codex como apoyo para auditoría de código, elaboración de scripts reproducibles, revisión de consistencia metodológica y corrección lingüística. La herramienta no sustituyó la ejecución de experimentos ni la interpretación científica. Los autores revisaron el código, reprodujeron las métricas contra los artefactos del modelo y asumen responsabilidad íntegra por el contenido final.”

### Consideraciones éticas

“El estudio utilizó datos agronómicos y climáticos públicos y no involucró participantes humanos, animales, historias clínicas ni intervención experimental sobre seres vivos. Por ello, no requirió aprobación de un comité de ética. El prototipo no debe emplearse para decisiones automatizadas de crédito, seguro, asignación de agua o sanción.”

### Conflictos de interés y financiamiento

Estas dos declaraciones requieren confirmación expresa de todos los autores. Si son verdaderas, pueden redactarse así: “Los autores declaran no tener conflictos de interés” y “Esta investigación no recibió financiamiento específico de organismos públicos, comerciales o sin fines de lucro”. No deben insertarse sin validación del equipo autoral.

### Disponibilidad de código y datos

“El código fuente, el contenedor Docker, el *checkpoint*, los metadatos de entrenamiento, los datasets procesados, las pruebas, los scripts Q1 y los artefactos regenerables se encuentran en [David42024/CeresPINN](https://github.com/David42024/CeresPINN), bajo licencia MIT para el software. La reproducción científica completa se ejecuta sin credenciales mediante `python scripts/reproduce.py`; el mismo comando forma parte de GitHub Actions. `reproducibility/manifest.json` fija tamaños, conteos y SHA-256 de los insumos. Los datos de rendimiento proceden de [USDA NASS Quick Stats](https://quickstats.nass.usda.gov/) y los forzantes climáticos de [NASA NEX-GDDP-CMIP6](https://registry.opendata.aws/nex-gddp-cmip6/); su procedencia y condiciones se documentan en `data/README.md`. Los años, muestras de prueba y normalización del checkpoint permanecen en `backend/models/cerespinn_metadata.json`, y la evaluación temporal 1990–2017 → 2018–2025 está publicada en `docs/q1_artifacts/temporal/`.”

La disponibilidad es verificable desde un clon limpio: `python -m pip install --requirement requirements-repro.txt` seguido de `python scripts/reproduce.py`. No se requiere `NASS_API_KEY`, base de datos ni secretos de despliegue porque los insumos procesados exactos están versionados.

## 9. Figuras y tablas

**Respuesta al evaluador.** Aceptamos la observación. Las figuras deben proceder de artefactos reproducibles, no de cifras simuladas en el frontend. Se incorporarán:

1. Dispersión observado–predicho de los ocho años independientes, en kg ha⁻¹, con línea 1:1 y R² = 0.8251.
2. Tabla de líneas base con RMSE, MAE y R² sobre el mismo *split*.
3. Barras de escenarios de manejo para el caso Iowa–SSP5-8.5–2050: basal 13,331 kg ha⁻¹; siembra adelantada 13,331; ciclo corto 11,731; riego deficitario 75 % 14,303; combinación 12,587.
4. Índices Sobol para las tres variables con variación auditada: temperatura, precipitación y CO₂. No se añadirá CDD mientras sea constante.

Los datos fuente están en `docs/q1_artifacts/hindcast_independent_years.csv`, `same_split_baseline_comparison.csv`, `robustness_results.csv` y `q1_statistics.json`.

## 10. Redacción, notación y ecuaciones

**Respuesta al evaluador.** Aceptamos la observación. El manuscrito canónico utilizará `seasonal_precip_mm`, “frente”, “régimen deficitario”, “normalización estadística”, “siembra”, “riego suplementario”, “simulación” y “gemelos digitales”. Las citas múltiples se separarán con punto y coma. La pérdida supervisada se renderizará como:

\[
\mathcal{L}_{data}=\frac{1}{N}\sum_{i=1}^{N}(y_i-\hat y_i)^2.
\]

La corrección lingüística final se realizará después de estabilizar métodos, resultados, figuras y declaraciones, para evitar revisar texto que todavía pueda cambiar.

---

## Síntesis de decisiones

| Punto | Decisión basada en el software | Estado |
|---|---|---|
| Definición PINN/Richards | Red físicamente regularizada + simulador de reservorios; no Richards PINN | Texto corregido; UI/API aún requieren limpieza |
| Métricas 24 vs. 8 | Reportar ambas y usar ocho años como unidad independiente | Resuelto |
| RQ | Incorporar RQ1–RQ5; no convertir hipótesis en preguntas | Texto listo |
| Baselines | CeresPINN mejora al MLP, pero no a lineal/Ridge | Experimento ejecutado |
| Optimización | Renombrar a simulación de escenarios | Resuelto conceptualmente |
| Eficiencia | Reportar 31.8 s de entrenamiento y 2.20 ms de inferencia; sin comparación DSSAT/APSIM | Medido |
| Estadística | Informar t, KS, bootstrap, Sobol y robustez con n real | Ejecutado |
| Declaraciones | IA y ética listas; conflictos/financiamiento requieren confirmación | Parcial |
| Ciencia abierta | Repositorio y artefactos identificados; licencia OSI pendiente | Parcial |
| Figuras | Cuatro productos definidos con datos reproducibles | Datos listos |

La conclusión científicamente defendible es que CeresPINN funciona como prototipo híbrido e interactivo y que la monotonicidad mejora la red neuronal equivalente en este *split*. No puede afirmarse que resuelva Richards, que realice optimización de manejo, que supere todas las líneas base o que haya demostrado superioridad computacional frente a modelos de proceso.
