"""Pydantic data models for Phase 9 Action Priority and Decision Engine."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.flood_models import FloodRiskLevel


class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ZonePriority(BaseModel):
    """Action priority evaluation, intervention ranking, and recommended measures for a catchment zone."""
    zone_id: str = Field(..., description="Unique catchment zone identifier")
    zone_name: str = Field(..., description="Zone or street corridor name")
    rank: int = Field(..., ge=1, description="Priority ranking position (1 = highest urgency)")
    priority_score: float = Field(
        ..., ge=0.0, le=100.0, description="Normalized multi-criteria priority score (0.0 to 100.0)"
    )
    priority_level: PriorityLevel = Field(..., description="Categorical intervention urgency level")
    flood_depth_cm: float = Field(..., ge=0.0, description="Estimated surface inundation depth in cm")
    risk_level: FloodRiskLevel = Field(..., description="Categorical flood risk level")
    drainage_utilization_percent: float = Field(..., ge=0.0, description="Drainage capacity utilization percentage")
    blockage_percent: float = Field(..., ge=0.0, le=100.0, description="Conduit physical blockage percentage")
    excess_flow_m3s: float = Field(..., ge=0.0, description="Uncontained drainage surcharge rate in m3/s")
    is_surcharged: bool = Field(..., description="True if conduit flow exceeds effective capacity")
    recommended_action: str = Field(..., description="Specific operational action recommended for municipal crews")
    reason: str = Field(..., description="Concise explanation justifying the assigned priority")
    score_breakdown: Dict[str, float] = Field(
        ..., description="Component sub-scores contributing to overall priority score"
    )
    data_provenance: str = Field(
        default="DECISION PRIORITY DERIVED FROM MODEL-DERIVED FLOOD, DRAINAGE AND DEMO INPUTS",
        description="Data provenance disclosure"
    )


class PrioritySummary(BaseModel):
    """Catchment-wide aggregation of priority interventions."""
    total_zones: int = Field(..., description="Total catchment zones evaluated")
    critical_count: int = Field(..., description="Number of zones categorized as CRITICAL priority")
    high_count: int = Field(..., description="Number of zones categorized as HIGH priority")
    medium_count: int = Field(..., description="Number of zones categorized as MEDIUM priority")
    low_count: int = Field(..., description="Number of zones categorized as LOW priority")
    top_priority_zone_id: Optional[str] = Field(default=None, description="Zone ID with highest priority score")
    highest_priority_score: float = Field(default=0.0, description="Maximum priority score observed")


class PriorityResponse(BaseModel):
    """Complete API response for action priority decision support."""
    location: str = Field(..., description="Catchment jurisdiction or area name")
    timestamp: str = Field(..., description="Inference and ranking timestamp")
    summary: PrioritySummary = Field(..., description="Summary statistics of priority counts")
    priorities: List[ZonePriority] = Field(..., description="Ranked zone priorities ordered descending by score")
    data_provenance: str = Field(
        default="DECISION PRIORITY DERIVED FROM MODEL-DERIVED FLOOD, DRAINAGE AND DEMO INPUTS",
        description="Data provenance disclosure"
    )
    disclaimer: str = Field(
        default="Decision-support prototype. Action priorities are algorithmic recommendations based on simulated hydraulic indicators, not official emergency dispatch authorizations.",
        description="Disclaimer note"
    )
