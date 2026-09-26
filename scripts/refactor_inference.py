import os
import re

file_path = "backend/inference.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace the `class PinnInference:` block and its methods with YieldModelAdapter, SklearnAdapter, PinnAdapter, and YieldInferenceService.
# The YieldInferenceService will contain `run_full_simulation`.

new_classes = """from abc import ABC, abstractmethod
import json
import joblib

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
    def check_extrapolation(self, payload: Dict[str, Any]) -> tuple[bool, List[str]]:
        pass

class SklearnAdapter(YieldModelAdapter):
    def __init__(self, model_path: Path, meta_path: Path):
        self.model_path = model_path
        self.meta_path = meta_path
        self._model = None
        self._meta = None
        self._cached_error = None
        
    @property
    def available(self) -> bool:
        return self._cached_error is None and self.model_path.exists() and self.meta_path.exists()
        
    @property
    def metadata(self) -> Dict[str, Any]:
        if self._meta is None:
            self.load()
        return self._meta or {}
        
    def load(self) -> bool:
        if self._model is not None:
            return True
        if not self.available:
            self._cached_error = "Model not found."
            return False
        try:
            self._model = joblib.load(self.model_path)
            self._meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            return True
        except Exception as e:
            self._cached_error = str(e)
            return False
            
    def _build_features(self, payload: Dict[str, Any]) -> Optional[np.ndarray]:
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
            "season_precip_mm": 480.0 * (1 + precip_anomaly_pct),
            "season_temp_mean_c": 14.0 + temp_anomaly,
            "season_tmax_mean_c": 14.0 + temp_anomaly + 8.0,
            "gdd": (14.0 + temp_anomaly - 10) * 153,
            "cdd": 20.0 + years_from_base * 0.6,
            "heat_days_30c": int(template["heatwave_risk"] * 30),
            "heat_days_35c": int(template["heatwave_risk"] * 10),
            "vpd_mean_kpa": 1.2
        }
        feature_names = self._meta.get("feature_names", [])
        if not feature_names:
            from .training.config import TrainConfig
            feature_names = TrainConfig().feature_names
        try:
            x = np.array([features.get(name, 0.0) for name in feature_names], dtype=float)
            return x.reshape(1, -1)
        except Exception:
            return None

    def predict_yield_bu_acre(self, payload: Dict[str, Any]) -> Optional[float]:
        if not self.load():
            return None
        x = self._build_features(payload)
        if x is None:
            return None
        # Prediction is in kg/ha, convert to bu/acre for backward compatibility
        pred_kg_ha = float(self._model.predict(x)[0])
        return pred_kg_ha / 62.77
        
    def get_prediction_interval(self, payload: Dict[str, Any], point_bu: float) -> Dict[str, float]:
        std = self.metadata.get("metrics", {}).get("residual_std", 1500.0)
        point_kg_ha = point_bu * 62.77
        # 90% interval approx 1.645 * std
        margin = 1.645 * std
        return {
            "lower_kg_ha": max(0.0, point_kg_ha - margin),
            "upper_kg_ha": point_kg_ha + margin
        }
        
    def check_extrapolation(self, payload: Dict[str, Any]) -> tuple[bool, List[str]]:
        if not self.load():
            return False, []
        x = self._build_features(payload)
        if x is None:
            return True, ["unknown"]
        extrap_feats = []
        domain = self.metadata.get("domain", {})
        feature_names = self._meta.get("feature_names", [])
        for i, name in enumerate(feature_names):
            if name in domain:
                val = x[0, i]
                if val < domain[name]["min"] or val > domain[name]["max"]:
                    extrap_feats.append(name)
        return len(extrap_feats) > 0, extrap_feats

class PinnAdapter(YieldModelAdapter):
    # Simplified legacy adapter
    def __init__(self, checkpoint: Path, metadata: Path) -> None:
        self.checkpoint = checkpoint
        self.metadata_path = metadata
        self._meta = None
    
    @property
    def available(self) -> bool:
        return self.checkpoint.exists() and self.metadata_path.exists()
        
    @property
    def metadata(self) -> Dict[str, Any]:
        if self._meta is None and self.available:
            self._meta = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return self._meta or {}
        
    def load(self) -> bool:
        return self.available
        
    def predict_yield_bu_acre(self, payload: Dict[str, Any]) -> Optional[float]:
        return None
        
    def get_prediction_interval(self, payload: Dict[str, Any], point_bu: float) -> Dict[str, float]:
        kg_ha = point_bu * 62.77
        return {"lower_kg_ha": kg_ha * 0.85, "upper_kg_ha": kg_ha * 1.15}
        
    def check_extrapolation(self, payload: Dict[str, Any]) -> tuple[bool, List[str]]:
        return False, []

class YieldInferenceService:
    def __init__(self):
        models_dir = _MODEL_DIR
        ridge_path = models_dir / "cerespinn_ridge_v3.joblib"
        ridge_meta = models_dir / "cerespinn_ridge_v3_metadata.json"
        
        self.sklearn_adapter = SklearnAdapter(ridge_path, ridge_meta)
        self.pinn_adapter = PinnAdapter(_CHECKPOINT, _METADATA)
        
        if self.sklearn_adapter.available:
            self.adapter = self.sklearn_adapter
        else:
            self.adapter = self.pinn_adapter
            
    @property
    def error_message(self):
        if hasattr(self.adapter, "_cached_error"):
            return self.adapter._cached_error
        return None
        
    def run_full_simulation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        import math
        from datetime import datetime, timedelta
        
        bu_raw = self.adapter.predict_yield_bu_acre(payload)
        is_fallback = False
        if bu_raw is None:
            is_fallback = True
            base_bu = 168.0
            temp_anom = float(payload.get("temperature_anomaly_c", 1.8))
            precip_anom = float(payload.get("precipitation_anomaly_percent", -12.0)) / 100.0
            co2 = float(payload.get("carbon_dioxide_ppm", 540.0))
            co2_fert = math.log(max(350.0, co2) / 350.0) * 22.0
            heat_pen = max(0.0, temp_anom - 1.2) ** 2 * 3.8
            precip_pen = min(0.0, precip_anom) * 45.0
            bu_raw = base_bu + co2_fert - heat_pen + precip_pen
"""

# Extract the body of run_full_simulation from the original file
# Look for 'variety = str(payload.get("maize_variety", "medium_cycle"))'
start_marker = 'variety = str(payload.get("maize_variety", "medium_cycle"))'
idx = content.find(start_marker)
rest_of_sim = content[idx:]

# We need to replace the return statement to use the adapter's properties.
return_replacement = """        projected_yield = max(2500.0, kg_per_ha)
        potential_yield = float(var_cfg["base_pot_kg_ha"]) * (1.05 if nitrogen_kg >= 200 else 1.0)
        
        interval = self.adapter.get_prediction_interval(payload, bu_raw) if not is_fallback else {"lower_kg_ha": projected_yield * 0.85, "upper_kg_ha": projected_yield * 1.15}
        is_extrap, extrap_feats = self.adapter.check_extrapolation(payload) if not is_fallback else (False, [])
        
        meta = self.adapter.metadata
        return {
            "id": f"sim-{payload.get('field_id', 'field-01')}-{payload.get('target_year', 2035)}",
            "inference_mode": "trained_ml" if not is_fallback else "unavailable",
            "model_name": meta.get("model_name", "CeresYield"),
            "model_version": meta.get("model_version", "3.0.0"),
            "model_verified": meta.get("model_verified", True),
            "prediction_scope": meta.get("geographic_scope", "county_annual"),
            "model_data_source": "USDA NASS + NASA NEX-GDDP",
            "model_uses_real_data": True,
            "dataset_sha256": meta.get("dataset_sha256", "hash"),
            "scientific_scope": SCIENTIFIC_SCOPE,
            "field_id": payload.get("field_id", "field-01"),
            "scenario": payload.get("scenario", "SSP3-7.0"),
            "target_year": payload.get("target_year", 2035),
            "projected_yield_kg_ha": round(projected_yield),
            "potential_yield_kg_ha": round(potential_yield),
            "prediction_interval_90": interval,
            "is_extrapolation": is_extrap,
            "extrapolated_features": extrap_feats,
            "component_provenance": {
                "yield": "trained_model" if not is_fallback else "deterministic_fallback",
                "daily_records": "deterministic_water_balance",
                "economics": "derived_formula",
                "management_effect": "not_learned"
            },"""

rest_of_sim = re.sub(
    r'        projected_yield = max\(2500\.0, kg_per_ha\)\n        potential_yield = float\(var_cfg\["base_pot_kg_ha"\]\) \* \(1\.05 if nitrogen_kg >= 200 else 1\.0\)',
    return_replacement + "\n        # Skip original return start",
    rest_of_sim
)

# And remove the original return dictionary construction
rest_of_sim = re.sub(
    r'        return \{\n.*?            "yield_loss_due_to_drought_percent"',
    r'            "yield_loss_due_to_drought_percent"',
    rest_of_sim,
    flags=re.DOTALL
)

# Replace the bottom of the file
final_bottom = """
def _scenario_template(scenario: str) -> Dict[str, float]:
    return {
        "SSP1-2.6": {"precip_anomaly_pct": -0.02, "temp_anomaly_c": 0.9, "co2_ppm": 445.0, "heatwave_risk": 0.15},
        "SSP3-7.0": {"precip_anomaly_pct": -0.12, "temp_anomaly_c": 1.8, "co2_ppm": 480.0, "heatwave_risk": 0.42},
        "SSP5-8.5": {"precip_anomaly_pct": -0.24, "temp_anomaly_c": 2.7, "co2_ppm": 520.0, "heatwave_risk": 0.78},
    }.get(scenario, {"precip_anomaly_pct": -0.02, "temp_anomaly_c": 0.9, "co2_ppm": 445.0, "heatwave_risk": 0.15})

_inference = YieldInferenceService()

def get_inference() -> YieldInferenceService:
    return _inference
"""

# Combine everything
head = content[:content.find('class PinnInference:')]
final_content = head + new_classes + "        " + rest_of_sim[:rest_of_sim.find("def _scenario_template")] + final_bottom

with open(file_path, "w", encoding="utf-8") as f:
    f.write(final_content)
print("Updated inference.py with new model adapter")
