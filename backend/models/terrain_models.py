"""Pydantic data models for terrain elevation, catchment zones, and surface runoff calculations."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RunoffTendency(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class TerrainZoneModel(BaseModel):
    """Represents a catchment zone or street terrain profile."""
    zone_id: str = Field(..., description="Unique zone identifier")
    name: str = Field(..., description="Human-readable zone or street name")
    elevation_m: float = Field(..., description="Mean elevation in meters above sea level")
    slope_percent: float = Field(..., ge=0.0, description="Surface slope percentage (gradient)")
    flow_accumulation: int = Field(..., ge=0, description="Upstream flow accumulation cell count")
    imperviousness: float = Field(..., ge=0.0, le=1.0, description="Fraction of impermeable surfaces (0.0 - 1.0)")
    area_hectares: float = Field(..., gt=0.0, description="Zone drainage catchment area in hectares")
    is_low_lying: bool = Field(..., description="Whether the area sits in a topographical depression")
    soil_type: Optional[str] = Field(None, description="Dominant soil or surface cover classification")


class TerrainOverviewResponse(BaseModel):
    """Response containing all registered terrain zones and catchment attributes."""
    location: str = Field(..., description="Target urban area name")
    data_type: str = Field(default="DEMO-SIMULATED", description="Data provenance classification")
    generated_at: str = Field(..., description="Timestamp of generation")
    zone_count: int = Field(..., description="Total number of catchment zones")
    zones: List[TerrainZoneModel] = Field(..., description="List of terrain zones")
    source_note: str = Field(
        default="Synthetic digital elevation model (DEM) and catchment data for prototype demonstration. Not municipal GIS survey.",
        description="Data disclaimer"
    )


class ZoneRunoffResult(BaseModel):
    """Calculated surface runoff parameters for an individual catchment zone."""
    zone_id: str = Field(..., description="Zone identifier")
    name: str = Field(..., description="Zone or street name")
    elevation_m: float = Field(..., description="Elevation in meters")
    slope_percent: float = Field(..., description="Surface slope percentage")
    imperviousness: float = Field(..., description="Surface imperviousness fraction")
    area_hectares: float = Field(..., description="Catchment area in hectares")
    runoff_coefficient_c: float = Field(..., ge=0.0, le=1.0, description="Calculated composite Rational runoff coefficient C")
    rainfall_intensity_mm_hr: float = Field(..., ge=0.0, description="Rainfall intensity applied in mm/hr")
    runoff_rate_mm_hr: float = Field(..., ge=0.0, description="Effective surface runoff generation rate in mm/hr")
    peak_discharge_m3_s: float = Field(..., ge=0.0, description="Calculated peak runoff discharge Q in m3/s")
    runoff_tendency: RunoffTendency = Field(..., description="Categorical classification of runoff tendency")
    accumulation_index: float = Field(..., ge=0.0, le=1.0, description="Relative flow accumulation index (0.0 - 1.0)")
    flood_prone_index: float = Field(..., ge=0.0, le=1.0, description="Composite terrain vulnerability index (0.0 - 1.0)")
    is_low_lying: bool = Field(..., description="Flag indicating low-lying depression")


class RunoffCalculationRequest(BaseModel):
    """Optional request payload for custom runoff scenario calculations."""
    rainfall_intensity_mm_hr: Optional[float] = Field(None, ge=0.0, le=500.0, description="Override rainfall intensity in mm/hr")
    zone_ids: Optional[List[str]] = Field(None, description="Optional subset of zone IDs to calculate")


class RunoffOverviewResponse(BaseModel):
    """Complete runoff calculation response across urban catchment zones."""
    location: str = Field(..., description="Target urban area name")
    data_type: str = Field(default="DEMO-SIMULATED", description="Data provenance classification")
    rainfall_intensity_used_mm_hr: float = Field(..., description="Rainfall intensity applied in calculation")
    total_discharge_m3_s: float = Field(..., description="Summed peak runoff discharge across evaluated zones in m3/s")
    highest_risk_zones: List[str] = Field(default_factory=list, description="Zones exhibiting SEVERE or HIGH runoff tendencies")
    methodology: str = Field(default="Rational Method: Q = (C * I * A) / 360", description="Hydrological formula applied")
    assumptions: List[str] = Field(default_factory=list, description="Explicit hydrological assumptions")
    results: List[ZoneRunoffResult] = Field(..., description="Zone-by-zone calculated runoff and accumulation results")
    source_note: str = Field(
        default="Synthetic runoff calculations for prototype demonstration. Not engineering hydraulic certification.",
        description="Data provenance disclaimer"
    )
