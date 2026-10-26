# Evaluación de acoplamiento con observaciones públicas de Bushland

Se implementó una extensión independiente del checkpoint nacional. Los resultados
no demuestran superioridad ni justifican recomendaciones de riego o cultivar.

## Fuentes y trazabilidad

Descriptor: Evett et al. (2025), Scientific Data 12, 209,
https://doi.org/10.1038/s41597-025-04539-2.

Colección USDA Ag Data Commons: https://doi.org/10.15482/USDA.ADC/1526317.
Los DOI individuales, versiones, identificadores de archivo, URL, licencia CC0,
tamaño y MD5 oficiales están en `data/external/bushland/acquisition_manifest.json`.
Cada descarga conserva su nombre y bytes originales y agrega SHA-256.

Los archivos originales abarcan crecimiento/rendimiento, calendarios, balance
hídrico, clima de 15 minutos, perfiles de humedad y propiedades del suelo.
Los CSV conservan archivo, hoja y fila fuente. El clima se agrega por DOY fuente
(el intervalo 24:00 pertenece al DOY registrado), con 96 intervalos diarios.
La radiación se integra de W/m² a MJ/m²/día. No se editaron los Excel originales.

## Protocolo y unidades

`protocol.json` se escribió antes del ajuste. Se habían inspeccionado algunos
valores de 2018 durante la extracción: no constituye preregistro ni una prueba
intacta. Calibración: 1989, 1990, 1994 y 2013. Evaluación: 2016 y 2018.
Hay 20 campo-campañas, 19 con rendimiento de cosechadora; 11 se usan para ajustar
rendimiento y ocho para evaluar. Los 104 submuestreos de cosecha y las mediciones
diarias no son 104 campañas independientes. Las cuatro parcelas son adyacentes
en una sola estación. No hay campos peruanos en esta evaluación.

El objetivo es grano seco kg/ha. Los valores de 2016 Este expresados en kg/m² se
multiplican por 10.000. Los valores de biomasa en g/m² se multiplican por 10.
El rendimiento a humedad estándar se conserva por separado. Las fechas de
cosecha copiadas de 1994 en el libro de 2016 se marcan como inconsistentes; el
año se toma de la campaña y no de esas celdas. Se respeta el prefijo de parcela
en los identificadores NE/SE/NW/SW y se excluyen las franjas de zinc.

## Modelo y ajuste

`backend/coupled_crop.py` conserva el agua en tres capas (0–30, 30–60, 60–150 cm).
Las propiedades se agregan por espesor desde el perfil Pullman medido. Es una
cubeta multicapa, sin solución de Richards. El tiempo térmico determina LAI y
raíces; agua disponible, radiación interceptada y temperatura determinan biomasa.
Grano = biomasa simulada × índice de cosecha. No entra el año como predictor.

Se ajustan seis parámetros mediante mínimos cuadrados acotados, solamente con
las cuatro campañas de calibración. Las escalas y el peso de las familias de
objetivos están en `calibration_parameters.json` y en el script. LAI/biomasa y
humedad se agregan por campo y fecha antes de comparar. Las propiedades del
suelo permanecen fijas; no se estimaron respuestas particulares de cultivares.
El rango numérico del Jacobiano no demuestra identificabilidad biológica.

La ETo sigue FAO-56: https://www.fao.org/4/X0490E/x0490e08.htm.
La temperatura, humedad, radiación y viento proceden de la estación. La presión
ausente de 2013 se deriva de la elevación de 1.170 m. La lluvia ausente del
lisímetro utiliza el pluviómetro. El riego ausente utiliza el registro de eventos;
si no hay evento se asume cero, con bandera explícita. El rocío ausente se asume
cero, también marcado. No se presentan estas sustituciones como observaciones.
Las cuentas exactas están en `external_metrics.json` y todas las banderas en
`data/bushland_processed/model_forcing.csv`.

La inicialización usa un perfil previo a la siembra cuando existe, con edad
reportada; en otro caso usa capacidad de campo. Trasladar un perfil anterior al
día de siembra omite posibles flujos intermedios y es una limitación. No se
asimilan mediciones futuras. Las entradas se extienden hasta DOY 320: se evalúa
una simulación condicionada al clima completo, no un pronóstico anticipado.
En esta extracción solo dos campos de 1994 tienen perfiles previos (seis y siete
días de antigüedad); todos los campos de evaluación se inicializan a capacidad
de campo. Las tablas extraídas incluyen registros de parcelas/fechas que no
pertenecen a la simulación: el ajuste usa únicamente los campo-campañas del
calendario y la ventana temporal especificada.

## Resultados de evaluación

| Modelo | RMSE grano seco kg/ha | R² |
|---|---:|---:|
| Media de calibración | 2.500,98 | −6,406 |
| Ridge de clima y riego | 1.604,19 | −2,047 |
| Proceso con parámetros fijos | 1.084,08 | −0,391 |
| Proceso acoplado calibrado | 3.248,07 | −11,491 |

No se seleccionó retrospectivamente el proceso fijo como modelo ganador ni se
retocaron parámetros por el resultado de evaluación. Las mejoras de calibración
no se trasladaron al grano de las temporadas posteriores. Todos los R² de grano
son negativos; no hay prueba de utilidad predictiva general.

El proceso calibrado obtiene RMSE de LAI 1,864; biomasa 4.095,52 kg/ha;
ET real 1,570 mm/día; humedad 0,05082 m³/m³. Biomasa y ET tienen R² 0,749 y
0,759; la humedad tiene R² −0,191. Son puntuaciones descriptivas de medidas
repetidas, sin interpretar los días como replicaciones independientes.

El residuo máximo absoluto de masa es 1,5632×10⁻¹³ mm. Este control verifica la
aritmética de conservación; no demuestra que las trayectorias sean correctas.
El residuo de la exportación del simulador legado permanece documentado aparte.

Los contrastes de riego NW–SW están confundidos con parcela. No se pueden estimar
efectos causales ni trasladar un coeficiente a los multiplicadores de la interfaz.
Dos años de evaluación no sostienen intervalos robustos entre temporadas.

## Reproducción

Desde la raíz del paquete, con `requirements-revision.txt`:

```powershell
python scripts/verify_bushland_sources.py
python scripts/prepare_bushland_data.py
python scripts/validate_bushland_coupling.py
python scripts/revision_figures.py
```

`--reuse-weather` permite reutilizar la agregación climática para ahorrar lectura;
la reproducción completa debe omitirlo. Los resultados están en CSV y JSON.
`processed_input_manifest.json` identifica los bytes usados por el ajuste.
Las pruebas comprueban conservación bajo una tormenta extrema, límites hídricos,
el camino agua–rendimiento, el ejemplo publicado FAO y rechazo de entradas faltantes.
