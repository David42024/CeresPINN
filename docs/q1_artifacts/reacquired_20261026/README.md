# Reconstrucción de fuentes y validación geográfica adicional

Se descargó un CSV original de la interfaz pública USDA NASS Quick Stats, sin
necesitar clave API, y 297 respuestas JSON originales de NOAA Climate at a Glance.
Las descargas nuevas no se presentan como los mismos bytes de adquisición antigua.

## Fidelidad de la tabla regional

El CSV NASS contiene 3.476 registros. Se conservan todos sus bytes y se excluyen
del análisis 16 estimaciones de condados combinados sin código individual.
Los 3.460 rendimientos restantes, con 99 condados y 36 años de cobertura,
coinciden con la tabla congelada (error máximo de redondeo 1,82×10⁻¹² kg/ha).
El resultado de la consulta y su captura están preservados junto al manifiesto.

NOAA aporta tres variables por condado (temperatura media, máxima y precipitación),
con 36 agregados abril–septiembre por respuesta. Se verifican unidades originales
Fahrenheit/pulgadas antes de convertir. Se conservan URL, fecha, cabeceras HTTP,
respuesta íntegra, tamaño y SHA-256. Son 10.692 valores estacionales en total;
se unen al subconjunto con rendimiento disponible mediante FIPS y año.

La tabla congelada coincide con las fuentes actuales hasta 2024. Para 2025 hay
20 diferencias de temperatura media, 22 de máxima y 14 de precipitación. Los
máximos son 0,167 °C y 32,512 mm. Sin las respuestas antiguas no se puede decidir
si se deben a revisiones del proveedor o a la ingestión anterior. No se alteran
los archivos congelados. `source_fidelity.json` conserva **verified=false** para
la igualdad numérica completa, y marca separadamente integridad de archivos,
cobertura y concordancia de rendimiento. No se ocultan discrepancias para que
un control aparezca aprobado.

```powershell
python scripts/verify_reacquired_county.py
```

El modo estricto anterior falla intencionalmente ante las diferencias climáticas
documentadas. Para reconstruir y comparar explícitamente la versión nueva:

```powershell
python scripts/audit_reacquired_county.py
```

Este comando verifica todos los datos fuente, permite solo el análisis separado
de diferencias climáticas y conserva el indicador de igualdad exacta en falso.
No permite aprobar cambios de rendimiento ni pérdida de cobertura. Las pruebas
comprueban que ni unidades distintas con checksum actualizado ni rendimientos
alterados pueden pasar inadvertidos.

## Resultados con fuentes actuales

La misma partición de cinco grupos de condados y años futuros produce RMSE de
1.173,590 kg/ha para tendencia, 1.268,859 para tendencia+clima y 2.991,756 para
solo clima. Los cambios frente a los datos congelados son 0, +0,243 y +0,222 kg/ha.
El orden de los baselines no cambia. Es una comprobación retrospectiva de
robustez de fuentes; no constituye una nueva cohorte independiente.

## Exclusión de distritos agrícolas completos

El CSV fuente conserva el distrito agrícola de cada condado. Las asignaciones
son constantes en los años y cubren nueve distritos oficiales: 10 a 90.
El [mapa oficial de USDA](https://www.nass.usda.gov/Statistics_by_State/Iowa/Publications/Crop_Report/IA_Ag_Districts_Map.pdf)
y la [definición de distritos](https://www.nass.usda.gov/Data_and_Statistics/County_Data_Files/Frequently_Asked_Questions/index.php)
documentan su base geográfica, climática y productiva.

`district_protocol.json` se guardó antes del ajuste. Cada modelo aprende de los
otros ocho distritos hasta 2017 y predice el distrito excluido durante 2018–2025.
Las variables y alpha=1 se mantienen iguales a los del benchmark anterior; no
se eligen límites geográficos ni hiperparámetros según los errores nuevos.

```powershell
python scripts/audit_geographic_districts.py
```

| Ridge | RMSE kg/ha | MAE kg/ha | R² |
|---|---:|---:|---:|
| Tendencia | 1.224,775 | 962,894 | 0,036 |
| Tendencia y clima | 1.302,875 | 1.014,619 | −0,091 |
| Solo clima | 2.996,043 | 2.728,080 | −4,769 |

Los nueve grupos comparten ocho años meteorológicos; no son nueve replicaciones
temporales independientes. Los intervalos descriptivos remuestrean años completos
en bloques de tres. Hay 696 condado-años de prueba en cada diseño. La prueba por
distrito es más exigente que la exclusión aleatoria, pero sigue en un solo estado,
carece de buffer espacial y no valida el checkpoint neuronal nacional.

## Archivos y reproducción

- `data/reacquired/nass/`: CSV original y manifiesto de consulta.
- `data/reacquired/noaa-cag/`: 297 respuestas y sus registros de procedencia.
- `data/reacquired/cerespinn_county_rebuilt.csv`: reconstrucción separada.
- `agency_source_comparison.csv`: comparación por FIPS, año y variable.
- `reacquired_county_benchmark.json`: errores de los tres modelos con fuentes nuevas.
- `district_benchmark.json`: protocolo, splits, métricas e intervalos por distrito.
- `held_district_future_predictions.csv`: predicciones fuera del distrito de ajuste.
- `held_district_errors.csv`: errores de cada distrito y modelo.

La recuperación NOAA puede repetirse con `scripts/reacquire_county_climate.py`.
Si existen respuestas con hashes válidos, reutiliza esa adquisición congelada;
para una adquisición con otra fecha se debe preservar una carpeta distinta.
El CSV USDA se obtiene desde la consulta pública y la opción Spreadsheet,
documentada en la guía de descarga y en su manifiesto, sin credenciales guardadas.
