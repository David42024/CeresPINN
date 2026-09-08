# Plan de Implementación: Internacionalización CeresPINN

Orden de ejecución sugerido por dependencias. Cada tarea tiene sus propios Test Requirements (TRs) locales.

---

## Task 1: Confirmación de dependencias i18n e infraestructura base
**Prioridad**: high | **Estado**: pending | **Dependencias**: Ninguna

### Descripción
Verificar que `i18next` y `react-i18next` están en `package.json` (sí lo están). Crear la carpeta `src/i18n/locales/` que no existe actualmente. Revisar que `src/i18n/index.ts` actual cumple AC-1 (fallback a `es`, `escapeValue: false`).

### TRs locales
| ID | Tipo | Descripción |
|---|---|---|
| T1-TR1 | **rule** | `package.json` contiene `"i18next": "^26.4.2"` y `"react-i18next": "^17.0.13"` (ya presentes). |
| T1-TR2 | **rule** | Existe la carpeta `src/i18n/locales/`. |
| T1-TR3 | **rule** | `src/i18n/index.ts` tiene `lng: storedLang ?? 'es'`, `fallbackLng: 'es'`, `supportedLngs: ['es','en','pt']`, y `interpolation: { escapeValue: false }`. |

---

## Task 2: Generación de archivos de traducciones (es.json, en.json, pt.json)
**Prioridad**: high | **Estado**: pending | **Dependencias**: Task 1

### Descripción
Crear los 3 archivos JSON de traducciones. Extraer TODO texto literal visible de:
- `src/App.tsx` → claves `app.*`
- `src/components/MainDashboard.tsx` → `mainDashboard.*`
- `src/components/ThreeFieldViewer.tsx` → `threeFieldViewer.*`
- `src/components/SimulationConfig.tsx` → `simulationConfig.*`
- `src/components/WhatIfStudio.tsx` → `whatIfStudio.*`
- `src/components/FieldMapManager.tsx` → `fieldMapManager.*`
- `src/components/ReportsModule.tsx` → `reportsModule.*`
- `src/components/MLOpsDashboard.tsx` → `mlOpsDashboard.*`
- `src/components/DataPipelinesView.tsx` → `dataPipelinesView.*`
- `src/components/UserManagement.tsx` → `userManagement.*`
- `src/components/ValidationReport.tsx` → `validationReport.*`
- `src/services/pinnEngine.ts` (líneas 422-467) → `pinn.*` con placeholders de interpolación: `{{variable}}`

**Regla estricta**: el valor de `es.json` debe ser el TEXTO LITERAL que existe HOY en el código. NO traducir/parafrasear el español.

### TRs locales
| ID | Tipo | Descripción |
|---|---|---|
| T2-TR1 | **rule** | `es.json`, `en.json`, `pt.json` existen y son JSON válidos (parseables). |
| T2-TR2 | **rule** | El conjunto de claves de los 3 archivos es idéntico (mismo tamaño, mismas keys). |
| T2-TR3 | **rule** | Todos los valores en `es.json` coinciden con los strings literales del código fuente (no inventados). |
| T2-TR4 | **rule** | Las claves `pinn.*` contienen placeholders `{{ }}` para interpolación (ej: `{{projectedYield}}`, `{{scenario}}`, `{{totalIrrigation}}`, `{{waterProductivity}}`, etc.). |

---

## Task 3: Refactor pinnEngine.ts — usar i18next.t() con interpolación
**Prioridad**: high | **Estado**: pending | **Dependencias**: Task 2

### Descripción
En `src/services/pinnEngine.ts` (líneas ~422-467):
- Importar la instancia: `import i18next from '../i18n';` (import relativo)
- Reemplazar `alerts.push({...})` que contienen strings en español por `i18next.t()` con variables dinámicas interpoladas
- Reemplazar el array `recommendations: string[]` con `i18next.t()` en cada entrada
- Mantener intacto el formato `**negrita**` (ya que `escapeValue: false`)
- Preservar exactamente la misma lógica condicional (if/else ternarios)

### TRs locales
| ID | Tipo | Descripción |
|---|---|---|
| T3-TR1 | **rule** | `pinnEngine.ts` importa `i18next` directamente (no `useTranslation`). |
| T3-TR2 | **rule** | No existen template strings literales en español en las 3 alertas ni en las 4 recommendations; se usa `i18next.t("pinn.X", {...})`. |
| T3-TR3 | **rule** | Al ejecutar `runPINNSimulation` con idioma `es`, el resultado `alerts[*].title/description/timing/recommendedAction` contiene el mismo texto que la versión original. |

---

## Task 4: Actualizar main.tsx — importar i18n antes de App
**Prioridad**: high | **Estado**: pending | **Dependencias**: Task 1 (compartida con Task 2-3)

### Descripción
En `src/main.tsx`, agregar la importación `import './i18n';` en la parte superior, antes de `import App from './App.tsx'` (o al menos antes de `createRoot(...).render`). Orden sugerido:
```
import './index.css';
import './i18n';
import App from './App.tsx';
```

### TRs locales
| ID | Tipo | Descripción |
|---|---|---|
| T4-TR1 | **rule** | `main.tsx` contiene `import './i18n'` y aparece textualmente ANTES de `createRoot(...).render(<App />`. |

---

## Task 5: Actualizar App.tsx — useTranslation + selector de idioma
**Prioridad**: high | **Estado**: pending | **Dependencias**: Tasks 2, 4

### Descripción
En `src/App.tsx`:
1. Agregar: `import { useTranslation } from 'react-i18next';`
2. Dentro del componente: `const { t, i18n } = useTranslation();`
3. Reemplazar TODO texto estático visible por `t("app.X")`:
   - Header: subtitle, tooltips, textos de botones (tabs, run button, theme toggle)
   - Status sub-bar: `Campo:`, `Usuario:`, `Escenario:`, `BD:`, `Estado:`, `OK`, `Mock`, `Simulando...`, `Listo`
   - KPIs rápidos bajo el viewer 3D (4 tarjetas)
   - Tabs de navegación (10 tabs con sus labels)
   - Footer: ambos spans
4. **Selector de idioma** al lado de `#btn-theme-toggle`:
   - Usar ícono `Globe` (ya importado)
   - Dropdown (`<select>` o menú) con ES / EN / PT
   - Mismas clases que el toggle: `p-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 ...`
   - `onChange`: `i18n.changeLanguage(value); localStorage.setItem('lang', value);`
5. Asegurar variantes `dark:` en TODO elemento nuevo.

### TRs locales
| ID | Tipo | Descripción |
|---|---|---|
| T5-TR1 | **rule** | App.tsx usa `useTranslation` y reemplaza todos los strings estáticos con `t()`. |
| T5-TR2 | **rule** | Existe un selector `<select>` (o dropdown equivalente) al lado de `#btn-theme-toggle` con 3 opciones: ES, EN, PT. |
| T5-TR3 | **rule** | El selector tiene las clases dark-mode correctas (`bg-slate-100 dark:bg-slate-900` etc., igual que el botón tema). |
| T5-TR4 | **rule** | Al cambiar el selector se ejecutan ambas acciones: `changeLanguage` y `localStorage.setItem("lang", ...)`. |

---

## Task 6: Traducir componentes (en orden, archivo por archivo)
**Prioridad**: high | **Estado**: pending | **Dependencias**: Task 5

### Sub-tareas (procesar UNO a la vez, según instrucción del usuario)
6A. `MainDashboard.tsx` — todas las tarjetas KPI, labels de alertas, botones del switcher de gráficas, títulos, placeholders
6B. `ThreeFieldViewer.tsx` — badges overlay, botones de layers/cámara, slider timeline, velocidad
6C. `SimulationConfig.tsx` — los 4 tabs (climate, crop, irrigation, soil), labels de escenarios, placeholders, botón ejecutar
6D. `WhatIfStudio.tsx` — 3 columnas (A/B/C), labels selects, resultados
6E. `FieldMapManager.tsx` — botones export/import/nuevo, formulario crear campo, lista campos, metadatos, mapa SVG labels
6F. `ReportsModule.tsx` — 3 tarjetas (PDF, Excel, Email), botones, placeholder email
6G. `MLOpsDashboard.tsx` — loss chart, retraining controls, model registry
6H. `DataPipelinesView.tsx` — tarjetas pipelines, botón sincronizar, statuses
6I. `UserManagement.tsx` — badges roles, form crear usuario, tabla usuarios
6J. `ValidationReport.tsx` — métricas hindcast, tests estadísticos, sobol, ensemble

### Patrón uniforme en cada componente:
```tsx
import { useTranslation } from 'react-i18next';
// ...
export const X: React.FC<...> = (...) => {
  const { t } = useTranslation();
  // ... reemplazar strings por t("nombreComponente.X")
};
```

### TRs locales
| ID | Tipo | Descripción |
|---|---|---|
| T6-TR1 | **rule** | Los 10 componentes importan y usan `useTranslation()`. |
| T6-TR2 | **rule** | No queda ningún string literal español visible en los 10 archivos .tsx (excepto nombres de datos/props/variables). |
| T6-TR3 | **rubric** | Cobertura visual: (0-2). 2 = todo texto, tooltips, placeholders y títulos de gráficas traducidos; 1 = >80%, faltan placeholders o títulos menores; 0 = muchos strings sin traducir. Umbral: ≥ 1. |

---

## Task 7: Verificación global — lint + build
**Prioridad**: high | **Estado**: pending | **Dependencias**: Tasks 3, 5, 6

### Descripción
Ejecutar:
1. `npm run lint` (tsc --noEmit) — confirmar sin errores de tipo
2. `npm run build` (vite build) — confirmar build exitoso
3. Revisión manual: abrir navegador, probar los 3 idiomas
   - Seleccionar EN → todo cambia a inglés
   - Seleccionar PT → todo cambia a portugués
   - F5 recarga → persiste el idioma
   - Toggle dark mode → selector y todo se ve bien en ambos temas

### TRs locales
| ID | Tipo | Descripción |
|---|---|---|
| T7-TR1 | **rule** | `npm run lint` termina con exit code 0. |
| T7-TR2 | **rule** | `npm run build` termina con exit code 0 y produce `dist/`. |
| T7-TR3 | **rule** | No aparecen warnings `i18next::translator: missingKey` en la consola al navegar por todas las tabs con los 3 idiomas. |

---

## Matriz de Cobertura de Criterios de Aceptación

| AC | Task(s) que cubren |
|---|---|
| AC-1 | Tasks 1, 4 |
| AC-2 | Tasks 5 |
| AC-3 | Task 2 |
| AC-4 | Task 2 |
| AC-5 | Task 3 |
| AC-6 | Task 5 |
| AC-7 | Task 4 |
| AC-8 | Task 7 |
| AC-9 | Task 7 |
| AC-10 (rubric) | Task 2, revisión final |
| AC-11 (rubric) | Tasks 5, 6, revisión final |
