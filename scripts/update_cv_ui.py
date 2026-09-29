from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'ml_lab/app.py'
s = p.read_text(encoding='utf-8-sig')
start = s.index('def render_training(df):')
end = s.index('def render_model_eval(meta):', start)
s = s[:start] + '''def render_training(df):
    render_cv_controls(df, default_nested=False)


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


''' + s[end:]
start = s.index('def render_tuning(df):')
end = s.index('def render_pytorch(df):', start)
s = s[:start] + '''def render_tuning(df):
    render_cv_controls(df, default_nested=True)


''' + s[end:]
# Avoid obsolete metrics being carried into new runs; old artifacts are left intact.
assert "['R2_temporal']" not in s
p.write_text(s, encoding='utf-8')
