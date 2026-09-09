"""Pydantic data models for flood prediction, depth calculation, risk assessment, and summary metrics."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FloodRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class ForecastTimePoint(BaseModel):
    """Temporal nowcast forecast step for flood depth progression."""
    minutes: int = Field(..., ge=0, description="Time offset in minutes")
    depth_cm: float = Field(..., ge=0.0, description="Predicted peak/average flood depth in cm")


class ZoneFloodPrediction(BaseModel):
    """Detailed street or catchment zone flood prediction metrics."""
    zone_id: str = Field(..., description="Unique zone identifier")
    name: str = Field(..., description="Street or catchment corridor name")
    latitude: float = Field(..., description="Geographical latitude")
    longitude: float = Field(..., description="Geographical longitude")
    elevation_m: float = Field(..., description="Surface elevation in meters")
    slope_percent: float = Field(..., description="Terrain gradient percentage")
    is_low_lying: bool = Field(..., description="True if zone sits in a depression")
    rainfall_intensity_mm_hr: float = Field(..., ge=0.0, description="Applied rainfall intensity in mm/hr")
    runoff_discharge_m3s: float = Field(..., ge=0.0, description="Calculated surface runoff peak discharge in m3/s")
    drainage_capacity_m3s: float = Field(..., ge=0.0, description="Underground design conduit capacity in m3/s")
    drainage_effective_capacity_m3s: float = Field(..., ge=0.0, description="Available capacity after blockage in m3/s")
    drainage_utilization_percent: float = Field(..., ge=0.0, description="Conduit hydraulic utilization percentage")
    blockage_percent: float = Field(..., ge=0.0, le=100.0, description="Drainage conduit blockage percentage")
    excess_flow_m3s: float = Field(..., ge=0.0, description="Uncontained surcharge overflow rate in m3/s")
    is_surcharged: bool = Field(..., description="True if conduit flow exceeds effective capacity")
    flood_depth_cm: float = Field(..., ge=0.0, description="Current estimated surface water depth in cm")
    peak_depth_cm: float = Field(..., ge=0.0, description="Predicted peak flood depth in cm during storm event")
    onset_minutes: int = Field(..., ge=0, description="Estimated minutes until surface ponding reaches hazardous depth")
    risk_level: FloodRiskLevel = Field(..., description="Categorical flood risk classification")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Model quality/confidence indicator")
    data_source: str = Field(
        default="MODEL-DERIVED FROM DEMO-SIMULATED INPUTS",
        description="Data provenance classification"
    )
    source_note: str = Field(
        default="Physics-informed prototype coupling rainfall, terrain runoff, and pipe surcharge. Not municipal certified.",
        description="Provenance note"
    )


class FloodSummaryModel(BaseModel):
    """Aggregated urban flood intelligence summary."""
    total_zones: int = Field(..., description="Total catchment zones analyzed")
    low_risk_zones: int = Field(..., description="Count of zones classified as LOW risk")
    moderate_risk_zones: int = Field(..., description="Count of zones classified as MODERATE risk")
    high_risk_zones: int = Field(..., description="Count of zones classified as HIGH risk")
    severe_risk_zones: int = Field(..., description="Count of zones classified as SEVERE risk")
    max_flood_depth_cm: float = Field(..., ge=0.0, description="Maximum predicted surface depth across all zones")
    avg_flood_depth_cm: float = Field(..., ge=0.0, description="Average predicted surface depth across all zones")
    max_drainage_utilization_percent: float = Field(..., ge=0.0, description="Peak conduit capacity utilization in network")
    surcharged_segments_count: int = Field(..., description="Number of drainage conduits operating above capacity")
    affected_roads_count: int = Field(..., description="Count of roads experiencing hazardous ponding (>15 cm)")
    critical_drainage_nodes_count: int = Field(..., description="Number of drainage nodes in critical or surcharged state")


class FloodPredictionResponse(BaseModel):
    """Comprehensive flood intelligence API response schema."""
    location: str = Field(..., description="Urban catchment area name")
    timestamp: str = Field(..., description="Calculation timestamp")
    data_type: str = Field(
        default="MODEL-DERIVED FROM DEMO-SIMULATED INPUTS",
        description="Data provenance classification"
    )
    # Backward compatibility fields for Member 1 frontend contract
    rainfall: Dict[str, Any] = Field(..., description="Rainfall summary state")
    flood: Dict[str, Any] = Field(..., description="Baseline flood summary contract")
    forecast: List[ForecastTimePoint] = Field(..., description="Temporal nowcast depth forecast sequence")
    # Extended Phase 5 intelligence fields
    summary: FloodSummaryModel = Field(..., description="Aggregated flood and drainage operational summary")
    zones: List[ZoneFloodPrediction] = Field(..., description="Zone-by-zone calculated flood depth and hydraulic metrics")
    methodology: str = Field(
        default="Physics-informed coupling: Rational Method Runoff + Surcharge Capacity Balance",
        description="Mathematical methodology summary"
    )
    assumptions: List[str] = Field(default_factory=list, description="Explicit hydrological assumptions")
    limitation_note: str = Field(
        default="Prototype flood intelligence model for demonstration. Surcharge depth uses capacity thresholding; not 2D hydrodynamic wave routing.",
        description="Limitations disclosure"
    )
