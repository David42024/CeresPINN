import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_simulate_digital_twin_scenarios():
    """Test that the Digital Twin API can handle multiple climate scenarios."""
    base_payload = {
        "field_id": "iowa_corn_01",
        "scenario": "Historical",
        "target_year": 2026,
        "temperature_anomaly_c": 0.0,
        "precipitation_anomaly_percent": 0.0,
        "carbon_dioxide_ppm": 415.0,
        "planting_date": "2026-05-01",
        "maize_variety": "medium_cycle",
        "irrigation_strategy": "rainfed",
        "soil_moisture_initial_percent": 60.0,
        "nitrogen_application_kg_ha": 180.0
    }
    
    # Historical base case
    response = client.post("/api/simulate", json=base_payload)
    assert response.status_code == 200
    data = response.json()
    assert "projected_yield_kg_ha" in data
    assert "model_verified" in data
    
    base_yield = data["projected_yield_kg_ha"]
    
    # Extreme Heat Scenario (SSP5-8.5 style)
    extreme_payload = base_payload.copy()
    extreme_payload["temperature_anomaly_c"] = 3.5
    extreme_payload["precipitation_anomaly_percent"] = -15.0
    
    res_extreme = client.post("/api/simulate", json=extreme_payload)
    assert res_extreme.status_code == 200
    data_extreme = res_extreme.json()
    
    # Physics check: extreme heat + drought should decrease yield
    assert data_extreme["projected_yield_kg_ha"] < base_yield

def test_api_healthcheck():
    """Verify digital twin endpoints are responsive."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "cerespinn-backend"
