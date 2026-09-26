import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace render_stats
stats_pattern = re.compile(r"def render_stats\(df\):.*?def render_training\(df\):", re.DOTALL)

new_stats = """def render_stats(df):
    st.title("📈 Pruebas Estadísticas Interactivas")
    st.markdown("---")
    st.markdown("Ejecuta pruebas de hipótesis a la medida para validar correlaciones y distribuciones agroclimáticas.")
    if df.empty:
        return
        
    import scipy.stats as stats
    
    st.subheader("1. Prueba T-Test: Impacto del Estrés Térmico")
    st.write("Selecciona un umbral de temperatura máxima estacional. Se comparará estadísticamente el rendimiento de los años por encima del umbral vs por debajo.")
    
    tmax_min = float(df['season_tmax_mean_c'].min())
    tmax_max = float(df['season_tmax_mean_c'].max())
    tmax_median = float(df['season_tmax_mean_c'].median())
    
    threshold = st.slider("Umbral de Temperatura Máxima (°C)", min_value=tmax_min, max_value=tmax_max, value=tmax_median)
    
    if st.button("Ejecutar T-Test"):
        df_hot = df[df['season_tmax_mean_c'] > threshold]
        df_cool = df[df['season_tmax_mean_c'] <= threshold]
        
        if len(df_hot) > 5 and len(df_cool) > 5:
            t_stat, p_val = stats.ttest_ind(df_hot['yield_kg_ha'].dropna(), df_cool['yield_kg_ha'].dropna(), equal_var=False)
            st.markdown(f\"\"\"
            - **Muestras Años Cálidos:** {len(df_hot)} | Promedio: {df_hot['yield_kg_ha'].mean():.0f} kg/ha
            - **Muestras Años Frescos:** {len(df_cool)} | Promedio: {df_cool['yield_kg_ha'].mean():.0f} kg/ha
            - **Estadístico T:** `{t_stat:.4f}` | **P-Value:** `{p_val:.4e}`
            
            {'✅ **Conclusión:** P-Value < 0.05. Existe una diferencia estadísticamente significativa debida al estrés térmico.' if p_val < 0.05 else '❌ **Conclusión:** No hay diferencia significativa en este umbral.'}
            \"\"\")
        else:
            st.error("No hay suficientes datos en uno de los grupos para ejecutar el T-Test. Cambia el umbral.")
            
    st.markdown("---")
    
    st.subheader("2. Análisis de Varianza (ANOVA): Zonas de Precipitación")
    st.write("Divide el dataset en 3 zonas de precipitaciones (Seco, Normal, Húmedo) basado en percentiles (e.g. 33%, 66%) y verifica si el agua marca una diferencia sistémica.")
    
    col1, col2 = st.columns(2)
    with col1:
        p_low = st.number_input("Percentil para 'Seco' (0-100)", value=33)
    with col2:
        p_high = st.number_input("Percentil para 'Húmedo' (0-100)", value=66)
        
    if st.button("Ejecutar ANOVA (One-Way)"):
        v_low = np.percentile(df['season_precip_mm'].dropna(), p_low)
        v_high = np.percentile(df['season_precip_mm'].dropna(), p_high)
        
        dry = df[df['season_precip_mm'] <= v_low]['yield_kg_ha'].dropna()
        normal = df[(df['season_precip_mm'] > v_low) & (df['season_precip_mm'] <= v_high)]['yield_kg_ha'].dropna()
        wet = df[df['season_precip_mm'] > v_high]['yield_kg_ha'].dropna()
        
        f_stat, p_val_anova = stats.f_oneway(dry, normal, wet)
        
        st.markdown(f\"\"\"
        - **Umbrales:** Seco <= {v_low:.1f} mm | Húmedo > {v_high:.1f} mm
        - **Estadístico F:** `{f_stat:.4f}` | **P-Value:** `{p_val_anova:.4e}`
        
        {'✅ **Conclusión:** Al menos uno de los regímenes de lluvia tiene una media significativamente distinta.' if p_val_anova < 0.05 else '❌ **Conclusión:** La precipitación estacional (a este nivel macro) no muestra impacto significativo en el test.'}
        \"\"\")
        
    st.markdown("---")
    
    st.subheader("3. Correlación de Pearson & Spearman")
    st.write("Calcula la significancia de la correlación entre una variable climática específica y el rendimiento.")
    
    climate_vars = ['season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
    climate_vars = [v for v in climate_vars if v in df.columns]
    
    selected_var = st.selectbox("Selecciona Variable Climática", climate_vars)
    
    if st.button("Ejecutar Test de Correlación"):
        valid_df = df[[selected_var, 'yield_kg_ha']].dropna()
        pearson_r, p_pearson = stats.pearsonr(valid_df[selected_var], valid_df['yield_kg_ha'])
        spearman_r, p_spearman = stats.spearmanr(valid_df[selected_var], valid_df['yield_kg_ha'])
        
        st.markdown(f\"\"\"
        - **Pearson (Relación Lineal):** r = `{pearson_r:.4f}`, P-Value = `{p_pearson:.4e}`
        - **Spearman (Relación Monótona):** ρ = `{spearman_r:.4f}`, P-Value = `{p_spearman:.4e}`
        \"\"\")
        
        import plotly.express as px
        fig = px.scatter(valid_df, x=selected_var, y="yield_kg_ha", trendline="ols", title=f"Dispersión: {selected_var} vs Rendimiento")
        st.plotly_chart(fig, use_container_width=True)
        
    st.markdown("---")
    
    st.subheader("4. Prueba de Normalidad (Kolmogorov-Smirnov)")
    st.write("Verifica si los rendimientos siguen una curva Normal o si requieren transformaciones matemáticas.")
    
    transf = st.radio("Aplicar Transformación:", ["Ninguna (Raw Yield)", "Logarítmica (Log Yield)"])
    
    if st.button("Ejecutar KS Test"):
        data = df['yield_kg_ha'].dropna()
        if transf == "Logarítmica (Log Yield)":
            data = np.log1p(data)
            
        ks_stat, ks_pval = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        st.write(f"**KS-Statistic:** `{ks_stat:.4f}` | **P-Value:** `{ks_pval:.4e}`")
        if ks_pval < 0.05:
            st.error(f"❌ La distribución **NO** es normal (P-Value < 0.05). Algoritmos OLS asumen normalidad y podrían fallar.")
        else:
            st.success(f"✅ La distribución es estadísticamente Normal.")

def render_training(df):"""

new_content = stats_pattern.sub(new_stats, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated interactive stats")
