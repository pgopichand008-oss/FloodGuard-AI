"""Pydantic data models for flood-aware safe routing, route segments, and route safety metrics."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.models.flood_models import FloodRiskLevel


class RouteStatus(str, Enum):
    """Overall status assessment of the calculated route."""
    SAFE_ROUTE = "SAFE_ROUTE"
    CAUTION_ROUTE = "CAUTION_ROUTE"
    NO_SAFE_ROUTE = "NO_SAFE_ROUTE"


class SegmentSafetyStatus(str, Enum):
    """Passability classification for individual road segments."""
    PASSABLE = "PASSABLE"
    CAUTION = "CAUTION"
    UNSAFE = "UNSAFE"


class RouteSegmentDetail(BaseModel):
    """Evaluation metrics for an individual leg of a travel route."""
    from_zone_id: str = Field(..., description="Origin zone of the road segment")
    to_zone_id: str = Field(..., description="Destination zone of the road segment")
    street_name: str = Field(..., description="Corridor or street segment description")
    distance_m: float = Field(..., ge=0.0, description="Base physical length of road segment in meters")
    flood_depth_cm: float = Field(..., ge=0.0, description="Predicted surface water depth in cm")
    risk_level: FloodRiskLevel = Field(..., description="Categorical flood risk classification")
    is_surcharged: bool = Field(..., description="True if underlying drainage conduit is surcharging")
    drainage_utilization_percent: float = Field(..., ge=0.0, description="Conduit capacity utilization percentage")
    blockage_percent: float = Field(..., ge=0.0, le=100.0, description="Conduit sediment blockage percentage")
    segment_cost: float = Field(..., ge=0.0, description="Composite flood-penalized traversal cost")
    safety_status: SegmentSafetyStatus = Field(..., description="Operational passability status")


class RouteRequest(BaseModel):
    """Request payload for finding a flood-safe route between two points."""
    origin: str = Field(..., description="Origin zone or drainage node ID (e.g. Z01, Z03, N02, N21)")
    destination: str = Field(..., description="Destination zone or drainage node ID (e.g. Z05, Z08, N01)")
    emergency: bool = Field(
        default=False,
        description="Enable emergency vehicle routing prioritization (higher clearance, critical corridor access)"
    )
    rainfall_mm_hr: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Optional scenario rainfall intensity override in mm/hr"
    )


class RouteResponse(BaseModel):
    """Structured response containing optimal flood-safe route and safety evaluations."""
    origin: str = Field(..., description="Supplied origin identifier")
    destination: str = Field(..., description="Supplied destination identifier")
    origin_zone_id: str = Field(..., description="Resolved standard origin zone ID")
    destination_zone_id: str = Field(..., description="Resolved standard destination zone ID")
    status: RouteStatus = Field(..., description="Route safety status (SAFE_ROUTE, CAUTION_ROUTE, NO_SAFE_ROUTE)")
    route: List[str] = Field(..., description="Ordered list of zone IDs along the selected route")
    route_names: List[str] = Field(..., description="Ordered human-readable street/corridor names along the route")
    total_distance_m: float = Field(..., ge=0.0, description="Total physical road distance in meters")
    total_cost: float = Field(..., ge=0.0, description="Total flood-aware navigation cost")
    flood_risk: FloodRiskLevel = Field(..., description="Highest flood risk encountered on the selected route")
    max_flood_depth_cm: float = Field(..., ge=0.0, description="Maximum surface flood depth encountered along route in cm")
    avg_flood_depth_cm: float = Field(..., ge=0.0, description="Average surface flood depth along route in cm")
    unsafe_segments_avoided: List[str] = Field(
        default_factory=list,
        description="Zones or road corridors deliberately avoided due to high flood, surcharge, or blockage"
    )
    segments: List[RouteSegmentDetail] = Field(
        default_factory=list,
        description="Detailed leg-by-leg metrics along the selected route"
    )
    is_emergency: bool = Field(..., description="Whether emergency vehicle routing rules were applied")
    reason: str = Field(..., description="Human-readable decision explanation for route selection or unavailability")
    data_source: str = Field(
        default="MODEL-DERIVED FROM DEMO-SIMULATED INPUTS",
        description="Data provenance classification"
    )
    provenance: str = Field(
        default="Routing derived from model-derived flood and drainage outputs using DEMO-SIMULATED DATA and ILLUSTRATIVE CONNECTIVITY.",
        description="Data provenance disclosure"
    )
    mapping_disclaimer: str = Field(
        default="Google Maps or another map provider may be used for visualization/base road information, but FloodGuard determines flood safety using its own flood intelligence.",
        description="Mapping authority disclaimer"
    )
