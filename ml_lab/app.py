import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import time
import sys
import warnings
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)


import joblib

class PyTorchWrapper:
    def __init__(self, pt_model, sc_X, sc_y):
        self.model = pt_model
        self.scaler_X = sc_X
        self.scaler_y = sc_y
    def predict(self, X):
        import torch
        X = X.replace([np.inf, -np.inf], np.nan) if isinstance(X, pd.DataFrame) else np.where(np.isfinite(X), X, np.nan)
        X_s = self.scaler_X.transform(X)
        X_t = torch.tensor(X_s, dtype=torch.float32)
        self.model.eval()
        with torch.no_grad():
            pred_s, _ = self.model(X_t)
        return self.scaler_y.inverse_transform(pred_s.numpy().reshape(-1, 1)).flatten()

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_lab.eda_quality import temporal_outlier_audit
from ml_lab.training_data import observed_targets, temporal_partitions
    
DATA_PATH = PROJECT_ROOT / "backend" / "data" / "processed" / "canonical_panel.parquet"
META_PATH = PROJECT_ROOT / "backend" / "models" / "cerespinn_spatial_v4_metadata.json"
MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "cerespinn_spatial_v4.joblib"

st.set_page_config(
    page_title="CeresPINN ML Lab",
    page_icon="🌽",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data
def load_data():
    CLEAN_PATH = PROJECT_ROOT / "backend" / "data" / "processed" / "canonical_panel_cleaned.parquet"
    if CLEAN_PATH.exists():
        return pd.read_parquet(CLEAN_PATH)
    if DATA_PATH.exists():
        return pd.read_parquet(DATA_PATH)
    return pd.DataFrame()

def load_meta():
    if META_PATH.exists():
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    return {}

def render_sidebar():
    with st.sidebar:
        st.title("🌽 CeresPINN ML Lab")
        st.markdown("---")
        page = st.radio(
            "Navegación",
            [
                "1. Dashboard General",
                "2. Análisis de Datos (EDA)",
                "3. Limpieza de Datos",
                "4. Entrenamiento",
                "5. Selección del mejor modelo",
                "6. Validación Cruzada",
                "7. Pruebas Estadísticas",
                "8. Evaluación del Modelo",
                "9. Explicabilidad del Modelo",
                "10. Distribución Geoespacial",
                "11. Reportes",
            ],
            key="ml_lab_page"
        )
        st.markdown("---")
        st.info("Plataforma exclusiva para análisis MLOps del Gemelo Digital CeresPINN.")
        return page

def render_dashboard(df, meta):
    st.markdown("""
    <style>
    .lab-hero {padding:28px 32px; border-radius:20px;
      background:linear-gradient(115deg,#064e3b,#087f70); color:white; margin-bottom:24px;}
    .lab-hero h1 {color:white; margin:8px 0 10px; font-size:2.35rem; letter-spacing:-.7px;}
    .lab-hero p {margin:0; color:#d1fae5; font-size:1.04rem; max-width:760px;}
    .lab-eyebrow {font-size:.8rem; font-weight:700; letter-spacing:1.8px; color:#a7f3d0;}
    [data-testid="stMetric"] {padding:18px; border-radius:14px;
      background:var(--secondary-background-color); border:1px solid rgba(128,128,128,.18);}
    [data-testid="stMetricLabel"] {font-size:.88rem;}
    @media(max-width:640px) {.lab-hero{padding:22px;} .lab-hero h1{font-size:1.8rem;}}
    </style>
    <div class="lab-hero"><div class="lab-eyebrow">CERESPINN · ML LAB</div>
      <h1>🌽 Tu laboratorio de maíz y clima</h1>
      <p>Explora tus datos, evalúa los modelos y reúne los resultados.
      Todo lo que necesitas para seguir el avance de tu investigación.</p></div>
    """, unsafe_allow_html=True)

    def read_result(path):
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            st.warning(f'No se pudo leer {path.name}.')
            return None

    folder = PROJECT_ROOT / 'ml_lab' / 'artifacts'
    benchmark = read_result(folder / 'common_benchmark.json')
    statistics = read_result(folder / 'statistical_analysis.json')
    cv_paths = sorted(folder.glob('cv_*.json'))
    reports = list((PROJECT_ROOT / 'ml_lab' / 'reports').glob('report_*.json'))
    years = pd.to_numeric(df['year'], errors='coerce').dropna() if 'year' in df else pd.Series(dtype=float)
    missing = float(df.isna().sum().sum() / df.size * 100) if df.size else None
    cards = st.columns(4)
    cards[0].metric('Observaciones disponibles', f'{len(df):,}')
    cards[1].metric('Condados representados', f"{df['fips'].nunique():,}" if 'fips' in df else 'Sin datos')
    cards[2].metric('Años de historia', f'{years.nunique():,}')
    cards[3].metric('Valores faltantes', f'{missing:.1f}%' if missing is not None else 'Sin datos')
    if not years.empty:
        cleaned = DATA_PATH.with_name('canonical_panel_cleaned.parquet').exists()
        st.caption(f"Cobertura {int(years.min())}–{int(years.max())} · "
                   f"{'Panel con limpieza guardada' if cleaned else 'Panel original'} · Rendimiento en kg/ha")

    st.subheader('¿Qué quieres hacer hoy?')
    def navigate(page):
        st.session_state['ml_lab_page'] = page
    shortcuts = [
        ('🔎 Explorar datos', '2. Análisis de Datos (EDA)'),
        ('🧠 Evaluar modelos', '6. Validación Cruzada'),
        ('🏅 Comparar resultados', '5. Selección del mejor modelo'),
        ('📄 Crear un reporte', '11. Reportes'),
    ]
    for column, (label, page) in zip(st.columns(4), shortcuts):
        column.button(label, on_click=navigate, args=(page,), use_container_width=True)

    st.markdown('')
    left, right = st.columns([1.6, 1], gap='large')
    with left:
        with st.container(border=True):
            st.subheader('Rendimiento a lo largo del tiempo')
            if {'year', 'yield_kg_ha'}.issubset(df.columns) and not df.empty:
                chart_data = df[['year', 'yield_kg_ha']].apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
                annual = chart_data.groupby('year', as_index=False)['yield_kg_ha'].mean()
                if annual.empty:
                    st.info('No hay rendimientos finitos para mostrar.')
                else:
                    if annual.year.nunique() > 1:
                        start, stop = st.slider('Periodo del gráfico', int(annual.year.min()),
                            int(annual.year.max()), (int(annual.year.min()), int(annual.year.max())))
                        annual = annual[annual.year.between(start, stop)]
                    fig = px.area(annual, x='year', y='yield_kg_ha',
                        labels={'year': 'Año', 'yield_kg_ha': 'Rendimiento promedio (kg/ha)'},
                        color_discrete_sequence=['#10a37f'])
                    fig.update_traces(mode='lines+markers', hovertemplate='Año %{x}<br>%{y:,.0f} kg/ha<extra></extra>')
                    fig.update_layout(height=320, margin=dict(l=10, r=10, t=15, b=10))
                    st.plotly_chart(fig, width='stretch')
                    st.caption('Promedio de observaciones disponibles por año. El selector filtra solo este gráfico.')
            else:
                st.info('Carga el panel de datos para visualizar su evolución histórica.')
    with right:
        with st.container(border=True):
            st.subheader('Modelo seleccionado')
            if benchmark and benchmark.get('results'):
                winner = benchmark.get('winner')
                result = next((r for r in benchmark['results'] if r['model'] == winner), None)
                if result:
                    st.markdown(f'**{winner}**')
                    a, b = st.columns(2)
                    a.metric('R² en prueba', f"{result['test_r2']:.3f}")
                    b.metric('RMSE en prueba', f"{result['test_rmse_kg_ha']:,.0f}")
                    st.caption('RMSE en kg/ha. Selección por validación independiente común.')
                    st.caption(f"Último benchmark: {benchmark.get('created_at', 'sin fecha')}")
                else:
                    st.info('El benchmark guardado no identifica una fila ganadora.')
            else:
                st.info('Aún no hay un ganador evaluado con el benchmark común.')
                st.button('Ejecutar mi primera comparación', on_click=navigate,
                          args=('5. Selección del mejor modelo',), use_container_width=True)
            if meta:
                st.caption(f"Modelo guardado: {meta.get('algorithm', 'sin nombre')}. "
                           'Puede corresponder a una ejecución diferente del benchmark.')

    st.subheader('Avance del laboratorio')
    milestones = [
        ('📊 Datos', not df.empty, f'{len(df):,} observaciones para explorar.' if not df.empty else 'Carga o extrae el panel climático.'),
        ('🧪 Validación', bool(cv_paths), f'{len(cv_paths)} evaluaciones guardadas.' if cv_paths else 'Evalúa años futuros o condados nuevos.'),
        ('📈 Estadísticas', statistics is not None, 'Suite estadística disponible.' if statistics else 'Calcula intervalos y compara errores.'),
        ('📄 Reportes', bool(reports), f'{len(reports)} informes guardados.' if reports else 'Genera tu primer informe.'),
    ]
    for column, (label, done, description) in zip(st.columns(4), milestones):
        with column:
            with st.container(border=True):
                st.markdown(f'**{label}**')
                st.caption('✅ Disponible' if done else '○ Pendiente')
                st.write(description)
    with st.expander('Conocer el proyecto'):
        st.write('CeresPINN reúne datos climáticos y rendimientos de maíz en un panel de condado y año. '
                 'La validación temporal evalúa años posteriores; la espacial evalúa condados no vistos. '
                 'Los resultados del laboratorio tienen alcance exploratorio.')


def render_eda(df):
    st.title("🔍 Análisis Exploratorio de Datos (EDA)")
    st.markdown("---")
    if df.empty:
        st.error("No se encontró el canonical_panel.parquet.")
        return
        
    st.subheader("Muestra del Dataset")
    st.dataframe(df.head(10))

    st.subheader("Estadísticas descriptivas generales")
    numeric = df.select_dtypes(include=[np.number])
    if not numeric.empty:
        summary = numeric.describe().T.rename(columns={
            'count': 'Observaciones', 'mean': 'Media', 'std': 'Desviación estándar',
            'min': 'Mínimo', '25%': 'Q1', '50%': 'Mediana', '75%': 'Q3', 'max': 'Máximo'})
        summary['Nulos'] = numeric.isna().sum()
        st.dataframe(summary, width='stretch')
        st.download_button("Descargar estadísticas CSV", summary.to_csv().encode('utf-8-sig'),
                           'estadisticas_eda.csv', 'text/csv')

    st.subheader("Boxplots por variable, año o condado")
    variables = list(numeric.columns)
    if variables:
        variable = st.selectbox("Variable del boxplot", variables,
                                index=variables.index('yield_kg_ha') if 'yield_kg_ha' in variables else 0)
        groups = ['Sin agrupación'] + [c for c in ['year', 'fips'] if c in df.columns and c != variable]
        group = st.selectbox("Agrupar boxplot", groups,
                             format_func=lambda v: {'year': 'Año', 'fips': 'Condado'}.get(v, v))
        plot_df = df.copy()
        if group == 'fips':
            counties = sorted(plot_df['fips'].dropna().astype(str).unique())
            selected = st.multiselect("Condados a comparar", counties, default=counties[:10])
            plot_df = plot_df[plot_df['fips'].astype(str).isin(selected)]
        if plot_df.empty:
            st.info("Selecciona al menos un condado con datos.")
        else:
            if group != 'Sin agrupación':
                plot_df[group] = plot_df[group].astype(str)
            st.plotly_chart(px.box(plot_df, x=None if group == 'Sin agrupación' else group,
                                   y=variable, points='outliers', title=f'Distribución de {variable}'),
                            width='stretch')

    st.subheader("Comprobación de duplicados")
    exact = df.duplicated(keep=False)
    extra = int(df.duplicated().sum())
    st.metric("Filas repetidas adicionales exactas", extra)
    if exact.any():
        st.dataframe(df[exact], width='stretch')
    else:
        st.success("No se encontraron filas duplicadas exactas.")
    if {'year', 'fips'}.issubset(df.columns):
        valid_key = df[['year', 'fips']].notna().all(axis=1)
        normalized_keys = df[['year', 'fips']].copy()
        normalized_keys['year'] = pd.to_numeric(normalized_keys['year'], errors='coerce')
        normalized_keys['fips'] = normalized_keys['fips'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5)
        repeated_keys = valid_key & normalized_keys.duplicated(keep=False)
        st.metric("Filas con clave condado y año repetida", int(repeated_keys.sum()))
        if repeated_keys.any():
            st.warning("Estas claves pueden contener valores contradictorios. Revisa los registros antes de eliminarlos.")
            st.dataframe(df[repeated_keys].sort_values(['year', 'fips']), width='stretch')
        st.caption(f"Filas con claves incompletas: {int((~valid_key).sum())}.")

    st.subheader("Limpieza con separación temporal")
    render_cleaning_controls(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribución de Rendimientos (kg/ha)")
        fig = px.histogram(df, x="yield_kg_ha", nbins=50, color_discrete_sequence=['#10b981'])
        st.plotly_chart(fig, width='stretch')
        
    with col2:
        st.subheader("Rendimiento a través del tiempo")
        yearly_yield = df.groupby("year")["yield_kg_ha"].mean().reset_index()
        fig2 = px.line(yearly_yield, x="year", y="yield_kg_ha", markers=True, color_discrete_sequence=['#06b6d4'])
        st.plotly_chart(fig2, width='stretch')
        
    st.subheader("Matriz de Correlación Climática")
    corr_cols = ['yield_kg_ha', 'season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
    # Filter only existing columns
    corr_cols = [c for c in corr_cols if c in df.columns]
    corr = df[corr_cols].corr()
    fig3 = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r")
    st.plotly_chart(fig3, width='stretch')

def render_data_cleaning(df):
    st.title("🧹 Limpieza de Datos")
    st.markdown("---")
    if df.empty:
        return
        
    st.subheader("Valores Nulos")
    nulls = df.isnull().sum()
    st.dataframe(pd.DataFrame({"Nulos": nulls, "Porcentaje": (nulls/len(df))*100}).style.format({"Porcentaje": "{:.2f}%"}))
    
    render_cleaning_controls(df)


def render_cleaning_controls(df):
    # Always fit on the original panel, not a previously filtered derivative.
    source = pd.read_parquet(DATA_PATH) if DATA_PATH.exists() else df.copy()
    st.caption("Auditoría sobre el panel original. Los años más recientes se reservan para evaluación.")
    fraction = st.slider("Proporción de años para entrenamiento", 0.5, 0.9, 0.8, 0.05)
    try:
        audit = temporal_outlier_audit(source, fraction)
    except ValueError as exc:
        st.warning(str(exc))
        return
    st.write(f"Entrenamiento: {int(audit['train_years'][0])}–{int(audit['train_years'][-1])} "
             f"({int(audit['train'].sum())} filas). Evaluación: "
             f"{int(audit['evaluation_years'][0])}–{int(audit['evaluation_years'][-1])} "
             f"({int(audit['evaluation'].sum())} filas).")
    st.dataframe(pd.DataFrame([{'Media de entrenamiento': audit['mean'],
        'Desviación de entrenamiento': audit['std'], 'Límite inferior': audit['lower'],
        'Límite superior': audit['upper']}]), width='stretch')
    a, b = st.columns(2)
    a.metric("Outliers de entrenamiento", int(audit['remove'].sum()))
    b.metric("Outliers de evaluación conservados", int((audit['outlier'] & audit['evaluation']).sum()))
    flagged = source[audit['outlier'] | audit['invalid']].copy()
    if not flagged.empty:
        flagged['Partición'] = np.where(audit['train'][audit['outlier'] | audit['invalid']],
                                        'Entrenamiento', 'Evaluación o año inválido')
        st.dataframe(flagged, width='stretch')
    st.info("Los umbrales de ±3 desviaciones se ajustan solo en entrenamiento. "
            "Se eliminan únicamente sus outliers; la evaluación permanece completa. "
            "Los valores faltantes o infinitos se señalan y no se eliminan automáticamente.")
    st.caption("Esta separación protege esta limpieza temporal. El K-Fold aleatorio del módulo "
               "de entrenamiento conserva su protocolo actual y requiere limpieza dentro de cada fold.")
    if st.button("Guardar limpieza de entrenamiento y conservar evaluación"):
        clean_df = source.loc[~audit['remove']].copy()
        clean_path = DATA_PATH.with_name('canonical_panel_cleaned.parquet')
        clean_df.to_parquet(clean_path)
        metadata = {k: audit[k] for k in ['mean', 'std', 'lower', 'upper']}
        metadata.update(train_years=[int(y) for y in audit['train_years']],
                        evaluation_years=[int(y) for y in audit['evaluation_years']],
                        removed_training_rows=int(audit['remove'].sum()),
                        evaluation_rows=int(audit['evaluation'].sum()),
                        source=str(DATA_PATH), train_fraction=fraction)
        clean_path.with_suffix('.audit.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        st.cache_data.clear()
        st.success(f"Limpieza guardada: {len(clean_df)} filas. Evaluación conservada íntegramente.")
        st.rerun()

def render_stats(df):
    st.title('Pruebas estadísticas e incertidumbre')
    st.subheader('Pruebas que puedes aplicar')
    tests = [
        ('🌡️ Comparación térmica', 'Diferencia de medias entre grupos cálidos y frescos.',
         'Bootstrap por condado y año · IC y Hedges g. Welch t como diagnóstico descriptivo.'),
        ('🌧️ Grupos de precipitación', 'Compara las medias de los grupos seco, intermedio y húmedo.',
         'Contraste global y comparaciones por pares con bootstrap · Eta² e IC.'),
        ('🔗 Pearson y Spearman', 'Evalúa la asociación del rendimiento con temperatura y precipitación.',
         'Correlación lineal y por rangos · IC y contraste con bootstrap agrupado.'),
        ('🔔 Normalidad KS', 'Contrasta un modelo nulo de normalidad con dependencia de condado y año.',
         'Calibración paramétrica aproximada · Media y desviación reestimadas en cada simulación.'),
        ('🧪 Supuestos del ANOVA', 'Revisa tamaños de grupo, varianzas y distribución de residuos.',
         'Levene y Shapiro como diagnósticos orientativos · F clásico solo descriptivo.'),
        ('⚖️ Comparación pareada', 'Compara errores absolutos de modelos sobre las mismas observaciones.',
         'Requiere benchmark · Bootstrap agrupado, IC y efecto dz.'),
    ]
    for offset in range(0, len(tests), 3):
        for column, (name, purpose, method) in zip(st.columns(3), tests[offset:offset + 3]):
            with column:
                with st.container(border=True):
                    st.markdown(f'**{name}**')
                    st.write(purpose)
                    st.caption(method)
    st.caption('Todas las pruebas inferenciales ejecutadas reciben corrección Holm por '
               'comparaciones múltiples. Las tarjetas describen los métodos disponibles; '
               'los resultados aparecen después de ejecutar la suite.')
    source = pd.read_parquet(DATA_PATH) if DATA_PATH.exists() else df.copy()
    required = {'year', 'fips', 'yield_kg_ha', 'season_tmax_mean_c', 'season_precip_mm'}
    if source.empty or not required.issubset(source.columns):
        st.warning('Se requiere un panel con año, condado, rendimiento, temperatura máxima y precipitación.')
        return
    st.info('El bootstrap remuestrea condados y años por separado y cruza sus multiplicidades. '
            'Así se considera la dependencia entre filas del mismo condado o año. '
            'La inferencia es aproximada y requiere suficientes grupos; no controla '
            'automáticamente autocorrelación entre años ni dependencia entre condados vecinos.')
    st.caption('Se usa el panel original. Las asociaciones observacionales no demuestran causalidad. '
               'Se requieren al menos cinco años y cinco condados en cada análisis agrupado.')
    temperatures = pd.to_numeric(source['season_tmax_mean_c'], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
    if temperatures.empty or temperatures.min() == temperatures.max():
        st.warning('La temperatura debe contener valores finitos y variación.')
        return
    threshold = st.slider('Umbral para grupos de temperatura (°C)',
        float(temperatures.min()), float(temperatures.max()), float(temperatures.median()))
    lower = st.number_input('Percentil inferior de precipitación', 1, 98, 33)
    upper = st.number_input('Percentil superior de precipitación', 2, 99, 66)
    alpha = st.selectbox('Nivel de significancia', [0.05, 0.01, 0.1])
    replicates = st.number_input('Réplicas bootstrap', 200, 5000, 500, 100)
    benchmark = PROJECT_ROOT / 'ml_lab' / 'artifacts' / 'common_benchmark.json'
    paired = st.checkbox('Incluir comparación pareada de todos los modelos del benchmark', value=False)
    if not benchmark.exists():
        st.caption('Las pruebas del panel están disponibles. La comparación de modelos quedará '
                   'pendiente hasta ejecutar el benchmark de la página 5.')
    st.caption('Holm se aplica a todos los contrastes, correlaciones y prueba de normalidad de esta '
               'ejecución, incluidas las comparaciones de modelos si se seleccionan. '
               'Los intervalos son percentiles marginales; no son intervalos simultáneos.')
    path = PROJECT_ROOT / 'ml_lab' / 'artifacts' / 'statistical_analysis.json'
    if st.button('Ejecutar suite estadística y bootstrap', type='primary'):
        from ml_lab.statistical_analysis import panel_suite, paired_model_tests, holm_adjust
        try:
            with st.spinner('Calculando intervalos y pruebas agrupadas...'):
                report = panel_suite(source, threshold, (lower, upper), int(replicates), alpha)
                report['paired_results'] = []
                report['paired_warning'] = None
                if paired:
                    try:
                        if not benchmark.exists():
                            raise ValueError('Ejecuta el benchmark común de la página 5 para comparar modelos.')
                        model_report = json.loads(benchmark.read_text(encoding='utf-8'))
                        report['paired_results'] = paired_model_tests(model_report, int(replicates), alpha)
                        report['benchmark_created_at'] = model_report.get('created_at', 'sin fecha')
                    except (ValueError, KeyError, OSError, ImportError) as exc:
                        report['paired_warning'] = f'Comparación pareada pendiente: {exc}'
                family = report['results'] + report['paired_results']
                for row, corrected in zip(family, holm_adjust([row['p_value'] for row in family])):
                    row.update(p_holm=corrected, reject=corrected < alpha)
                from datetime import datetime, timezone
                report['created_at'] = datetime.now(timezone.utc).isoformat()
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix('.tmp')
                temporary.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
                temporary.replace(path)
                st.success('Pruebas del panel calculadas. Los resultados se muestran abajo.')
        except Exception as exc:
            st.error(f'No se completó la suite: {exc}. Revisa los grupos y las columnas.')
            return
    if not path.exists():
        st.info('Ejecuta la suite para visualizar los resultados.')
        return
    report = json.loads(path.read_text(encoding='utf-8'))
    if report.get('paired_warning'):
        st.warning(report['paired_warning'])
    st.caption(f"Resultados guardados: {report['created_at']}. Alfa: {report['alpha']}; "
               f"réplicas: {report['replicates']}; umbral térmico: {report['temperature_threshold']:.2f} °C. "
               f"Filas excluidas: {report['excluded_rows']}.")
    st.subheader('Tamaños y cobertura de los grupos')
    st.dataframe(pd.DataFrame(report['groups']), width='stretch')
    st.subheader('Contrastes, tamaños del efecto e intervalos de confianza')
    table = pd.DataFrame(report['results'])
    table['Decisión con Holm'] = np.where(table['reject'], 'Rechazar H0', 'No rechazar H0')
    st.dataframe(table, width='stretch')
    st.caption('Diferencias de medias en kg/ha; Hedges g es una diferencia estandarizada. '
               'Pearson y Spearman cuantifican asociación. Los valores p de los contrastes '
               'usan la distribución bootstrap centrada bajo H0.')
    st.caption('El estadístico t de Welch se conserva como descripción en los diagnósticos; '
               'la decisión del contraste térmico usa el bootstrap agrupado y Holm.')
    st.write('Una diferencia entre grupos térmicos es una asociación: no demuestra que '
             'el calor causó la diferencia. No rechazar H0 tampoco demuestra igualdad.')
    st.subheader('ANOVA y comprobación de supuestos')
    st.json(report['anova_diagnostics'])
    st.write('Se comprueban tamaño y cobertura de cada grupo, homogeneidad de varianzas '
             'con Levene y normalidad de residuos con Shapiro. Sus valores p IID son '
             'diagnósticos orientativos. Como las filas del panel son dependientes, '
             'la decisión global usa bootstrap agrupado; el F clásico se muestra solo '
             'como descripción. Eta cuadrado cuantifica la proporción de variación entre grupos.')
    st.subheader('Normalidad con parámetros estimados')
    normal = next(row for row in report['results'] if row['test'].startswith('KS normalidad'))
    st.write('KS se calibra mediante simulaciones de un modelo nulo gaussiano con efectos '
             'aleatorios de condado y año. En cada simulación se reestiman media y desviación. '
             'Es una calibración aproximada condicionada a ese modelo; no es el valor p del KS IID.')
    st.write('Se rechaza el modelo nulo de normalidad al nivel ajustado.' if normal['reject'] else
             'No hay evidencia suficiente para rechazar el modelo nulo de normalidad; esto no confirma normalidad.')
    st.subheader('Distribuciones bootstrap')
    distributions = pd.DataFrame(report['bootstrap'])
    selected = st.selectbox('Contraste para visualizar', distributions['test'].unique())
    st.plotly_chart(px.histogram(distributions[distributions['test'] == selected],
        x='difference_kg_ha', nbins=40, title='Diferencia de medias en réplicas agrupadas'), width='stretch')
    intervals = table.dropna(subset=['ci_lower', 'ci_upper']).copy()
    if not intervals.empty:
        intervals['Inferior'] = intervals['estimate'] - intervals['ci_lower']
        intervals['Superior'] = intervals['ci_upper'] - intervals['estimate']
        # Endpoint bars remain valid even if a percentile interval does not contain the point estimate.
        intervals['Centro IC'] = (intervals['ci_lower'] + intervals['ci_upper']) / 2
        intervals['Semiancho IC'] = (intervals['ci_upper'] - intervals['ci_lower']) / 2
        st.plotly_chart(px.scatter(intervals, x='Centro IC', y='test', error_x='Semiancho IC',
            title='Intervalos percentiles marginales; cada fila conserva sus unidades'), width='stretch')
    st.subheader('Pruebas pareadas de errores de modelos')
    if report['paired_results']:
        st.dataframe(pd.DataFrame(report['paired_results']), width='stretch')
        st.caption('Diferencia de error absoluto A menos B sobre las mismas filas de prueba. '
                   'Un valor negativo favorece A. El bootstrap conserva el emparejamiento '
                   'y agrupa por condado y año. dz es el efecto estandarizado pareado.')
    else:
        st.info('Selecciona la comparación pareada y ejecuta la suite después de generar el benchmark común.')
    st.download_button('Descargar informe estadístico JSON', json.dumps(report, indent=2),
                       'estadistica_bootstrap.json', 'application/json')
    st.download_button('Descargar tabla estadística CSV', table.to_csv(index=False).encode('utf-8-sig'),
                       'estadistica.csv', 'text/csv')


def render_training(df):
    render_pytorch(df)


def render_cv_controls(df, default_nested=False):
    st.title('Validación cruzada temporal y espacial')
    st.write('La validación temporal entrena con años anteriores y evalúa años posteriores. '
             'La espacial deja condados completos fuera del entrenamiento. '
             'Son evaluaciones distintas y sus resultados se presentan por separado.')
    protocol = st.selectbox('Protocolo', ['temporal', 'spatial'],
        format_func=lambda value: 'Temporal por años futuros' if value == 'temporal' else 'Espacial por condados nuevos')
    nested = st.checkbox('Validación anidada para evaluar la búsqueda de hiperparámetros', value=default_nested)
    splits = st.number_input('Particiones externas', min_value=2, max_value=5, value=3)
    epochs = st.number_input('Épocas PyTorch por ajuste', min_value=10, max_value=2000, value=100, step=10)
    st.caption('Incluye Ridge, Random Forest, HistGradientBoosting, MLP, ensamble Ridge y MLP '
               'y PyTorch con regularización por derivadas. La imputación y normalización se '
               'ajustan únicamente con los datos de entrenamiento de cada fold.')
    if nested:
        st.info('Cada fold externo contiene una búsqueda interna de dos folds con el mismo protocolo. '
                'El fold externo nunca participa en la selección de parámetros. '
                'La búsqueda puede requerir numerosos entrenamientos, especialmente en PyTorch.')
    path = PROJECT_ROOT / 'ml_lab' / 'artifacts' / f"cv_{protocol}_{'nested' if nested else 'fixed'}.json"
    if st.button('Ejecutar validación cruzada', type='primary'):
        from ml_lab.cross_validation import run_cross_validation
        source = pd.read_parquet(DATA_PATH) if DATA_PATH.exists() else df.copy()
        progress = st.progress(0.0)
        status = st.empty()
        def update(value, message):
            progress.progress(value)
            status.text(message)
        try:
            report = run_cross_validation(source, protocol, nested=nested,
                n_splits=int(splits), epochs=int(epochs), progress=update)
            from datetime import datetime, timezone
            report['created_at'] = datetime.now(timezone.utc).isoformat()
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix('.tmp')
            temp.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
            temp.replace(path)
        except Exception as exc:
            st.error(f'No se completó la evaluación: {exc}')
            return
    if not path.exists():
        st.info('No hay resultados guardados de este protocolo. Ejecuta la evaluación.')
        return
    try:
        report = json.loads(path.read_text(encoding='utf-8'))
        folds = pd.DataFrame(report['results'])
    except (ValueError, KeyError) as exc:
        st.error(f'No se pudo leer el resultado: {exc}')
        return
    st.caption(f"Ejecución: {report['created_at']}. Métrica: {report['metric_name']}. "
               f"Folds externos: {report['outer_folds']}; internos: {report['inner_folds']}.")
    summary = folds.groupby('model').agg(R2_media=('r2', 'mean'), R2_desviacion=('r2', 'std'),
        RMSE_media_kg_ha=('rmse_kg_ha', 'mean'), MAE_media_kg_ha=('mae_kg_ha', 'mean')).reset_index()
    st.subheader('Resultados externos por modelo')
    st.dataframe(summary.sort_values('R2_media', ascending=False), width='stretch')
    st.plotly_chart(px.box(folds, x='model', y='r2', points='all',
        title='R² por fold externo'), width='stretch')
    st.subheader('Auditoría de particiones y parámetros elegidos')
    st.dataframe(folds, width='stretch')
    st.download_button('Descargar resultados CV', json.dumps(report, indent=2),
                       path.name, 'application/json')
    st.caption('Las métricas describen generalización bajo el protocolo elegido. '
               'La validación temporal permite condados ya observados; la espacial puede '
               'compartir años. No constituyen una prueba conjunta de años y regiones nuevos.')


def render_model_eval(meta):
    st.title("🤖 Evaluación del Modelo Desplegado en Producción")
    st.markdown("---")
    if not meta:
        st.warning("No hay metadata generada. Entrena el modelo en la Fase 3 del backend.")
        return
        
    st.subheader("Metadatos del Checkpoint v4")
    st.json(meta)


def render_xai(df):
    st.title("🧠 Inteligencia Artificial Explicable (XAI)")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown("Entrena un modelo interpretativo rápido (Random Forest) para entender qué variables dominan las predicciones del rendimiento agrícola.")
    
    if st.button("Generar Explicabilidad (SHAP / Feature Importance)"):
        from sklearn.ensemble import RandomForestRegressor
        import plotly.express as px
        
        feature_names = ['season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
        feature_names = [f for f in feature_names if f in df.columns]
        
        training_df, excluded = observed_targets(df)
        st.caption(f'Rendimientos faltantes o no finitos excluidos: {excluded}.')
        if len(training_df) < 5:
            st.error('Se requieren al menos cinco rendimientos observados.')
            return
        X = training_df[feature_names].replace([np.inf, -np.inf], np.nan).fillna(0)
        y = training_df['yield_kg_ha']
        
        rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        rf.fit(X, y)
        
        importances = rf.feature_importances_
        imp_df = pd.DataFrame({"Variable": feature_names, "Importancia (%)": importances * 100})
        imp_df = imp_df.sort_values("Importancia (%)", ascending=True)
        
        st.subheader("1. Importancia Relativa de las Variables (Feature Importance)")
        st.markdown("¿Qué factor climático pesa más para que el cultivo tenga éxito o fracase?")
        
        fig = px.bar(imp_df, x="Importancia (%)", y="Variable", orientation='h', title="Random Forest: Importancia de Variables Gini")
        st.plotly_chart(fig, width='stretch')
        
        st.subheader("2. Curvas de Dependencia Parcial (PDP)")
        st.markdown("¿Cómo cambia la predicción del modelo al aislar una sola variable (ej. Temp Máxima) manteniendo el resto constante?")
        
        try:
            from sklearn.inspection import PartialDependenceDisplay
            import matplotlib.pyplot as plt
            
            fig_pdp, ax = plt.subplots(figsize=(10, 4))
            # Plot PDP for the top 2 features
            top_features = imp_df.sort_values("Importancia (%)", ascending=False)["Variable"].head(2).tolist()
            display = PartialDependenceDisplay.from_estimator(rf, X, top_features, ax=ax)
            st.pyplot(fig_pdp)
            st.info("💡 **Tipping Points:** Si la curva cae drásticamente después de cierto valor en el eje X, el modelo ha encontrado un umbral crítico de tolerancia agronómica.")
        except ImportError:
            st.warning("No se pudo generar PDP. Faltan dependencias de matplotlib.")

def render_geospatial(df, meta):
    st.title("🗺️ Análisis Geoespacial de Rendimiento")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown("Visualiza el rendimiento de maíz proyectado a nivel del mapa del estado de Iowa.")
    
    if 'fips' not in df.columns:
        st.warning("No hay columna FIPS para mapear.")
        return
        
    if st.button("Renderizar Heatmap (Iowa)"):
        import urllib.request
        import json
        import plotly.express as px
        
        # Aggregate by fips
        county_avg = df.groupby('fips')['yield_kg_ha'].mean().reset_index()
        county_avg['fips'] = county_avg['fips'].astype(str).str.zfill(5)
        
        st.write("Calculando promedios geoespaciales...")
        
        url = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
        try:
            with urllib.request.urlopen(url) as response:
                counties = json.load(response)
                
            fig = px.choropleth(
                county_avg, 
                geojson=counties, 
                locations='fips', 
                color='yield_kg_ha',
                color_continuous_scale="Viridis",
                scope="usa",
                title="Rendimiento Promedio Histórico (kg/ha) por Condado"
            )
            fig.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig, width='stretch')
            
            st.info("💡 La variación espacial demuestra que los modelos puramente temporales (Series de Tiempo) fracasan, justificando un enfoque espacial (CeresPINN).")
        except Exception as e:
            st.error(f"Error al descargar la geometría geojson: {e}")


def render_tuning(df):
    render_cv_controls(df, default_nested=True)


def render_pytorch(df):
    st.title("🧠 Entrenamiento")
    st.caption("Ajusta la red PyTorch. La selección común de modelos y la validación cruzada tienen sus propias páginas.")
    st.info("Separación temporal por años: aproximadamente 60% entrenamiento, 20% validación "
            "y 20% prueba final. Los rendimientos faltantes o no finitos se excluyen.")
    # Use the original panel so earlier target-based cleaning cannot bias holdouts.
    source = pd.read_parquet(DATA_PATH) if DATA_PATH.exists() else df.copy()
    if source.empty or not {'year', 'yield_kg_ha'}.issubset(source.columns):
        st.warning("Se necesita un panel con year y yield_kg_ha.")
        return
    try:
        parts, excluded = temporal_partitions(source)
    except ValueError as exc:
        st.error(str(exc))
        return
    names = ['Entrenamiento', 'Validación', 'Prueba independiente']
    st.caption(f"Filas excluidas por rendimiento o año inválido: {excluded}.")
    st.dataframe(pd.DataFrame([{'Partición': name, 'Desde': int(part.year.min()),
        'Hasta': int(part.year.max()), 'Observaciones': len(part)}
        for name, part in zip(names, parts)]), width='stretch')
    epochs = st.number_input("Épocas (Epochs)", 100, 2000, 300, 100)
    lr = st.number_input("Tasa de Aprendizaje (LR)", 0.0001, 0.1, 0.001, format='%f')
    weight = st.slider("Peso de regularización por derivadas", 0.0, 1.0, 0.5)
    st.caption("La penalización favorece rendimiento no creciente con temperatura y no decreciente "
               "con precipitación. Son restricciones locales de monotonicidad; no garantizan "
               "conservación física ni extrapolación correcta. Las derivadas usan variables normalizadas.")
    train_btn = st.button("🔥 Iniciar Entrenamiento Simple", type='primary')
    search_btn = False
    if not (train_btn or search_btn):
        return
    import torch
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    from backend.training.pinn import CeresPINN, physics_loss
    from backend.training.config import TrainConfig
    from datetime import datetime
    from itertools import product

    feature_names = [f for f in ['year', 'season_temp_mean_c', 'season_tmax_mean_c',
        'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa'] if f in source.columns]
    if not {'season_tmax_mean_c', 'season_precip_mm'}.issubset(feature_names):
        st.error("La regularización requiere season_tmax_mean_c y season_precip_mm en el panel.")
        return
    scaler_X = Pipeline([('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
                         ('scaler', StandardScaler())])
    scaler_y = StandardScaler()
    X_frames = [part[feature_names].replace([np.inf, -np.inf], np.nan) for part in parts]
    X_train = scaler_X.fit_transform(X_frames[0])
    X_val = scaler_X.transform(X_frames[1])
    X_test = scaler_X.transform(X_frames[2])
    y_train = scaler_y.fit_transform(parts[0]['yield_kg_ha'].to_numpy().reshape(-1, 1))
    x_train = torch.tensor(X_train, dtype=torch.float32)
    x_val = torch.tensor(X_val, dtype=torch.float32)
    x_test = torch.tensor(X_test, dtype=torch.float32)
    y_tensor = torch.tensor(y_train, dtype=torch.float32).squeeze(-1)
    options = list(product([300, 500, 800], [0.001, 0.005, 0.01], [0.1, 0.5, 0.9])) if search_btn else [(epochs, lr, weight)]
    progress = st.progress(0.0)
    chart = st.empty()
    status = st.empty()
    best_score, best_model, best_params = -np.inf, None, None
    best_history = []
    results = []
    for number, (ep, rate, pw) in enumerate(options):
        torch.manual_seed(42)
        cfg = TrainConfig(feature_names=feature_names, loss_physics_weight=pw)
        model = CeresPINN(train_config=cfg, input_dim=len(feature_names))
        optimizer = torch.optim.Adam(model.parameters(), lr=rate, weight_decay=1e-5)
        history = []
        for epoch in range(1, ep + 1):
            model.train()
            optimizer.zero_grad()
            prediction, _ = model(x_train)
            mse = torch.nn.functional.mse_loss(prediction, y_tensor)
            # physics_loss already applies cfg.loss_physics_weight once.
            physics = physics_loss(model, x_train, cfg)
            loss = mse + physics
            loss.backward()
            optimizer.step()
            if epoch == 1 or epoch % 10 == 0 or epoch == ep:
                model.eval()
                with torch.no_grad():
                    val_pred, _ = model(x_val)
                    val_original = scaler_y.inverse_transform(val_pred.numpy().reshape(-1, 1)).ravel()
                val_mse = mean_squared_error(parts[1]['yield_kg_ha'], val_original)
                history.append({'Época': epoch, 'MSE entrenamiento normalizado': mse.item(),
                                'MSE validación normalizado': val_mse / scaler_y.scale_[0] ** 2,
                                'Penalización por derivadas ponderada': physics.item(),
                                'Pérdida total entrenamiento': loss.item()})
                if not search_btn:
                    chart.plotly_chart(px.line(pd.DataFrame(history), x='Época',
                        y=['MSE entrenamiento normalizado', 'MSE validación normalizado',
                           'Penalización por derivadas ponderada', 'Pérdida total entrenamiento']), width='stretch')
                status.text(f"Variante {number + 1}/{len(options)}, época {epoch}/{ep}")
        model.eval()
        with torch.no_grad():
            pred_val, _ = model(x_val)
            observed_scale = scaler_y.inverse_transform(pred_val.numpy().reshape(-1, 1)).ravel()
        score = r2_score(parts[1]['yield_kg_ha'], observed_scale)
        results.append({'Épocas': ep, 'LR': rate, 'Peso física': pw, 'R² validación': score})
        if np.isfinite(score) and score > best_score:
            best_score, best_model = score, model
            best_params = {'epochs': ep, 'lr': rate, 'physics_weight': pw}
            best_history = history
        progress.progress((number + 1) / len(options))
    if best_model is None:
        st.error("No se obtuvo un modelo con métricas finitas. No se guardó ningún artefacto.")
        return
    st.dataframe(pd.DataFrame(results).sort_values('R² validación', ascending=False), width='stretch')
    if search_btn:
        chart.plotly_chart(px.line(pd.DataFrame(best_history), x='Época',
            y=['MSE entrenamiento normalizado', 'MSE validación normalizado',
               'Penalización por derivadas ponderada', 'Pérdida total entrenamiento'],
            title='Curvas de la configuración seleccionada'), width='stretch')
    # Test is evaluated once, after selecting the configuration using validation.
    best_model.eval()
    with torch.no_grad():
        test_prediction, _ = best_model(x_test)
        prediction = scaler_y.inverse_transform(test_prediction.numpy().reshape(-1, 1)).ravel()
    actual = parts[2]['yield_kg_ha'].to_numpy()
    metrics = {'R2_test_temporal': float(r2_score(actual, prediction)),
               'RMSE_test_kg_ha': float(np.sqrt(mean_squared_error(actual, prediction))),
               'MAE_test_kg_ha': float(mean_absolute_error(actual, prediction)),
               'R2_validation': float(best_score)}
    st.subheader("Resultados de prueba independiente")
    a, b, c = st.columns(3)
    a.metric("R² prueba", f"{metrics['R2_test_temporal']:.4f}")
    b.metric("RMSE prueba (kg/ha)", f"{metrics['RMSE_test_kg_ha']:.2f}")
    c.metric("MAE prueba (kg/ha)", f"{metrics['MAE_test_kg_ha']:.2f}")
    comparison = pd.DataFrame({'Observado': actual, 'Predicho': prediction, 'Año': parts[2]['year'].to_numpy()})
    st.plotly_chart(px.scatter(comparison, x='Observado', y='Predicho', color='Año',
        title='Rendimiento observado frente a predicho en prueba independiente'), width='stretch')
    st.download_button('Descargar predicciones de prueba', comparison.to_csv(index=False).encode('utf-8-sig'),
                       'pytorch_prueba.csv', 'text/csv')
    wrapper = PyTorchWrapper(best_model, scaler_X, scaler_y)
    joblib.dump(wrapper, MODEL_PATH)
    metadata = {'algorithm': 'CeresPINN_PyTorch_AutoTuned' if search_btn else 'CeresPINN_PyTorch_Real',
        'metrics': metrics, 'feature_names': feature_names, 'best_params': best_params,
        'trained_at': datetime.now().isoformat(), 'excluded_invalid_rows': excluded,
        'evaluation_protocol': 'chronological_year_train_validation_test',
        'physics_regularization': 'temperature_precipitation_monotonicity_normalized_gradients',
        'history': best_history,
        'partitions': {name: {'years': sorted(int(y) for y in part.year.unique()), 'rows': len(part)}
                       for name, part in zip(['train', 'validation', 'test'], parts)}}
    META_PATH.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    st.success("Modelo y métricas independientes guardados.")


def render_final_comparison():
    st.title("🏅 Selección del mejor modelo")
    st.write("Los seis algoritmos se entrenan sobre los mismos años y variables. "
             "El ganador se selecciona con validación independiente común; "
             "la prueba final se reserva para evaluar todos los candidatos.")
    st.caption("Este benchmark ejecuta configuraciones reproducibles. Los resultados de otros "
               "módulos con particiones distintas no se mezclan en el ranking.")
    artifact = PROJECT_ROOT / 'ml_lab' / 'artifacts' / 'common_benchmark.json'
    epochs = st.number_input('Épocas PyTorch del benchmark', 100, 2000, 300, 100)
    weight = st.slider('Peso física del benchmark', 0.0, 1.0, 0.5)
    if st.button('Ejecutar benchmark común', type='primary'):
        from ml_lab.benchmark import run_benchmark
        source = pd.read_parquet(DATA_PATH) if DATA_PATH.exists() else load_data()
        progress = st.progress(0.0)
        status = st.empty()
        def update(value, message):
            progress.progress(value)
            status.text(message)
        try:
            report = run_benchmark(source, epochs=epochs, physics_weight=weight, progress=update)
        except Exception as exc:
            st.error(f'No se completó el benchmark: {exc}. No se guardó un ranking nuevo.')
            return
        artifact.parent.mkdir(parents=True, exist_ok=True)
        # Persist only complete runs; preserve the previous report on failure.
        temporary = artifact.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
        temporary.replace(artifact)
        history = artifact.parent / 'benchmark_history'
        history.mkdir(exist_ok=True)
        stamp = report['created_at'].replace(':', '').replace('+', '_')
        (history / f'{stamp}.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    if not artifact.exists():
        st.info('Todavía no hay resultados reales del benchmark común. Ejecuta el benchmark para generar la comparativa.')
        return
    try:
        report = json.loads(artifact.read_text(encoding='utf-8'))
        table = pd.DataFrame(report['results']).sort_values(
            ['validation_r2', 'validation_rmse_kg_ha', 'model'], ascending=[False, True, True])
    except (ValueError, KeyError) as exc:
        st.error(f'No se puede leer el resultado guardado: {exc}')
        return
    st.caption(f"Ejecución guardada: {report['created_at']}. Huella del dataset: {report['dataset_sha256']}.")
    st.json({'Particiones': report['partitions'], 'Configuración': report['configuration']})
    st.success(f"Modelo seleccionado por validación: {report['winner']}")
    st.dataframe(table.rename(columns={'model': 'Modelo', 'validation_r2': 'R² validación',
        'validation_rmse_kg_ha': 'RMSE validación (kg/ha)', 'test_r2': 'R² prueba',
        'test_rmse_kg_ha': 'RMSE prueba (kg/ha)', 'test_mae_kg_ha': 'MAE prueba (kg/ha)',
        'test_rows': 'Observaciones prueba'}), width='stretch')
    metric = st.selectbox('Métrica del gráfico', ['test_r2', 'test_rmse_kg_ha', 'test_mae_kg_ha', 'validation_r2'],
        format_func=lambda key: {'test_r2': 'R² prueba', 'test_rmse_kg_ha': 'RMSE prueba (kg/ha)',
            'test_mae_kg_ha': 'MAE prueba (kg/ha)', 'validation_r2': 'R² validación'}[key])
    st.plotly_chart(px.bar(table, x='model', y=metric, text_auto='.4f',
        title='Resultados reales sobre particiones comunes'), width='stretch')
    chosen = st.selectbox('Modelo para gráfico de predicciones', table['model'].tolist())
    comparison = pd.DataFrame({'Observado': report['test_observed'],
        'Predicho': report['test_predictions'][chosen], 'Año': report['test_years']})
    st.plotly_chart(px.scatter(comparison, x='Observado', y='Predicho', color='Año'), width='stretch')
    st.download_button('Descargar métricas CSV', table.to_csv(index=False).encode('utf-8-sig'),
                       'benchmark_metricas.csv', 'text/csv')
    st.download_button('Descargar ejecución completa JSON', json.dumps(report, indent=2),
                       'benchmark_completo.json', 'application/json')
    st.caption('El ganador refleja esta ejecución y este conjunto de validación. '
               'El ranking no demuestra superioridad universal ni se utiliza para afirmar extrapolación perfecta.')


def main():
    page = render_sidebar()
    df = load_data()
    meta = load_meta()
    
    if page == "1. Dashboard General":
        render_dashboard(df, meta)
    elif page == "2. Análisis de Datos (EDA)":
        render_eda(df)
    elif page == "3. Limpieza de Datos":
        render_data_cleaning(df)
    elif page == "4. Entrenamiento":
        render_training(df)
    elif page == "5. Selección del mejor modelo":
        render_final_comparison()
    elif page == "6. Validación Cruzada":
        render_cv_controls(df)
    elif page == "7. Pruebas Estadísticas":
        render_stats(df)
    elif page == "8. Evaluación del Modelo":
        render_model_eval(meta)
    elif page == "9. Explicabilidad del Modelo":
        render_xai(df)
    elif page == "10. Distribución Geoespacial":
        render_geospatial(df, meta)
    elif page == "11. Reportes":
        import importlib
        # Resolve the registered module rather than a stale package attribute.
        report_ui = importlib.import_module('ml_lab.report_ui')
        importlib.reload(report_ui)
        report_ui.render_report_generator_ui(df=df)

if __name__ == "__main__":
    main()
