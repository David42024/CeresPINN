from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'ml_lab/app.py'
s = p.read_text(encoding='utf-8-sig')
a = s.index('            [\n', s.index('def render_sidebar'))
b = s.index('            ],', a)
pages = ['1. Dashboard General', '2. Análisis de Datos (EDA)', '3. Limpieza de Datos',
         '4. Entrenamiento', '5. Selección del mejor modelo', '6. Validación Cruzada',
         '7. Pruebas Estadísticas', '8. Evaluación del Modelo', '9. Explicabilidad del Modelo',
         '10. Distribución Geoespacial', '11. Reportes']
s = s[:a] + '            [\n' + ''.join(f'                "{page}",\n' for page in pages) + s[b:]
s = s.replace("'4. Entrenamiento y Validación Cruzada'", "'6. Validación Cruzada'")
s = s.replace("'11. Comparativa Final de Modelos'", "'5. Selección del mejor modelo'")
s = s.replace("'12. Reportes'", "'11. Reportes'")
s = s.replace('benchmark de la página 11', 'benchmark de la página 5')
s = s.replace('benchmark común de la página 11', 'benchmark común de la página 5')
s = s.replace('def render_training(df):\n    render_cv_controls(df, default_nested=False)',
              'def render_training(df):\n    render_pytorch(df)')
s = s.replace('    with st.expander(\'Validación cruzada PyTorch y comparación bajo el mismo protocolo\'):\n        render_cv_controls(df, default_nested=True)\n', '')
s = s.replace('    st.title("🧠 Entrenamiento CeresPINN PyTorch")', '    st.title("🧠 Entrenamiento")\n    st.caption("Ajusta la red PyTorch. La selección común de modelos y la validación cruzada tienen sus propias páginas.")')
s = s.replace('    search_btn = st.button("🔍 Iniciar Auto-Tuning (Grid Search)")', '    search_btn = False')
s = s.replace('    st.title("🏅 Comparativa final de modelos")', '    st.title("🏅 Selección del mejor modelo")')
start = s.index('    if page == "1. Dashboard General":', s.index('def main():'))
s = s[:start] + '''    if page == "1. Dashboard General":
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
        from ml_lab.report_ui import render_report_generator_ui
        render_report_generator_ui(df=df)

if __name__ == "__main__":
    main()
'''
p.write_text(s, encoding='utf-8')
ui = p.parent / 'report_ui.py'
ui.write_text(ui.read_text(encoding='utf-8').replace("st.title('12. Reportes')", "st.title('11. Reportes')"), encoding='utf-8')
