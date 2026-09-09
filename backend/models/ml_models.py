"""Pydantic data models for machine learning flood predictions, model metadata, and status metrics."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.flood_models import FloodRiskLevel


class MLModelStatus(BaseModel):
    """Metadata and validation performance indicators for the trained ML ensemble."""
    model_loaded: bool = Field(..., description="True if models are initialized and in memory")
    model_type: str = Field(
        default="RandomForestRegressor + RandomForestClassifier (scikit-learn)",
        description="Underlying machine learning model family"
    )
    training_samples: int = Field(..., description="Number of synthetic hydrological samples used in training")
    features: List[str] = Field(..., description="Ordered list of feature names used for inference")
    validation_metrics: Dict[str, float] = Field(..., description="Evaluation metrics computed on synthetic validation split")
    trained_at: str = Field(..., description="ISO timestamp when model was fitted")
    data_provenance: str = Field(
        default="SYNTHETIC ML TRAINING DATA",
        description="Data provenance disclosure"
    )
    disclaimer: str = Field(
        default="Trained on synthetic hydrological simulation curves for prototype demonstration. Does not reflect real-world physical validation.",
        description="Explicit limitation statement"
    )


class ZoneMLPrediction(BaseModel):
    """Machine learning predicted flood depth, hazard probability, and confidence for a catchment zone."""
    zone_id: str = Field(..., description="Catchment zone identifier")
    name: str = Field(..., description="Street or corridor name")
    predicted_flood_depth_cm: float = Field(..., ge=0.0, description="ML predicted surface flood depth in cm")
    predicted_risk_level: FloodRiskLevel = Field(..., description="Predicted hazard category (LOW, MODERATE, HIGH, SEVERE)")
    flood_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of hazardous street ponding (>= 15 cm)")
    model_confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence indicator (0.0 to 1.0)")
    physics_baseline_depth_cm: float = Field(..., ge=0.0, description="Baseline flood depth from physics/rule-based engine in cm")
    physics_risk_level: FloodRiskLevel = Field(..., description="Baseline risk category from physics engine")
    delta_depth_cm: float = Field(..., description="Difference between ML predicted depth and physics baseline depth in cm")
    model_type: str = Field(
        default="RandomForestRegressor + RandomForestClassifier",
        description="Model architecture"
    )
    data_provenance: str = Field(
        default="ML-DERIVED FROM SYNTHETICALLY TRAINED MODEL USING DEMO-SIMULATED INPUTS",
        description="Data provenance statement"
    )


class MLPredictionResponse(BaseModel):
    """Full API response schema for ML flood prediction endpoint."""
    location: str = Field(..., description="Urban catchment location")
    timestamp: str = Field(..., description="Inference timestamp")
    data_type: str = Field(
        default="ML-DERIVED FROM SYNTHETICALLY TRAINED MODEL USING DEMO-SIMULATED INPUTS",
        description="Data classification"
    )
    model_type: str = Field(
        default="RandomForestRegressor + RandomForestClassifier",
        description="Model architecture"
    )
    total_zones_predicted: int = Field(..., description="Count of zones evaluated")
    high_risk_zones: List[str] = Field(default_factory=list, description="Zones predicted as HIGH or SEVERE flood risk")
    predictions: List[ZoneMLPrediction] = Field(..., description="Zone-by-zone ML predictions")
    features_used: List[str] = Field(..., description="Features ingested by the ML model")
    source_note: str = Field(
        default="ML model complements the physics-based flood engine; trained on synthetic hydrology simulation data.",
        description="Methodological transparency note"
    )
    limitation_note: str = Field(
        default="Synthetic ML prototype model. Predictions are intended for demonstration and decision support prototyping, not operational emergency deployment.",
        description="Limitations disclosure"
    )
