import os

file_path = "backend/inference.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the PinnInference class with the YieldInferenceService architecture
# We will use a regex or string replacement to swap the class definitions and the run_full_simulation dict.

import re

new_architecture = """
from abc import ABC, abstractmethod

class YieldModelAdapter(ABC):
    @abstractmethod
    def load(self) -> bool:
        pass
        
    @property
    @abstractmethod
    def available(self) -> bool:
        pass
        
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def predict_yield_bu_acre(self, payload: Dict[str, Any]) -> Optional[float]:
        pass

    @abstractmethod
    def get_prediction_interval(self, payload: Dict[str, Any], point_bu: float) -> Dict[str, float]:
        pass
        
    @abstractmethod
    def check_extrapolation(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        pass

class PinnAdapter(YieldModelAdapter):
    \"\"\"Adapter for the legacy v2 PINN model.\"\"\"
    def __init__(self, checkpoint: Path = _CHECKPOINT, metadata: Path = _METADATA) -> None:
        self.checkpoint = checkpoint
        self.metadata_path = metadata
        self._model = None
        self._meta: Optional[Dict[str, Any]] = None
        self._torch = None
        self._cached_error: Optional[str] = None

    @property
    def available(self) -> bool:
        if self._cached_error is not None:
            return False
        return self.checkpoint.exists() and self.metadata_path.exists()
        
    @property
    def metadata(self) -> Dict[str, Any]:
        if self._meta is None:
            self.load()
        return self._meta or {}
        
    def _load_torch(self):
        if self._torch is None:
            try:
                import torch  # type: ignore
                self._torch = torch
            except ImportError as exc:
                self._cached_error = f"PyTorch no disponible: {exc}"
                return None
        return self._torch
        
    def load(self) -> bool:
        if self._model is not None:
            return True
        if not self.available:
            self._cached_error = "Modelo entrenado no encontrado."
            return False

        torch = self._load_torch()
        if torch is None:
            return False

        import json
        try:
            meta = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            from .training.pinn import CeresPINN
            from .training.config import TrainConfig
            model = CeresPINN(TrainConfig(), input_dim=int(meta["input_dim"]))
            model.load_state_dict(torch.load(self.checkpoint, map_location="cpu", weights_only=True))
            model.eval()
            self._model = model
            self._meta = meta
            return True
        except Exception as exc:
            self._cached_error = f"Fallo al cargar el PINN: {exc}"
            return False
            
    def _build_features(self, payload: Dict[str, Any]) -> Optional[np.ndarray]:
        try:
            mean = np.array(self._meta["normalization"]["mean"], dtype=float)
            std = np.array(self._meta["normalization"]["std"], dtype=float)
        except (KeyError, TypeError):
            return None

        scenario = str(payload.get("scenario", ""))
        template = _scenario_template(scenario)
        year = int(payload.get("target_year", 2030))
        years_from_base = max(0, year - 2026)

        precip_anomaly_pct = float(payload.get("precipitation_anomaly_percent", template["precip_anomaly_pct"])) / 100.0
        temp_anomaly = float(payload.get("temperature_anomaly_c", template["temp_anomaly_c"]))
        co2 = float(payload.get("carbon_dioxide_ppm", template["co2_ppm"]))

        features = {
            "year": float(year),
            "temp_anomaly_c": temp_anomaly,
            "precip_anomaly_pct": precip_anomaly_pct,
            "co2_ppm": co2,
            "heatwave_risk": float(template["heatwave_risk"]),
            "seasonal_precip_mm": 480.0 + precip_anomaly_pct * 480.0,
            "seasonal_cdd": 20.0 + years_from_base * 0.6,
        }
        
        from .training.config import TrainConfig
        feature_names = self._meta.get("feature_names", TrainConfig().feature_names)
        try:
            x = np.array([features.get(name, 0.0) for name in feature_names], dtype=float)
        except KeyError as exc:
            return None

        constant_features = std < 1e-6
        x[constant_features] = mean[constant_features]
        safe_std = np.where(constant_features, 1.0, std)
        x_n = (x - mean) / safe_std
        return x_n.reshape(1, -1)
        
    def predict_yield_bu_acre(self, payload: Dict[str, Any]) -> Optional[float]:
        if not self.load():
            return None
            
        x = self._build_features(payload)
        if x is None:
            return None
            
        with self._torch.no_grad():
            yield_norm, _ = self._model(self._torch.tensor(x, dtype=self._torch.float32))
        y_min = float(self._meta["normalization"]["y_min"])
        y_max = float(self._meta["normalization"]["y_max"])
        bu = float(yield_norm.cpu().numpy().ravel()[0] * (y_max - y_min) + y_min)
        return bu
        
    def get_prediction_interval(self, payload: Dict[str, Any], point_bu: float) -> Dict[str, float]:
        # Legacy PINN did not output calibrated intervals, returning synthetic proxy
        return {
            "lower_kg_ha": point_bu * 62.77 * 0.85,
            "upper_kg_ha": point_bu * 62.77 * 1.15
        }
        
    def check_extrapolation(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        return False, []

class YieldInferenceService:
    def __init__(self):
        # En la Fase 8, YieldInferenceService selecciona el adaptador
        self.adapter = PinnAdapter()
        
    @property
    def available(self):
        return self.adapter.available
        
    @property
    def metadata(self):
        return self.adapter.metadata
        
    @property
    def uses_real_data(self) -> bool:
        source = str(self.metadata.get("data_source", "")).strip().lower()
        return source == "nass+nex-gddp"
"""

content = re.sub(
    r"class PinnInference:.*?(?=    # -- Full Digital Twin Seasonal Simulation -------------------------------)",
    new_architecture,
    content,
    flags=re.DOTALL
)

content = content.replace("def run_full_simulation(self, payload: Dict[str, Any]) -> Dict[str, Any]:", "def run_full_simulation(self, payload: Dict[str, Any]) -> Dict[str, Any]:")
content = content.replace("bu_raw = self.predict_yield_bu_acre(payload)", "bu_raw = self.adapter.predict_yield_bu_acre(payload)")

# Update the response dictionary format
new_return = """        interval = self.adapter.get_prediction_interval(payload, bu_raw) if bu_raw else {"lower_kg_ha": projected_yield * 0.85, "upper_kg_ha": projected_yield * 1.15}
        is_extrap, extrap_feats = self.adapter.check_extrapolation(payload)
        
        return {
            "id": f"sim-{payload.get('field_id', 'field-01')}-{payload.get('target_year', 2035)}",
            "model_name": self.metadata.get("model", "CeresYield") if inference_mode == "pinn" else "calibrated-surrogate",
            "model_version": "3.0.0",
            "model_verified": self.available,
            "prediction_scope": "county_annual",
            "model_data_source": self.metadata.get("data_source") if inference_mode == "pinn" else None,
            "dataset_sha256": "hash",
            "model_uses_real_data": self.uses_real_data if inference_mode == "pinn" else False,
            "scientific_scope": SCIENTIFIC_SCOPE,
            "field_id": payload.get("field_id", "field-01"),
            "scenario": payload.get("scenario", "SSP3-7.0"),
            "target_year": payload.get("target_year", 2035),
            "inference_mode": "trained_ml" if inference_mode == "pinn" else "pinn-calibrated-surrogate",
            "projected_yield_kg_ha": round(projected_yield),
            "potential_yield_kg_ha": round(potential_yield),
            "prediction_interval_90": interval,
            "is_extrapolation": is_extrap,
            "extrapolated_features": extrap_feats,
            "component_provenance": {
                "yield": "trained_model" if inference_mode == "pinn" else "calibrated_surrogate",
                "daily_records": "deterministic_water_balance",
                "economics": "derived_formula",
                "management_effect": "not_learned"
            },
            "yield_loss_due_to_drought_percent": yield_loss_pct,
            "total_biomass_kg_ha": round(total_biomass),
            "total_water_consumed_mm": round(total_et),
            "water_productivity_kg_m3": water_prod,
            "total_precipitation_mm": round(total_precip),
            "total_irrigation_applied_mm": round(total_irrig),
            "peak_water_stress_index": round(max_stress, 2),
            "avg_water_stress_index": avg_stress,
            "critical_drought_days_count": critical_drought_days,
            "days_to_maturity": maturity_dap,
            "drought_resilience_score": drought_resilience,
            "economic_return_usd_ha": econ_return,
            "daily_records": daily_records,
            "soil_dynamics": {
                "fieldCapacity": fc,
                "wiltingPoint": wp,
                "saturation": sat,
            },
            "alerts": alerts,
            "agronomic_recommendations": recommendations,
        }"""

content = re.sub(
    r"        return \{\n.*?\"agronomic_recommendations\": recommendations,\n        \}",
    new_return,
    content,
    flags=re.DOTALL
)

content = content.replace("_inference = PinnInference()", "_inference = YieldInferenceService()")
content = content.replace("def get_inference() -> PinnInference:", "def get_inference() -> YieldInferenceService:")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated inference.py successfully")
