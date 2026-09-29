from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'ml_lab/app.py'
s = p.read_text(encoding='utf-8-sig')
start = s.index('def render_final_comparison():')
end = s.index('def main():', start)
s = s[:start] + '''def render_final_comparison():
    st.title("🏅 Comparativa final de modelos")
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


''' + s[end:]
p.write_text(s, encoding='utf-8')
