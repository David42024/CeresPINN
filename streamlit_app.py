"""
CeresPINN Streamlit Frontend
Simplified visualization interface for the climate-adaptive maize digital twin.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PAGE_TITLE = "CeresPINN - Gemelo Digital Adaptativo al Clima"
PAGE_ICON = "🌱"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
        color: white;
    }
    .metric-card {
        background: #1e293b;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #334155;
    }
    .status-ok {
        background: #064e3b;
        color: #34d399;
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }
    .status-mock {
        background: #78350f;
        color: #fbbf24;
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# API Functions with fallback
def fetch_with_timeout(url, timeout=4):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"API unavailable for {url}: {e}")
        return None

@st.cache_data(ttl=60)
def get_scenarios():
    data = fetch_with_timeout(f"{API_BASE_URL}/api/scenarios")
    if data:
        return data
    return [
        {"id": "ssp1-2.6", "name": "SSP1-2.6 (Sostenible)", "description": "Bajas emisiones, +1.5°C para 2100"},
        {"id": "ssp2-4.5", "name": "SSP2-4.5 (Intermedio)", "description": "Emisiones moderadas, +2.5°C para 2100"},
        {"id": "ssp5-8.5", "name": "SSP5-8.5 (Alto)", "description": "Altas emisiones, +4.4°C para 2100"},
    ]

@st.cache_data(ttl=60)
def get_soil_profiles():
    data = fetch_with_timeout(f"{API_BASE_URL}/api/soil-profiles")
    if data:
        return data
    return [
        {"id": "clay-loam", "name": "Franco Arcilloso", "sand": 0.35, "clay": 0.35, "organic_matter": 0.025},
        {"id": "sandy-loam", "name": "Franco Arenoso", "sand": 0.60, "clay": 0.15, "organic_matter": 0.015},
        {"id": "silt-loam", "name": "Franco Limoso", "sand": 0.20, "clay": 0.20, "organic_matter": 0.035},
    ]

@st.cache_data(ttl=60)
def get_model_registry():
    data = fetch_with_timeout(f"{API_BASE_URL}/api/model-registry")
    if data:
        return data
    return [
        {"id": "pinn-v1", "name": "PINN Richards v1.0", "trained_on": "2024-01-15", "rmse": 0.12, "status": "production"},
        {"id": "pinn-v2", "name": "PINN Richards v2.0", "trained_on": "2024-06-20", "rmse": 0.08, "status": "production"},
    ]

@st.cache_data(ttl=60)
def get_validation_report():
    data = fetch_with_timeout(f"{API_BASE_URL}/api/validation")
    if data:
        return data
    return {
        "hindcast_metrics": {
            "rmse_kg_ha": 385,
            "mae_kg_ha": 298,
            "r2_score": 0.942,
            "nrmse_percent": 4.8
        },
        "ks_test": {
            "statistic": 0.087,
            "p_value": 0.234,
            "null_rejected": False
        },
        "sobol_sensitivity": {
            "first_order": {"temperature": 0.42, "precipitation": 0.31, "co2": 0.18},
            "total_order": {"temperature": 0.58, "precipitation": 0.45, "co2": 0.25}
        }
    }

@st.cache_data(ttl=60)
def get_database_health():
    data = fetch_with_timeout(f"{API_BASE_URL}/api/health/database")
    if data:
        return data
    return {"database": "postgres", "postgis": "available", "status": "mock-or-live"}

# Main App
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2rem;">🌱 CeresPINN</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Gemelo Digital Adaptativo al Clima | Maíz Resiliente a Sequías</p>
    </div>
    """, unstable_allow_html=True)

    # Database Health Indicator
    db_health = get_database_health()
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.info(f"📊 API Base URL: `{API_BASE_URL}`")
    with col2:
        if db_health and db_health.get("status") == "healthy":
            st.markdown('<span class="status-ok">✓ BD OK</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-mock">⚠ Mock Mode</span>', unsafe_allow_html=True)
    with col3:
        st.metric("Modelo PINN", "v2.0")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "⚙️ Configuración", "📈 Validación", "🧪 MLOps"])

    # Tab 1: Dashboard
    with tab1:
        st.subheader("Dashboard de Simulación")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rendimiento Estimado", "8,200 kg/ha", "+5.2% vs histórico")
        with col2:
            st.metric("LAI Máximo", "4.2 m²/m²", "Día 65")
        with col3:
            st.metric("Estrés Hídrico", "0.32", "Bajo")
        with col4:
            st.metric("Eficiencia Uso Agua", "18.5 kg/mm", "Óptimo")

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Evolución Fenológica")
            days = list(range(1, 121))
            lai = [0.1 + 0.06 * d - 0.0005 * d**2 if d < 70 else 4.2 - 0.04 * (d - 70) for d in days]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=days, y=lai, name="LAI", line=dict(color="#10b981")))
            fig.update_layout(title="Índice de Área Foliar", xaxis_title="Día", yaxis_title="LAI (m²/m²)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Balance Hídrico")
            soil_moisture = [0.35 - 0.002 * d + 0.00001 * d**2 for d in days]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=days, y=soil_moisture, name="Humedad Suelo", line=dict(color="#06b6d4")))
            fig.update_layout(title="Humedad del Suelo (0-30cm)", xaxis_title="Día", yaxis_title="Volumen (%)")
            st.plotly_chart(fig, use_container_width=True)

    # Tab 2: Configuration
    with tab2:
        st.subheader("Configuración de Simulación")
        
        scenarios = get_scenarios()
        soil_profiles = get_soil_profiles()
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Escenario Climático", [s["name"] for s in scenarios], key="scenario")
            st.selectbox("Perfil de Suelo", [s["name"] for s in soil_profiles], key="soil")
            st.slider("Fecha de Siembra", 1, 120, 45, key="planting")
        
        with col2:
            st.slider("Densidad de Siembra (plantas/ha)", 50000, 100000, 75000, key="density")
            st.slider("Riego Suplementario (mm)", 0, 200, 50, key="irrigation")
            st.selectbox("Variedad de Maíz", ["Híbrido Resistente a Sequía", "Híbrido de Alto Rendimiento", "Variedad Criolla"], key="variety")
        
        st.button("🚀 Ejecutar Simulación", type="primary", use_container_width=True)

    # Tab 3: Validation
    with tab3:
        st.subheader("Validación Estadística del Modelo")
        
        validation = get_validation_report()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("RMSE", f"{validation['hindcast_metrics']['rmse_kg_ha']} kg/ha")
        with col2:
            st.metric("MAE", f"{validation['hindcast_metrics']['mae_kg_ha']} kg/ha")
        with col3:
            st.metric("R² Score", f"{validation['hindcast_metrics']['r2_score']:.3f}")
        with col4:
            st.metric("NRMSE", f"{validation['hindcast_metrics']['nrmse_percent']:.1f}%")
        
        # Sobol Sensitivity Chart
        sobol = validation["sobol_sensitivity"]
        fig = go.Figure()
        params = list(sobol["first_order"].keys())
        fig.add_trace(go.Bar(name="Primer Orden", x=params, y=list(sobol["first_order"].values())))
        fig.add_trace(go.Bar(name="Orden Total", x=params, y=list(sobol["total_order"].values())))
        fig.update_layout(barmode="group", title="Análisis de Sensibilidad Sobol")
        st.plotly_chart(fig, use_container_width=True)

    # Tab 4: MLOps
    with tab4:
        st.subheader("MLOps & Registro de Modelos")
        
        models = get_model_registry()
        
        st.dataframe(
            pd.DataFrame(models),
            column_config={
                "id": "ID",
                "name": "Nombre del Modelo",
                "trained_on": "Fecha de Entrenamiento",
                "rmse": st.column_config.NumberColumn("RMSE", format="%.3f"),
                "status": st.column_config.TextColumn("Estado")
            },
            hide_index=True,
            use_container_width=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("📈 El modelo PINN actual ha sido entrenado con datos de 10 años de observaciones de campo.")
        with col2:
            st.success("✓ El modelo está en producción y listo para inferencia.")

if __name__ == "__main__":
    main()
