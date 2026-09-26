import os
from backend.app import simulate, SimulationRequest

def test():
    req = SimulationRequest(
        field_id="field-iowa-01",
        scenario="SSP3-7.0",
        target_year=2035,
        planting_date="2035-05-15",
        maize_variety="medium_cycle",
        irrigation_strategy="rainfed",
        soil_moisture_initial_percent=60.0,
        nitrogen_application_kg_ha=150.0,
        carbon_dioxide_ppm=480.0,
        temperature_anomaly_c=1.5,
        precipitation_anomaly_percent=-5.0
    )
    
    print("Ejecutando simulación...")
    res = simulate(req)
    
    print(f"Modo: {res['inference_mode']}")
    print(f"Modelo: {res['model_name']} v{res['model_version']}")
    print(f"Rendimiento proyectado: {res['projected_yield_kg_ha']} kg/ha")
    print(f"Intervalo 90%: {res['prediction_interval_90']}")
    print(f"Extrapolación: {res['is_extrapolation']} (Features: {res['extrapolated_features']})")
    print(f"Procedencia: {res['component_provenance']}")

if __name__ == "__main__":
    test()
