# Sensibilidad del ajuste neuronal al límite de iteraciones

Esta evaluación retrospectiva repite la auditoría regional de Iowa sin cambiar los datos, nueve distritos, particiones, variables, arquitectura ni tres semillas. El único cambio de configuración del ajuste neuronal es aumentar el límite de 300 a 1.000 iteraciones. Se preserva por separado la auditoría anterior en `../regional_neural_20261026/`.

No es una prueba independiente nueva ni una evaluación del predictor nacional: los resultados y las particiones ya se habían examinado. El protocolo se guardó antes de esta ejecución, pero no constituye un preregistro anterior a la inspección de los resultados originales. No se seleccionó ni reemplazó el modelo de producción.

## Resultados

| Modelo | RMSE con 300 iteraciones (kg/ha) | RMSE con 1.000 iteraciones (kg/ha) | Advertencias de convergencia antes → después |
| --- | ---: | ---: | ---: |
| Red: clima | 3.145,03 | 3.149,33 | 6 → 0 |
| Red: clima y tendencia explícita | 1.292,24 | 1.294,81 | 7 → 0 |
| Red: año y clima | 1.772,78 | 1.801,32 | 27 → 0 |
| Ridge: tendencia | 1.224,77 | 1.224,77 | No aplicable |

Las 40 advertencias de convergencia se redujeron a cero en los 81 ajustes neuronales. La ausencia de advertencias solo indica que el optimizador satisfizo su criterio de parada: no garantiza un óptimo global ni un modelo predictivo válido. Los tres errores neuronales aumentaron; Ridge con tendencia continúa con menor RMSE que cada una de esas redes. Por tanto, no hay evidencia aquí para recomendar un predictor neuronal regional, producir rankings de vulnerabilidad o retirar las restricciones de uso del software.

Se compararon las mismas 696 combinaciones de condado y año por modelo, agrupadas en solo ocho años de evaluación comunes. No hay separación espacial adicional entre distritos. Los intervalos son descriptivos y deben leerse junto con `metrics.json`. Las predicciones y estados de convergencia permiten verificar los resultados; el código verifica que los hashes de las dos entradas coincidan con los del experimento anterior.

## Reproducibilidad

Se ejecutó con Python del entorno científico, NumPy 2.3.5, pandas 2.2.3 y scikit-learn 1.9.0, limitando a un hilo las bibliotecas numéricas:

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python scripts/audit_regional_convergence.py
python -m pytest backend/tests/test_regional_neural_transfer.py -q
```

Se comprobó que los seis modelos predicen cada condado-año de prueba una sola vez y que el RMSE de `metrics.json` se reconstruye a partir de `predictions.csv`. Las cuatro pruebas regionales existentes pasaron. Las limitaciones de representatividad, calibración territorial, datos espaciales y acoplamiento al predictor nacional permanecen abiertas.
