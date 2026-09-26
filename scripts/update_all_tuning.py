import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

tuning_pattern = re.compile(r"def render_tuning\(df\):.*?def main\(\):", re.DOTALL)

new_tuning = """def render_tuning(df):
    st.title("🎛️ Auto-Tuning Avanzado (Búsqueda Exhaustiva de Hiperparámetros)")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown("Encuentra la combinación algorítmica perfecta explorando exhaustivamente (Grid Search) cientos de variantes para cualquier modelo.")
    
    model_choice = st.selectbox("Selecciona el Algoritmo a Refinar", [
        "Red Neuronal MLP (CeresPINN)",
        "Random Forest Regressor",
        "HistGradientBoosting",
        "Regresión Ridge"
    ])
    
    st.write("### Espacios de Búsqueda (Grid)")
    
    if model_choice == "Red Neuronal MLP (CeresPINN)":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Arquitecturas (Neuronas)**")
            arch_shallow = st.checkbox("Shallow: (32, 16)", value=True)
            arch_standard = st.checkbox("Standard: (64, 32)", value=True)
            arch_deep = st.checkbox("Deep: (128, 64, 32)", value=True)
            arch_wide = st.checkbox("Wide: (256, 128)", value=True)
        with col2:
            st.markdown("**Activación**")
            act_relu = st.checkbox("ReLU", value=True)
            act_tanh = st.checkbox("Tanh", value=True)
        with col3:
            st.markdown("**Regularización L2 (Alpha)**")
            alpha_low = st.checkbox("Baja (0.0001)", value=True)
            alpha_high = st.checkbox("Fuerte (0.1)", value=True)
            
    elif model_choice == "Random Forest Regressor":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Número de Árboles (n_estimators)**")
            rf_n50 = st.checkbox("50 Árboles", value=True)
            rf_n100 = st.checkbox("100 Árboles", value=True)
            rf_n200 = st.checkbox("200 Árboles", value=False)
        with col2:
            st.markdown("**Profundidad Máxima (max_depth)**")
            rf_d10 = st.checkbox("Profundidad 10", value=True)
            rf_d20 = st.checkbox("Profundidad 20", value=True)
            rf_dnone = st.checkbox("Sin Límite (None)", value=False)
            
    elif model_choice == "HistGradientBoosting":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Tasa de Aprendizaje (learning_rate)**")
            gb_lr01 = st.checkbox("Lento (0.01)", value=True)
            gb_lr10 = st.checkbox("Rápido (0.1)", value=True)
        with col2:
            st.markdown("**Iteraciones Máximas (max_iter)**")
            gb_i100 = st.checkbox("100 Iteraciones", value=True)
            gb_i300 = st.checkbox("300 Iteraciones", value=True)
            
    elif model_choice == "Regresión Ridge":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fuerza de Penalización (Alpha)**")
            rd_a01 = st.checkbox("Débil (0.1)", value=True)
            rd_a1 = st.checkbox("Normal (1.0)", value=True)
            rd_a10 = st.checkbox("Fuerte (10.0)", value=True)
        with col2:
            st.markdown("**Solver Matemático**")
            rd_auto = st.checkbox("Auto", value=True)
            rd_svd = st.checkbox("SVD", value=True)

    if st.button("🚀 Ejecutar Búsqueda Grid Search (5-Fold CV)"):
        from sklearn.neural_network import MLPRegressor
        from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import GridSearchCV, KFold
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        
        param_grid = {}
        
        if model_choice == "Red Neuronal MLP (CeresPINN)":
            base_model = MLPRegressor(max_iter=300, random_state=42)
            layers = []
            if arch_shallow: layers.append((32, 16))
            if arch_standard: layers.append((64, 32))
            if arch_deep: layers.append((128, 64, 32))
            if arch_wide: layers.append((256, 128))
            
            acts = []
            if act_relu: acts.append('relu')
            if act_tanh: acts.append('tanh')
            
            alphas = []
            if alpha_low: alphas.append(0.0001)
            if alpha_high: alphas.append(0.1)
            
            param_grid = {'model__hidden_layer_sizes': layers, 'model__activation': acts, 'model__alpha': alphas}
            
        elif model_choice == "Random Forest Regressor":
            base_model = RandomForestRegressor(random_state=42)
            n_est = []
            if rf_n50: n_est.append(50)
            if rf_n100: n_est.append(100)
            if rf_n200: n_est.append(200)
            
            depths = []
            if rf_d10: depths.append(10)
            if rf_d20: depths.append(20)
            if rf_dnone: depths.append(None)
            
            param_grid = {'model__n_estimators': n_est, 'model__max_depth': depths}
            
        elif model_choice == "HistGradientBoosting":
            base_model = HistGradientBoostingRegressor(random_state=42)
            lrs = []
            if gb_lr01: lrs.append(0.01)
            if gb_lr10: lrs.append(0.1)
            
            iters = []
            if gb_i100: iters.append(100)
            if gb_i300: iters.append(300)
            
            param_grid = {'model__learning_rate': lrs, 'model__max_iter': iters}
            
        elif model_choice == "Regresión Ridge":
            base_model = Ridge(random_state=42)
            alphas = []
            if rd_a01: alphas.append(0.1)
            if rd_a1: alphas.append(1.0)
            if rd_a10: alphas.append(10.0)
            
            solvers = []
            if rd_auto: solvers.append('auto')
            if rd_svd: solvers.append('svd')
            
            param_grid = {'model__alpha': alphas, 'model__solver': solvers}
            
        # Verify grid is not empty
        empty_keys = [k for k, v in param_grid.items() if len(v) == 0]
        if empty_keys:
            st.error("Debes seleccionar al menos una opción en cada categoría.")
            return
            
        feature_names = ['year', 'season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
        feature_names = [f for f in feature_names if f in df.columns]
        
        X = df[feature_names].fillna(0)
        y = df['yield_kg_ha'].fillna(0)
        
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', base_model)
        ])
        
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        grid_search = GridSearchCV(pipeline, param_grid, cv=cv, scoring='r2', n_jobs=-1)
        
        with st.spinner('Entrenando todas las variantes simultáneamente...'):
            grid_search.fit(X, y)
            
        results_df = pd.DataFrame(grid_search.cv_results_)
        
        # Format columns dynamically
        cols_to_keep = [c for c in results_df.columns if c.startswith('param_')] + ['mean_test_score', 'std_test_score', 'rank_test_score']
        results_df = results_df[cols_to_keep]
        results_df = results_df.sort_values('rank_test_score')
        
        st.success("¡Búsqueda completada exitosamente!")
        st.subheader(f"Top 5 Variantes: {model_choice}")
        st.dataframe(results_df.head(5).style.highlight_max(subset=['mean_test_score'], color='lightgreen'))
        
        best = grid_search.best_params_
        st.markdown(f\"\"\"
        ### 👑 La Configuración Ganadora:
        \"\"\")
        for k, v in best.items():
            st.markdown(f"- **{k.replace('model__', '')}:** `{v}`")
        st.markdown(f"**Desempeño del Ganador (R² Promedio):** `{grid_search.best_score_:.4f}`")

def main():"""

new_content = tuning_pattern.sub(new_tuning, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Multi-model tuning appended successfully.")
