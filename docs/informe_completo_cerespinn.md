# Climate-Adaptive Digital Twin for Drought-Resilient Maize Production: Integration of CMIP6 Projections and a Physics-Informed Neural Network (CeresPINN)

**David Adrian Lucano Nieves¹, Geraldine Daniela Rojas Villegas¹**
¹ Universidad Nacional de Trujillo, Escuela de Ingeniería de Sistemas, Trujillo, Perú
Autores de correspondencia: dalucanoni@unitru.edu.pe; gdrojasvi@unitru.edu.pe

## RESUMEN

El cambio climático incrementa la exposición del maíz a sequías, olas de calor y desajustes entre disponibilidad hídrica y etapas fenológicas sensibles. Este estudio presenta CeresPINN, un prototipo de gemelo digital climático que integra observaciones de rendimiento de USDA-NASS, forzantes derivados de NASA NEX-GDDP-CMIP6, una red neuronal regularizada mediante conocimiento físico y un simulador estacional de fenología y balance hídrico en tres capas de suelo. La red utiliza siete entradas climáticas y temporales, cuatro capas ocultas de 128 unidades y dos cabezas para rendimiento y disponibilidad hídrica. Su función de pérdida combina error supervisado, regularización L2 y restricciones de monotonicidad que penalizan aumentos del rendimiento ante calentamiento y reducciones ante mayor precipitación dentro del régimen deficitario considerado. El *checkpoint* fue entrenado con 22,160 observaciones NASS agregadas en 36 medianas anuales y 98 registros climáticos regionales, con separación agrupada por año. Sobre ocho años retenidos, alcanzó RMSE = 712.1 kg ha⁻¹, MAE = 604.2 kg ha⁻¹ y R² = 0.8251. Un caso demostrativo para Iowa, SSP5-8.5 y 2050 mostró que el riego deficitario al 75 % elevó el rendimiento simulado en 7.29 %, mientras que adelantar la siembra 14 días no cambió el rendimiento y aumentó el estrés hídrico. El análisis global de sensibilidad atribuyó 97.72 % de la varianza del modelo al CO₂ dentro de los rangos analizados, señal de posible confusión entre CO₂, año y tendencia tecnológica. La igualdad de rendimiento entre cuatro campos demostró que la versión actual todavía no aprende vulnerabilidad espacial. CeresPINN permite exploración interactiva y trazable, pero requiere calibración espacial, validación externa, propagación de incertidumbre climática y acoplamiento diferenciable entre estados diarios y rendimiento antes de utilizarse como sistema prescriptivo.

**Palabras clave:** gemelo digital; maíz; CMIP6; NEX-GDDP; red neuronal informada por física; sequía; adaptación climática; balance hídrico.

---

## 1. INTRODUCCIÓN

El maíz es particularmente vulnerable a la coincidencia de calor extremo y déficit hídrico con la floración y el llenado de grano. En Estados Unidos, la sequía y las temperaturas extremas reducen no solo el rendimiento por unidad de superficie, sino también la fracción efectivamente cosechada; por ello, evaluar únicamente el rendimiento puede subestimar el riesgo productivo y alimentario (Xiao et al., 2025). Esta preocupación coincide con evaluaciones globales de nueva generación: Jägermeyr et al. (2021) estimaron que la productividad media del maíz hacia finales de siglo cambia de −6 % bajo SSP1-2.6 a cerca de −24 % bajo SSP5-8.5, mientras que Xu et al. (2024) proyectaron pérdidas medias de 21.4 % para maíz en el nordeste de China. Aunque estas magnitudes dependen de región, modelo y supuestos de adaptación, muestran que la respuesta no puede analizarse como una tendencia climática aislada.

Los modelos de cultivo basados en procesos, como DSSAT/CERES-Maize, APSIM, AquaCrop, WOFOST y SIMPLACE, constituyen la base mecanicista de gran parte de la investigación agronómica. La aplicación de DSSAT a la predicción de maíz mantiene un crecimiento bibliográfico anual de 12.93 %, con énfasis en cambio climático, nitrógeno, riego y adaptación (Sakthivel et al., 2025). Estos modelos pueden operar con clima futuro y no deben caracterizarse como incapaces de usar CMIP6; sus dificultades prácticas se relacionan con calibración, parametrización local, costo de ensambles extensos y propagación de incertidumbre. En el Corn Belt, incorporar variables simuladas por APSIM a modelos de aprendizaje automático redujo el RMSE de predicción entre 7 % y 20 %, lo que evidencia el valor de combinar mecanismos y datos (Shahhosseini et al., 2021).

La literatura de gemelos digitales agrícolas propone una representación virtual que recibe datos del sistema físico, actualiza sus estados y permite explorar decisiones. Sin embargo, todavía son escasos los gemelos diseñados específicamente para integrar proyecciones climáticas de largo plazo con simulación agronómica interactiva (Escribà-Gelonch et al., 2024). Melesse (2025) concluye que los modelos híbridos —físicos y basados en datos— ofrecen una combinación especialmente útil de precisión y flexibilidad, aunque la reproducción de procesos biológicos, la integración de fuentes heterogéneas y la sincronización en zonas rurales continúan siendo barreras. Zhang et al. (2025c) organizan estos sistemas en capas de percepción, red y aplicación y resaltan que formatos, escalas espaciales, frecuencias temporales y limitaciones de conectividad complican la integración. Purcell et al. (2023) añaden una advertencia socioecológica: sin un modelo conceptual claro, una optimización de caja negra puede generar recomendaciones incompatibles con las dependencias biológicas o ambientales del agroecosistema.

Las redes neuronales informadas por física (PINN) ofrecen un puente entre ambos paradigmas. En su formulación clásica, principios físicos o ecuaciones gobernantes se incorporan a la función de pérdida para restringir el espacio de soluciones (Raissi, Perdikaris, & Karniadakis, 2019; Farea, Yli-Harja, & Emmert-Streib, 2024). En agricultura, Shi et al. (2025) mostraron que los marcos híbridos PBM–DL son más robustos que los modelos aislados cuando hay ruido, pocos datos o ubicaciones no vistas. Posteriormente, AgriPINN restringió las trayectorias de biomasa mediante procesos biofísicos, recuperó variables latentes de estrés y redujo el RMSE hasta 43 % respecto de determinadas líneas base (Shi et al., 2026). Otros trabajos han incrustado relaciones de respuesta del rendimiento al agua en redes recurrentes (Miranda et al., 2025), combinado asimilación de datos y aprendizaje automático para reducir costos regionales en más de 99.8 % (Yu et al., 2025), o acoplado PINN y AquaCrop para optimizar riego deficitario (Zhang et al., 2025a).

CeresPINN se ubica en esta transición, pero con un alcance que debe definirse con precisión. El componente entrenado no resuelve todavía la ecuación de Richards dentro de su pérdida: emplea restricciones diferenciales de monotonicidad sobre temperatura y precipitación. La dinámica hídrica de tres capas se calcula después mediante un simulador determinista acoplado. En consecuencia, el sistema se describe como una red neuronal físicamente regularizada dentro de un gemelo digital híbrido, no como una PINN de Richards completamente diferenciable.

El objetivo general fue desarrollar y auditar un prototipo capaz de vincular observaciones históricas de rendimiento, forzantes CMIP6 y alternativas de manejo para explorar riesgo climático en maíz. Los objetivos específicos fueron: (i) documentar la arquitectura y el linaje de datos; (ii) evaluar el rendimiento predictivo mediante retención agrupada por año; (iii) examinar estrategias de fecha de siembra, duración varietal y riego; (iv) cuantificar la sensibilidad interna del modelo; y (v) identificar las condiciones necesarias para una validación espacial y externa.

El protocolo original planteó dos hipótesis: H0, ausencia de diferencia entre SSP2-4.5 y SSP5-8.5 en 2050; y H1, pérdida de al menos 15 % bajo SSP5-8.5 con mitigación de al menos 50 % mediante adaptación. Estas hipótesis se conservan como preguntas de investigación, pero no se consideran confirmadas: el *checkpoint* actual no contiene SSP2-4.5 en su expansión de entrenamiento y el módulo de adaptación todavía utiliza multiplicadores deterministas.

---

## 2. MARCO CONCEPTUAL Y ESTADO DEL ARTE

### 2.1. Gemelos digitales agrícolas y toma de decisiones

Un gemelo digital agrícola integra una entidad física, su representación computacional y un flujo de información que permite monitorizar, simular y retroalimentar decisiones. La revisión de Escribà-Gelonch et al. (2024) señala que existen gemelos climáticos y meteorológicos relacionados con agricultura, pero persiste una carencia de implementaciones específicamente agrícolas. Melesse (2025) organiza el gemelo en cinco capas —espacio físico, datos, red, espacio digital y aplicación— y destaca que los modelos híbridos pueden unir conocimiento fisiológico, sensores y adaptabilidad estadística. En una taxonomía más compacta, Zhang et al. (2025c) distinguen percepción, red y aplicación, pero advierten que la interoperabilidad y la conectividad rural limitan la sincronización en tiempo real.

La utilidad principal del gemelo no es producir una cifra aislada, sino comparar escenarios *what-if*. Purcell et al. (2023) consideran esta capacidad especialmente relevante para adaptación climática, siempre que se reconozcan las dependencias ecológicas y la incertidumbre. En trigo, Xu et al. (2025a) implementaron un ciclo de retroalimentación en tiempo real para actualizar simulaciones y decisiones de manejo, mostrando el valor operacional del concepto. CeresPINN adopta esta lógica en su interfaz; sin embargo, al no recibir todavía sensores en línea, corresponde con mayor precisión a un prototipo de gemelo digital orientado a escenarios.

### 2.2. Modelos híbridos, aprendizaje informado y predicción de rendimiento

La evidencia disponible no sostiene que un algoritmo sea universalmente superior. Los resultados dependen de datos, escala, diseño de validación y variable objetivo. Han et al. (2024) encontraron que Random Forest alcanzó R² = 0.77 y MAPE = 7.1 % al predecir rendimiento de cultivares y apoyar selección varietal a nivel de distrito o condado. Cheng et al. (2022) obtuvieron R² = 0.77 y rRMSE = 16.15 % al combinar productividad primaria, temperatura superficial, evapotranspiración e índice de área foliar; la predicción conservó utilidad hasta 24 días antes de madurez. Pukrongta, Taparugssanagorn y Sangpradit (2023) evaluaron el uso de clorofila e índices de vegetación para estimar rendimiento, ilustrando el valor de mediciones próximas al cultivo, aunque ese estudio de conferencia no debe confundirse con investigaciones UAV de 17,100 imágenes citadas erróneamente en algunas matrices bibliográficas.

El agua disponible aparece de forma consistente como variable estructural. Hlavinka et al. (2017) compararon 16 indicadores y encontraron que la evapotranspiración real acumulada entre mayo y agosto explicó mejor la variación del rendimiento del maíz forrajero, con R² = 0.77. Miranda et al. (2025) partieron igualmente de la relación entre disponibilidad de agua y productividad para construir una pérdida informada que mantiene variables intermedias dentro de límites agronómicos. Su PG-LSTM alcanzó R² = 0.82, pero perdió capacidad de transferencia en años no vistos, recordando que una restricción física no sustituye la validación temporal.

Los enfoques híbridos intentan aprovechar estas relaciones. Shi et al. (2025) mostraron mayor robustez ante ruido, muestras pequeñas y generalización espacial al combinar modelos de proceso y aprendizaje profundo. Alimagham et al. (2025) reprodujeron salidas de WOFOST con diferencias inferiores a 20 % en 95 % de los casos mediante aprendizaje guiado por variables ecofisiológicas en regiones con pocos datos. Dokoohaki et al. (2022) utilizaron emuladores para sustituir APSIM durante calibración y redujeron el RMSE fuera de muestra de 2532 a 1554 kg ha⁻¹. Yu et al. (2025) combinaron asimilación de datos, SWAP y emuladores, manteniendo precisión regional con una reducción computacional superior a 99.8 %. Estos antecedentes justifican la búsqueda de inferencia rápida, pero también muestran que la calidad del emulador está limitada por los supuestos del modelo que lo genera.

PINN-SM ofrece un antecedente hidrológico más directo: Chavoshi et al. (2025) reportaron reducciones de RMSE frente a una PINN convencional y una ANN, con mejoras particularmente claras durante picos de humedad y capacidad de transferencia con pocos datos nuevos. En agricultura, el DR-DPINN acoplado a AquaCrop incrementó en un caso de Xinjiang el rendimiento en 10.08 % y la eficiencia del uso del agua en 11.15 % al redistribuir 472 mm de riego (Zhang et al., 2025a). AgriPINN mostró que una función de pérdida informada por procesos puede actuar como restricción biofísica y recuperar estados latentes sin supervisión directa (Shi et al., 2026). Estos modelos son referentes más exigentes que CeresPINN, porque integran procesos diferenciables o datos experimentales que la versión actual aún no incorpora.

Los modelos fraccionarios podrían representar memoria, heterogeneidad y transporte no local que una difusión clásica omite, y las fPINN aparecen como una posible vía para resolver tales sistemas con datos escasos (Granella, 2026). No obstante, su costo, identificabilidad paramétrica y falta de *benchmarks* hacen que esa extensión sea una línea futura, no parte de la implementación presente.

### 2.3. CMIP6, escenarios SSP y reducción de escala

CMIP6 se organiza alrededor de experimentos comunes DECK, simulaciones históricas estandarizadas y proyectos de intercomparación especializados, lo que permite comparar modelos y preguntas científicas bajo una infraestructura federada (Eyring et al., 2016). ScenarioMIP seleccionó como nivel prioritario SSP1-2.6, SSP2-4.5, SSP3-7.0 y SSP5-8.5 para cubrir un rango amplio de forzamiento e incertidumbre socioeconómica; SSP3-7.0 añadió una trayectoria no mitigada que cubría una brecha de CMIP5 (O’Neill et al., 2016).

NASA NEX-GDDP-CMIP6 ofrece proyecciones diarias históricas y futuras de 1950 a 2100, derivadas de 35 modelos, cinco experimentos y ocho variables a 0.25° mediante una variante diaria de corrección de sesgo y desagregación espacial (Thrasher et al., 2022). Esta resolución es adecuada para estudios regionales, pero no equivale a clima parcelario observado. La reducción de escala añade valor, aunque conserva errores del GCM y dificultades para representar precipitación convectiva, subdiaria y extrema, especialmente cuando las relaciones estadísticas dejan de ser estacionarias (Maraun et al., 2010).

La literatura adjunta muestra varias alternativas de corrección. En Senegal, CDF-t redujo el sesgo medio de precipitación anual de −223.37 a −49.17 mm y el térmico de +0.8 a +0.22 °C preservando tendencias de largo plazo (Mbengue et al., 2026). QDM corrige distribuciones históricas y conserva cambios específicos por cuantil, lo que ayuda a mantener señales de calentamiento en la cola superior (de Souza et al., 2026). Galmarini et al. (2024) encontraron que los métodos multivariados son preferibles cuando el modelo de cultivo responde a relaciones conjuntas de temperatura, precipitación y radiación. CeresPINN no aplicó adicionalmente CDF-t, QDM ni MBCn: utilizó los datos regionales NEX ya procesados y plantillas cuando faltaron valores. Estas referencias definen mejoras futuras y no deben describirse como pasos ya ejecutados.

CHIRPS y CHIRTS son fuentes potenciales para observación histórica. Alsilibe et al. (2023) encontraron buen comportamiento estacional de CHIRPS en una cuenca árida, con correlación de 0.79 en la estación húmeda, aunque menor habilidad diaria y para lluvias ligeras. Uscamayta-Ferrano et al. (2025) refinaron CHIRTS de 5 a 1 km mediante ML y restricciones físicas; Random Forest redujo el RMSE de temperatura mínima en 47.1 %, pero las mejoras temporales fueron pequeñas y dependieron de la representatividad espacial. Ninguna de estas dos fuentes formó parte efectiva del *checkpoint* reportado, por lo que se consideran insumos recomendados para la siguiente versión.

### 2.4. Adaptación de maíz bajo cambio climático

La adaptación no es una intervención única. Wakatsuki et al. (2023) estimaron un potencial medio de 4–5 % por grado de calentamiento, menor en regiones ya cálidas; fecha de siembra, cultivar, riego y fertilizante concentran aproximadamente 90 % de las opciones estudiadas. Minoli et al. (2022) estimaron que adaptar oportunamente los periodos de crecimiento podría elevar rendimientos actuales cerca de 12 % a escala global, mientras que Abramoff et al. (2023) identificaron el método de riego como una de las estrategias más eficaces para evitar grandes pérdidas de maíz.

La eficacia depende de contexto y recursos. En el acuífero Ogallala, Zhang et al. (2025b) observaron que el rendimiento responde rápidamente al riego cuando hay déficit, pero el beneficio marginal disminuye conforme aumenta el agua disponible. Yang et al. (2026) proyectaron que los requerimientos de riego de maíz podrían aumentar 26.4 % bajo SSP5-8.5 hacia finales de siglo, aunque acortar el ciclo 15 y 30 días redujo el requerimiento total 9 % y 14 %. Niu et al. (2026) mostraron que ajustar conjuntamente fecha de siembra y nitrógeno puede reducir exposición térmica y lixiviación, pero también que APSIM con clima diario no resuelve todos los daños fisiológicos de extremos transitorios. En conjunto, estas evidencias justifican comparar siembra, ciclo y riego, pero no garantizan que una estrategia sea beneficiosa en todos los ambientes.

---

## 3. MATERIALES Y MÉTODOS

### 3.1. Dominio de estudio y alcance espacial

El dominio conceptual corresponde a la producción de maíz de Estados Unidos, con interés particular en el Corn Belt y un caso demostrativo localizado en Story County, Iowa. La calibración efectiva no fue espacial: 22,160 registros NASS de condado y estado fueron agregados mediante la mediana anual nacional. Por ello, los criterios originalmente propuestos de exigir 20 años por condado y excluir condados con más de 50 % de riego no se aplicaron al *checkpoint* vigente. El análisis espacial de cuatro campos —Iowa, El Bajío, Pampas y Ebro— se utilizó únicamente para probar la respuesta del simulador a perfiles edáficos contrastantes.

### 3.2. Fuentes y procesamiento de datos

#### 3.2.1. Rendimiento observado

Se utilizaron datos de rendimiento de maíz de USDA-NASS Quick Stats entre 1990 y 2025. Tras convertir la columna de rendimiento a valores numéricos y eliminar faltantes, se conservaron 22,160 observaciones. Para estabilizar el entrenamiento, se calculó la mediana por año, obteniendo 36 objetivos independientes expresados en bu acre⁻¹. La conversión utilizada fue 1 bu acre⁻¹ = 62.77 kg ha⁻¹.

#### 3.2.2. Forzantes climáticos

El artefacto climático contenía 98 filas regionales de NEX-GDDP-CMIP6. Las temperaturas máximas se convirtieron de kelvin a grados Celsius y se expresaron como anomalías respecto de la media histórica 1990–2014 cuando esta estuvo disponible. La precipitación, originalmente en kg m⁻² s⁻¹, se convirtió a acumulado de una estación mayo–septiembre de 153 días. Para años intermedios entre muestras NEX se aplicó interpolación lineal dentro de cada escenario.

Cuando faltó una combinación año–escenario, se emplearon plantillas representativas: SSP1-2.6 (+0.9 °C, −2 % de precipitación, 445 ppm CO₂, riesgo de ola de calor 0.15), SSP3-7.0 (+1.8 °C, −12 %, 480 ppm, 0.42) y SSP5-8.5 (+2.7 °C, −24 %, 520 ppm, 0.78). Después de 2026, la plantilla añade 0.02 °C y 1.5 ppm CO₂ por año hasta que un valor NEX la sustituye. Estas reglas aseguran continuidad operativa, pero son supuestos del prototipo, no proyecciones probabilísticas.

#### 3.2.3. Suelo y observaciones futuras

El simulador contiene cuatro perfiles fijos de capacidad de campo, punto de marchitez, saturación y conductividad para los campos demostrativos. No se utilizaron SoilGrids, POLARIS ni mediciones parcelarias durante el entrenamiento. Xu, Torres-Rojas, Vergopolan y Chaney (2023) demostraron que mapas modernos de propiedades edáficas y funciones de pedotransferencia pueden mejorar la representación vertical e hidráulica de la humedad del suelo. La integración de estos productos constituye una prioridad para sustituir perfiles codificados por parámetros espacialmente trazables.

### 3.3. Arquitectura y formulación del modelo

#### 3.3.1. Entradas, estados y salidas

La entrada directa de la red fue

\[
\mathbf{x}=[a,\Delta T,\Delta P,CO_2,H,P_s,CDD],
\]

donde \(a\) es el año, \(\Delta T\) la anomalía térmica, \(\Delta P\) la anomalía porcentual de precipitación, \(CO_2\) la concentración atmosférica, \(H\) el riesgo de ola de calor, \(P_s\) la precipitación estacional y \(CDD\) un indicador de días secos consecutivos. Las entradas se normalizaron mediante media y desviación estándar del conjunto de entrenamiento; el rendimiento se escaló a [0,1].

La red es un MLP de cuatro capas ocultas, 128 unidades por capa, activación `tanh` y *dropout* = 0.05. Una cabeza 128–64–1 predice rendimiento; otra 128–32–1 con salida sigmoidal genera un indicador hídrico entre 0 y 1. Las variables de manejo —fecha, cultivar, riego y nitrógeno— y las propiedades del suelo ingresan al simulador posterior, no a la red entrenada.

Los estados diarios incluyen GDD, estadio VE–R6, LAI, profundidad radical, altura de dosel, humedad en 0–30, 30–60 y 60–100 cm, evapotranspiración, infiltración, drenaje, CWSI y estrés térmico. Las salidas resumen rendimiento, biomasa, madurez, agua consumida, riego, productividad hídrica, retorno económico y resiliencia.

#### 3.3.2. Restricciones físicas y balance de procesos

La salida aprendida se representa como \(\hat{Y}=f_\theta(\mathbf{x})\). El entrenamiento impone dos priors locales: \(\partial\hat{Y}/\partial\Delta T\leq0\) y \(\partial\hat{Y}/\partial P_s\geq0\). Estas relaciones son razonables en el régimen térmico supraóptimo e hídrico deficitario estudiado, pero no son universales.

El postprocesador calcula un balance por capa:

\[
S_{l,t+1}=S_{l,t}+I_{l,t}-ET_{l,t}-D_{l,t},
\]

donde \(S\) es almacenamiento, \(I\) infiltración por lluvia y riego, \(ET\) extracción evaporativa y transpiratoria y \(D\) percolación. Los estados se restringen por punto de marchitez, capacidad de campo y saturación. La evapotranspiración de referencia se aproxima con Priestley–Taylor, se multiplica por un coeficiente fenológico y se distribuye según profundidad radical. El CWSI se estima como \(1-K_s\). Esta implementación es un balance de reservorios inspirado en Richards, no una solución numérica del residuo PDE.

#### 3.3.3. Función de pérdida y entrenamiento

La pérdida implementada fue

\[
\mathcal{L}=\mathcal{L}_{data}+0.5\mathcal{L}_{mono}+10^{-4}\|\theta\|_2^2,
\]

\[
\mathcal{L}_{data}=\frac{1}{N}\sum_{i=1}^{N}(y_i-\hat{y}_i)^2,
\]

\[
\mathcal{L}_{mono}=E\left[ReLU\left(\frac{\partial\hat y}{\partial\Delta T}\right)\right]
+E\left[ReLU\left(-\frac{\partial\hat y}{\partial P_s}\right)\right]+\mathcal{L}_{range}.
\]

Las derivadas se obtuvieron con `torch.autograd`. \(\mathcal{L}_{range}\) mantiene el indicador hídrico entre cero y uno, aunque la activación sigmoidal ya satisface ese intervalo. El entrenamiento usó Adam, tasa 0.001, decaimiento 10⁻⁵, lotes de 64, 300 épocas y semilla 42. No se implementaron \(\mathcal{L}_{Richards}\) ni \(\mathcal{L}_{boundary}\); los valores mostrados con esos nombres por una versión de la interfaz son marcadores heredados y se excluyeron del análisis.

#### 3.3.4. Módulo de comparación de manejo

El módulo evalúa alternativas discretas y no realiza todavía optimización matemática. El rendimiento de la red se ajusta con multiplicadores de ciclo: 0.88, 1.00 y 1.12 para corto, medio y largo; y de riego: 0.85, 0.96, 1.03, 1.08 y 1.06 para secano, déficit 50 %, déficit 75 %, óptimo y sensor inteligente. Nitrógeno y CO₂ aportan respuestas acotadas. Estos factores son reglas del prototipo, no coeficientes calibrados con tratamientos experimentales.

Para cada estrategia \(j\), el cambio relativo se calculó como

\[
\Delta Y_j=100(Y_j-Y_0)/Y_0.
\]

El diseño compara rendimiento, consumo de agua, riego, CWSI, días críticos, resiliencia y retorno. Estudios como Zhang et al. (2025a) demuestran que una optimización real de riego requiere datos experimentales, calibración y un algoritmo de búsqueda; por ello, el módulo se denomina comparación de alternativas.

### 3.4. Calibración y validación

Cada mediana anual fue replicada en tres escenarios, generando 108 filas: 84 de entrenamiento y 24 de prueba. La partición se realizó por año completo para impedir que copias SSP del mismo objetivo aparecieran en ambos conjuntos. Los años de prueba fueron 1991, 1992, 1998, 2001, 2003, 2004, 2011 y 2024.

Se calcularon MSE, RMSE, MAE y R². Para la evaluación por año, las tres predicciones de escenario se promediaron antes de calcular métricas. Se utilizó además Kolmogorov–Smirnov como comprobación descriptiva de la distribución, reconociendo su baja potencia con ocho pares.

No se realizó validación externa. El protocolo recomendado es reservar condados completos, campañas posteriores y ensayos con rendimiento, humedad y fenología; comparar contra una media histórica, una red sin regularización y un modelo de proceso; y reportar cobertura de intervalos además de error puntual.

### 3.5. Escenarios climáticos

La interfaz reconoce los cuatro SSP prioritarios de ScenarioMIP, pero el conjunto que entrenó el *checkpoint* contiene solamente SSP1-2.6, SSP3-7.0 y SSP5-8.5. SSP2-4.5 aparece en módulos auxiliares, no como categoría de la expansión de entrenamiento. En consecuencia, la comparación formal SSP2-4.5 versus SSP5-8.5 se pospuso.

### 3.6. Estrategias de adaptación

Se evaluaron tres intervenciones: adelanto de siembra de 14 días, cultivar de ciclo corto y riego deficitario al 75 %, además de su combinación. La selección está respaldada por la literatura: fecha, ciclo, riego y fertilización concentran la mayoría de las adaptaciones analizadas (Wakatsuki et al., 2023); el ajuste del periodo de crecimiento puede recuperar rendimiento (Minoli et al., 2022); y el riego es especialmente efectivo bajo déficit, aunque con beneficios marginales decrecientes (Abramoff et al., 2023; Zhang et al., 2025b).

### 3.7. Análisis estadístico e incertidumbre

La sensibilidad del *checkpoint* se calculó con un diseño Saltelli–Jansen de 32,768 muestras, semilla 42 y año 2050. Se variaron temperatura entre +2.2 y +3.4 °C, precipitación entre −28 % y −15 % y CO₂ entre 500 y 600 ppm, informando índices de primer orden \(S_i\) y efecto total \(S_{Ti}\). Estos valores cuantifican varianza interna en esos rangos, no causalidad.

La incertidumbre futura deberá separar observación, GCM/SSP, parámetros y estructura. Los intervalos auxiliares actuales se generan con una curva determinista y no se reportaron como intervalos del PINN. Una implementación completa deberá ejecutar cada miembro NEX a través del *checkpoint*, reentrenar un ensamble de semillas y propagar parámetros edáficos y de manejo.

---

## 4. RESULTADOS

### 4.1. Caracterización de los datos y escenarios

El linaje final fue NASS + NEX-GDDP: 22,160 observaciones de rendimiento, 36 objetivos anuales y 98 filas climáticas regionales. La expansión produjo 108 ejemplos, pero el tamaño efectivo del objetivo siguió siendo 36. Esta diferencia es fundamental: la replicación por escenario condiciona el modelo, pero no añade observaciones independientes.

| Componente | Resultado verificable |
|---|---:|
| Observaciones NASS originales | 22,160 |
| Periodo | 1990–2025 |
| Medianas anuales independientes | 36 |
| Filas NEX regionales | 98 |
| Escenarios de entrenamiento | SSP1-2.6, SSP3-7.0, SSP5-8.5 |
| Filas de entrenamiento / prueba | 84 / 24 |

### 4.2. Desempeño retrospectivo

En las 24 filas de prueba, CeresPINN obtuvo MSE = 130.6244 (bu acre⁻¹)², RMSE = 11.4291 bu acre⁻¹ (717.4 kg ha⁻¹), MAE = 9.8505 bu acre⁻¹ (618.3 kg ha⁻¹) y R² = 0.8225. Tras agregar por año, RMSE fue 712.1 kg ha⁻¹, MAE 604.2 kg ha⁻¹ y R² 0.8251.

| Métrica | 24 filas SSP | 8 años agregados |
|---|---:|---:|
| RMSE (kg ha⁻¹) | 717.4 | 712.1 |
| MAE (kg ha⁻¹) | 618.3 | 604.2 |
| R² | 0.8225 | 0.8251 |

La prueba KS produjo \(D=0.25\) y \(p=0.9801\). No se detectó diferencia entre distribuciones, pero el resultado no establece equivalencia por el bajo tamaño muestral. El desempeño es comparable a valores de R² cercanos a 0.77–0.82 informados en estudios de cultivar, indicadores remotos y aprendizaje informado (Han et al., 2024; Cheng et al., 2022; Miranda et al., 2025), aunque las escalas y diseños no permiten una comparación directa.

### 4.3. Proyección demostrativa bajo SSP5-8.5

Se ejecutó un caso para Ames Norte, Iowa, en 2050, con +2.7 °C, −24 % de precipitación, CO₂ = 520 ppm, siembra el 15 de mayo, ciclo medio, riego deficitario al 50 %, humedad inicial de 60 % y 180 kg N ha⁻¹. La salida fue 13,331 kg ha⁻¹, pérdida relativa de 1.3 % frente al potencial parametrizado, 585 mm consumidos, 220 mm de riego, CWSI máximo 0.83 y 54 días críticos.

Este valor no constituye una proyección regional de CMIP6: es una simulación puntual condicionada por la plantilla y los multiplicadores del prototipo. No se informó una curva SSP1–SSP5 porque el experimento factorial con miembros GCM aún no se ejecutó. Las pérdidas de 6–24 % publicadas en evaluaciones regionales o globales (Xiao et al., 2025; Jägermeyr et al., 2021; Xu et al., 2024) se emplean como contexto, no como sustituto de resultados propios.

### 4.4. Efectividad de la adaptación

| Estrategia | Rendimiento (kg ha⁻¹) | Δ vs. basal | Agua (mm) | Riego (mm) | CWSI máx. | Días críticos | Resiliencia | Retorno (USD ha⁻¹) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Basal | 13,331 | 0.00 % | 585 | 220 | 0.83 | 54 | 63 | 2,603 |
| Siembra 14 días antes | 13,331 | 0.00 % | 591 | 260 | 0.95 | 67 | 52 | 2,543 |
| Ciclo corto | 11,731 | −12.00 % | 513 | 200 | 0.82 | 34 | 68 | 2,281 |
| Riego deficitario 75 % | 14,303 | +7.29 % | 585 | 240 | 0.85 | 51 | 64 | 2,787 |
| Estrategia combinada | 12,587 | −5.58 % | 512 | 240 | 0.95 | 47 | 56 | 2,409 |

Solo el riego al 75 % aumentó simultáneamente rendimiento y retorno. El ciclo corto redujo consumo, días críticos y duración, pero perdió 12 % de rendimiento. Adelantar la siembra no modificó la salida de rendimiento y agravó el estrés diario. El resultado apoya la idea de beneficios decrecientes del agua y compromisos entre productividad y eficiencia (Zhang et al., 2025b), pero no confirma la H1 ni puede generalizarse.

### 4.5. Sensibilidad

| Entrada | \(S_i\) | \(S_{Ti}\) |
|---|---:|---:|
| Anomalía térmica | 0.0175 | 0.0163 |
| Anomalía de precipitación | 0.0050 | 0.0068 |
| CO₂ | 0.9772 | 0.9810 |

Los índices de primer orden sumaron 0.9997. La dominancia del CO₂ no se interpretó fisiológicamente: CO₂, año y escenario están correlacionados y cada rendimiento anual se replicó en tres escenarios. El análisis revela dependencia interna y posible confusión temporal. Se requiere una ablación sin CO₂, separación cronológica y variables de tendencia tecnológica.

### 4.6. Vulnerabilidad espacial

| Campo demostrativo | CWSI máx. | CWSI medio | Días críticos | Resiliencia | Riego (mm) |
|---|---:|---:|---:|---:|---:|
| Ames Norte, Iowa | 0.83 | 0.46 | 54 | 63 | 220 |
| Santa Elena, El Bajío | 0.89 | 0.47 | 54 | 62 | 220 |
| La Vanguardia, Pampas | 0.84 | 0.46 | 55 | 63 | 220 |
| Canal d’Urgell, Ebro | 0.85 | 0.47 | 58 | 62 | 240 |

El orden por CWSI máximo fue El Bajío > Ebro > Pampas > Iowa. Los cuatro campos produjeron 13,331 kg ha⁻¹ porque el campo y el suelo no forman parte de la cabeza de rendimiento. En consecuencia, la interfaz muestra vulnerabilidad hídrica del simulador, no vulnerabilidad espacial aprendida ni validada.

---

## 5. DISCUSIÓN

### 5.1. Evaluación de las hipótesis

H0 no pudo contrastarse porque SSP2-4.5 no integra la expansión usada para entrenar el *checkpoint*. H1 tampoco quedó confirmada: no se ejecutó un ensamble GCM completo, la pérdida del caso demostrativo fue 1.3 % y ninguna combinación mitigó una pérdida climática igual o superior a 15 %. El riego al 75 % mejoró 7.29 % respecto del manejo basal, pero ese efecto procede parcialmente de un multiplicador predefinido.

Esta conclusión negativa es metodológicamente más valiosa que una aceptación basada en estadísticas sustitutas. Los estudios externos muestran que las pérdidas pueden ser importantes y que las adaptaciones ayudan (Jägermeyr et al., 2021; Xu et al., 2024; Abramoff et al., 2023), pero no sustituyen la evidencia del sistema estudiado.

### 5.2. Contraste con la literatura

El R² interno de 0.8251 indica que la red reproduce una parte sustancial de la variación anual retenida. Su magnitud es semejante al R² = 0.82 de Miranda et al. (2025) y superior al 0.77 de varios estudios de ML (Han et al., 2024; Cheng et al., 2022), pero la comparación debe limitarse porque CeresPINN usa objetivos nacionales agregados y solo ocho años de prueba. La literatura híbrida muestra mejoras reales cuando los estados de proceso entran al aprendizaje: APSIM + ML redujo RMSE 7–20 % (Shahhosseini et al., 2021), WOFOST + ML reprodujo escenarios con diferencias acotadas (Alimagham et al., 2025) y AgriPINN aprendió variables latentes (Shi et al., 2026). CeresPINN todavía calcula sus estados diarios fuera de la red; integrarlos es el paso necesario para alcanzar una hibridación comparable.

La importancia agronómica de ET y humedad respalda esa extensión. Hlavinka et al. (2017) identificaron ET real acumulada como el indicador de sequía más explicativo, y Yu et al. (2025) encontraron que radiación, humedad y lluvia en elongación fueron determinantes en la estimación regional. La sensibilidad casi exclusiva al CO₂ de CeresPINN contradice este patrón y debe entenderse como diagnóstico de confusión, no descubrimiento.

### 5.3. Por qué la fecha de siembra puede —o no— mitigar el estrés térmico

Adelantar la siembra puede desplazar VT–R1 hacia días más frescos, preservar viabilidad del polen, sincronía antesis–emisión de estigmas y número de granos. Minoli et al. (2022) mostraron potencial global al adaptar periodos, y Niu et al. (2026) identificaron una fecha más temprana bajo SSP5-8.5 para disminuir estrés térmico en su sistema. No obstante, la respuesta depende de temperatura del suelo, heladas, lluvia, cultivar, fotoperiodo y exposición posterior a sequía. Acortar el ciclo puede reducir demanda de riego, como mostró Yang et al. (2026), pero también sacrificar potencial de rendimiento.

En CeresPINN, la siembra temprana empeoró CWSI y no cambió rendimiento. La causa es tanto climática como arquitectónica: desplaza la serie diaria, pero no entra en la red ni retroalimenta el rendimiento escalar. Para probar el mecanismo, fecha de siembra, temperaturas máximas en VT–R1, duración del intervalo antesis–estigmas y estrés acumulado deben afectar directamente formación de grano.

### 5.4. Eficiencia computacional

Una medición local exploratoria, con 100 ejecuciones en CPU después de calentamiento, promedió 8.10 ms por simulación estacional. Esto demuestra capacidad interactiva, no superioridad frente a DSSAT, APSIM o AquaCrop. Una comparación justa requiere mismo hardware, resolución, entradas, estados y precisión. Dokoohaki et al. (2022) y Yu et al. (2025) muestran que los emuladores reducen costos de manera sustancial; AgriPINN también informó mayor eficiencia en su banco de pruebas (Shi et al., 2026). Ninguna de esas razones permite trasladar automáticamente una aceleración “8×” a CeresPINN.

### 5.5. Calidad climática, suelo e incertidumbre espacial

NEX-GDDP es una base defendible por su cobertura diaria, escenarios y 0.25° (Thrasher et al., 2022), pero no elimina la incertidumbre del GCM ni representa microclima de parcela. CDF-t, QDM y MBCn ofrecen alternativas para reducir sesgo y preservar señales o dependencias (Mbengue et al., 2026; de Souza et al., 2026; Galmarini et al., 2024). La implementación futura deberá elegir y validar un método, no acumularlos sin criterio. CHIRPS y CHIRTS pueden servir como referencia histórica, con precaución en extremos diarios y transferencia topográfica (Alsilibe et al., 2023; Uscamayta-Ferrano et al., 2025).

La igualdad de rendimiento entre campos también evidencia que el suelo no está acoplado a la salida aprendida. Mapas digitales modernos permiten representar textura y propiedades hidráulicas por profundidad (Xu et al., 2023). Incorporarlos, junto con validación de humedad, convertiría el mapa de vulnerabilidad de una demostración visual a una evaluación espacial reproducible.

### 5.6. Ética y equidad

Los gemelos agrícolas procesan datos que pueden revelar productividad, prácticas y capacidad financiera. Se requieren consentimiento, finalidad limitada, cifrado, control de acceso, trazabilidad y reglas de propiedad. Purcell et al. (2023) advierten que ignorar relaciones socioecológicas puede generar retroalimentaciones negativas; Escribà-Gelonch et al. (2024), Melesse (2025) y Zhang et al. (2025c) subrayan interoperabilidad, seguridad y brecha de infraestructura.

El sesgo geográfico es igualmente importante. Un modelo entrenado con medianas de Estados Unidos no debe emitir prescripciones para México, Argentina o España sin datos locales. Las recomendaciones deben presentar supuestos, incertidumbre y opciones de bajo costo, y nunca automatizar crédito, seguro o asignación de agua. El productor debe conservar soberanía sobre sus datos y decisión final.

### 5.7. Limitaciones y trabajo futuro

Las principales limitaciones son: tamaño efectivo de 36 años; agregación nacional que elimina variación por condado; replicación SSP del mismo objetivo; ausencia de SSP2-4.5 en entrenamiento; falta de validación externa espacial o de campo; restricciones de signo en vez de un residuo físico completo; estados diarios no diferenciables; manejo por multiplicadores fijos; suelo sin influencia en rendimiento; y bandas de incertidumbre todavía basadas en un sustituto. La evaluación prospectiva adicional, entrenada en 1990–2017 y probada en 2018–2025, obtuvo RMSE = 855.22 kg ha⁻¹, MAE = 683.62 kg ha⁻¹ y R² = −0.8318 para el ensamble de diez semillas. Por tanto, disponer de un protocolo temporal sin fuga no implica generalización satisfactoria: el resultado obliga a moderar cualquier afirmación predictiva fuera del periodo de calibración.

Además, la salida no incluye fracción cosechable pese a su relevancia documentada por Xiao et al. (2025), ni lixiviación de nitratos como la examinada por Niu et al. (2026). El simulador diario tampoco representa de manera explícita mortalidad de polen, encharcamiento subdiario o memoria hidrológica. Las fPINN podrían modelar memoria y transporte no local (Granella, 2026), pero primero deben resolverse problemas más básicos de datos, calibración y validación.

La hoja de ruta prioritaria es: (1) conservar rendimiento a nivel condado y división espacial; (2) incorporar SSP2-4.5 y miembros GCM reales; (3) añadir suelo espacial de SoilGrids/POLARIS; (4) hacer que fecha, suelo, estrés y fenología afecten el rendimiento; (5) comparar PINN, MLP, RF y modelo de proceso bajo el mismo protocolo; (6) validar en años y sitios externos; (7) ejecutar ensambles de GCM, semillas y parámetros; y (8) reemplazar recomendaciones fijas por optimización multiobjetivo calibrada.

---

## 6. CONCLUSIONES

CeresPINN demuestra que es técnicamente viable integrar una red entrenada, forzantes CMIP6 y un simulador fenológico-hídrico en una aplicación interactiva. El *holdout* agrupado aleatorio alcanzó R² = 0.8251 y errores cercanos a 0.7 t ha⁻¹, pero la evaluación prospectiva 2018–2025 obtuvo R² = −0.8318 y RMSE = 0.855 t ha⁻¹. La diferencia muestra que el desempeño interno favorable no se mantiene al extrapolar cronológicamente.

Sin embargo, la evidencia actual no permite afirmar validación externa, vulnerabilidad espacial, solución PINN de Richards ni confirmación de las hipótesis climáticas. El caso SSP5-8.5 mostró un beneficio de 7.29 % para riego deficitario al 75 %, pero no para adelanto de siembra o ciclo corto. La sensibilidad dominada por CO₂ y la igualdad de rendimiento entre campos identifican dos prioridades: romper la confusión temporal y acoplar suelo, fenología y estrés al rendimiento.

El valor actual del sistema es exploratorio: permite visualizar trayectorias, comparar supuestos y auditar cómo cambia una recomendación. Su transición a herramienta agronómica requiere datos espaciales, ensambles climáticos, tratamientos de manejo observados y validación independiente. Presentar estas limitaciones explícitamente fortalece el estudio y establece una ruta reproducible hacia un gemelo digital realmente adaptativo.

### Disponibilidad de código y datos

El repositorio público [David42024/CeresPINN](https://github.com/David42024/CeresPINN) distribuye el software bajo licencia MIT e incluye el checkpoint, sus metadatos, los datasets procesados, los scripts Q1, las tablas de resultados, las dependencias científicas fijadas y un manifiesto de integridad SHA-256. Desde un clon limpio, `python scripts/reproduce.py` verifica los insumos y regenera la auditoría principal, la auditoría extendida y la validación temporal prospectiva. GitHub Actions ejecuta el mismo pipeline en cada *push* y *pull request*. La procedencia USDA NASS y NASA NEX-GDDP-CMIP6, junto con las limitaciones de independencia de las copias SSP, se documenta en `data/README.md`.

---

## REFERENCIAS

Abramoff, R. Z., Ciais, P., Zhu, P., Hasegawa, T., Wakatsuki, H., & Makowski, D. (2023). Adaptation strategies strongly reduce the future impacts of climate change on simulated crop yields. *Earth’s Future, 11*, e2022EF003190. https://doi.org/10.1029/2022EF003190

Alimagham, S., van Loon, M. P., Ramirez-Villegas, J., Berghuijs, H. N. C., Rosenstock, T. S., & van Ittersum, M. K. (2025). Integrating crop models and machine learning for projecting climate change impacts on crops in data-limited environments. *Agricultural Systems*. https://doi.org/10.1016/j.agsy.2025.104367

Alsilibe, F., Bene, K., Bilal, G., Alghafli, K., & Shi, X. (2023). Accuracy assessment and validation of multi-source CHIRPS precipitation estimates for water resource management in the Barada Basin, Syria. *Remote Sensing, 15*, 1778. https://doi.org/10.3390/rs15071778

Chavoshi, A., Dashtian, H., Bakhshian, S., Young, M. H., & Niyogi, D. (2025). PINN-SM: A physics-informed neural networks model for vadose zone soil moisture profile prediction. *Journal of Geophysical Research: Machine Learning and Computation, 2*, e2024JH000547. https://doi.org/10.1029/2024JH000547

Cheng, M., Peñuelas, J., McCabe, M. F., Atzberger, C., Jiao, X., Wu, W., & Jin, X. (2022). Combining multi-indicators with machine-learning algorithms for maize yield early prediction at the county-level in China. *Agricultural and Forest Meteorology, 323*, 109057. https://doi.org/10.1016/j.agrformet.2022.109057

de Souza, E. B., et al. (2026). Projected heatwave hazards in an eastern Amazonian metropolis under contrasting CMIP6 scenarios. *Scientific Reports*. https://doi.org/10.1038/s41598-026-57944-x

Dokoohaki, H., Rai, T., Kivi, M., Lewis, P., Gómez-Dans, J. L., & Yin, F. (2022). Linking remote sensing with APSIM through emulation and Bayesian optimization to improve yield prediction. *Remote Sensing, 14*, 5389. https://doi.org/10.3390/rs14215389

Escribà-Gelonch, M., Liang, S., van Schalkwyk, P., Fisk, I., Long, N. V. D., & Hessel, V. (2024). Digital twins in agriculture: Orchestration and applications. *Journal of Agricultural and Food Chemistry, 72*(19), 10737–10752. https://doi.org/10.1021/acs.jafc.4c01934

Eyring, V., Bony, S., Meehl, G. A., Senior, C. A., Stevens, B., Stouffer, R. J., & Taylor, K. E. (2016). Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) experimental design and organization. *Geoscientific Model Development, 9*, 1937–1958. https://doi.org/10.5194/gmd-9-1937-2016

Farea, A., Yli-Harja, O., & Emmert-Streib, F. (2024). Understanding physics-informed neural networks: Techniques, applications, trends, and challenges. *AI, 5*(3), 1534–1557. https://doi.org/10.3390/ai5030074

Galmarini, S., Solazzo, E., Ferrise, R., Srivastava, A. K., et al. (2024). Assessing the impact on crop modelling of multi- and uni-variate climate model bias adjustments. *Agricultural Systems, 216*, 103846. https://doi.org/10.1016/j.agsy.2023.103846

Granella, S. J. (2026). Anomalous diffusion in drying: A fractional calculus perspective on modeling and applications in agro-food systems. *Food Physics*. https://doi.org/10.1016/j.foodp.2026.100088

Han, Y., Wang, K., Yang, F., Pan, S., Liu, Z., Zhang, Q., & Zhang, Q. (2024). Prediction of maize cultivar yield based on machine learning algorithms for precise promotion and planting. *Agricultural and Forest Meteorology, 355*, 110123. https://doi.org/10.1016/j.agrformet.2024.110123

Hlavinka, P., Trnka, M., Balek, J., Semerádová, D., Hayes, M., Svoboda, M., Eitzinger, J., Možný, M., Fischer, M., Hunt, E., & Žalud, Z. (2017). Impacts of water availability and drought on maize yield: A comparison of 16 indicators. *Agricultural Water Management*. https://doi.org/10.1016/j.agwat.2017.04.007

Jägermeyr, J., Müller, C., Ruane, A. C., Elliott, J., Balkovic, J., Castillo, O., et al. (2021). Climate impacts on global agriculture emerge earlier in new generation of climate and crop models. *Nature Food, 2*(11), 873–885. https://doi.org/10.1038/s43016-021-00400-y

Maraun, D., Wetterhall, F., Ireson, A. M., Chandler, R. E., Kendon, E. J., Widmann, M., et al. (2010). Precipitation downscaling under climate change: Recent developments to bridge the gap between dynamical models and the end user. *Reviews of Geophysics, 48*(3), RG3003. https://doi.org/10.1029/2009RG000314

Mbengue, A., Sultan, B., Lguensat, R., Vrac, M., Diongue-Niang, A., Ndiaye, O., & Gaye, A. T. (2026). High-resolution downscaled CMIP6 projections dataset of key climate variables for Senegal. *Scientific Data*. https://doi.org/10.1038/s41597-026-07059-9

Melesse, T. Y. (2025). Digital twin-based applications in crop monitoring. *Heliyon, 11*(2), e42137. https://doi.org/10.1016/j.heliyon.2025.e42137

Minoli, S., Jägermeyr, J., Asseng, S., Urfels, A., & Müller, C. (2022). Global crop yields can be lifted by timely adaptation of growing periods to climate change. *Nature Communications, 13*, 7079. https://doi.org/10.1038/s41467-022-34411-5

Miranda, M., Charfuelan, M., Valdenegro-Toro, M., & Dengel, A. (2025). Informed learning for estimating drought stress at fine-scale resolution enables accurate yield prediction. In *ECAI 2025, Frontiers in Artificial Intelligence and Applications* (Vol. 413, pp. 5384–5391). https://doi.org/10.3233/FAIA251477

Niu, X., Yang, Z., Zhang, J., Sun, X., Liu, Z., Jin, S., Cai, J., Zhang, B., & Sun, Y. (2026). Optimizing sowing date and nitrogen management to trade off yield and nitrate leaching in maize-soybean intercropping under CMIP6 climate scenarios in the North China Plain. *Plants, 15*, 1753. https://doi.org/10.3390/plants15111753

O’Neill, B. C., Tebaldi, C., van Vuuren, D. P., Eyring, V., Friedlingstein, P., et al. (2016). The Scenario Model Intercomparison Project (ScenarioMIP) for CMIP6. *Geoscientific Model Development, 9*, 3461–3482. https://doi.org/10.5194/gmd-9-3461-2016

Pukrongta, N., Taparugssanagorn, A., & Sangpradit, K. (2023). Assessing a machine learning model for predicting maize grain yield based on chlorophyll content and vegetation indices. In *2023 International Conference on Power, Energy and Innovations (ICPEI)*. IEEE. https://ieeexplore.ieee.org/document/10473794

Purcell, W., Neubauer, T., & Mallinger, K. (2023). Digital twins in agriculture: Challenges and opportunities for environmental sustainability. *Current Opinion in Environmental Sustainability, 61*, 101252. https://doi.org/10.1016/j.cosust.2022.101252

Raissi, M., Perdikaris, P., & Karniadakis, G. E. (2019). Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. *Journal of Computational Physics, 378*, 686–707. https://doi.org/10.1016/j.jcp.2018.10.045

Sakthivel, S., Pazhanivelan, S., Thiruvarassan, S., Prabu, P. C., Gnanachitra, M., Rahale, C. S., Sivamurugan, A. P., Ragunath, K. P., & Satheesh, S. (2025). A comprehensive bibliometric review of DSSAT applications in maize yield prediction. *Maydica, 68*(1). https://creajournals.crea.gov.it/index.php/maydica/article/view/2633

Shahhosseini, M., Hu, G., Huber, I., & Archontoulis, S. V. (2021). Coupling machine learning and crop modeling improves crop yield prediction in the US Corn Belt. *Scientific Reports, 11*, 1606. https://doi.org/10.1038/s41598-020-80820-1

Shi, Y., Han, L., Zhang, X., Sobeih, T., Gaiser, T., Thuy, N. H., Behrend, D., Srivastava, A. K., Halder, K., & Ewert, F. (2025). Deep learning meets process-based models: A hybrid approach to agricultural challenges [Preprint]. *arXiv*. https://doi.org/10.48550/arXiv.2504.16141

Shi, Y., Han, L., Zhang, X., Sobeih, T., Gaiser, T., Thuy, N. H., Behrend, D., Srivastava, A. K., Halder, K., & Ewert, F. (2026). AgriPINN: A process-informed neural network for interpretable and scalable crop biomass prediction under water stress [Preprint]. *arXiv*. https://doi.org/10.48550/arXiv.2601.16045

Thrasher, B., Wang, W., Michaelis, A., Melton, F., Lee, T., & Nemani, R. (2022). NASA global daily downscaled projections, CMIP6. *Scientific Data, 9*, 262. https://doi.org/10.1038/s41597-022-01393-4

Uscamayta-Ferrano, E., et al. (2025). CHIRTS gridded air temperature downscaling integrating machine learning and physical constraints. *Atmosphere, 16*, 1188. https://doi.org/10.3390/atmos16101188

Wakatsuki, H., Ju, H., Nelson, G. C., Farrell, A. D., Deryng, D., Meza, F., & Hasegawa, T. (2023). Research trends and gaps in climate change impacts and adaptation potentials in major crops. *Current Opinion in Environmental Sustainability, 61*, 101249. https://doi.org/10.1016/j.cosust.2022.101249

Xiao, K., Zhou, X., Gui, H., Tian, Y., Chen, X., Li, Y., Matomela, N., & Xin, Q. (2025). Drought and extreme heat reduce wheat and maize production in the United States by lowering both crop yields and harvestable fraction. *Earth’s Future, 13*, e2024EF005557. https://doi.org/10.1029/2024EF005557

Xu, C., Torres-Rojas, L., Vergopolan, N., & Chaney, N. W. (2023). The benefits of using state-of-the-art digital soil properties maps to improve the modeling of soil moisture in land surface models. *Water Resources Research, 59*, e2022WR032336. https://doi.org/10.1029/2022WR032336

Xu, Q., Liang, H., Wei, Z., et al. (2024). Assessing climate change impacts on crop yields and exploring adaptation strategies in Northeast China. *Earth’s Future, 12*, e2023EF004063. https://doi.org/10.1029/2023EF004063

Xu, X., Gao, F., Du, X., Xiong, D., Fan, Z., Xiong, S., Dong, P., Qiao, H., & Ma, X. (2025a). Digital twin-based winter wheat growth simulation and optimization. *Field Crops Research, 329*, 109953. https://doi.org/10.1016/j.fcr.2025.109953

Yang, H., Yang, J., Ochsner, T. E., Zhang, Q., Jiao, X., Fang, S., Zhou, Y., & Zou, C. B. (2026). Increasing irrigation water requirements across croplands in the contiguous United States throughout the 21st century. *Agricultural Water Management*. https://doi.org/10.1016/j.agwat.2025.110044

Yu, D., Zha, Y., Zeng, Y., Lai, P., Zhu, W., Bian, J., Yang, Q., Huang, X., & Su, Z. (2025). An efficient and physics-informed regional maize yield estimation scheme by combining data assimilation and machine learning. *Computers and Electronics in Agriculture*. https://doi.org/10.1016/j.compag.2025.111142

Zhang, H., Zhao, J., Hong, M., & Ma, L. (2025a). Optimization of deficit irrigation system for drip-irrigated corn in northern Xinjiang using dynamic reconstruction and dual physics-informed neural networks to drive AquaCrop. *Frontiers in Plant Science*. https://doi.org/10.3389/fpls.2025.1678277

Zhang, L., Bai, G., Evett, S. R., Colaizzi, P. D., Xue, Q., Marek, G., Dhungel, R., Zhao, H., Wan, N., & Lin, X. (2025b). Increased irrigation could mitigate future warming-induced maize yield losses in the Ogallala Aquifer. *Communications Earth & Environment, 6*, 483. https://doi.org/10.1038/s43247-025-02459-y

Zhang, R., Zhu, H., Chang, Q., & Mao, Q. (2025c). A comprehensive review of digital twins technology in agriculture. *Agriculture, 15*(9), 903. https://doi.org/10.3390/agriculture15090903
