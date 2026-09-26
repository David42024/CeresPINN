# Auditoría crítica del paper de CeresPINN frente al repositorio

**Fecha de corte:** 2026-09-26  
**Paper:** `Texto pegado.txt`, SHA-256 `0069F2F51C0DBC55EF8A8AF27763B4B187665B1054B365B36F42B923460A31B7`, 342 líneas, sin paginación. Las referencias se dan por sección y línea.  
**Repositorio:** `HEAD 5df3da13c06a0382fad4038e5e6d22ea667b8978`.  
**Commit declarado por el paper:** `6c22e543b0fefbc498f5d811732974f48c1089c2`.

## 1. Resumen ejecutivo

1. La arquitectura científica descrita sí está versionada: MLP PyTorch de siete entradas, cuatro capas de 128 unidades, dos cabezas, regularización de monotonicidad y simulador diario determinista posterior.
2. Las cifras centrales del paper (RMSE 712.1, MAE 604.2 y R² 0.8251), los baselines, la ablación multi-semilla, Sobol y el caso Iowa 2050 continúan trazables a los artefactos Q1 del checkpoint v2.5.
3. La aplicación sí consume el checkpoint PyTorch entrenado cuando está presente; `YieldInferenceService` lo prioriza sobre los artefactos nuevos de scikit-learn. Sin embargo, después aplica multiplicadores deterministas de manejo y CO₂, por lo que el rendimiento final no es una salida pura de la red.
4. El repositorio incorporó modelos Ridge v3 y espacial v4, pero producción no los selecciona mientras `/api/validation` sí lee el metadato v4. Predicción y validación corresponden actualmente a modelos distintos.
5. El v4 tampoco corresponde al paper: usa nueve variables, datos condado-año y scikit-learn. Su metadato presenta una inconsistencia grave: anuncia R² temporal 0.9462 para `MLP_Small`, mientras `metrics_all_models.MLP_Small` registra R² −0.0063.
6. La selección React de escenario/año fue corregida y ahora actualiza los forzantes enviados. Persisten, no obstante, distintas parametrizaciones entre React, backend y Streamlit.
7. El commit fijado por el paper sigue sin contener el paquete de reproducibilidad que se le atribuye; tampoco hay un CSV versionado de exactamente 98 filas climáticas.
8. La evaluación prospectiva del checkpoint del artículo sigue siendo desfavorable (R² −0.8318) y debe cuantificarse en el cuerpo del manuscrito, no solo calificarse como “débil”.
9. El paper declara Gemini, PostgreSQL/PostGIS y un único motor híbrido, mientras el `HEAD` usa OpenAI, reporta SQLite y mantiene motores/modelos divergentes.
10. **Dictamen:** no enviar todavía. Debe congelarse un release del modelo exacto del paper, separar modelos experimentales, reparar la validación y corregir disponibilidad, datos y resultados prospectivos.

## 2. Tabla de concordancias

| ID | Dimensión | Elemento | Evidencia paper | Evidencia código | Comentario |
|---|---|---|---|---|---|
| C-01 | Arquitectura | Red aprendida y simulador determinista desacoplado | Introducción, l. 16; §3.3.2, ll. 52–54 | `backend/training/pinn.py:39-71`; `backend/inference.py:303-643` | La separación existe y el paper reconoce correctamente que los estados diarios no retroalimentan la red. |
| C-02 | Modelo | Siete entradas y orden del checkpoint | §3.3.1, ll. 33–35 | `backend/models/cerespinn_metadata.json:5-13`; `backend/inference.py:206-239` | Coincidencia para v2.5; no para v4 (D-02). |
| C-03 | Modelo | 4×128, Tanh, dropout 0.05 y dos cabezas | Tabla 1, ll. 66–105 | `backend/training/pinn.py:47-70`; `backend/models/cerespinn_metadata.json` | El checkpoint conserva esta arquitectura y 63,042 parámetros. |
| C-04 | Método | Regularización de signo, no Richards/EDP | Introducción, l. 16; §3.3.2, ll. 50–54 | `backend/training/pinn.py:76-115` | Penaliza gradientes de rendimiento con temperatura y precipitación; no resuelve Richards. |
| C-05 | Datos Q1 | 22,160 registros → 36 medianas anuales → 108 filas año–escenario | §3.2, ll. 27–28; §4.1, l. 154 | `backend/models/cerespinn_metadata.json` (`data_lineage`); `data/cerespinn_training_iowa.csv` | Coincide con el experimento v2.5. “108 de entrenamiento” debe corregirse a 108 totales (D-06). |
| C-06 | Partición Q1 | 28 años train y 8 test agrupados por año | §3.4.1, l. 125 | `backend/models/cerespinn_metadata.json` (`evaluation.split`); `docs/q1_artifacts/q1_statistics.json:3-43` | Coincidencia exacta para el checkpoint del paper. |
| C-07 | Métricas Q1 | RMSE 712.1, MAE 604.2, R² 0.8251 | Resumen, l. 7; §4.2, ll. 159–164 | `docs/q1_artifacts/q1_statistics.json:45-51` | Coinciden dentro del redondeo. |
| C-08 | Baselines/ablación | Lineal y Ridge mejores puntualmente; CeresPINN mejor que MLP equivalente | §4.2, ll. 164–170; §5.2, l. 193 | `docs/q1_artifacts/same_split_baseline_comparison.csv`; `docs/q1_artifacts/extended/multiseed_neural_summary.csv` | La conclusión prudente del paper está soportada por los artefactos Q1. |
| C-09 | Sensibilidad | Sobol dominado por CO₂ y fuerte confusión entre entradas | §4.5 y §5.6 | `docs/q1_artifacts/extended/sobol_checkpoint.csv`; `training_feature_correlations.csv` | Concordancia para el checkpoint v2.5; no debe extrapolarse al v4. |
| C-10 | Manejo | Iowa–SSP5-8.5–2050 y +7.29 % con riego 75 % | §4.3–4.4, ll. 173–178 | `docs/q1_artifacts/extended/management_scenarios.csv`; multiplicadores en `backend/inference.py:325-358` | El número se reproduce, pero es una regla determinista posterior, como admite el paper. |
| C-11 | UI | Cambio de escenario y año sincroniza los forzantes enviados | Afirmación general de aplicación interactiva, resumen y conclusiones | `src/components/SimulationConfig.tsx:73-95`; `src/services/api.ts:239-248` | Corrige la discrepancia de la auditoría anterior: T, P y CO₂ ya se actualizan en el estado enviado. |
| C-12 | Alcance | Límites de uso y ausencia de validación externa | §5.5–5.6; disponibilidad, l. 256 | `backend/inference.py:29-48`; avisos de alcance del frontend | El alcance exploratorio está codificado y descrito. |

## 3. Tabla de discrepancias

| ID | Dimensión | Elemento | Evidencia paper | Evidencia código | Tipo | Severidad | Impacto | Recomendación |
|---|---|---|---|---|---|---|---|---|
| D-01 | Consumo del modelo | Predicción y validación usan modelos distintos | Paper describe y evalúa exclusivamente el checkpoint PyTorch v2.5 | `backend/inference.py:283-295` prioriza `PinnAdapter`; `backend/validation.py:6-28` lee `cerespinn_spatial_v4_metadata.json` | Contradicción | **Crítico** | La aplicación valida un modelo distinto del que responde `/api/simulate`. | Introducir un registro de modelo activo único; inferencia, estado, validación y UI deben resolver el mismo `model_id`, hash y esquema. |
| D-02 | Estado de implementación | El nuevo modelo v4 no corresponde al paper | Paper: siete entradas, PyTorch, 4×128 y regularización monotónica | `backend/training/train_v4_spatial.py:44-74` usa nueve entradas y Ridge/RF/HGB/MLP 16×8 de scikit-learn; metadato v4 declara versión 4.0.0 | Contradicción | **Crítico** | Si v4 se considera “modelo actual”, arquitectura, datos, métricas y conclusiones del manuscrito quedan obsoletos. | Elegir: congelar v2.5 para el paper o reescribir/revalidar el paper para v4; no mezclar ambos. |
| D-03 | Métricas v4 | Metadato v4 internamente imposible/inconsistente | Paper exige trazabilidad y resultados auditables | `cerespinn_spatial_v4_metadata.json`: métricas superiores R² 0.9462; `metrics_all_models.MLP_Small.R2_temporal` = −0.0063, aunque `algorithm` es ese MLP | Contradicción | **Crítico** | `/api/validation` publica una cifra no respaldada por la tabla del mismo archivo. | Regenerar el artefacto desde un pipeline limpio, bloquear edición posterior y validar igualdad `metrics == metrics_all_models[algorithm]`. |
| D-04 | Reproducibilidad | Commit citado no contiene lo prometido | Disponibilidad, ll. 253–254 | El árbol de `6c22e5…` carece de dataset procesado, `scripts/reproduce.py`, manifiesto, workflow, licencia y artefactos Q1 declarados | Contradicción | **Crítico** | Un revisor no puede reproducir el artículo desde el hash publicado. | Crear release/tag inmutable desde un commit completo y sustituir el hash; verificar desde clon limpio. |
| D-05 | Datos climáticos | No existe CSV versionado de exactamente 98 filas | §3.2, l. 28; disponibilidad, l. 253 | `data/cerespinn_training_iowa.csv` tiene muchas más filas en el `HEAD` actual; no hay CSV rastreado de 98 filas | Vacío | **Crítico** | El linaje exacto de las forzantes del checkpoint no es reconstruible. | Publicar el archivo exacto, esquema, hash y generador o eliminar la afirmación de disponibilidad. |
| D-06 | Terminología de datos | “108 ejemplos del conjunto de entrenamiento” | §4.1, l. 154 | Metadato v2.5: 84 filas train y 24 test | Información incorrecta | Medio | Confunde total con muestra optimizada. | Escribir “108 filas totales; 84 de entrenamiento y 24 de prueba”. |
| D-07 | Validación prospectiva | Resultado negativo omitido cuantitativamente | Disponibilidad, l. 256: solo “capacidad… débil” | `docs/q1_artifacts/temporal/temporal_validation_1990_2017_to_2018_2025.json`: R² −0.8318, RMSE 855.22 kg ha⁻¹ | Información faltante | **Crítico** | El resumen favorable puede interpretarse como capacidad de extrapolación futura que no está demostrada. | Reportar protocolo, cifras, IC y baselines en resumen, métodos, resultados, discusión y conclusiones. |
| D-08 | API de validación | Valores cero presentados como pruebas no ejecutadas | El paper reporta t, KS, bootstrap y Sobol reales del v2.5 | `backend/validation.py:30-45` devuelve t/p/Sobol en cero y un ensamble vacío; el frontend los visualiza | Contradicción | Alto | Cero puede interpretarse como resultado estadístico real y no como “no disponible”. | Usar `null` + estado `not_computed`, o servir los artefactos Q1 del mismo modelo activo. |
| D-09 | Estado/API | `/api/model/status` asume atributos y metadatos específicos | Paper afirma aplicación reproducible y trazable | `backend/app.py:197-224` usa `inv.checkpoint`, pero `YieldInferenceService` no define ese atributo; además espera `test_metrics` aunque v4 usa `metrics` | Defecto | Alto | El endpoint de trazabilidad puede fallar o devolver métricas nulas al cambiar de adaptador. | Exponer una interfaz común (`artifact_path`, `metrics`, `model_id`) y probar ambos adaptadores. |
| D-10 | Inferencia | Rendimiento final no es solo predicción del checkpoint | Paper explica multiplicadores de manejo, pero denomina globalmente “salida de rendimiento” al sistema | `backend/inference.py:308-358` obtiene `bu_raw` y luego aplica variedad, riego, N y CO₂ | Diferencia de alcance | Alto | La salida final mezcla modelo aprendido y reglas; CO₂ puede contabilizarse dos veces porque ya es entrada de la red. | Devolver `raw_model_yield` y `adjusted_yield` por separado y justificar/calibrar cada multiplicador. |
| D-11 | Clima | Parametrizaciones incompatibles entre interfaces | Caso paper SSP5-8.5/2050: +2.7 °C, −24 %, 520 ppm | Backend `inference.py:662-667`; React `pinnEngine.ts:28-60` incorpora deriva; Streamlit conserva otro juego | Contradicción | Alto | El mismo rótulo produce experimentos diferentes según interfaz. | Centralizar forcings en backend/config versionada y eliminar cálculos científicos duplicados del cliente. |
| D-12 | Simuladores | Dos motores diarios divergentes | Paper habla de un simulador diario | `backend/inference.py:303-643` y `src/services/pinnEngine.ts:177-519`; `api.ts` conserva fallback local | Ambigüedad/contradicción | Alto | Resultados dependen de disponibilidad del backend. | Deshabilitar el motor local en modo científico o etiquetarlo como demo y registrar motor/versión en la salida. |
| D-13 | Ksat | Ksat se lee pero no gobierna el flujo | §3.2 y §3.3.2, ll. 29, 38 y 52 | `backend/inference.py:375` lee `ks`; no hay uso posterior; drenaje está limitado por reglas fijas cerca de ll. 503–530 | Contradicción | Alto | Un parámetro hidráulico declarado no afecta la simulación. | Implementar su efecto y validar balance de masa o describirlo como metadato inactivo. |
| D-14 | Proveedor LLM | Gemini vs OpenAI | Disponibilidad, l. 255: Google Gemini | `backend/app.py:35,130,386,433` y `backend/llm.py` usan `OPENAI_API_KEY`/ChatOpenAI | Contradicción | Alto | Arquitectura y despliegue documentados no corresponden al código. | Elegir proveedor y alinear paper, código, README y configuración de despliegue. |
| D-15 | Persistencia | PostgreSQL/PostGIS vs ejecución reportada como SQLite | Disponibilidad, l. 255 | `backend/app.py:181-194` devuelve `database: sqlite3`; `backend/db.py` admite SQLite y PostGIS simulado | Diferencia de estado | Medio | La arquitectura publicada sobredeclara la infraestructura activa. | Describir PostgreSQL/PostGIS como opción de despliegue, no como dependencia efectiva del experimento. |
| D-16 | Reproducibilidad | `--verify-only` no valida contenido de outputs | Disponibilidad, l. 254 | `scripts/reproduce.py:67-84` comprueba presencia de salidas y algunos campos, no hashes/valores de cada resultado | Diferencia de alcance | Alto | Artefactos alterados u obsoletos pueden pasar la verificación. | Añadir hashes/tolerancias para todas las salidas y figuras. |
| D-17 | Reentrenamiento | No se reconstruye el checkpoint v2.5 desde insumos publicados | Paper afirma regenerar todos los resultados | `scripts/reproduce.py:97-101` regenera análisis sobre el checkpoint existente; no recrea ese checkpoint desde las fuentes originales | Vacío | Alto | Se reproduce la auditoría del binario, no el entrenamiento que lo originó. | Añadir pipeline end-to-end con snapshot de datos, seed, entorno y comparación numérica. |
| D-18 | Figuras | Figuras del paper sin generador/activo trazable | Figuras 1–3, secciones 4.1–4.2 | No hay generador determinista ni activos finales incluidos en el manifiesto Q1 | Vacío | Alto | No puede verificarse que las figuras provengan de los CSV/JSON publicados. | Versionar script, imágenes y hashes. |
| D-19 | Benchmark | Tiempos del paper no coinciden con artefactos actuales | §5.4, l. 202: 31.36 s, 2.00 ms, 5.66 ms | `q1_statistics.json`: 5.84 s, mediana 0.2102 ms, p95 0.7354 ms | No verificable | Medio | El benchmark publicado carece de artefacto coincidente. | Publicar el registro exacto del entorno citado o actualizar el manuscrito. |
| D-20 | Variables/unidades | Riesgo de doble escala en precipitación por defecto | Paper usa −24 % como porcentaje | `_scenario_template` guarda −0.24, pero `SklearnAdapter._build_features` divide el default entre 100 (`inference.py:115-127`) | Defecto latente | Medio | Si se omite el campo, v3/v4 recibe −0.24 %, no −24 %. | Usar una sola unidad contractual y pruebas de omisión. |
| D-21 | Incertidumbre | Intervalo fijo ±15 % presentado como intervalo de predicción | Paper no valida una distribución predictiva de este tipo | `PinnAdapter.get_prediction_interval`, `backend/inference.py:276-278` | Información no sustentada | Alto | Produce apariencia de incertidumbre calibrada sin cobertura empírica. | Renombrar a banda heurística o calibrar cobertura en validación independiente. |
| D-22 | Datos/UI | Metadata demo todavía contradice el experimento | Paper: 22,160 NASS; ensamble GCM no ejecutado | `src/data/mockData.ts:264,275`: “32 Ensemble Models” y “45,200 County-Year” | Contradicción | Alto | El frontend puede mostrar procedencia ficticia como si fuera evidencia del paper. | Eliminarla o marcarla inequívocamente como demostración ficticia. |
| D-23 | Terminología | “Pérdida debida a sequía” no es causal | El paper advierte que la brecha no es pérdida climática atribuible | `backend/inference.py:577,638`; `backend/app.py:466` mantienen `yield_loss_due_to_drought_percent` | Inconsistencia conceptual | Medio | Reintroduce una interpretación causal que el manuscrito rechaza. | Renombrar a `gap_to_heuristic_potential_percent`. |

## 4. Vacíos y ambigüedades

| ID | Tipo | Dimensión | Elemento | Evidencia | Severidad | Acción recomendada |
|---|---|---|---|---|---|---|
| V-01 | Vacío reconocido | Validación | No hay validación externa espacial/de campo del modelo del paper | Paper §3.4.2; alcance en `backend/inference.py:29-48` | Crítico para uso prescriptivo | Mantener uso exploratorio y preparar validación geográfica preregistrada. |
| V-02 | Ambigüedad nueva | Modelo activo | No existe una fuente única de verdad entre v2.5, v3 y v4 | Tres pares de artefactos en `backend/models/` | **Crítico** | Definir registro y promoción explícita por entorno; no seleccionar por mera existencia de archivos. |
| V-03 | Vacío | Datos v4 | La supuesta calibración espacial no forma parte del paper ni de sus resultados | `train_v4_spatial.py` usa panel condado-año y nueve variables | Alto | Tratarlo como estudio separado hasta documentar origen, split, leakage, métricas y revisión. |
| V-04 | Vacío reconocido | Acoplamiento | Suelo y estados diarios no entran en la cabeza v2.5 | Paper §4.6; `SCIENTIFIC_SCOPE` | Alto | Acoplarlos solo con objetivos observados y nueva validación. |
| V-05 | Vacío reconocido | Manejo | Respuestas de cultivar/riego/N no están aprendidas | Paper §3.3.4 y §4.4; multiplicadores en inferencia | Alto | Etiquetar como heurísticas o calibrar con ensayos. |
| V-06 | Ambigüedad | “Gemelo digital” | No hay sincronización continua con observaciones reales | Flujo one-shot de `/api/simulate` | Medio/alto | Usar “prototipo de gemelo” y definir requisitos para operación real. |
| V-07 | Ambigüedad | “PINN” | Nombre histórico para un MLP regularizado por signos | `backend/training/pinn.py:1-18` | Medio | Usar consistentemente “red neuronal físicamente regularizada”. |
| V-08 | Vacío | Variables intermedias | Fenología, humedad, CWSI, biomasa y economía no se validan contra targets | No hay objetivos observados en el entrenamiento v2.5 | Alto | Validar cada estado o presentarlo como salida simulada no validada. |
| V-09 | Ambigüedad | Balance hídrico | No hay demostración robusta de cierre de masa | Simulador redondea/exporta estados; no hay prueba de conservación en producción | Medio | Añadir test de balance con estados sin redondeo y tolerancia física. |
| V-10 | Vacío reconocido | Incertidumbre | No hay propagación conjunta climática, paramétrica y estructural | Paper reconoce que el ensamble GCM no se ejecutó | Alto | Ejecutar ensamble real y separar fuentes; retirar bandas heurísticas con apariencia inferencial. |
| V-11 | Vacío | Trazabilidad NASS | Falta snapshot/consulta original completamente reconstruible para v2.5 | CSV final no conserva toda la procedencia de los 22,160 registros | Alto | Publicar consulta, claves geográficas y manifiesto compatible con términos de uso. |
| V-12 | Ambigüedad | Reproducibilidad v4 | Metadato v4 indica `training_commit` antiguo y `created_at` posterior | `cerespinn_spatial_v4_metadata.json` | Alto | Registrar commit limpio, hash del script, lockfile y dataset, y firmar el paquete. |

## 5. Priorización de riesgos y recomendaciones

### P0 — Bloquean la publicación

1. **Congelar el modelo del paper.** Si el artículo sigue describiendo v2.5, crear un release donde API, `/api/model/status`, `/api/validation`, UI y artefactos usen exactamente ese checkpoint y su hash. Apartar v3/v4 de ese release.
2. **Reparar la validación.** No publicar las métricas inconsistentes del v4 ni ceros como resultados; implementar tests de identidad entre modelo activo, dataset, esquema y métricas.
3. **Corregir disponibilidad.** Sustituir el commit `6c22e5…` por un tag completo y publicar el CSV exacto de 98 filas o retirar ese claim.
4. **Reportar el resultado prospectivo negativo.** Incluir R² −0.8318 y métricas asociadas en todo el relato científico relevante.

### P1 — Antes de revisión por pares

5. Centralizar forzantes climáticos y desactivar motores alternativos en modo científico.
6. Separar predicción neuronal cruda, ajustes deterministas y simulación diaria en el contrato API.
7. Añadir reproducción end-to-end del entrenamiento, hashes de outputs y generadores de figuras.
8. Resolver Ksat, doble escala de precipitación, banda ±15 % y endpoint de estado.
9. Alinear proveedor LLM, persistencia y metadata visible con el release real.

### P2 — Fortalecimiento metodológico

10. Validar estados biofísicos y cierre hídrico; calibrar manejo con datos experimentales.
11. Publicar linaje NASS/NEX completo y distinguir claramente estudios v2.5 y v4.
12. Normalizar terminología: “prototipo híbrido”, “MLP físicamente regularizado” y “brecha a potencial heurístico”.

## 6. Verificaciones realizadas

| Verificación | Resultado |
|---|---|
| Comparación del nuevo anexo con el anterior | Solo elimina un párrafo introductorio duplicado y corrige Chavoshi 2025→2024; las afirmaciones técnicas no cambian. |
| Inspección del `HEAD` | `5df3da13c06a0382fad4038e5e6d22ea667b8978`; se inspeccionaron modelos, inferencia, validación, frontend, datos, scripts y CI. |
| Consumo del checkpoint | Confirmado por lectura: `PinnAdapter` se selecciona si `cerespinn_pinn.pt` y metadato existen; ambos están presentes. |
| Ejecución de pytest | No verificada en esta sesión: el `.venv` apunta a un Python inexistente y el runtime disponible no incluye pytest. Esto es además un problema de reproducibilidad local. |
| Métricas Q1 | Verificadas contra CSV/JSON versionados, no regeneradas en esta sesión. |

## 7. Preguntas para aclarar antes de la versión final

1. ¿El artículo se publicará sobre el checkpoint PyTorch v2.5 o sobre el nuevo modelo espacial v4?
2. ¿Por qué `/api/validation` usa v4 mientras `/api/simulate` prioriza v2.5?
3. ¿Cuál es el R² verdadero del v4: 0.9462 o −0.0063 para `MLP_Small`?
4. ¿Se retirarán v3/v4 del release del paper o se documentarán como experimentos separados?
5. ¿Qué commit/tag completo reemplazará al hash `6c22e5…`?
6. ¿Dónde se publicará el CSV exacto de 98 filas y su generador?
7. ¿Aceptan incorporar en resumen y conclusiones el R² prospectivo −0.8318?
8. ¿La salida oficial será el rendimiento crudo del checkpoint o el rendimiento posterior a multiplicadores?
9. ¿CO₂ debe afectar dos veces el resultado —como feature de la red y como multiplicador posterior—?
10. ¿React, Streamlit o FastAPI es la interfaz científica canónica?
11. ¿Ksat debía intervenir realmente en drenaje/infiltración?
12. ¿La banda ±15 % es solo heurística o existe una calibración de cobertura no versionada?
13. ¿El asistente final usa Gemini u OpenAI?
14. ¿PostgreSQL/PostGIS es una dependencia del experimento o solo una opción de despliegue?
15. ¿Existen scripts originales para las figuras y el benchmark publicado?

## 8. Dictamen

El paper describe de forma razonablemente honesta el experimento **CeresPINN v2.5**, y sus métricas principales siguen presentes. El problema central ya no es solo editorial: el repositorio evolucionó hacia v3/v4 sin una frontera de release, y la aplicación mezcla inferencia v2.5 con validación v4. Por ello, el sistema actual no constituye una implementación única y coherente del manuscrito. La ruta de menor riesgo es congelar y corregir un release científico v2.5 para este paper, dejar v4 como línea futura separada y no presentar la aplicación pública como evidencia del artículo hasta unificar selección, validación y trazabilidad del modelo.
