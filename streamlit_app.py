"""CeresPINN Streamlit client for the deployed FastAPI backend.

The UI never manufactures model outputs. When FastAPI is unavailable it keeps
configuration controls visible, marks scientific results as unavailable and
does not substitute demonstration metrics for checkpoint inference.
"""
from __future__ import annotations

from datetime import date
import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
PAGE_TITLE = "CeresPINN - Gemelo Digital Adaptativo al Clima"
PAGE_ICON = "🌱"
REQUEST_TIMEOUT_SECONDS = 4

SCENARIO_DEFAULTS = {
    "SSP1-2.6": {"temperature": 0.9, "precipitation": -2.0, "co2": 445.0},
    "SSP2-4.5": {"temperature": 1.4, "precipitation": -7.0, "co2": 480.0},
    "SSP3-7.0": {"temperature": 1.8, "precipitation": -12.0, "co2": 540.0},
    "SSP5-8.5": {"temperature": 2.6, "precipitation": -24.0, "co2": 600.0},
}

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
        color: white;
    }
    .status-ok, .status-offline {
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }
    .status-ok { background: #064e3b; color: #34d399; }
    .status-offline { background: #7f1d1d; color: #fecaca; }
</style>
""",
    unsafe_allow_html=True,
)


def normalize_validation(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize the real `/api/validation` response for Streamlit widgets."""
    data = dict(raw or {})
    hindcast = data.get("hindcast", {}) or {}
    metrics = hindcast.get("metrics", {}) or {}

    # Prefer the nested hindcast produced during the request. The legacy
    # top-level object is accepted only when the nested report is absent.
    if metrics:
        rmse = float(metrics.get("rmse_kg_ha") or 0.0)
        mae = float(metrics.get("mae_kg_ha") or 0.0)
        r2 = float(metrics.get("r2", metrics.get("r2_score", 0.0)) or 0.0)
        by_year = hindcast.get("by_year", []) or []
        observed = [
            float(row["observed_kg_ha"])
            for row in by_year
            if row.get("observed_kg_ha") is not None
        ]
        mean_observed = sum(observed) / len(observed) if observed else 0.0
        data["hindcast_metrics"] = {
            "rmse_kg_ha": rmse,
            "mae_kg_ha": mae,
            "r2_score": r2,
            "nrmse_percent": round(rmse / mean_observed * 100.0, 1)
            if mean_observed
            else None,
        }
    elif data.get("hindcast_metrics"):
        current = dict(data["hindcast_metrics"])
        current["r2_score"] = float(current.get("r2_score", current.get("r2", 0.0)))
        data["hindcast_metrics"] = current

    sobol = data.get("sobol_sensitivity", {}) or {}
    if isinstance(sobol.get("first_order"), list):
        parameters = sobol.get("parameters", []) or []
        data["sobol_sensitivity"] = {
            "first_order": dict(zip(parameters, sobol.get("first_order", []))),
            "total_order": dict(zip(parameters, sobol.get("total", []))),
        }
    elif "total" in sobol and "total_order" not in sobol:
        data["sobol_sensitivity"] = {
            **sobol,
            "total_order": sobol.get("total", {}),
        }
    return data


def display_name(item: Any) -> str:
    """Return a stable human-readable name for API dictionaries."""
    if isinstance(item, dict):
        return str(item.get("name") or item.get("label") or item.get("id") or item)
    return str(item)


def fetch_with_timeout(url: str, timeout: int = REQUEST_TIMEOUT_SECONDS) -> Any | None:
    """Fetch one JSON resource and surface failures without inventing data."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.warning(f"API no disponible para {url}: {exc}")
        return None


@st.cache_data(ttl=60)
def get_scenarios() -> list[dict[str, Any]]:
    data = fetch_with_timeout(f"{API_BASE_URL}/api/scenarios")
    if isinstance(data, list) and data:
        return data
    return [
        {"id": scenario_id, "label": scenario_id, "source": "local configuration"}
        for scenario_id in SCENARIO_DEFAULTS
    ]


@st.cache_data(ttl=60)
def get_soil_profiles() -> list[dict[str, Any]]:
    data = fetch_with_timeout(f"{API_BASE_URL}/api/soil-profiles")
    if isinstance(data, list) and data:
        return data
    return [
        {"id": "clay_loam", "label": "Franco Arcilloso"},
        {"id": "sandy_loam", "label": "Franco Arenoso"},
        {"id": "loam", "label": "Franco"},
    ]


@st.cache_data(ttl=60)
def get_fields() -> list[dict[str, Any]]:
    data = fetch_with_timeout(f"{API_BASE_URL}/api/fields")
    if isinstance(data, list) and data:
        return data
    return [
        {
            "id": "field-iowa-01",
            "name": "Parcela Experimental Ames Norte",
            "source": "local configuration",
        }
    ]


@st.cache_data(ttl=60)
def get_model_registry() -> list[dict[str, Any]]:
    data = fetch_with_timeout(f"{API_BASE_URL}/api/model-registry")
    return data if isinstance(data, list) else []


@st.cache_data(ttl=60)
def get_validation_report() -> dict[str, Any] | None:
    data = fetch_with_timeout(f"{API_BASE_URL}/api/validation")
    return normalize_validation(data) if isinstance(data, dict) else None


@st.cache_data(ttl=60)
def get_database_health() -> dict[str, Any]:
    data = fetch_with_timeout(f"{API_BASE_URL}/api/health/database")
    if isinstance(data, dict):
        return data
    return {"database": "unknown", "postgis": "unknown", "status": "unavailable"}


def execute_simulation(payload: dict[str, Any]) -> dict[str, Any]:
    """Call the trained-model endpoint; errors are handled by the UI caller."""
    response = requests.post(
        f"{API_BASE_URL}/api/simulate",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if result.get("inference_mode") != "pinn":
        raise RuntimeError("El backend no confirmó inferencia mediante el checkpoint.")
    if not result.get("model_uses_real_data"):
        raise RuntimeError("El backend no confirmó procedencia de datos reales.")
    if not isinstance(result.get("projected_yield_kg_ha"), (int, float)):
        raise RuntimeError("La respuesta del modelo no contiene rendimiento válido.")
    return result


def _id_lookup(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id") or item.get("version")): item for item in items}


def _metric_value(result: dict[str, Any] | None, key: str, suffix: str = "") -> str:
    if not result or not isinstance(result.get(key), (int, float)):
        return "—"
    value = result[key]
    if isinstance(value, float):
        return f"{value:,.2f}{suffix}"
    return f"{value:,}{suffix}"


def render_dashboard(result: dict[str, Any] | None) -> None:
    st.subheader("Dashboard de Simulación")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Rendimiento calculado",
            _metric_value(result, "projected_yield_kg_ha", " kg/ha"),
        )
    with col2:
        st.metric(
            "Biomasa total",
            _metric_value(result, "total_biomass_kg_ha", " kg/ha"),
        )
    with col3:
        st.metric(
            "Estrés hídrico pico",
            _metric_value(result, "peak_water_stress_index"),
        )
    with col4:
        st.metric(
            "Productividad del agua",
            _metric_value(result, "water_productivity_kg_m3", " kg/m³"),
        )

    records = result.get("daily_records", []) if result else []
    if not records:
        st.info("Ejecuta una simulación para visualizar las trayectorias devueltas por el backend.")
        return

    frame = pd.DataFrame(records)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Evolución fenológica")
        fig = go.Figure()
        if "lai" in frame:
            fig.add_trace(
                go.Scatter(x=frame.get("dap"), y=frame["lai"], name="LAI", line={"color": "#10b981"})
            )
        fig.update_layout(xaxis_title="DAP", yaxis_title="LAI (m²/m²)")
        st.plotly_chart(fig, width="stretch")
    with col2:
        st.subheader("Balance hídrico")
        fig = go.Figure()
        if "soil_moisture_avg" in frame:
            fig.add_trace(
                go.Scatter(
                    x=frame.get("dap"),
                    y=frame["soil_moisture_avg"],
                    name="Humedad media",
                    line={"color": "#06b6d4"},
                )
            )
        fig.update_layout(xaxis_title="DAP", yaxis_title="Fracción volumétrica")
        st.plotly_chart(fig, width="stretch")


def render_configuration() -> None:
    st.subheader("Configuración de Simulación")
    scenarios = get_scenarios()
    soils = get_soil_profiles()
    fields = get_fields()
    scenario_lookup = _id_lookup(scenarios)
    soil_lookup = _id_lookup(soils)
    field_lookup = _id_lookup(fields)

    col1, col2 = st.columns(2)
    with col1:
        field_id = st.selectbox(
            "Campo",
            list(field_lookup),
            format_func=lambda value: display_name(field_lookup[value]),
            key="field_id",
        )
        scenario_id = st.selectbox(
            "Escenario Climático",
            list(scenario_lookup),
            format_func=lambda value: display_name(scenario_lookup[value]),
            key="scenario",
        )
        st.selectbox(
            "Perfil de Suelo",
            list(soil_lookup),
            format_func=lambda value: display_name(soil_lookup[value]),
            key="soil",
        )
        target_year = st.slider("Año objetivo", 2026, 2070, 2035, key="target_year")
        planting_date = st.date_input("Fecha de siembra", value=date(2026, 5, 1), key="planting_date")

    with col2:
        maize_variety = st.selectbox(
            "Variedad de Maíz",
            ["short_cycle", "medium_cycle", "long_cycle"],
            format_func=lambda value: {
                "short_cycle": "Ciclo corto",
                "medium_cycle": "Ciclo medio",
                "long_cycle": "Ciclo largo",
            }[value],
            key="variety",
        )
        irrigation_strategy = st.selectbox(
            "Estrategia de Riego",
            ["rainfed", "deficit_50", "deficit_75", "optimal"],
            format_func=lambda value: {
                "rainfed": "Secano",
                "deficit_50": "Déficit 50 %",
                "deficit_75": "Déficit 75 %",
                "optimal": "Óptimo",
            }[value],
            key="irrigation_strategy",
        )
        soil_moisture = st.slider("Humedad inicial del suelo (%)", 5, 50, 28, key="soil_moisture")
        nitrogen = st.slider("Nitrógeno aplicado (kg/ha)", 0, 300, 180, key="nitrogen")

    forcing = SCENARIO_DEFAULTS.get(scenario_id, SCENARIO_DEFAULTS["SSP3-7.0"])
    payload = {
        "field_id": field_id,
        "scenario": scenario_id,
        "target_year": int(target_year),
        "planting_date": planting_date.isoformat(),
        "maize_variety": maize_variety,
        "irrigation_strategy": irrigation_strategy,
        "soil_moisture_initial_percent": float(soil_moisture),
        "nitrogen_application_kg_ha": float(nitrogen),
        "carbon_dioxide_ppm": forcing["co2"],
        "temperature_anomaly_c": forcing["temperature"],
        "precipitation_anomaly_percent": forcing["precipitation"],
    }

    if st.button("🚀 Ejecutar Simulación", type="primary", width="stretch", key="run_simulation"):
        try:
            with st.spinner("Ejecutando checkpoint PyTorch…"):
                st.session_state["simulation_result"] = execute_simulation(payload)
            st.success("Simulación calculada por el checkpoint desplegado.")
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            st.session_state.pop("simulation_result", None)
            st.error(f"No fue posible ejecutar el modelo: {exc}")


def render_validation(validation: dict[str, Any] | None) -> None:
    st.subheader("Validación Estadística del Modelo")
    metrics = validation.get("hindcast_metrics") if validation else None
    if not metrics:
        st.warning("La validación no está disponible; no se muestran métricas sustitutas.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("RMSE", f"{float(metrics.get('rmse_kg_ha', 0)):,.2f} kg/ha")
    with col2:
        st.metric("MAE", f"{float(metrics.get('mae_kg_ha', 0)):,.2f} kg/ha")
    with col3:
        st.metric("R² Score", f"{float(metrics.get('r2_score', 0)):.3f}")
    with col4:
        nrmse = metrics.get("nrmse_percent")
        st.metric("NRMSE", f"{float(nrmse):.1f}%" if nrmse is not None else "No calculado")

    sobol = validation.get("sobol_sensitivity", {}) or {}
    first_order = sobol.get("first_order", {}) or {}
    total_order = sobol.get("total_order", {}) or {}
    if first_order:
        fig = go.Figure()
        parameters = list(first_order)
        fig.add_trace(go.Bar(name="Primer orden", x=parameters, y=list(first_order.values())))
        fig.add_trace(
            go.Bar(name="Orden total", x=parameters, y=[total_order.get(name, 0) for name in parameters])
        )
        fig.update_layout(barmode="group", title="Análisis de sensibilidad reportado por el backend")
        st.plotly_chart(fig, width="stretch")


def render_model_registry(models: list[dict[str, Any]]) -> None:
    st.subheader("MLOps & Checkpoint desplegado")
    if not models:
        st.warning("El backend no reportó un checkpoint disponible.")
        return
    rows = [
        {
            "Versión": model.get("version"),
            "Modelo": model.get("name"),
            "Arquitectura": model.get("architecture"),
            "Fecha": model.get("trainedDate"),
            "Épocas": model.get("epochs"),
            "R² test": model.get("testR2"),
            "RMSE kg/ha": model.get("testRmseKgHa"),
            "Estado": model.get("status"),
        }
        for model in models
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.info("Se muestran únicamente metadatos entregados por `/api/model-registry`.")


def main() -> None:
    st.markdown(
        """
        <div class="main-header">
            <h1 style="margin: 0; font-size: 2rem;">🌱 CeresPINN</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Gemelo Digital Adaptativo al Clima | Maíz Resiliente a Sequías</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    db_health = get_database_health()
    models = get_model_registry()
    validation = get_validation_report()
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.info(f"📊 API Base URL: `{API_BASE_URL}`")
    with col2:
        if db_health.get("status") == "connected":
            st.markdown('<span class="status-ok">✓ BD conectada</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-offline">✗ BD no disponible</span>', unsafe_allow_html=True)
    with col3:
        active_model = next((model for model in models if model.get("active")), None)
        st.metric("Checkpoint", "Disponible" if active_model else "No disponible")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Dashboard", "⚙️ Configuración", "📈 Validación", "🧪 MLOps"]
    )
    # Configuration is evaluated before the dashboard so a button click can
    # publish the new result during the same Streamlit rerun. The visual tab
    # order remains Dashboard -> Configuration.
    with tab2:
        render_configuration()
    with tab1:
        render_dashboard(st.session_state.get("simulation_result"))
    with tab3:
        render_validation(validation)
    with tab4:
        render_model_registry(models)


if __name__ == "__main__":
    main()
