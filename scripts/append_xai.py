import re

file_path = "ml_lab/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update sidebar
sidebar_old = """                "6. Entrenamiento y Validación Cruzada",
                "7. Evaluación de Modelos Espaciales"
            ]
        )"""
sidebar_new = """                "6. Entrenamiento y Validación Cruzada",
                "7. Evaluación de Modelos Espaciales",
                "8. IA Explicable (XAI): Importancia & PDP",
                "9. Análisis Geoespacial de Errores"
            ]
        )"""
content = content.replace(sidebar_old, sidebar_new)

# 2. Update main()
main_old = """    elif page == "7. Evaluación de Modelos Espaciales":
        render_model_eval(meta)

if __name__ == "__main__":"""
main_new = """    elif page == "7. Evaluación de Modelos Espaciales":
        render_model_eval(meta)
    elif page == "8. IA Explicable (XAI): Importancia & PDP":
        render_xai(df)
    elif page == "9. Análisis Geoespacial de Errores":
        render_geospatial(df, meta)

if __name__ == "__main__":"""
content = content.replace(main_old, main_new)

# 3. Inject the new functions right above main()
xai_functions = """
def render_xai(df):
    st.title("🧠 Inteligencia Artificial Explicable (XAI)")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown("Entrena un modelo interpretativo rápido (Random Forest) para entender qué variables dominan las predicciones del rendimiento agrícola.")
    
    if st.button("Generar Explicabilidad (SHAP / Feature Importance)"):
        from sklearn.ensemble import RandomForestRegressor
        import plotly.express as px
        
        feature_names = ['season_temp_mean_c', 'season_tmax_mean_c', 'season_precip_mm', 'gdd', 'cdd', 'vpd_mean_kpa']
        feature_names = [f for f in feature_names if f in df.columns]
        
        X = df[feature_names].fillna(0)
        y = df['yield_kg_ha'].fillna(0)
        
        rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        rf.fit(X, y)
        
        importances = rf.feature_importances_
        imp_df = pd.DataFrame({"Variable": feature_names, "Importancia (%)": importances * 100})
        imp_df = imp_df.sort_values("Importancia (%)", ascending=True)
        
        st.subheader("1. Importancia Relativa de las Variables (Feature Importance)")
        st.markdown("¿Qué factor climático pesa más para que el cultivo tenga éxito o fracase?")
        
        fig = px.bar(imp_df, x="Importancia (%)", y="Variable", orientation='h', title="Random Forest: Importancia de Variables Gini")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("2. Curvas de Dependencia Parcial (PDP)")
        st.markdown("¿Cómo cambia la predicción del modelo al aislar una sola variable (ej. Temp Máxima) manteniendo el resto constante?")
        
        try:
            from sklearn.inspection import PartialDependenceDisplay
            import matplotlib.pyplot as plt
            
            fig_pdp, ax = plt.subplots(figsize=(10, 4))
            # Plot PDP for the top 2 features
            top_features = imp_df.sort_values("Importancia (%)", ascending=False)["Variable"].head(2).tolist()
            display = PartialDependenceDisplay.from_estimator(rf, X, top_features, ax=ax)
            st.pyplot(fig_pdp)
            st.info("💡 **Tipping Points:** Si la curva cae drásticamente después de cierto valor en el eje X, el modelo ha encontrado un umbral crítico de tolerancia agronómica.")
        except ImportError:
            st.warning("No se pudo generar PDP. Faltan dependencias de matplotlib.")

def render_geospatial(df, meta):
    st.title("🗺️ Análisis Geoespacial de Rendimiento")
    st.markdown("---")
    if df.empty:
        return
        
    st.markdown("Visualiza el rendimiento de maíz proyectado a nivel del mapa del estado de Iowa.")
    
    if 'fips' not in df.columns:
        st.warning("No hay columna FIPS para mapear.")
        return
        
    if st.button("Renderizar Heatmap (Iowa)"):
        import urllib.request
        import json
        import plotly.express as px
        
        # Aggregate by fips
        county_avg = df.groupby('fips')['yield_kg_ha'].mean().reset_index()
        county_avg['fips'] = county_avg['fips'].astype(str).str.zfill(5)
        
        st.write("Calculando promedios geoespaciales...")
        
        url = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
        try:
            with urllib.request.urlopen(url) as response:
                counties = json.load(response)
                
            fig = px.choropleth(
                county_avg, 
                geojson=counties, 
                locations='fips', 
                color='yield_kg_ha',
                color_continuous_scale="Viridis",
                scope="usa",
                title="Rendimiento Promedio Histórico (kg/ha) por Condado"
            )
            fig.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 La variación espacial demuestra que los modelos puramente temporales (Series de Tiempo) fracasan, justificando un enfoque espacial (CeresPINN).")
        except Exception as e:
            st.error(f"Error al descargar la geometría geojson: {e}")

"""

# Insert right before main
content = content.replace("def main():", xai_functions + "def main():")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("XAI and Geospatial modules appended successfully.")
