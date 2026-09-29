from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'ml_lab/app.py'
s = p.read_text(encoding='utf-8-sig')
s = s.replace('                "4. Clustering (Método del Codo)",\n', '')
s = s.replace('    elif page == "4. Clustering (Método del Codo)":\n        render_elbow_method(df)\n', '')
start = s.index('def render_elbow_method(df):')
end = s.index('def render_stats(df):', start)
s = s[:start] + s[end:]
for old, new in [
    ('5. Pruebas Estadísticas', '4. Pruebas Estadísticas'),
    ('6. Entrenamiento y Validación Cruzada', '5. Entrenamiento y Validación Cruzada'),
    ('7. Evaluación de Modelos Espaciales', '6. Evaluación del Modelo'),
    ('8. IA Explicable (XAI): Importancia & PDP', '7. Explicabilidad del Modelo'),
    ('9. Análisis Geoespacial de Errores', '8. Distribución Geoespacial'),
    ('10. Auto-Tuning CeresPINN (Grid Search)', '9. Búsqueda de Hiperparámetros'),
    ('11. Entrenamiento Profundo (CeresPINN PyTorch)', '10. Entrenamiento PyTorch'),
    ('12. Comparativa Final de Modelos', '11. Comparativa Final de Modelos'),
    ('13. Reportes', '12. Reportes'),
    ('página 12.', 'página 11.'),
]:
    s = s.replace(old, new)
s = s.replace('            "Navegación",\n', '            "Navegación",\n')
s = s.replace('                "12. Reportes"\n            ]\n', '                "12. Reportes"\n            ],\n            key="ml_lab_page"\n')
start = s.index('def render_dashboard(df, meta):')
end = s.index('def render_eda(df):', start)
s = s[:start] + '''def render_dashboard(df, meta):
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
        ('🧠 Evaluar modelos', '5. Entrenamiento y Validación Cruzada'),
        ('🏅 Comparar resultados', '11. Comparativa Final de Modelos'),
        ('📄 Crear un reporte', '12. Reportes'),
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
                          args=('11. Comparativa Final de Modelos',), use_container_width=True)
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


''' + s[end:]
p.write_text(s, encoding='utf-8')
reports = p.parent / 'report_ui.py'
reports.write_text(reports.read_text(encoding='utf-8').replace("st.title('13. Reportes')", "st.title('12. Reportes')"), encoding='utf-8')
