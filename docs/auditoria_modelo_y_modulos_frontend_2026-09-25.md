# Auditoría del consumo del modelo y utilidad de módulos React

Fecha de verificación: 2026-09-25  
Commit inspeccionado: `8bf6d695a9683231ef8710efa32bd149691bf78b`  
Alcance: frontend React, API FastAPI, checkpoint PyTorch y despliegues públicos de Vercel/Render. No se modificó código de la aplicación.

## 1. Conclusión ejecutiva

Sí: la ruta de simulación de producción consume el checkpoint entrenado `backend/models/cerespinn_pinn.pt`. Se comprobó tanto localmente mediante `TestClient` como contra el backend público: `/api/model/status` respondió `status=ready`, `inference_mode=pinn`, `checkpoint=cerespinn_pinn.pt`, `real_data=true`, y un `POST /api/simulate` devolvió `inference_mode=pinn`, `model_uses_real_data=true` y 115 registros diarios. El bundle público de Vercel contiene la URL `https://cerespinn-backend.onrender.com`.

Sin embargo, el checkpoint no genera todo lo que presenta la interfaz. La red predice únicamente un rendimiento base a partir de siete variables climáticas/temporales. Variedad, riego, nitrógeno y CO2 adicional se aplican mediante multiplicadores deterministas; la serie diaria de suelo, fenología, biomasa, estrés, alertas y economía es posprocesamiento programado. El suelo y las coordenadas no son entradas de la red de rendimiento.

El frontend de producción no acepta silenciosamente el motor local si falla Render, porque `import.meta.env.PROD` activa `REQUIRE_REMOTE_PINN`. Aun así, `App` se inicializa con una simulación local y la conserva si falla la primera llamada, por lo que puede mostrar datos sustitutos mientras indica que el modelo está fuera de línea.

La navegación actual mezcla módulos científicos útiles con prototipos visuales, estados semilla y acciones cosméticas. Deben retirarse de la publicación actual la Validación heredada, la Comparación de campos como supuesto análisis territorial, el GIS demostrativo y el falso RBAC. Pipelines debe quedar solo para administración técnica y reflejar su estado real. Adaptación y What-if deben fusionarse.

## 2. Evidencia de que sí se consume el checkpoint entrenado

### Trazado de código

1. React llama `POST /api/simulate` en `src/services/api.ts:204-233`.
2. En producción valida que la respuesta sea `inference_mode=pinn`, use datos reales y tenga todos los KPI y registros diarios (`src/services/api.ts:48-81`).
3. FastAPI recibe la solicitud y llama `inv.run_full_simulation(payload_dict)` (`backend/app.py:292-309`).
4. `run_full_simulation` invoca `predict_yield_bu_acre` (`backend/inference.py:187-205`).
5. `predict_yield_bu_acre` carga el checkpoint, construye el tensor, ejecuta el modelo bajo `torch.no_grad()` y desnormaliza el resultado (`backend/inference.py:98-184`).
6. El checkpoint inspeccionado tiene 258,098 bytes y SHA-256 `600F4A2BFD8C8F3A4CE08E623CEBED4087D64BAE341EBD5FE71C32507ABDE7E4`.

### Comprobación de ejecución

- Local `/api/model/status`: `CeresPINN-maize-v2.5`, `ready`, `pinn`, `real_data=true`, R2 0.8225, RMSE 717.4 kg/ha.
- Local `/api/simulate`: HTTP 200, `pinn`, `nass+nex-gddp`, `model_uses_real_data=true`, 11,832 kg/ha y 115 registros diarios para el caso probado.
- Render público `/api/model/status`: mismos nombre, métricas, fecha de entrenamiento y checkpoint.
- Render público `/api/simulate`: HTTP 200, `pinn`, datos reales, 11,832 kg/ha y 115 registros diarios.
- Vercel público: el bundle `assets/index-CTu_jE2Z.js` contiene `https://cerespinn-backend.onrender.com`.

### Qué está entrenado y qué no

El checkpoint recibe siete entradas: año, anomalía térmica, anomalía de precipitación, CO2, riesgo de ola de calor, precipitación estacional y CDD estacionales (`backend/models/cerespinn_metadata.json`). La clase es un MLP de dos cabezas (`backend/training/pinn.py:38-72`). La regularización impone signos locales de derivadas temperatura/rendimiento y precipitación/rendimiento; no resuelve una EDP ni impone conservación de masa (`backend/training/pinn.py:1-18,75-117`). Por rigor, debe describirse como **MLP con regularización monotónica de inspiración física**, no como una PINN de residuales de ecuaciones gobernantes.

El rendimiento final incorpora multiplicadores codificados para variedad, riego, nitrógeno y CO2 (`backend/inference.py:207-243`). Los suelos se resuelven después para el balance hídrico diario (`backend/inference.py:245-280`), no para la inferencia neuronal de rendimiento. Una prueba con cuatro perfiles produjo exactamente 11,832 kg/ha en todos, aunque cambió agua total de 392 a 362 mm y CWSI pico de 0.85 a 0.74.

## 3. Matriz de módulos y decisión recomendada

| Módulo | ¿Consume el checkpoint? | Función real comprobada | Evaluación | Decisión recomendada |
|---|---|---|---|---|
| Estado del modelo en cabecera | Sí, consulta `/api/model/status` y la simulación activa | Indica disponibilidad, R2, procedencia y modo de inferencia (`src/App.tsx:113-145,283-284,513-522`) | Es la trazabilidad más importante para el usuario | **Conservar y reforzar**. Mostrar hash, fecha, fuente y una etiqueta inequívoca “checkpoint remoto”/“sin resultado”. |
| Gemelo 3D | Indirectamente; representa `dailyRecords` ya calculados | Anima fenología, humedad, biomasa y CWSI en Three.js (`ThreeFieldViewer.tsx:31-130,444-583`) | Útil para comunicación, no para validación ni cálculo adicional | **Conservar como visualización opcional**, renombrada “Visualización 3D de la simulación”. No llamarla evidencia del modelo. |
| Dashboard y KPI | Sí para rendimiento base; indirectamente para el resto | Presenta KPI, alertas y series temporales (`MainDashboard.tsx:38-231,271+`) | Es la pantalla operativa principal | **Conservar**, pero etiquetar cada KPI por procedencia: red, posproceso o cálculo económico. **Eliminar de inmediato** el bloque “32 modelos CMIP6”: usa un IC fijo de ±8% y valores fijos no derivados (`MainDashboard.tsx:233-269`). |
| Configuración de simulación | Sí, por `simulateScenario` | Configura escenario, año, variedad, riego, N y humedad (`SimulationConfig.tsx`) | Esencial, pero hoy puede enviar forzantes distintos de los que muestra | **Conservar y corregir antes de publicar**. Al cambiar escenario/año, actualizar CO2, temperatura y precipitación enviados; usar una única fuente de forzamiento. |
| Recomendaciones de adaptación | Sí, ejecuta tres simulaciones remotas | Compara adelanto de siembra, ciclo corto y riego al 75% (`AdaptationPanel.tsx:42-135`) | Hay valor exploratorio, pero duplica What-if y algunos valores como “agua ahorrada” se calculan con porcentajes ad hoc | **Fusionar con What-if**. Mantener estrategias predefinidas como plantillas, no como recomendaciones prescriptivas. |
| What-if Studio | Sí, ejecuta tres simulaciones remotas | Compara escenarios configurables y elige un “ganador” (`WhatIfStudio.tsx:36-178`) | Útil para explorar; “ganador” y margen económico pueden inducir a decisión no validada | **Conservar como comparador exploratorio**, fusionado con Adaptación. Sustituir “ganador/optimización” por “comparación” y mostrar incertidumbre/procedencia. |
| Gestor GIS/campos | Solo manda `field_id`; campos nuevos no llegan a la base ni sus suelos a la API | Crea coordenadas aleatorias, importa/exporta solo el primer feature y dibuja un SVG ficticio (`FieldMapManager.tsx:47-157,412-462`) | No es un GIS real ni una entrada espacial válida del modelo | **Eliminar de la navegación pública**. Solo conservar si se implementan mapa real, validación GeoJSON, persistencia y envío explícito de suelo. |
| Reportes | Exporta la simulación activa, por tanto incluye el resultado remoto | PDF y XLSX se generan localmente con KPI, serie diaria y alcance científico (`ReportsModule.tsx:53-278`) | Exportar trazabilidad sí aporta valor | **Conservar PDF/XLSX**. Eliminar el envío por correo: solo activa un mensaje visual (`ReportsModule.tsx:280-284`). Eliminar `fetchReports`, `reportsData` y `loadingReports`, que actualmente no se renderizan. |
| MLOps/registro | Sí, consulta metadata del checkpoint desplegado | Solo presenta el modelo activo y no inventa curvas (`MLOpsDashboard.tsx:7-14,21-107`; `backend/app.py:564-591`) | Correcto y auditable, pero técnico para usuario final | **Conservar en “Acerca del modelo / Transparencia”**, no como módulo principal. |
| Pipelines de datos | No participa en inferencia; administra extractores | Lista manifiestos y puede disparar jobs (`backend/pipelines_api.py`) | En producción los tres responden `status=never`; Render está configurado con `CERESPINN_DRY_RUN=1`. La UI conserva estados locales “healthy” para `never` (`DataPipelinesView.tsx:29-44`) | **Ocultar del frontend público o mover a administración**. No mostrar “extracción real” ni fechas/conteos semilla. Si permanece, leer `dry_run`, estado y manifiesto sin mezclar valores locales. |
| Usuarios/RBAC | No | Login compara credenciales incrustadas y guarda un ID en `localStorage`; alta y cambio de usuario son locales (`LoginScreen.tsx:8-44`; `UserManagement.tsx:29-95,256-263`) | No hay autenticación, autorización ni RBAC real; la lista de API no controla el acceso | **Eliminar por completo para demo pública** o reemplazar con autenticación real. No presentarlo como seguridad. |
| Validación científica | Parcialmente: el hindcast sí usa muestras del checkpoint; el resto mezcla sustitutos | Render expone el hindcast correcto y también métricas heredadas, t-test, Sobol y ensamble simulados (`backend/validation.py:451-513`) | La UI prioriza R2 0.7842/RMSE 2090, aunque el checkpoint da R2 0.8251/RMSE 712.1; muestra H1 confirmada y ensamble no ejecutado | **Ocultar inmediatamente antes de publicar** y reescribir para leer únicamente artefactos Q1 versionados con hash/procedencia. Es el mayor riesgo científico del frontend. |
| Comparación de campos | Sí, pero coordenadas/suelo no afectan la red de rendimiento | Ejecuta 3 escenarios por campo y ordena indicadores (`FieldScenarioComparison.tsx:37-109`) | La propia vista admite que no es validación espacial; los rendimientos iguales entre campos pueden parecer un análisis territorial | **Retirar de navegación principal**. Conservar solo en un anexo de limitaciones o reimplementar después de calibración espacial. |
| Chatbot | No ejecuta el checkpoint; recibe un resumen de KPI ya calculados | Envía contexto a Langflow/OpenAI y devuelve texto (`ChatbotWidget.tsx:47-87`; `backend/app.py:324-380`) | Conveniencia explicativa, no función científica; tiene costo y riesgo de interpretación | **Opcional**. Mantener solo si se etiqueta “asistente explicativo”, cita el modo/fuente y no prescribe. Es eliminable sin perder capacidad del gemelo. |
| Aviso de alcance científico | No, pero refleja limitaciones reales | Expone falta de calibración espacial, no uso de suelo en la red y usos prohibidos (`ScientificScopeNotice.tsx:5-39`) | Reduce riesgo de sobreinterpretación | **Conservar obligatoriamente**, hacerlo más visible en comparadores y exportaciones. |

## 4. Fallos funcionales que explican información irrelevante o pantallas que “no sirven”

### Críticos

1. **Validación contradictoria.** `/api/validation` contiene el hindcast real R2 0.8251/RMSE 712.1, pero también `hindcast_metrics` codificado con R2 0.7842/RMSE 2090. React usa primero el segundo objeto (`ValidationReport.tsx:101-106,171-211`). El t-test, Sobol y “ensamble” proceden de `deterministic_yield`, no del checkpoint ni de un ensamble GCM ejecutado (`backend/validation.py:296-302,363-408,451-513`).
2. **Forzamiento visible distinto del enviado.** `SimulationConfig` calcula lo que muestra mediante `getCMIP6ClimateForcing`, pero sus handlers solo cambian `scenario` y `targetYear` (`SimulationConfig.tsx:73-80`). La API envía los antiguos `carbonDioxidePpm`, `temperatureAnomalyC` y `precipitationAnomalyPercent` guardados en el estado (`api.ts:212-223`). Además, el selector de año del gemelo cambia solo el año (`App.tsx:670-678`).
3. **Tres definiciones climáticas incompatibles.** El frontend local, el backend y Streamlit mantienen tablas distintas. Por ejemplo, SSP5-8.5 no representa los mismos CO2/temperatura/precipitación en los tres motores. Debe existir una sola definición versionada.
4. **Pipelines aparentan estar sanos cuando nunca se sincronizaron.** El backend público devolvió `never` para CHIRPS, NEX-GDDP y NASS. La fusión React conserva el estado local anterior para cualquier valor distinto de `healthy/error/empty`, y los seeds declaran fechas y millones de registros (`DataPipelinesView.tsx:29-44`; `mockData.ts:245-278`).

### Altos

5. **El mapa no alimenta el modelo.** La creación usa `Math.random()` y solo actualiza estado React (`FieldMapManager.tsx:47-83`). `simulateScenario` manda `field_id` pero no los parámetros del suelo (`api.ts:212-224`); un ID importado/desconocido cae al suelo por defecto de Bajío (`backend/inference.py:245-257`).
6. **El selector de perfil edáfico no cambia nada.** Su `onClick` solo hace `console.log` (`SimulationConfig.tsx:516-529`).
7. **La aplicación puede conservar una simulación local al arrancar.** El estado inicial se crea con `runPINNSimulation` (`App.tsx:164-167`) y se mantiene si falla la inferencia inicial (`App.tsx:141-150`). En producción conviene mostrar “sin resultado” o un esqueleto, no datos sustitutos.
8. **La denominación PINN exagera la física incorporada.** El propio código reconoce que la pérdida no es residual de ecuaciones gobernantes ni demuestra conservación (`backend/training/pinn.py:1-18`).

### Medios/bajos

9. **Reportes consulta datos que nunca muestra.** `reportsData` y `loadingReports` se escriben, pero no se leen en el render. El endpoint público devuelve un resumen estático regional irrelevante para la simulación activa.
10. **Enviar correo es cosmético.** No hay API de correo; el formulario solo cambia `isEmailSent` durante cuatro segundos.
11. **What-if añade 600 ms artificiales** para “latencia percibida” (`WhatIfStudio.tsx:77-78`). No aporta rigor ni funcionalidad.
12. **Adaptación muestra ahorros calculados por reglas fijas.** Por ejemplo, 5% y 18% no son diferencias de dos salidas comparables (`AdaptationPanel.tsx:96,112`).

## 5. Arquitectura frontend mínima recomendada

### Navegación pública

1. **Simular:** configuración unificada + estado inequívoco del checkpoint.
2. **Resultados:** KPI y series con etiquetas de procedencia.
3. **Comparar:** un único módulo que fusione What-if y plantillas de adaptación.
4. **Visualizar:** gemelo 3D opcional.
5. **Exportar:** PDF/XLSX con hash y alcance científico.
6. **Acerca del modelo:** metadata MLOps y limitaciones.

### Fuera de la navegación pública

- Administración técnica: pipelines reales, solo para administradores autenticados.
- Desarrollo futuro: GIS, usuarios/RBAC y comparación territorial.
- Retirado hasta corrección: validación heredada.
- Opcional: chatbot.

Esta reducción baja de once pestañas científicas/operativas a seis áreas coherentes y evita presentar prototipos como capacidades productivas.

## 6. Orden de corrección antes de publicación

1. Ocultar Validación actual y eliminar el bloque de 32 GCM del Dashboard.
2. Unificar y sincronizar forzamientos climáticos entre estado React, request y backend.
3. Retirar GIS, comparación territorial y RBAC falso de la navegación pública.
4. Corregir Pipelines para no mezclar `never` con seeds “healthy”; mantenerlo admin-only.
5. Fusionar Adaptación y What-if; retirar lenguaje prescriptivo, “ganador” y cálculos ad hoc.
6. Mantener Reportes, MLOps y aviso científico; añadir hash/procedencia a cada resultado exportado.
7. Renombrar el método con precisión: MLP regularizado por monotonicidad, o implementar una pérdida física basada en ecuaciones si se conservará el término PINN fuerte.

