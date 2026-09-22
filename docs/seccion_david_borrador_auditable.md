# Borrador auditable — sección de David

## Nota editorial previa (no incluir literalmente en el manuscrito)

Este texto representa el estado verificable del código y del *checkpoint* `CeresPINN-maize-v2.5`. Se adoptan cuatro decisiones para no sobreinterpretar el prototipo:

1. El componente aprendido se describe como **red neuronal informada o regularizada por conocimiento físico**, porque su pérdida impone monotonicidad ecofisiológica, pero no incorpora todavía el residuo diferencial de Richards. El balance hídrico de tres capas es un simulador determinista acoplado a la inferencia.
2. La evaluación disponible es una **retención interna agrupada por año**. Aún no existe validación externa con condados, campañas o ensayos independientes.
3. Los resultados de adaptación y vulnerabilidad son **experimentos demostrativos del prototipo**, no estimaciones regionales generalizables.
4. Se excluyen del artículo el bloque heredado `hindcast_metrics` (R² = 0.7842) y los residuos PDE/condiciones de frontera mostrados por la interfaz, porque no proceden del *checkpoint* vigente. Las métricas trazables son R² = 0.8225 para las 24 filas de prueba y R² = 0.8251 para los ocho años retenidos agregados.

También conviene sustituir en la introducción la afirmación de que DSSAT o APSIM “suponen clima estacionario” o “no admiten proyecciones climáticas”. Ambos pueden ejecutarse con clima futuro; sus principales dificultades son la parametrización, calibración, propagación de incertidumbre y costo de ejecutar ensambles extensos.

---

# MATERIALES Y MÉTODOS

## 3.3. Arquitectura y formulación del modelo PINN

CeresPINN se implementó como una arquitectura híbrida de dos componentes. El primero es una red neuronal multicapa entrenada para predecir rendimiento anual de maíz a partir de covariables climáticas y temporales. El segundo es un simulador estacional determinista que transforma esa predicción basal en trayectorias diarias de fenología, balance hídrico y estrés, condicionadas por suelo y manejo. Esta separación permite conservar una inferencia rápida, pero implica que las variables edáficas y de manejo no son entradas directas de la red entrenada.

La red contiene siete entradas, cuatro capas ocultas de 128 unidades con activación hiperbólica tangente y *dropout* de 0.05, y dos cabezas de salida. La primera cabeza consta de una capa de 64 unidades con ReLU y produce el rendimiento normalizado; la segunda contiene 32 unidades con ReLU y una salida sigmoidal que representa un indicador latente de disponibilidad hídrica entre 0 y 1. La formulación sigue el principio general de restringir una red neuronal con conocimiento del dominio, aunque es más ligera que una PINN clásica basada en el residuo explícito de una ecuación diferencial parcial (Raissi, Perdikaris, & Karniadakis, 2019; Farea, Yli-Harja, & Emmert-Streib, 2024).

### 3.3.1. Variables de entrada, estados y salidas

El vector de entrada directa de la red fue:

\[
\mathbf{x}= [a,\Delta T,\Delta P,CO_2,H,P_s,CDD],
\]

donde \(a\) es el año, \(\Delta T\) la anomalía de temperatura (°C), \(\Delta P\) la anomalía porcentual de precipitación, \(CO_2\) la concentración atmosférica (ppm), \(H\) el riesgo de ola de calor, \(P_s\) la precipitación estacional acumulada (mm) y \(CDD\) un indicador de días secos consecutivos. Las entradas se estandarizaron mediante puntuaciones \(z\) calculadas exclusivamente sobre el conjunto de entrenamiento. El rendimiento objetivo, expresado originalmente en bu acre⁻¹, se transformó al intervalo [0,1] mediante normalización mínimo–máximo y se reconvirtió a kg ha⁻¹ para la comunicación de resultados.

El simulador acoplado recibe adicionalmente la fecha de siembra, el ciclo del cultivar (corto, medio o largo), la estrategia de riego, la dosis de nitrógeno, la humedad inicial y parámetros hidráulicos asociados al campo. A partir de estos valores genera estados diarios: grados-día acumulados, estadio fenológico, índice de área foliar, profundidad radical, contenido volumétrico de agua en tres capas (0–30, 30–60 y 60–100 cm), precipitación, riego, evapotranspiración, drenaje, CWSI y estrés térmico. Estas variables son estados del simulador, no variables latentes aprendidas por la red.

Las salidas principales son rendimiento proyectado y potencial (kg ha⁻¹), pérdida relativa, duración del ciclo, fecha de madurez, consumo de agua, riego acumulado, productividad del agua, retorno económico e índice de resiliencia. Las series diarias permiten además localizar la coincidencia entre estrés y etapas críticas como VT–R1. Los indicadores denominados “residuo de Richards”, “pérdida de frontera” o “conservación PDE” no se utilizaron como evidencia experimental, pues la versión actual no los calcula a partir de la función de pérdida entrenada.

### 3.3.2. Formulación física y balance de procesos

La predicción aprendida puede expresarse como \(\hat{Y}=f_\theta(\mathbf{x})\). El conocimiento físico entra durante el entrenamiento mediante dos restricciones locales de signo: dentro del dominio de entrenamiento, el rendimiento no debe aumentar al elevarse la anomalía térmica y no debe disminuir al aumentar la precipitación estacional. Estas relaciones no representan leyes universales —por ejemplo, el exceso de agua puede reducir el rendimiento—, sino priors válidos para el régimen hídrico deficitario que motivó el estudio.

Después de la inferencia, el motor estacional aplica un balance hídrico discreto por capa:

\[
S_{l,t+1}=S_{l,t}+I_{l,t}-ET_{l,t}-D_{l,t},
\]

donde \(S_{l,t}\) es el almacenamiento de agua en la capa \(l\), \(I_{l,t}\) reúne infiltración de precipitación y riego, \(ET_{l,t}\) es la extracción por evaporación y transpiración, y \(D_{l,t}\) el flujo de percolación hacia la capa siguiente. El almacenamiento se restringe mediante saturación, capacidad de campo y punto de marchitez. Por tanto, el módulo constituye una aproximación tipo reservorio estratificado inspirada en Richards, no una solución numérica diferenciable de la ecuación de Richards.

La evapotranspiración de referencia se estima con Priestley–Taylor y se ajusta mediante un coeficiente de cultivo dependiente del estadio fenológico. El estrés hídrico se resume mediante \(CWSI=1-K_s\), donde \(K_s\) depende del agua disponible respecto de los umbrales edáficos. La temperatura impulsa la acumulación de grados-día, determina las transiciones fenológicas y activa una penalización de estrés cuando las temperaturas máximas coinciden con ventanas reproductivas sensibles. Este acoplamiento produce trayectorias agronómicamente interpretables, aunque todavía no retropropaga los estados diarios hacia el rendimiento final de la red.

### 3.3.3. Función de pérdida y entrenamiento

La función objetivo implementada fue:

\[
\mathcal{L}_{total}=\mathcal{L}_{data}+\lambda_{phy}\mathcal{L}_{mono}+\lambda_{reg}\|\theta\|_2^2,
\]

con \(\lambda_{phy}=0.5\), \(\lambda_{reg}=10^{-4}\) y

\[
\mathcal{L}_{data}=\frac{1}{N}\sum_{i=1}^{N}(y_i-\hat{y}_i)^2,
\]

\[
\mathcal{L}_{mono}=\operatorname{E}\left[\operatorname{ReLU}\left(\frac{\partial \hat y}{\partial \Delta T}\right)\right]
+\operatorname{E}\left[\operatorname{ReLU}\left(-\frac{\partial \hat y}{\partial P_s}\right)\right]
+\mathcal{L}_{range}.
\]

Las derivadas se calcularon con diferenciación automática de PyTorch. \(\mathcal{L}_{range}\) penaliza valores del indicador hídrico fuera de [0,1], aunque su contribución es nula por construcción al utilizar una activación sigmoidal. No se incluyeron términos \(\mathcal{L}_{Richards}\) ni \(\mathcal{L}_{boundary}\) en la versión evaluada.

El entrenamiento utilizó Adam, tasa de aprendizaje de 0.001, decaimiento de pesos de \(10^{-5}\), lotes de 64 observaciones, 300 épocas y semilla 42. Los artefactos finales fueron el grafo de parámetros `cerespinn_pinn.pt` y los metadatos de normalización, linaje y evaluación `cerespinn_metadata.json`. La configuración se mantuvo fija durante el ajuste reportado; por ello, los resultados deben interpretarse como desempeño de una configuración preespecificada y no como resultado de una búsqueda exhaustiva de hiperparámetros.

### 3.3.4. Módulo de optimización de manejo

En el estado actual, este componente es más precisamente un **módulo de comparación de alternativas de manejo**. La aplicación evalúa escenarios discretos de fecha de siembra, duración varietal y riego, y compara rendimiento, agua aplicada, CWSI, duración del ciclo, resiliencia y retorno económico. No existe todavía un algoritmo de optimización continua ni una función objetivo calibrada con preferencias del productor.

El rendimiento final se obtiene mediante la predicción de la red y multiplicadores deterministas de manejo. Para el ciclo se emplean factores 0.88, 1.00 y 1.12 para cultivares corto, medio y largo; para riego se utilizan 0.85, 0.96, 1.03, 1.08 y 1.06 para secano, déficit al 50 %, déficit al 75 %, riego óptimo y sensores inteligentes, respectivamente. También se aplican respuestas acotadas de nitrógeno y CO₂. Por consiguiente, la respuesta al manejo no fue aprendida de ensayos agronómicos y debe considerarse una regla de decisión exploratoria.

El análisis comparativo se ejecutó manteniendo constantes campo, escenario climático y año objetivo, y modificando una estrategia por vez. Se calculó el efecto relativo como

\[
\Delta Y_j(\%)=100\frac{Y_j-Y_0}{Y_0},
\]

donde \(Y_0\) es el escenario basal y \(Y_j\) la alternativa. En una versión futura, este módulo podrá formularse como optimización multiobjetivo —maximizar rendimiento, resiliencia y margen económico y minimizar uso de agua—, pero tal extensión no forma parte de los resultados presentes.

## 3.4. Calibración y validación del modelo

La fuente de rendimiento fue USDA-NASS Quick Stats, que contiene estimaciones oficiales agrícolas de Estados Unidos. El conjunto procesado reunió 22,160 registros entre 1990 y 2025, resumidos en 36 medianas anuales. Las covariables climáticas provinieron de 98 filas regionales NEX-GDDP-CMIP6. NASA describe este producto como proyecciones diarias corregidas y reducidas a 0.25° para 35 modelos climáticos, con simulaciones históricas y escenarios SSP (Thrasher et al., 2022).

Cada rendimiento anual fue expandido a tres filas climáticas de escenario, generando 108 filas de modelado. La separación se realizó por año para evitar que copias SSP del mismo rendimiento aparecieran simultáneamente en entrenamiento y prueba. Se usaron 28 años para entrenamiento (84 filas) y ocho años para prueba (24 filas). Esta expansión aumenta el número de filas, pero no el número efectivo de observaciones independientes de rendimiento, que permanece en 36.

### 3.4.1. Validación histórica (*hindcast*)

La evaluación retrospectiva se realizó mediante retención agrupada aleatoria de los años 1991, 1992, 1998, 2001, 2003, 2004, 2011 y 2024. En las 24 filas SSP retenidas, el modelo obtuvo MSE = 130.62 (bu acre⁻¹)², MAE = 9.85 bu acre⁻¹ (618.3 kg ha⁻¹) y R² = 0.8225. Al promediar las tres copias de escenario por año, la evaluación sobre ocho valores independientes produjo RMSE = 712.1 kg ha⁻¹, MAE = 604.2 kg ha⁻¹ y R² = 0.8251.

La prueba de Kolmogorov–Smirnov entre las ocho predicciones y las ocho observaciones dio \(D=0.25\) y \(p=0.9801\). Este resultado indica que no se detectó una diferencia distributiva con esa muestra, pero no demuestra equivalencia: con \(n=8\) la potencia estadística es limitada. Asimismo, como los años de prueba están intercalados en el periodo de entrenamiento, la prueba se describe como retención temporal interna y no como *hindcast* cronológico estricto.

### 3.4.2. Validación externa

La validación externa no se ha completado y no debe atribuirse a los cuatro campos demostrativos de la interfaz. Se propone reservar un conjunto completamente independiente en tres niveles: (i) condados del Corn Belt ausentes de la calibración; (ii) campañas posteriores al último año de entrenamiento; y (iii) ensayos de campo con rendimiento, humedad de suelo y fenología observados. La evaluación deberá estratificarse por régimen hídrico, textura del suelo y escenario térmico, y reportar RMSE, MAE, sesgo medio, R², cobertura de intervalos predictivos y calibración de CWSI.

Para probar transferencia espacial, el modelo deberá entrenarse excluyendo condados completos y evaluarse sin recalibración. Para transferencia temporal, se recomienda entrenar con 1990–2018, calibrar hiperparámetros con 2019–2021 y reservar 2022–2025 como prueba final bloqueada. La hipótesis de utilidad agronómica requerirá además comparar CeresPINN con un modelo ingenuo, una red sin regularización física y un modelo de proceso calibrado bajo idénticos datos de entrada. Hasta completar este protocolo, la evidencia disponible sustenta validación interna, no validez externa ni causal.

## 3.7. Análisis estadístico y cuantificación de incertidumbre

El desempeño predictivo se resumió con RMSE, MAE y R² sobre años no empleados en el ajuste. Los residuos deben presentarse por año y no por las tres copias SSP, para conservar la unidad experimental. La comparación de alternativas de manejo debe realizarse de manera pareada dentro de cada combinación año–modelo climático–campo. Se recomienda informar la mediana de \(\Delta Y\), su intervalo de confianza bootstrap al 95 % y la probabilidad de beneficio \(P(\Delta Y>0)\), en lugar de depender únicamente de una prueba *t*.

La sensibilidad global del *checkpoint* se estimó mediante un diseño tipo Saltelli–Jansen con 32,768 muestras, semilla 42, año 2050 y contexto SSP5-8.5. Se variaron \(\Delta T\) entre 2.2 y 3.4 °C, \(\Delta P\) entre −28 % y −15 %, y CO₂ entre 500 y 600 ppm. Se calcularon índices de primer orden \(S_i\) y efecto total \(S_{Ti}\), siguiendo el marco de descomposición de varianza de Saltelli et al. (2010). Estos índices describen varianza del modelo dentro de los rangos elegidos y no efectos causales del clima.

La incertidumbre deberá separarse en cuatro componentes: (i) incertidumbre observacional de NASS; (ii) incertidumbre climática entre GCM, SSP y variabilidad interna; (iii) incertidumbre paramétrica de la red y del simulador; y (iv) incertidumbre estructural debida a la formulación del modelo. La versión actual contiene bandas exploratorias generadas con un sustituto determinista; por ello, esas bandas no deben presentarse como incertidumbre predictiva del *checkpoint* hasta que cada miembro climático sea procesado por la red entrenada y el simulador completo.

# RESULTADOS

## 4.4. Efectividad de la adaptación

Se ejecutó un experimento ilustrativo para la parcela de Iowa bajo SSP5-8.5 en 2050, con siembra basal el 15 de mayo, cultivar de ciclo medio, riego deficitario al 50 %, humedad inicial de 60 %, 180 kg N ha⁻¹, CO₂ = 520 ppm, anomalía térmica de +2.7 °C y anomalía de precipitación de −24 %. El escenario basal produjo 13,331 kg ha⁻¹, 585 mm de consumo hídrico, 220 mm de riego, CWSI máximo de 0.83, 54 días críticos, resiliencia de 63 puntos y retorno estimado de USD 2,603 ha⁻¹.

| Estrategia | Rendimiento (kg ha⁻¹) | Δ vs. basal | Agua consumida (mm) | Riego (mm) | CWSI máx. | Días críticos | Resiliencia | Retorno (USD ha⁻¹) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Basal | 13,331 | 0.00 % | 585 | 220 | 0.83 | 54 | 63 | 2,603 |
| Siembra 14 días antes | 13,331 | 0.00 % | 591 | 260 | 0.95 | 67 | 52 | 2,543 |
| Cultivar de ciclo corto | 11,731 | −12.00 % | 513 | 200 | 0.82 | 34 | 68 | 2,281 |
| Riego deficitario al 75 % | 14,303 | +7.29 % | 585 | 240 | 0.85 | 51 | 64 | 2,787 |
| Combinación de las tres | 12,587 | −5.58 % | 512 | 240 | 0.95 | 47 | 56 | 2,409 |

En este caso, solo el riego deficitario al 75 % aumentó rendimiento y retorno respecto de la línea basal. El ciclo corto redujo consumo de agua, días críticos y duración hasta madurez, pero introdujo una penalización de rendimiento. El adelanto de siembra no modificó el rendimiento y empeoró los indicadores de estrés. Por tanto, el experimento no confirma que una estrategia individual sea universalmente efectiva y tampoco satisface todavía la hipótesis de mitigar al menos 50 % de la pérdida climática. Los resultados son coherentes con un problema multiobjetivo: la alternativa que maximiza rendimiento no necesariamente minimiza agua o exposición al estrés.

## 4.5. Sensibilidad

El análisis global del *checkpoint* mostró una fuerte concentración de la varianza en la entrada de CO₂:

| Entrada | Índice de primer orden \(S_i\) | Efecto total \(S_{Ti}\) |
|---|---:|---:|
| Anomalía térmica | 0.0175 | 0.0163 |
| Anomalía de precipitación | 0.0050 | 0.0068 |
| CO₂ | 0.9772 | 0.9810 |

La suma de los índices de primer orden fue 0.9997, lo que indica interacciones pequeñas en el dominio muestreado. Sin embargo, esta dominancia no debe interpretarse como que el CO₂ controla causalmente 97.7 % del rendimiento real. En el conjunto de entrenamiento, CO₂, año y escenario evolucionan de manera correlacionada, y los mismos rendimientos observados fueron replicados bajo varias filas SSP. El resultado revela una sensibilidad interna potencialmente espuria y constituye una alerta de confusión temporal. Antes de usar el modelo para recomendaciones, se requiere una ablación sin CO₂, validación fuera de distribución y datos que desacoplen tendencia tecnológica, año y concentración atmosférica.

## 4.6. Vulnerabilidad espacial

Con la misma configuración climática y de manejo, los cuatro campos demostrativos produjeron el mismo rendimiento de 13,331 kg ha⁻¹ y una pérdida de 1.3 %, porque la identidad del campo y el suelo no entran en la cabeza de rendimiento. Las diferencias aparecieron únicamente en la dinámica hídrica diaria:

| Campo | CWSI máx. | CWSI medio | Días críticos | Resiliencia | Riego (mm) |
|---|---:|---:|---:|---:|---:|
| Parcela Experimental Ames Norte, Iowa | 0.83 | 0.46 | 54 | 63 | 220 |
| Rancho Santa Elena, El Bajío | 0.89 | 0.47 | 54 | 62 | 220 |
| Estancia La Vanguardia, Pampas | 0.84 | 0.46 | 55 | 63 | 220 |
| Finca Canal d’Urgell, Ebro | 0.85 | 0.47 | 58 | 62 | 240 |

El orden de vulnerabilidad hídrica simulada según CWSI máximo fue El Bajío > Ebro > Pampas > Iowa. No obstante, la igualdad de rendimiento confirma que la versión actual no constituye todavía un modelo espacialmente calibrado. El mapa debe describirse como visualización de escenarios edáficos y no como cartografía validada de vulnerabilidad. Una evaluación espacial genuina requiere coordenadas o identificadores de condado, parámetros de suelo observados y entrenamiento con rendimientos no agregados espacialmente.

# DISCUSIÓN

## 5.3. Cuándo y por qué el adelanto de siembra puede mitigar el estrés térmico en floración

El mecanismo agronómico esperado consiste en desplazar VT–R1 hacia una ventana más fresca. Una menor temperatura máxima durante antesis y emisión de estigmas puede preservar la viabilidad del polen, la receptividad de los estigmas, la sincronía antesis–emisión de estigmas y el número final de granos. Experimentos de campo han mostrado que el calor alrededor de floración reduce el crecimiento de la mazorca, aumenta fallas de polinización y aborto de granos, y que el ajuste de la fecha de siembra puede mejorar las condiciones térmicas y la fotosíntesis alrededor de floración (Guo et al., 2022; Wang et al., 2022; Wu et al., 2024).

Sin embargo, “siembra temprana” no es sinónimo de “adaptación efectiva”. Su efecto depende del clima local, humedad del suelo, riesgo de heladas, cultivar, duración del ciclo y coincidencia posterior con sequía. Kusmec y Schnable (2024), usando 80 años de ensayos de maíz en Estados Unidos y CMIP6, concluyeron que la adaptación fenológica por sí sola puede ser insuficiente para compensar las pérdidas por calentamiento. Esa cautela coincide con CeresPINN: en el experimento de Iowa, adelantar 14 días no cambió el rendimiento y elevó CWSI y días críticos.

La ausencia de respuesta de rendimiento tiene además una explicación computacional: la fecha de siembra desplaza la serie diaria, pero no es una entrada de la red ni retroalimenta la salida escalar final. En consecuencia, el prototipo puede visualizar un desplazamiento fenológico, pero todavía no puede probar que dicho desplazamiento mitigue la pérdida de rendimiento. Para evaluar esta hipótesis deberá incorporarse fecha de siembra, exposición térmica específica de VT–R1 y estrés hídrico acumulado como entradas aprendidas o como estados diferenciables que afecten explícitamente la formación de grano.

## 5.4. Eficiencia computacional frente a modelos de proceso tradicionales

La ventaja operativa del enfoque híbrido es que la red realiza una sola propagación hacia adelante y el postprocesador integra un balance diario simplificado, lo que permite interacción en tiempo casi real. En una medición local preliminar sobre CPU, 100 ejecuciones posteriores al calentamiento promediaron 8.10 ms por simulación estacional completa. Esta cifra demuestra aptitud para el estudio *what-if* de la interfaz, pero no constituye una comparación controlada con DSSAT, APSIM o CERES-Maize.

Los modelos de proceso resuelven más mecanismos, estados y dependencias de manejo, por lo que una comparación justa requiere idéntico hardware, horizonte, resolución temporal, entradas, salidas y tolerancias. AgriPINN ofrece evidencia externa de que una arquitectura diferenciable informada por procesos puede superar líneas base de aprendizaje profundo y un modelo de proceso en su propio banco de pruebas, con reducciones de RMSE de hasta 43 % y mayor eficiencia computacional; esas cifras no son transferibles automáticamente a CeresPINN (Shi et al., 2026). La conclusión defendible es, por tanto, que CeresPINN es suficientemente rápido para análisis interactivo, no que sea ocho veces más rápido o más exacto que los modelos tradicionales.

## 5.5. Ética y equidad

El uso de un gemelo digital para recomendar riego, fertilización o cambio varietal puede redistribuir riesgos y beneficios. Los datos parcelarios, productivos y de sensores pueden revelar prácticas, capacidad financiera o vulnerabilidades del productor; por ello, deben existir consentimiento informado, propósito limitado, cifrado, control de acceso, trazabilidad y reglas explícitas de propiedad y eliminación. La literatura sobre gemelos digitales agrícolas identifica precisamente privacidad, propiedad de datos, privilegio del desarrollador y brecha digital como problemas abiertos (Wang, 2024; Purcell, Neubauer, & Mallinger, 2023).

La equidad también exige evaluar desempeño por escala de explotación, región, régimen de riego y disponibilidad de sensores. Un modelo entrenado con datos agregados de Estados Unidos no debe recomendar inversiones en México, Argentina o España sin recalibración local. Las recomendaciones deben mostrar supuestos, rango de incertidumbre, alternativas de bajo costo y razones del resultado; nunca deben automatizar decisiones crediticias, aseguradoras o de acceso al agua. La decisión final debe permanecer bajo supervisión humana y conocimiento agronómico local.

Se propone una gobernanza mínima basada en cinco principios: soberanía del productor sobre sus datos; minimización y seguridad de datos; auditoría de sesgo y deriva; comunicación de incertidumbre y límites de dominio; y acceso equitativo mediante modos de baja conectividad y recomendaciones que no presupongan sensores o riego costoso. El gemelo debe optimizar bienestar agronómico y ambiental, no únicamente rendimiento o retorno monetario.

## 5.6. Limitaciones

Primero, aunque el origen NASS contiene 22,160 registros, la agregación usada por el entrenamiento produce solo 36 rendimientos anuales independientes. La expansión de cada año a tres filas SSP no crea nueva información de rendimiento y puede inducir confusión entre escenario, año, CO₂ y tendencia tecnológica. Segundo, el uso de una mediana anual nacional impide sostener que el modelo fue calibrado a nivel de condado o que captura heterogeneidad espacial.

Tercero, la regularización física se limita a restricciones de signo sobre temperatura y precipitación. No existe todavía residuo de Richards, término de frontera ni conservación de masa en la pérdida de entrenamiento; el balance hídrico se calcula en un postprocesador no diferenciable. Cuarto, la dominancia del CO₂ en la sensibilidad revela posible aprendizaje de una tendencia temporal no causal. Quinto, los efectos de cultivar, riego y nitrógeno se introducen mediante multiplicadores fijos y no mediante respuestas calibradas con tratamientos experimentales.

Sexto, fecha de siembra, suelo y estados diarios no retroalimentan el rendimiento final; esto explica la falta de efecto del adelanto de siembra y la igualdad de rendimiento entre campos. Séptimo, además del *holdout* aleatorio de ocho años, se ejecutó una evaluación prospectiva con entrenamiento en 1990–2017 y prueba en 2018–2025. El ensamble de diez semillas obtuvo RMSE = 855.22 kg ha⁻¹, MAE = 683.62 kg ha⁻¹ y R² = −0.8318, con IC bootstrap 95 % del R² [−5.0445, −0.0251]. El resultado revela generalización temporal insuficiente; no existe aún validación externa espacial o de campo. Octavo, las bandas de ensamble disponibles se originan en un sustituto determinista y aún no cuantifican conjuntamente incertidumbre climática, paramétrica y estructural del modelo entrenado.

Noveno, NEX-GDDP-CMIP6 reduce sesgos y resolución, pero conserva incertidumbres heredadas de los GCM y del método de *downscaling*. Décimo, la velocidad de inferencia se midió únicamente en un entorno de desarrollo y no contra modelos de proceso bajo un protocolo común. El repositorio sí conserva ahora el dataset procesado, el checkpoint, los scripts Q1, los artefactos, un manifiesto SHA-256, dependencias científicas fijadas y un workflow CI; esto hace reproducible la evidencia reportada, pero no corrige por sí mismo las limitaciones de validez externa. Estas limitaciones restringen el uso actual a exploración y desarrollo metodológico; el prototipo todavía no debe emplearse como sistema autónomo de prescripción agronómica.

# REFERENCIAS

Abramoff, R. Z., Ciais, P., Zhu, P., Hasegawa, T., Wakatsuki, H., & Makowski, D. (2023). Adaptation strategies strongly reduce the future impacts of climate change on simulated crop yields. *Earth’s Future, 11*, e2022EF003190. https://doi.org/10.1029/2022EF003190

Escribà-Gelonch, M., Liang, S., van Schalkwyk, P., Fisk, I., Long, N. V. D., & Hessel, V. (2024). Digital twins in agriculture: Orchestration and applications. *Journal of Agricultural and Food Chemistry, 72*(19), 10737–10752. https://doi.org/10.1021/acs.jafc.4c01934

Farea, A., Yli-Harja, O., & Emmert-Streib, F. (2024). Understanding physics-informed neural networks: Techniques, applications, trends, and challenges. *AI, 5*(3), 1534–1557. https://doi.org/10.3390/ai5030074

Guo, D., Chen, C., Li, X., Wang, R., Ding, Z., Ma, W., Wang, X., Li, C., Zhao, M., Li, M., & Zhou, B. (2022). Adjusting sowing date improves the photosynthetic capacity and grain yield by optimizing temperature condition around flowering of summer maize in the North China Plain. *Frontiers in Plant Science, 13*, 934618. https://doi.org/10.3389/fpls.2022.934618

Kusmec, A., & Schnable, P. S. (2024). Phenological adaptation is insufficient to offset climate change-induced yield losses in US hybrid maize. *Global Change Biology, 30*(10), e17539. https://doi.org/10.1111/gcb.17539

Melesse, T. Y. (2025). Digital twin-based applications in crop monitoring. *Heliyon, 11*(2), e42137. https://doi.org/10.1016/j.heliyon.2025.e42137

Purcell, W., Neubauer, T., & Mallinger, K. (2023). Digital twins in agriculture: Challenges and opportunities for environmental sustainability. *Current Opinion in Environmental Sustainability, 61*, 101252. https://doi.org/10.1016/j.cosust.2022.101252

Raissi, M., Perdikaris, P., & Karniadakis, G. E. (2019). Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. *Journal of Computational Physics, 378*, 686–707. https://doi.org/10.1016/j.jcp.2018.10.045

Sakthivel, S., Pazhanivelan, S., Thiruvarassan, S., Prabu, P. C., Gnanachitra, M., Rahale, C. S., Sivamurugan, A. P., Ragunath, K. P., & Satheesh, S. (2025). A comprehensive bibliometric review of DSSAT applications in maize yield prediction. *Maydica, 68*(1). https://creajournals.crea.gov.it/index.php/maydica/article/view/2633

Saltelli, A., Annoni, P., Azzini, I., Campolongo, F., Ratto, M., & Tarantola, S. (2010). Variance based sensitivity analysis of model output: Design and estimator for the total sensitivity index. *Computer Physics Communications, 181*(2), 259–270. https://doi.org/10.1016/j.cpc.2009.09.018

Shi, Y., Han, L., Zhang, X., Sobeih, T., Gaiser, T., Thuy, N. H., Behrend, D., Srivastava, A. K., Halder, K., & Ewert, F. (2025). Deep learning meets process-based models: A hybrid approach to agricultural challenges [Preprint]. *arXiv*. https://doi.org/10.48550/arXiv.2504.16141

Shi, Y., Han, L., Zhang, X., Sobeih, T., Gaiser, T., Thuy, N. H., Behrend, D., Srivastava, A. K., Halder, K., & Ewert, F. (2026). AgriPINN: A process-informed neural network for interpretable and scalable crop biomass prediction under water stress [Preprint]. *arXiv*. https://doi.org/10.48550/arXiv.2601.16045

Thrasher, B., Wang, W., Michaelis, A., Melton, F., Lee, T., & Nemani, R. (2022). NASA global daily downscaled projections, CMIP6. *Scientific Data, 9*, 262. https://doi.org/10.1038/s41597-022-01393-4

United States Department of Agriculture, National Agricultural Statistics Service. (s. f.). *Quick Stats database*. https://www.nass.usda.gov/Data_and_Statistics/

Wang, L. (2024). Digital twins in agriculture: A review of recent progress and open issues. *Electronics, 13*(11), 2209. https://doi.org/10.3390/electronics13112209

Wang, N., et al. (2022). Impacts of heat stress around flowering on growth and development dynamic of maize (*Zea mays* L.) ear and yield formation. *Plants, 11*(24), 3515. https://doi.org/10.3390/plants11243515

Wu, W., Yue, W., Bi, J., Zhang, L., Xu, D., Peng, C., Chen, X., & Wang, S. (2024). Influence of climatic variables on maize grain yield and its components by adjusting the sowing date. *Frontiers in Plant Science, 15*, 1411009. https://doi.org/10.3389/fpls.2024.1411009

Xiao, K., Zhou, X., Gui, H., Tian, Y., Chen, X., Li, Y., Matomela, N., & Xin, Q. (2025). Drought and extreme heat reduce wheat and maize production in the United States by lowering both crop yields and harvestable fraction. *Earth’s Future, 13*, e2024EF005557. https://doi.org/10.1029/2024EF005557

Zhang, R., Zhu, H., Chang, Q., & Mao, Q. (2025). A comprehensive review of digital twins technology in agriculture. *Agriculture, 15*(9), 903. https://doi.org/10.3390/agriculture15090903
