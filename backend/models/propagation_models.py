"""Pydantic data models for Phase 10 Flood Propagation Engine."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.flood_models import FloodRiskLevel


class PropagationRelationship(str, Enum):
    SOURCE = "SOURCE"
    DIRECTLY_AFFECTED = "DIRECTLY_AFFECTED"
    DOWNSTREAM = "DOWNSTREAM"
    OVERLAND_SPILLOVER = "OVERLAND_SPILLOVER"
    BACKPRESSURE = "BACKPRESSURE"


class PropagationSourceModel(BaseModel):
    """Source node or zone originating flood propagation."""
    node_id: Optional[str] = Field(default=None, description="Drainage node ID if tied to infrastructure")
    zone_id: str = Field(..., description="Source catchment zone ID")
    name: str = Field(..., description="Source corridor or street name")
    risk: FloodRiskLevel = Field(..., description="Source flood risk classification")
    flood_depth_cm: float = Field(..., ge=0.0, description="Surface flood depth at source in cm")
    drainage_utilization_percent: float = Field(default=0.0, description="Conduit flow capacity utilization %")
    is_surcharged: bool = Field(default=False, description="True if source conduit is surcharged")


class PropagationStepModel(BaseModel):
    """Sequential step in the flood propagation chain."""
    order: int = Field(..., ge=1, description="Sequence in propagation chain (1 = first directly affected)")
    zone_id: str = Field(..., description="Affected zone identifier")
    name: str = Field(..., description="Affected street or corridor name")
    relationship: str = Field(..., description="Hydraulic or spatial relationship (e.g. DIRECTLY_AFFECTED, DOWNSTREAM)")
    risk: FloodRiskLevel = Field(..., description="Current flood risk classification of affected zone")
    flood_depth_cm: float = Field(..., ge=0.0, description="Current surface water depth in cm")
    elevation_m: float = Field(..., description="Surface elevation in meters")
    mechanism: str = Field(..., description="Hydraulic transmission mechanism (e.g. overland flow, pipe backpressure)")


class ZonePropagationResponse(BaseModel):
    """Flood propagation chain radiating from a specific source zone."""
    zone_id: str = Field(..., description="Target or origin zone ID")
    source: PropagationSourceModel = Field(..., description="Propagation origin attributes")
    propagation: List[PropagationStepModel] = Field(..., description="Ordered list of connected affected zones")
    affected_zone_count: int = Field(..., description="Count of downstream/connected zones in propagation chain")
    propagation_path: List[str] = Field(..., description="Human-readable corridor chain in traversal sequence")
    provenance: str = Field(
        default="PROPAGATION DERIVED FROM DEMO-SIMULATED FLOOD AND DRAINAGE DATA",
        description="Data provenance disclosure"
    )
    disclaimer: str = Field(
        default="Illustrative flood propagation network for prototype decision support and visualization. Not based on certified 2D overland hydrodynamic modeling.",
        description="Operational limitation disclosure"
    )


class CatchmentPropagationResponse(BaseModel):
    """Catchment-wide propagation analysis across all urban zones."""
    location: str = Field(..., description="Catchment location name")
    timestamp: str = Field(..., description="Evaluation timestamp")
    total_sources: int = Field(..., description="Total catchment zones analyzed as potential propagation sources")
    propagations: List[ZonePropagationResponse] = Field(..., description="Propagation chains per zone")
    provenance: str = Field(
        default="PROPAGATION DERIVED FROM DEMO-SIMULATED FLOOD AND DRAINAGE DATA",
        description="Data provenance disclosure"
    )
    disclaimer: str = Field(
        default="Illustrative flood propagation network for prototype decision support and visualization. Not based on certified 2D overland hydrodynamic modeling.",
        description="Operational limitation disclosure"
    )
