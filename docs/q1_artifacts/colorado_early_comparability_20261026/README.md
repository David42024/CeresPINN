# Comparabilidad de los ensayos de riego de Colorado

## Conclusión

Las colecciones USDA de 2008–2011 y 2012–2013 comparten la estación LIRF en
Colorado, un diseño de bloques aleatorizados con cuatro repeticiones y
rendimientos de grano expresados en kg/ha al 15,5 % de humedad. **Sus etiquetas
de tratamiento y sus porcentajes no son equivalentes automáticamente**: antes de
integrar los ensayos hay que modelar las exposiciones y períodos realmente
comparables, la campaña, el bloque y los datos faltantes.

El estudio 2008–2011 usa seis tratamientos cuyo objetivo es cubrir 100, 85, 75,
70, 55 y 40 % de las necesidades de agua de T1. La metodología indica que se
reguló el estrés en diferentes etapas y que la evapotranspiración efectivamente
alcanzada difirió de los objetivos. En cambio, 2012–2013 usa 12 combinaciones
con porcentajes por separado para las etapas vegetativa tardía y de llenado de
grano. Por ejemplo, T3 de la primera colección no debe equipararse con 80/80 ni
con el multiplicador de riego «75 %» de la aplicación.

Fuentes: [USDA, colección 2008–2011](https://doi.org/10.15482/USDA.ADC/1254006),
metodología original `LIRF Methodology r1.pdf`, páginas 5–7; y [USDA, colección
2012–2013](https://doi.org/10.15482/USDA.ADC/1439968), diccionario de datos del
archivo compilado. Las fuentes brutas, sus licencias y hashes están conservados
en `data/external/colorado_irrigation_2008_2011/` y
`data/external/colorado_irrigation_2012_2013/`.

## Inventario verificado de 2008–2011

| Año | Parcela-años | Tratamientos | Bloques | Grano observado | Biomasa observada | LAI máximo observado |
|---:|---:|---:|---:|---:|---:|---:|
| 2008 | 24 | 6 | 4 | 24 | 24 | 0 |
| 2009 | 24 | 6 | 4 | 24 | 24 | 5 |
| 2010 | 24 | 6 | 4 | 24 | 24 | 16 |
| 2011 | 24 | 6 | 4 | 24 | 24 | 24 |

Son 96 registros de parcela-año en **una estación y cuatro campañas**, no 96
localidades o años independientes. Las parcelas se trasladaron cada año a otra
sección contigua bajo rotación de cultivos. La metodología indica aplicaciones
de nitrógeno distintas para algunos tratamientos en 2011 y que el agua de riego
aportaba nitrógeno: esto limita la atribución exclusiva al agua.

Los valores originales de grano a humedad estándar y grano seco se conservan en
columnas separadas. En los 96 registros, la relación documentada
`grano seco = 0,845 × grano al 15,5 % de humedad` coincide con los valores fuente.
El máximo LAI ausente se conserva vacío; no se deduce a partir del rendimiento.
Los estados y flujos diarios por tratamiento no deben tratarse como mediciones
independientes de cada una de las cuatro parcelas.

## Alcance y siguiente paso

Este inventario es descriptivo y retrospectivo: no estima efectos de tratamiento,
no calibra los multiplicadores de manejo y no valida el predictor nacional ni el
modelo acoplado. Para una comparación posterior se deben definir por adelantado
los contrastes y ventanas de entrenamiento y evaluación, usar los tratamientos
según su diseño original y documentar las condiciones que impiden combinarlos.
No se debe seleccionar el análisis por los resultados ya observados.

`plot_inventory.csv` registra archivo, hoja y fila fuente de cada parcela;
`inventory.json` registra cobertura y SHA-256. Para reproducir:

```powershell
python scripts/acquire_colorado_irrigation.py --previous --verify-only
python scripts/audit_colorado_early_study.py
python -m pytest backend/tests/test_colorado_early_study.py -q
```
