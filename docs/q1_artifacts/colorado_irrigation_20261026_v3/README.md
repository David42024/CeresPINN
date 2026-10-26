# Auditoría de tratamientos de riego y estados observados en Colorado

Se incorporó un experimento público independiente del USDA en Greeley, Colorado,
con 12 tratamientos de riego y cuatro parcelas por tratamiento en cada una de
las campañas 2012 y 2013. La descripción científica está en Comas et al. (2018),
[DOI 10.1016/j.dib.2018.10.140](https://doi.org/10.1016/j.dib.2018.10.140),
y los datos son [USDA Ag Data Commons, DOI 10.15482/USDA.ADC/1439968](https://doi.org/10.15482/USDA.ADC/1439968).
Los cuatro archivos originales, licencia de dominio público, MD5 oficiales y
SHA-256 se conservan en `data/external/colorado_irrigation_2012_2013/`.

También se preservaron los 12 archivos del experimento previo de la misma
estación, 2008–2011, incluido el libro con propiedades de suelo, con sus MD5 y
SHA-256: [DOI 10.15482/USDA.ADC/1254006](https://doi.org/10.15482/USDA.ADC/1254006).
Esas cuatro campañas no están incluidas en los contrastes ni en la evaluación
de la tabla siguiente; hacen posible un análisis posterior, pero su sola descarga
no constituye validación del modelo acoplado.

La fuente tiene 96 parcela-años; esto representa **una localidad y dos campañas**,
no 96 localidades ni 96 años independientes. Los tratamientos se asignaron de
forma aleatoria por bloques. El diccionario original identifica el primer dígito
del código de parcela como bloque y la letra como sección del campo; no se usan
las secciones como bloques separados. Las cifras 100/50 y 80/80 representan los
porcentajes objetivo de reposición de evapotranspiración durante los períodos
vegetativo tardío y de llenado de grano, respectivamente; no equivalen a un
porcentaje uniforme aplicado a toda la temporada.

## FON-06: contrastes de riego observados

Se comparan 100/50 y 80/80 frente a 100/100, dentro del mismo bloque y año, usando
rendimiento a 15,5 % de humedad. Los valores siguientes son tratamiento menos
control. Los intervalos t por diferencias emparejadas son descriptivos y usan
solo tres o cuatro bloques; la prueba de signos es discreta y se ajusta mediante
Holm por las cuatro comparaciones. Los intervalos t no están ajustados por
multiplicidad y dependen de supuestos sobre las diferencias entre bloques que no
pueden comprobarse bien con muestras tan pequeñas. El análisis es retrospectivo
y no preregistrado.

| Año | Tratamiento | Pares completos | Diferencia kg/ha | IC descriptivo del 95 % kg/ha | p ajustada |
|---:|---|---:|---:|---:|---:|
| 2012 | 100/50 | 4 | −3.060,29 | −7.984,81 a 1.864,24 | 1,000 |
| 2012 | 80/80 | 4 | −787,67 | −4.746,20 a 3.170,87 | 1,000 |
| 2013 | 100/50 | 3 | −2.457,45 | −5.938,06 a 1.023,16 | 1,000 |
| 2013 | 80/80 | 3 | −306,28 | −2.387,01 a 1.774,46 | 1,000 |

En 2013 falta el rendimiento de la parcela de control D31: se excluye su pareja
del bloque 3 en ambos contrastes. También falta C46, correspondiente a otro
tratamiento. No se imputan esos valores. Todos los intervalos contienen cero;
esto no demuestra equivalencia ni ausencia de efecto. No se calibraron ni
sustituyeron los multiplicadores de la interfaz, y estos resultados no respaldan
una recomendación aplicable a otros sitios, cultivares o fechas de siembra.

## FON-07: relación condicionada con un estado medido

La fuente no incluye biomasa aérea final medida para las 48 parcelas de 2013.
No se reconstruye desde el rendimiento y el índice de cosecha: hacerlo usaría el
propio objetivo y causaría fuga de información. Como alternativa separada, se
ajusta en 2012 una regresión Ridge con el máximo observado de LAI y se evalúa en
las 46 parcelas de 2013 con rendimiento disponible. El objetivo se convierte a
grano seco multiplicando el rendimiento estándar por 0,845.

| Predicción de grano seco en 2013 | RMSE kg/ha | R² |
|---|---:|---:|
| Media observada en entrenamiento 2012 | 1.779,31 | −0,005 |
| Ridge con máximo LAI observado | 1.886,40 | −0,130 |

El LAI máximo se conoce a partir de mediciones durante la campaña: es una
comparación condicionada por un estado observado, no un pronóstico temprano ni
una validación del modelo acoplado de Bushland o de la red nacional. Ridge con
LAI no supera la media en esta evaluación; no se selecciona como solución de
despliegue. No se evaluaron efectos de cultivar ni de fecha de siembra.

## Trazabilidad y reproducción

`protocol.json` se escribió antes de calcular los contrastes. Durante la revisión
del archivo se detectaron datos faltantes y que la letra del código identifica
sección, no bloque. Se preservan los protocolos de los dos intentos anteriores en
las carpetas `colorado_irrigation_20261026` y `colorado_irrigation_20261026_v2`;
ninguno produjo resultados de contrastes. La versión v3 documenta las reglas
corregidas. Se habían visto metadatos y algunas filas antes del protocolo: el
estudio no es prospectivo ni preregistrado.

```powershell
python scripts/acquire_colorado_irrigation.py --verify-only
python scripts/acquire_colorado_irrigation.py --previous --verify-only
python scripts/audit_colorado_irrigation.py
python -m pytest backend/tests/test_colorado_irrigation_audit.py -q
```

`plot_observations.csv` conserva número de fila fuente y datos faltantes;
`conditional_state_predictions.csv` y `results.json` permiten reconstruir las
métricas y contrastes. La ejecución repetida generó resultados idénticos. Estos
archivos nuevos no recuperan la descarga nacional NASS ni la extracción CMIP6
usadas originalmente para el predictor nacional.
