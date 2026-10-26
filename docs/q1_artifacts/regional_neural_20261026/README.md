# Evaluación neuronal regional por distrito y año futuro

Esta auditoría agrega un experimento con redes neuronales regionales. No valida
ni sustituye el predictor nacional guardado: aquel fue ajustado con medianas
nacionales y no recibe coordenadas o variables climáticas por condado en el
mismo esquema de esta prueba. La comparación no demuestra que el modelo nacional
sea válido para predecir un condado.

## Diseño

Se usan 3.460 registros de 99 condados de Iowa, reconstruidos desde USDA NASS y
NOAA. En cada una de nueve particiones se excluye un distrito completo: el ajuste
usa los demás distritos hasta 2017 y la evaluación usa el distrito excluido en
2018–2025. Cada modelo genera predicciones para 696 condado-años. Estos registros
comparten ocho años meteorológicos; no son 696 años ni nueve ensayos temporales
independientes. Los distritos no tienen una zona de separación espacial.

El protocolo especifica antes del ajuste tres semillas, dos capas de 16 y 8
neuronas, activación tanh y hasta 300 iteraciones, sin selección posterior según
errores de prueba. Se estandarizan entradas y objetivo exclusivamente con datos de
entrenamiento. Las tres variantes neuronales usan clima y año, solo clima, o
solo clima para aprender los residuos de una tendencia lineal ajustada únicamente
con los años de entrenamiento. Se comparan en las mismas particiones con Ridge
para tendencia, tendencia más clima, y solo clima.

Las variables climáticas son temperatura media y precipitación estacional. No se
incluyen CO₂, `heatwave_risk`, escenario ni la variable constante `seasonal_cdd`.
La variante sin tendencia tampoco usa el año; la variante residual añade una
tendencia explícita después de la predicción de la red. Esto evita los proxies
especificados en el nuevo experimento, sin identificar efectos causales ni
deshacer la confusión del modelo nacional anterior.

Este es un análisis interno retrospectivo: los datos y algunos resultados de Iowa
ya se habían examinado, por lo que la prueba no constituye un registro previo ni
una cohorte externa intacta. Las fuentes y diferencias entre la adquisición NOAA
actual y la tabla congelada se documentan en `../reacquired_20261026/README.md`.

## Resultados de evaluación

| Modelo | RMSE kg/ha | MAE kg/ha | R² |
|---|---:|---:|---:|
| Ridge, tendencia | 1.224,77 | 962,89 | 0,036 |
| Ridge, tendencia y clima | 1.302,87 | 1.014,62 | −0,091 |
| Ridge, solo clima | 2.996,04 | 2.728,08 | −4,769 |
| MLP, año y clima | 1.772,78 | 1.422,40 | −1,020 |
| MLP, solo clima | 3.145,03 | 2.847,73 | −5,357 |
| MLP, clima y tendencia explícita | 1.292,24 | 1.021,01 | −0,073 |

La red de residuos con tendencia explícita reduce el error frente a la red que
usa solo clima, pero no supera el RMSE de Ridge con tendencia. Los intervalos
descriptivos remuestrean años completos en bloques de tres y figuran en
`metrics.json`; son inciertos por contar con solo ocho años de evaluación.
El resultado no establece superioridad causal ni equivalencia entre modelos.

De 81 ajustes neuronales, 40 alcanzaron el límite sin convergencia según la
advertencia de scikit-learn: 27 de 27 con año y clima, 6 de 27 solo clima y 7 de
27 con tendencia explícita. No se aumentó el número de iteraciones ni se eligió
otro modelo después de ver los errores: las métricas deben interpretarse con
esa limitación. `metrics.json` conserva el estado y las iteraciones por semilla
y distrito; `predictions.csv` contiene todas las predicciones fuera de distrito.

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python scripts/audit_regional_neural_transfer.py
python -m pytest backend/tests/test_regional_neural_transfer.py -q
```

El protocolo, los hashes de las dos tablas de entrada, las particiones y las
predicciones permiten auditar esta ejecución. Ninguna salida autoriza prescribir
riego o desplegar la red como predictor agrícola validado.
