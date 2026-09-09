"""Pydantic data models for the WHY-FLOOD Explainability Engine, factor attribution, and API responses."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.flood_models import FloodRiskLevel


class FactorSeverity(str, Enum):
    NEGLIGIBLE = "NEGLIGIBLE"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ContributionLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ContributingFactor(BaseModel):
    """Specific environmental or hydraulic driver contributing to flood risk."""
    factor: str = Field(..., description="Name of the contributing driver (e.g. Drainage Utilization)")
    severity: FactorSeverity = Field(..., description="Assessed severity level of this factor")
    value: float = Field(..., description="Observed or simulated numerical magnitude")
    unit: str = Field(..., description="Measurement unit (e.g. mm/hr, %, m, m3/s, cm)")
    threshold: Optional[float] = Field(default=None, description="Engineering benchmark or warning threshold")
    contribution_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized attribution score (0.0 = none, 1.0 = dominant)"
    )
    contribution: ContributionLevel = Field(..., description="Categorical impact rating")
    explanation: str = Field(..., description="Contextual explanation of how this driver influences inundation")


class ZoneExplanation(BaseModel):
    """Comprehensive WHY-FLOOD explainability profile for a single catchment zone."""
    zone_id: str = Field(..., description="Unique catchment zone identifier")
    name: str = Field(..., description="Catchment or corridor name")
    risk_level: FloodRiskLevel = Field(..., description="Predicted categorical flood risk level")
    flood_depth_cm: float = Field(..., ge=0.0, description="Estimated surface flood depth in cm")
    primary_cause: str = Field(..., description="Dominant primary driver derived from attribution scoring")
    secondary_cause: Optional[str] = Field(default=None, description="Secondary contributing factor if significant")
    summary_explanation: str = Field(..., description="Synthesized human-readable explanation for operational authorities")
    contributing_factors: List[ContributingFactor] = Field(
        ..., description="Ordered list of contributing drivers sorted by contribution score"
    )
    evidence: Dict[str, Any] = Field(
        ..., description="Complete dictionary of underlying hydraulic, terrain, and rainfall metrics"
    )
    ml_insights: Optional[Dict[str, Any]] = Field(
        default=None, description="ML ensemble predictions, flood probability, and physics agreement"
    )
    data_provenance: str = Field(
        default="RULE-BASED EXPLANATION FROM MODEL-DERIVED AND DEMO-SIMULATED INPUTS",
        description="Data provenance disclosure"
    )
    methodology_note: str = Field(
        default="Transparent multi-factor engineering attribution scoring. Does not claim formal empirical causal proof.",
        description="Methodological transparency disclosure"
    )


class ExplanationResponse(BaseModel):
    """Complete API response payload for urban catchment flood explainability."""
    location: str = Field(..., description="Catchment jurisdiction or city area")
    timestamp: str = Field(..., description="Timestamp of explainability evaluation")
    total_zones_explained: int = Field(..., description="Number of zones analyzed")
    primary_causes_summary: Dict[str, int] = Field(
        ..., description="Aggregation of primary causes identified across all zones"
    )
    explanations: List[ZoneExplanation] = Field(..., description="Zone-by-zone explainability profiles")
    data_provenance: str = Field(
        default="RULE-BASED EXPLANATION FROM MODEL-DERIVED AND DEMO-SIMULATED INPUTS",
        description="Data provenance disclosure"
    )
    disclaimer: str = Field(
        default="Transparent rule-based explainability layer for operational decision support. Explanations reflect model-derived and demo-simulated hydraulic indicators.",
        description="Disclaimer note"
    )
