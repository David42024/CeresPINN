from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'ml_lab/app.py'
s = p.read_text(encoding='utf-8-sig')
start = s.index('def render_stats(df):')
end = s.index('def render_training(df):', start)
s = s[:start] + '''def render_stats(df):
    st.title('Pruebas estadísticas e incertidumbre')
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
    paired = st.checkbox('Incluir comparación pareada de todos los modelos del benchmark', value=False)
    st.caption('Holm se aplica a todos los contrastes, correlaciones y prueba de normalidad de esta '
               'ejecución, incluidas las comparaciones de modelos si se seleccionan. '
               'Los intervalos son percentiles marginales; no son intervalos simultáneos.')
    path = PROJECT_ROOT / 'ml_lab' / 'artifacts' / 'statistical_analysis.json'
    benchmark = PROJECT_ROOT / 'ml_lab' / 'artifacts' / 'common_benchmark.json'
    if st.button('Ejecutar suite estadística y bootstrap', type='primary'):
        from ml_lab.statistical_analysis import panel_suite, paired_model_tests, holm_adjust
        try:
            with st.spinner('Calculando intervalos y pruebas agrupadas...'):
                report = panel_suite(source, threshold, (lower, upper), int(replicates), alpha)
                report['paired_results'] = []
                if paired:
                    if not benchmark.exists():
                        raise ValueError('Ejecuta primero el benchmark común de la página 12.')
                    model_report = json.loads(benchmark.read_text(encoding='utf-8'))
                    report['paired_results'] = paired_model_tests(model_report, int(replicates), alpha)
                    report['benchmark_created_at'] = model_report['created_at']
                family = report['results'] + report['paired_results']
                for row, corrected in zip(family, holm_adjust([row['p_value'] for row in family])):
                    row.update(p_holm=corrected, reject=corrected < alpha)
                from datetime import datetime, timezone
                report['created_at'] = datetime.now(timezone.utc).isoformat()
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix('.tmp')
                temporary.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
                temporary.replace(path)
        except Exception as exc:
            st.error(f'No se completó la suite: {exc}. Revisa los grupos y las columnas.')
            return
    if not path.exists():
        st.info('Ejecuta la suite para visualizar los resultados.')
        return
    report = json.loads(path.read_text(encoding='utf-8'))
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


''' + s[end:]
p.write_text(s, encoding='utf-8')
