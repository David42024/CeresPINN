# Especificación: Internacionalización (i18n) de CeresPINN

## Problema
La aplicación CeresPINN actualmente tiene todo el texto de la interfaz codificado directamente en español. Los usuarios de otros idiomas (inglés y portugués) no pueden usar la aplicación en su idioma nativo, lo que limita la adopción internacional.

## Usuarios
- Agricultores, investigadores, consultores y administradores de habla hispana (idioma actual por defecto)
- Usuarios angloparlantes internacionales
- Usuarios lusohablantes (Brasil, Portugal)

## Metas
1. Implementar internacionalización completa con `react-i18next` e `i18next`
2. Soportar 3 idiomas: Español (por defecto), Inglés y Portugués
3. Persistir la selección de idioma del usuario en `localStorage`
4. Extraer TODO el texto visible actual (sin inventar texto) y traducirlo
5. Traducir también las cadenas dinámicas generadas fuera de componentes React (motor PINN)
6. Proporcionar un selector de idioma accesible en el header junto al toggle de tema
7. Mantener compatibilidad total con el modo oscuro existente

## No Metas
- No traducir datos de dominio provenientes del backend (nombres de campos, países, etc.)
- No modificar la lógica de negocio de `pinnEngine.ts`, solo las cadenas de texto
- No tocar el backend ni la carpeta `ml_lab/`
- No crear documentación adicional (*.md) a menos que sea el spec/tasks/review
- No agregar comentarios en el código

---

## Requisitos Funcionales

### RF1: Configuración i18n Base
- Crear/confirmar `src/i18n/index.ts` con:
  - Idiomas soportados: `es`, `en`, `pt`
  - Idioma por defecto: `es`
  - Detección desde `localStorage` con clave `lang`; si no existe, usar `es`
  - Importar e inicializar react-i18next correctamente
  - `escapeValue: false` en interpolación (para permitir markdown `**negrita**`)

### RF2: Archivos de Traducciones
- Crear `src/i18n/locales/es.json`, `en.json`, `pt.json`
- El JSON de `es` DEBE contener el texto literal existente en la app (sin inventar)
- Organizar claves jerárquicamente por archivo/sección:
  - `app.*` — para App.tsx (header, tabs, tooltips, statusBar, footer)
  - `mainDashboard.*`, `threeFieldViewer.*`, `simulationConfig.*`, `whatIfStudio.*`, `fieldMapManager.*`, `reportsModule.*`, `mlOpsDashboard.*`, `dataPipelinesView.*`, `userManagement.*`, `validationReport.*` — para cada componente
  - `pinn.*` — para el texto dinámico de `pinnEngine.ts`
- Todas las claves definidas en `es.json` deben existir también en `en.json` y `pt.json` con traducciones coherentes

### RF3: Texto Dinámico en pinnEngine.ts (líneas ~429-473)
- Mover todas las frases con template strings a claves `pinn.*`
- Usar interpolación de i18next (`t("clave", { variable })`) para:
  - Números (rendimiento, mm, %, etc.)
  - Valores dinámicos (`config.scenario`, `soil.label`, etc.)
- Mantener el formato markdown `**negrita**` dentro de las traducciones
- Importar la instancia de `i18next` directamente (no `useTranslation`) porque la función corre fuera de componentes React

### RF4: Integración en Componentes
- En cada `src/components/*.tsx` y en `src/App.tsx`:
  - Importar `useTranslation` from `react-i18next`
  - Invocar el hook: `const { t } = useTranslation();`
  - Reemplazar TODO string estático visible por `t("clave_correspondiente")`
- Mantener IDs de elementos y atributos `title`/`placeholder` también traducidos

### RF5: Selector de Idioma en Header
- Ubicación: en `App.tsx`, justo al lado del botón `btn-theme-toggle`
- Estilo visual idéntico al toggle:
  - `p-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-all`
- Ícono: `Globe` (ya importado de lucide-react)
- Dropdown con 3 opciones: ES / EN / PT
- Al seleccionar:
  1. `i18n.changeLanguage(codigo)`
  2. `localStorage.setItem("lang", codigo)`

### RF6: Integración en main.tsx
- Importar `./i18n` ANTES de renderizar `<App />` y ANTES/AL lado de `import './index.css'`
- El orden importa: i18n debe estar inicializado antes de que cualquier componente use `useTranslation`

### RF7: Compatibilidad Modo Oscuro
- TODOS los elementos nuevos (selector de idioma, dropdowns, badges) deben usar variantes `dark:` existentes
- Verificar que se vean correctamente en ambos temas

---

## Requisitos No Funcionales

### RNF1: Integridad Tipográfica
- Todo código TypeScript debe compilar sin errores (`tsc --noEmit`)
- Build de producción debe pasar sin errores (`vite build`)

### RNF2: Ausencia de Errores Runtime
- No deben aparecer warnings "missing key" en consola del navegador
- Todas las claves usadas deben estar definidas en los 3 archivos JSON

### RNF3: Persistencia y Restablecimiento
- Al recargar la página, el idioma seleccionado debe persistir correctamente
- Si `localStorage.lang` contiene un valor inválido, debe caer a `es` sin errores

### RNF4: Convención de Código
- Usar el estilo de código existente en el proyecto
- Sin `console.log` de depuración ni comentarios
- Sin inventar texto para las traducciones al español: debe ser el texto literal actual

---

## Restricciones y Dependencias

- Dependencias ya presentes (verificadas en package.json):
  - `i18next`: ^26.4.2
  - `react-i18next`: ^17.0.13
- **No instalar nuevas dependencias**
- Archivo `src/i18n/index.ts` ya existe con estructura base (verificar antes de sobreescribir)
- Alcance exclusivo a `src/` — no tocar `backend/`, `ml_lab/`
- Icono `Globe` ya importado en App.tsx

## Supuestos

- Los valores dinámicos como nombres de campos, nombres de usuario, países, códigos de etapa fenológica (VT, R1, etc.) y parámetros técnicos (Richards, CMIP6, Van Genuchten) no se traducen (son nombres propios/términos científicos).
- El texto dentro de archivos de exportación PDF/Excel (ReportsModule) que no es UI visible queda en español (se trata como contenido generado, no interfaz).

## Preguntas Abiertas

- Ninguna — los requisitos han sido especificados explícitamente por el usuario.

---

## Criterios de Aceptación

| ID | Tipo | Descripción |
|---|---|---|
| AC-1 | **rule** | La aplicación se carga sin errores JS y `i18n.language` === `'es'` cuando `localStorage.lang` no existe. |
| AC-2 | **rule** | Al seleccionar "EN" en el selector, toda la UI cambia a inglés; al recargar, persiste "EN"; al seleccionar "PT" cambia a portugués y persiste. |
| AC-3 | **rule** | `src/i18n/locales/es.json` contiene únicamente el texto literal actualmente visible en la app (sin texto inventado). |
| AC-4 | **rule** | Todas las claves presentes en `es.json` existen también en `en.json` y `pt.json` con valores no vacíos. |
| AC-5 | **rule** | `pinnEngine.ts` genera las mismas frases que antes (en español) cuando lang=es, usando `i18next.t()` con interpolación; el formato `**negrita**` se preserva. |
| AC-6 | **rule** | El selector de idioma en App.tsx está visualmente al lado de `#btn-theme-toggle` y usa las mismas clases de estilo y variantes `dark:`. |
| AC-7 | **rule** | `main.tsx` importa `./i18n` antes de `createRoot(...).render(<App />)`. |
| AC-8 | **rule** | Ejecutando `npm run lint` (tsc --noEmit) no hay errores de tipo. |
| AC-9 | **rule** | Ejecutando `npm run build` (vite build) termina con exit code 0. |
| AC-10 | **rubric** | Coherencia de traducción al inglés y portugués: (0-2 puntos). 2 = términos agronómicos técnicos traducidos profesionalmente sin pérdida semántica; 1 = entendible pero impreciso en algunos términos; 0 = errores graves o claves sin traducir. Umbral de aprobación: ≥ 1. |
| AC-11 | **rubric** | Cobertura de traducciones: (0-2 puntos). 2 = 100% del texto UI visible traducido (incluyendo tooltips, placeholders, títulos); 1 = >80% traducido, faltan algunos strings menores; 0 = >20% texto sin traducir. Umbral de aprobación: ≥ 1. |
