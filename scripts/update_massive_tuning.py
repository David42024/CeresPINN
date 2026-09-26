import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

tuning_pattern = re.compile(r"def render_tuning\(df\):.*?def main\(\):", re.DOTALL)

new_tuning = """def render_tuning(df):
    st.title("🎛️ Torneo de Auto-Tuning Masivo (Grid Search)")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown("Busca la combinación algorítmica perfecta para TODOS los modelos al mismo tiempo y actualiza automáticamente el cerebro (archivo .joblib) de CeresPINN.")
    
    st.write("### Espacios de Búsqueda (Grid)")
    
    st.markdown("#### 1. Red Neuronal MLP (CeresPINN)")
    col1, col2, col3 = st.columns(3)
    with col1:
        arch_shallow = st.checkbox("Shallow: (32, 16)", value=True, key="m1")
        arch_standard = st.checkbox("Standard: (64, 32)", value=True, key="m2")
        arch_deep = st.checkbox("Deep: (128, 64, 32)", value=True, key="m3")
    with col2:
        act_relu = st.checkbox("ReLU", value=True, key="m4")
        act_tanh = st.checkbox("Tanh", value=True, key="m5")
    with col3:
        alpha_low = st.checkbox("Alpha Baja (0.0001)", value=True, key="m6")
        alpha_high = st.checkbox("Alpha Fuerte (0.1)", value=True, key="m7")
            
    st.markdown("#### 2. Random Forest Regressor")
    col1, col2 = st.columns(2)
    with col1:
        rf_n50 = st.checkbox("50 Árboles", value=True, key="r1")
        rf_n100 = st.checkbox("100 Árboles", value=True, key="r2")
    with col2:
        rf_d10 = st.checkbox("Profundidad 10", value=True, key="r3")
        rf_d20 = st.checkbox("Profundidad 20", value=True, key="r4")
            
    st.markdown("#### 3. HistGradientBoosting")
    col1, col2 = st.columns(2)
    with col1:
        gb_lr01 = st.checkbox("Lento (0.01)", value=True, key="g1")
        gb_lr10 = st.checkbox("Rápido (0.1)", value=True, key="g2")
    with col2:
        gb_i100 = st.checkbox("100 Iter", value=True, key="g3")
        gb_i300 = st.checkbox("300 Iter", value=True, key="g4")
            
    st.markdown("#### 4. Regresión Ridge")
    col1, col2 = st.columns(2)
    with col1:
        rd_a01 = st.checkbox("Alpha 0.1", value=True, key="d1")
        rd_a1 = st.checkbox("Alpha 1.0", value=True, key="d2")
    with col2:
        rd_auto = st.checkbox("Solver Auto", value=True, key="d3")
        rd_svd = st.checkbox("Solver SVD", value=True, key="d4")

    if st.button("🚀 Iniciar Auto-Tuning Masivo y Actualizar Producción", type="primary"):
        from sklearn.neural_network import MLPRegressor
        from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import GridSearchCV, KFold
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        import joblib
        import json
        from datetime import datetime
        
        feature_names = ['year', 'season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
        feature_names = [f for f in feature_names if f in df.columns]
        
        X = df[feature_names].fillna(0)
        y = df['yield_kg_ha'].fillna(0)
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        
        # Build Parameter Grids
        grids = {}
        
        # 1. MLP
        layers = []
        if arch_shallow: layers.append((32, 16))
        if arch_standard: layers.append((64, 32))
        if arch_deep: layers.append((128, 64, 32))
        acts = []
        if act_relu: acts.append('relu')
        if act_tanh: acts.append('tanh')
        alphas = []
        if alpha_low: alphas.append(0.0001)
        if alpha_high: alphas.append(0.1)
        grids["MLP"] = (MLPRegressor(max_iter=300, random_state=42), {'model__hidden_layer_sizes': layers, 'model__activation': acts, 'model__alpha': alphas})
        
        # 2. RF
        n_est = []
        if rf_n50: n_est.append(50)
        if rf_n100: n_est.append(100)
        depths = []
        if rf_d10: depths.append(10)
        if rf_d20: depths.append(20)
        grids["RandomForest"] = (RandomForestRegressor(random_state=42), {'model__n_estimators': n_est, 'model__max_depth': depths})
        
        # 3. HistGB
        lrs = []
        if gb_lr01: lrs.append(0.01)
        if gb_lr10: lrs.append(0.1)
        iters = []
        if gb_i100: iters.append(100)
        if gb_i300: iters.append(300)
        grids["HistGBM"] = (HistGradientBoostingRegressor(random_state=42), {'model__learning_rate': lrs, 'model__max_iter': iters})
        
        # 4. Ridge
        r_alphas = []
        if rd_a01: r_alphas.append(0.1)
        if rd_a1: r_alphas.append(1.0)
        solvers = []
        if rd_auto: solvers.append('auto')
        if rd_svd: solvers.append('svd')
        grids["Ridge"] = (Ridge(random_state=42), {'model__alpha': r_alphas, 'model__solver': solvers})
        
        tournament_results = []
        best_mlp_pipeline = None
        best_mlp_score = -999
        best_mlp_params = {}
        
        progress_bar = st.progress(0)
        log_txt = st.empty()
        
        for i, (name, (base_model, param_grid)) in enumerate(grids.items()):
            log_txt.info(f"[{i+1}/{len(grids)}] Ejecutando GridSearch para {name}...")
            
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('model', base_model)
            ])
            
            grid_search = GridSearchCV(pipeline, param_grid, cv=cv, scoring='r2', n_jobs=-1, refit=True)
            grid_search.fit(X, y)
            
            best_score = grid_search.best_score_
            best_params = grid_search.best_params_
            
            tournament_results.append({
                "Algoritmo": name,
                "R2 Promedio Ganador": best_score,
                "Mejores Hiperparámetros": str({k.replace('model__',''): v for k,v in best_params.items()})
            })
            
            if name == "MLP":
                best_mlp_pipeline = grid_search.best_estimator_
                best_mlp_score = best_score
                best_mlp_params = best_params
                
            progress_bar.progress((i + 1) / len(grids))
            
        log_txt.success("¡Torneo de Tuning Finalizado!")
        
        st.subheader("🏆 Tabla de Campeones (Mejor Variante por Algoritmo)")
        results_df = pd.DataFrame(tournament_results).sort_values("R2 Promedio Ganador", ascending=False)
        st.dataframe(results_df.style.highlight_max(subset=['R2 Promedio Ganador'], color='lightgreen'), use_container_width=True)
        
        # UPDATE PRODUCTION MODEL
        st.subheader("💾 Despliegue a Producción (CeresPINN v4)")
        if best_mlp_pipeline is not None:
            # Save Joblib
            joblib.dump(best_mlp_pipeline, MODEL_PATH)
            
            # Update Metadata
            meta = {}
            if META_PATH.exists():
                meta = json.loads(META_PATH.read_text(encoding="utf-8"))
                
            meta['algorithm'] = f"MLP_Tuned_{best_mlp_params.get('model__hidden_layer_sizes', 'Custom')}"
            if 'metrics' not in meta:
                meta['metrics'] = {}
            meta['metrics']['R2_temporal'] = float(best_mlp_score) # Proxy
            meta['trained_at'] = datetime.now().isoformat()
            
            META_PATH.write_text(json.dumps(meta, indent=2))
            
            st.success(f"✅ El cerebro de CeresPINN ha sido actualizado y sobrescrito en: `{MODEL_PATH.name}`")
            st.write(f"- Nueva arquitectura instalada: **{best_mlp_params.get('model__hidden_layer_sizes')}**")
            st.write(f"- Función de activación instalada: **{best_mlp_params.get('model__activation')}**")
            st.info("El Backend FastAPI y el Gemelo Digital cargarán automáticamente esta nueva versión en su próxima inferencia.")
            st.cache_data.clear()

def main():"""

new_content = tuning_pattern.sub(new_tuning, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Massive tuning module appended successfully.")
