import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update sidebar
sidebar_old = """                "8. IA Explicable (XAI): Importancia & PDP",
                "9. Análisis Geoespacial de Errores"
            ]
        )"""
sidebar_new = """                "8. IA Explicable (XAI): Importancia & PDP",
                "9. Análisis Geoespacial de Errores",
                "10. Auto-Tuning CeresPINN (Grid Search)"
            ]
        )"""
content = content.replace(sidebar_old, sidebar_new)

# 2. Update main()
main_old = """    elif page == "9. Análisis Geoespacial de Errores":
        render_geospatial(df, meta)

if __name__ == "__main__":"""
main_new = """    elif page == "9. Análisis Geoespacial de Errores":
        render_geospatial(df, meta)
    elif page == "10. Auto-Tuning CeresPINN (Grid Search)":
        render_tuning(df)

if __name__ == "__main__":"""
content = content.replace(main_old, main_new)

# 3. Inject render_tuning right above main()
tuning_functions = """
def render_tuning(df):
    st.title("🎛️ Auto-Tuning CeresPINN (Búsqueda de Hiperparámetros)")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown("Encuentra la combinación arquitectónica perfecta para la red neuronal CeresPINN explorando exhaustivamente (Grid Search) cientos de variantes matemáticas.")
    
    st.write("Selecciona los espacios de búsqueda:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Arquitecturas (Neuronas)**")
        arch_shallow = st.checkbox("Shallow: (32, 16)", value=True)
        arch_standard = st.checkbox("Standard: (64, 32)", value=True)
        arch_deep = st.checkbox("Deep: (128, 64, 32)", value=True)
        arch_wide = st.checkbox("Wide: (256, 128)", value=True)
    with col2:
        st.markdown("**Funciones de Activación**")
        act_relu = st.checkbox("ReLU (Clásica)", value=True)
        act_tanh = st.checkbox("Tanh (Suavizada)", value=True)
        act_logistic = st.checkbox("Logistic (Sigmoide)", value=False)
    with col3:
        st.markdown("**Regularización L2 (Alpha)**")
        alpha_low = st.checkbox("Baja (0.0001)", value=True)
        alpha_med = st.checkbox("Media (0.01)", value=True)
        alpha_high = st.checkbox("Fuerte (0.1)", value=True)
        
    if st.button("🚀 Ejecutar Búsqueda Grid Search"):
        from sklearn.neural_network import MLPRegressor
        from sklearn.model_selection import GridSearchCV, KFold
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        
        # Build grid
        hidden_layers = []
        if arch_shallow: hidden_layers.append((32, 16))
        if arch_standard: hidden_layers.append((64, 32))
        if arch_deep: hidden_layers.append((128, 64, 32))
        if arch_wide: hidden_layers.append((256, 128))
        
        activations = []
        if act_relu: activations.append('relu')
        if act_tanh: activations.append('tanh')
        if act_logistic: activations.append('logistic')
            
        alphas = []
        if alpha_low: alphas.append(0.0001)
        if alpha_med: alphas.append(0.01)
        if alpha_high: alphas.append(0.1)
        
        if not hidden_layers or not activations or not alphas:
            st.error("Debes seleccionar al menos una opción en cada categoría.")
            return
            
        param_grid = {
            'model__hidden_layer_sizes': hidden_layers,
            'model__activation': activations,
            'model__alpha': alphas
        }
        
        num_combinations = len(hidden_layers) * len(activations) * len(alphas)
        st.info(f"Explorando {num_combinations} combinaciones de redes neuronales CeresPINN con Validación Cruzada de 5 particiones (Total: {num_combinations * 5} entrenamientos)...")
        
        feature_names = ['year', 'season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
        feature_names = [f for f in feature_names if f in df.columns]
        
        X = df[feature_names].fillna(0)
        y = df['yield_kg_ha'].fillna(0)
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', MLPRegressor(max_iter=300, random_state=42))
        ])
        
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        grid_search = GridSearchCV(pipeline, param_grid, cv=cv, scoring='r2', n_jobs=-1, verbose=1)
        
        with st.spinner('Entrenando cientos de variantes simultáneamente...'):
            grid_search.fit(X, y)
            
        results_df = pd.DataFrame(grid_search.cv_results_)
        results_df = results_df[['param_model__hidden_layer_sizes', 'param_model__activation', 'param_model__alpha', 'mean_test_score', 'std_test_score', 'rank_test_score']]
        results_df.columns = ['Arquitectura', 'Activación', 'Alpha (L2)', 'R2 Promedio (5-Fold)', 'Desviación Est. R2', 'Ranking']
        results_df = results_df.sort_values('Ranking')
        
        st.success("¡Búsqueda completada exitosamente!")
        st.subheader("Top 5 Variantes de CeresPINN")
        st.dataframe(results_df.head(5).style.highlight_max(subset=['R2 Promedio (5-Fold)'], color='lightgreen'))
        
        best = grid_search.best_params_
        st.markdown(f\"\"\"
        ### 👑 El Modelo Perfecto Encontrado:
        - **Capas Ocultas:** `{best['model__hidden_layer_sizes']}`
        - **Función de Activación:** `{best['model__activation']}`
        - **Tasa de Regularización:** `{best['model__alpha']}`
        
        **Desempeño del Ganador:** R² = `{grid_search.best_score_:.4f}`
        
        Este es el modelo que deberías exportar a producción para CeresPINN.
        \"\"\")

"""

content = content.replace("def main():", tuning_functions + "def main():")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Auto-tuning module appended successfully.")
