import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace render_stats and render_training
import_pattern = re.compile(r"def render_stats\(df\):.*?def render_model_eval\(meta\):", re.DOTALL)

new_functions = """def render_stats(df):
    st.title("📈 Pruebas Estadísticas")
    st.markdown("---")
    st.markdown("Esta sección ejecuta pruebas de hipótesis rigurosas sobre los datos agroclimáticos para validar suposiciones fundamentales del modelo CeresPINN.")
    if df.empty:
        return
        
    st.subheader("1. Impacto del Calor Extremo (T-Test de Welch)")
    st.markdown("Comprueba si las altas temperaturas extremas (días cálidos vs días frescos) causan una caída real y significativa en el rendimiento, justificando la necesidad de que el modelo aprenda esa relación física.")
    if 'season_tmax_mean_c' not in df.columns:
        st.warning("Falta la columna season_tmax_mean_c")
        return
        
    median_tmax = df['season_tmax_mean_c'].median()
    df_hot = df[df['season_tmax_mean_c'] > median_tmax]
    df_cool = df[df['season_tmax_mean_c'] <= median_tmax]
    
    st.write(f"**Umbral de Temp Máxima (Mediana de corte):** {median_tmax:.2f} °C")
    
    import scipy.stats as stats
    t_stat, p_val = stats.ttest_ind(df_hot['yield_kg_ha'].dropna(), df_cool['yield_kg_ha'].dropna(), equal_var=False)
    
    st.markdown(f\"\"\"
    - **Estadístico T:** `{t_stat:.4f}`
    - **P-Value:** `{p_val:.4e}`
    
    {'✅ **Conclusión:** P-Value < 0.05. Existe una diferencia estadísticamente significativa en el rendimiento debida al estrés térmico.' if p_val < 0.05 else '❌ **Conclusión:** No hay diferencia significativa. El modelo no debería forzar una penalización por temperatura.'}
    \"\"\")
    
    st.subheader("2. Prueba de Normalidad (Kolmogorov-Smirnov)")
    st.markdown("Comprueba si los rendimientos siguen una distribución Gaussiana perfecta. Si no es así, algoritmos tradicionales como OLS pueden fallar y algoritmos no-lineales (Random Forest, Redes Neuronales) serán más adecuados.")
    ks_stat, ks_pval = stats.kstest(df['yield_kg_ha'].dropna(), 'norm', args=(df['yield_kg_ha'].mean(), df['yield_kg_ha'].std()))
    st.write(f"**KS-Statistic:** `{ks_stat:.4f}` | **P-Value:** `{ks_pval:.4e}`")
    st.info("💡 Si el P-Value < 0.05, el rendimiento NO sigue una distribución normal perfecta, validando la necesidad de algoritmos de Machine Learning avanzados.")

def render_training(df):
    st.title("⚙️ Entrenamiento y Validación Cruzada (K-Fold)")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown(\"\"\"
    ### Configuración de MLOps
    Esta sección entrena **5 algoritmos** utilizando validación cruzada real de 5 particiones (5-Fold CV).
    - **Modelos Tradicionales (3):** Regresión Ridge, Random Forest, HistGradientBoosting.
    - **Modelos Híbridos/Avanzados (2):** CeresPINN-Lite (Perceptrón Multicapa) y Ensamble Físico-Estadístico (Stacking de Ridge + MLP).
    
    La **Validación Cruzada** divide el dataset en 5 partes, entrena con 4 y evalúa con 1, rotando hasta probar todo.
    \"\"\")
    
    if st.button("🚀 Iniciar Entrenamiento y Cross-Validation", type="primary"):
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, StackingRegressor
        from sklearn.neural_network import MLPRegressor
        from sklearn.model_selection import KFold, cross_val_score, cross_validate
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        
        feature_names = ['year', 'season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
        feature_names = [f for f in feature_names if f in df.columns]
        
        X = df[feature_names].fillna(0)
        y = df['yield_kg_ha'].fillna(0)
        
        mlp_base = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=200, random_state=42)
        
        models = {
            "Tradicional: Ridge (Lineal)": Ridge(alpha=1.0),
            "Tradicional: Random Forest": RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42),
            "Tradicional: HistGBM (Boosted)": HistGradientBoostingRegressor(max_iter=100, random_state=42),
            "Híbrido: CeresPINN-Lite (MLP)": mlp_base,
            "Híbrido: Ensamble (Ridge+MLP)": StackingRegressor(
                estimators=[('ridge', Ridge(alpha=1.0)), ('mlp', mlp_base)],
                final_estimator=Ridge()
            )
        }
        
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()
        
        results = []
        fold_results = []
        
        with log_container:
            for i, (name, model) in enumerate(models.items()):
                status_text.text(f"Entrenando y Validando (5 Folds): {name}...")
                
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('model', model)
                ])
                
                # Ejecutar Cross Validation detallada
                cv_results = cross_validate(pipeline, X, y, cv=cv, scoring=('r2', 'neg_root_mean_squared_error'), n_jobs=-1)
                
                r2_scores = cv_results['test_r2']
                rmse_scores = -cv_results['test_neg_root_mean_squared_error']
                
                mean_r2 = r2_scores.mean()
                mean_rmse = rmse_scores.mean()
                
                results.append({"Algoritmo": name, "R2 Promedio": mean_r2, "RMSE Promedio (kg/ha)": mean_rmse})
                
                # Guardar info de cada fold para visualizacion
                for fold_idx in range(5):
                    fold_results.append({
                        "Algoritmo": name, 
                        "Fold": f"Fold {fold_idx+1}", 
                        "R2": r2_scores[fold_idx],
                        "RMSE": rmse_scores[fold_idx]
                    })
                
                st.write(f"✅ **{name}** -> R2: `{mean_r2:.4f}` | RMSE: `{mean_rmse:.2f} kg/ha`")
                progress_bar.progress((i + 1) / len(models))
                
        status_text.text("✅ Pipeline de validación cruzada completado exitosamente.")
        
        st.subheader("1. Resultados de Desempeño Promedio (Tabla Final)")
        results_df = pd.DataFrame(results).sort_values("R2 Promedio", ascending=False)
        st.dataframe(results_df.style.highlight_max(subset=['R2 Promedio'], color='lightgreen').highlight_min(subset=['RMSE Promedio (kg/ha)'], color='lightgreen'), use_container_width=True)
        
        st.subheader("2. Detalle de Validación Cruzada (Estabilidad por Fold)")
        st.markdown("La gráfica inferior demuestra cómo varió el R² de cada modelo al rotar los datos de validación (K-Fold=5). Modelos con cajas muy anchas sufren de inestabilidad espacial/temporal.")
        fold_df = pd.DataFrame(fold_results)
        import plotly.express as px
        fig = px.box(fold_df, x="Algoritmo", y="R2", color="Algoritmo", title="Distribución de R² en los 5 Folds (Cross-Validation)")
        st.plotly_chart(fig, use_container_width=True)

def render_model_eval(meta):"""

new_content = import_pattern.sub(new_functions, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated stats and training")
