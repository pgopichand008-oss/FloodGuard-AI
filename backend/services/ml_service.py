"""ML coordination service mediating between physics pipeline features and ML inference engine."""
from datetime import datetime, timezone
from typing import List, Optional

from backend.engines.ml_engine import MLEngine, default_ml_engine
from backend.models.flood_models import FloodRiskLevel
from backend.models.ml_models import (
    MLModelStatus,
    MLPredictionResponse,
    ZoneMLPrediction,
)
from backend.services.flood_service import FloodService, default_flood_service


class MLServiceError(Exception):
    """Base exception for ML service failures."""
    pass


class MLService:
    """Coordinates feature extraction from the existing FloodGuard pipeline and runs ML inference."""

    def __init__(
        self,
        ml_engine: Optional[MLEngine] = None,
        flood_service: Optional[FloodService] = None,
    ):
        self.ml_engine = ml_engine or default_ml_engine
        self.flood_service = flood_service or default_flood_service

    def get_predictions(
        self,
        rainfall_override_mm_hr: Optional[float] = None,
        zone_id: Optional[str] = None,
    ) -> MLPredictionResponse:
        """Extracts features from the integrated flood pipeline and executes ML ensemble inference."""
        # 1. Fetch live physics baseline predictions from FloodService
        flood_resp = self.flood_service.get_predictions(
            rainfall_override_mm_hr=rainfall_override_mm_hr,
            zone_id=zone_id,
        )

        # 2. Forecast peak rainfall for feature vector
        peak_rain = float(flood_resp.rainfall.get("peak_mm_per_hr", flood_resp.rainfall.get("current_mm_per_hr", 86.0)))

        predictions: List[ZoneMLPrediction] = []
        high_risk_zones: List[str] = []

        for z in flood_resp.zones:
            feature_dict = {
                "rainfall_intensity_mm_hr": z.rainfall_intensity_mm_hr,
                "forecast_peak_rainfall_mm_hr": peak_rain,
                "elevation_m": z.elevation_m,
                "slope_percent": z.slope_percent,
                "flow_accumulation": float(1850 if z.is_low_lying else 500),  # Derived from terrain
                "imperviousness": 0.85 if z.is_low_lying else 0.50,
                "runoff_coefficient_c": 0.82 if z.is_low_lying else 0.45,
                "runoff_discharge_m3_s": z.runoff_discharge_m3s,
                "is_low_lying": 1.0 if z.is_low_lying else 0.0,
                "drainage_capacity_m3s": z.drainage_capacity_m3s,
                "drainage_effective_capacity_m3s": z.drainage_effective_capacity_m3s,
                "drainage_utilization_percent": z.drainage_utilization_percent,
                "blockage_percent": z.blockage_percent,
                "excess_flow_m3s": z.excess_flow_m3s,
                "physics_flood_depth_cm": z.flood_depth_cm,
            }

            pred_depth, pred_risk, prob, conf = self.ml_engine.predict_zone(feature_dict)
            delta = round(pred_depth - z.flood_depth_cm, 1)

            pred_model = ZoneMLPrediction(
                zone_id=z.zone_id,
                name=z.name,
                predicted_flood_depth_cm=pred_depth,
                predicted_risk_level=pred_risk,
                flood_probability=prob,
                model_confidence=conf,
                physics_baseline_depth_cm=z.flood_depth_cm,
                physics_risk_level=z.risk_level,
                delta_depth_cm=delta,
                model_type="RandomForestRegressor + RandomForestClassifier",
                data_provenance="ML-DERIVED FROM SYNTHETICALLY TRAINED MODEL USING DEMO-SIMULATED INPUTS"
            )
            predictions.append(pred_model)

            if pred_risk in [FloodRiskLevel.HIGH, FloodRiskLevel.SEVERE]:
                high_risk_zones.append(f"{z.name} ({z.zone_id})")

        now_iso = datetime.now(timezone.utc).isoformat()

        return MLPredictionResponse(
            location=flood_resp.location,
            timestamp=now_iso,
            data_type="ML-DERIVED FROM SYNTHETICALLY TRAINED MODEL USING DEMO-SIMULATED INPUTS",
            model_type="RandomForestRegressor + RandomForestClassifier (scikit-learn)",
            total_zones_predicted=len(predictions),
            high_risk_zones=high_risk_zones,
            predictions=predictions,
            features_used=self.ml_engine.FEATURE_NAMES,
            source_note="ML model complements the physics-based flood engine; trained on synthetic hydrology simulation curves.",
            limitation_note="Synthetic ML prototype model. Predictions are intended for demonstration and decision support prototyping, not operational emergency deployment."
        )

    def get_status(self) -> MLModelStatus:
        """Retrieves model status, hyperparameters, and synthetic validation scores."""
        return self.ml_engine.get_status()


# Global singleton instance
default_ml_service = MLService()
