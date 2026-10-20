# Validación del frontend React

Fecha: 20/10/2026. Resultado: **APROBADO para las funciones de tablas, zoom y exportación solicitadas**.

Se integró `origin/feat/figure-export-600dpi` en `lucano` mediante avance directo hasta `0bc63e5`. Se completaron los controles de zoom y las descargas Excel que faltaban en esa rama.

## Archivos entregados

| Contenido | Excel | Figura PNG |
| --- | --- | --- |
| Biomasa e índice de área foliar | `cerespinn_reporte_biomasa_lai.xlsx` | `cerespinn_reporte_biomasa_lai_600dpi.png` |
| Balance hídrico diario | `cerespinn_reporte_balance_hidrico.xlsx` | `cerespinn_reporte_balance_hidrico_600dpi.png` |

Los dos archivos Excel contienen 110 registros diarios cada uno. Se verificaron las cabeceras, la cantidad de registros y los valores de las filas inicial, intermedia y final contra las tablas del frontend. Las magnitudes se conservan como celdas numéricas.

Las dos imágenes tienen 3406 × 2438 píxeles. Se comprobó la rasterización a escala 600/96 y el bloque PNG `pHYs`: 23622 píxeles por metro en ambos ejes, equivalente a 599.9988 dpi por el redondeo entero del formato PNG. Incluyen título, ejes, leyendas e interpretación y fueron revisadas visualmente.

## Pruebas realizadas

- Inicio de sesión con la cuenta de demostración y navegación a **Exportar**.
- Presencia de dos tablas HTML y dos figuras en el módulo de reportes.
- Zoom de 1× a 2× en cada figura, con cambio comprobado en los días del eje horizontal.
- Desplazamiento del período, zoom de regreso a 1× y restablecimiento del período completo.
- Descargas de los PNG y Excel mediante los botones reales del frontend.
- Apertura y lectura de los Excel descargados, validación de dimensiones y resolución de los PNG.
- Revisión visual de las figuras y capturas del frontend en escritorio y móvil. El módulo no desborda horizontalmente a 390 píxeles de ancho; las tablas permiten desplazamiento interno.
- TypeScript: `npm run lint`, correcto.
- Compilación: `npm run build`, correcta. Vite conserva un aviso de tamaño del paquete principal.
- Ningún error JavaScript no controlado durante las pruebas del navegador.

## Alcance de los datos

Los archivos contienen la simulación local que muestra la aplicación para Parcela Experimental Ames Norte y el escenario SSP3-7.0. El backend no estaba activo. **No se validaron la inferencia del servidor ni la conexión a la base de datos.**

Por restricciones de acceso a localhost en el entorno, Chrome recibió la compilación real de `dist` desde disco mediante el enrutamiento de Playwright. No se inyectaron ni sustituyeron los registros de la aplicación. Las rutas API no estaban disponibles en ese transporte y la interfaz mantuvo su simulación local.

Las capturas son evidencia del frontend; los archivos terminados en `_600dpi.png` son las figuras de alta resolución. `validacion.json` contiene las comprobaciones y métricas. La prueba reproducible está en `scripts/validate-report-exports.cjs` y usa Playwright del runtime local.
