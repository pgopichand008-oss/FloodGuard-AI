"""Pydantic data models for Phase 8 WHAT-IF flood simulation, scenario requests, and baseline comparisons."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from backend.models.flood_models import FloodRiskLevel


class SimulationImpact(str, Enum):
    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    WORSENED = "WORSENED"


class SimulationRequest(BaseModel):
    """What-if simulation scenario specification."""
    rainfall_mm_hr: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Simulated rainfall intensity in mm/hr (minimum 0.0)"
    )
    blockage_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Simulated conduit blockage percentage (0.0 to 100.0)"
    )
    zone_id: Optional[str] = Field(
        default=None,
        description="Optional catchment zone ID filter (e.g. Z01)"
    )

    @model_validator(mode="after")
    def check_at_least_one_parameter(self) -> "SimulationRequest":
        """Requires at least one simulation scenario parameter."""
        if self.rainfall_mm_hr is None and self.blockage_percent is None:
            raise ValueError(
                "At least one simulation parameter ('rainfall_mm_hr' or 'blockage_percent') must be provided."
            )
        return self


class ZoneSimulationComparison(BaseModel):
    """Direct comparison between baseline and simulated conditions for an individual zone."""
    zone_id: str = Field(..., description="Catchment zone identifier")
    name: str = Field(..., description="Catchment corridor or street name")
    baseline_flood_depth_cm: float = Field(..., ge=0.0, description="Baseline flood depth in cm")
    simulated_flood_depth_cm: float = Field(..., ge=0.0, description="Simulated scenario flood depth in cm")
    depth_change_cm: float = Field(..., description="Difference: simulated_depth - baseline_depth (cm)")
    baseline_risk_level: FloodRiskLevel = Field(..., description="Baseline risk category")
    simulated_risk_level: FloodRiskLevel = Field(..., description="Simulated risk category")
    baseline_rainfall_mm_hr: float = Field(..., ge=0.0, description="Baseline rainfall rate in mm/hr")
    simulated_rainfall_mm_hr: float = Field(..., ge=0.0, description="Simulated scenario rainfall rate in mm/hr")
    baseline_drainage_utilization_percent: float = Field(..., ge=0.0, description="Baseline pipe capacity utilization %")
    simulated_drainage_utilization_percent: float = Field(..., ge=0.0, description="Simulated pipe capacity utilization %")
    baseline_blockage_percent: float = Field(..., ge=0.0, le=100.0, description="Baseline pipe blockage %")
    simulated_blockage_percent: float = Field(..., ge=0.0, le=100.0, description="Simulated pipe blockage %")
    baseline_excess_flow_m3s: float = Field(..., ge=0.0, description="Baseline uncontained surcharge in m3/s")
    simulated_excess_flow_m3s: float = Field(..., ge=0.0, description="Simulated uncontained surcharge in m3/s")
    impact: SimulationImpact = Field(..., description="Categorical impact assessment: IMPROVED, UNCHANGED, WORSENED")
    impact_summary: str = Field(..., description="Human-readable synthesis of scenario hydraulic impact")


class SimulationSummary(BaseModel):
    """Aggregate catchment-level simulation impact metrics."""
    total_zones_simulated: int = Field(..., description="Number of zones evaluated in scenario")
    zones_improved: int = Field(..., description="Count of zones where flood depth decreased")
    zones_unchanged: int = Field(..., description="Count of zones where flood depth remained constant")
    zones_worsened: int = Field(..., description="Count of zones where flood depth increased")
    max_depth_change_cm: float = Field(..., description="Maximum depth difference across all simulated zones (cm)")
    avg_depth_change_cm: float = Field(..., description="Average depth difference across all simulated zones (cm)")


class SimulationResponse(BaseModel):
    """Complete API response for WHAT-IF flood scenario simulation."""
    scenario_name: str = Field(..., description="Concise label describing the scenario evaluated")
    scenario_description: str = Field(..., description="Detailed narrative of scenario assumptions")
    timestamp: str = Field(..., description="Timestamp when simulation was executed")
    location: str = Field(..., description="Catchment location")
    parameters_applied: Dict[str, Any] = Field(..., description="Simulation inputs applied")
    summary: SimulationSummary = Field(..., description="Catchment summary impact statistics")
    results: List[ZoneSimulationComparison] = Field(..., description="Zone-by-zone comparison results")
    data_provenance: str = Field(
        default="SCENARIO SIMULATION USING MODEL-DERIVED FLOOD AND DEMO INPUTS",
        description="Data provenance disclosure"
    )
    disclaimer: str = Field(
        default="What-if simulation system for decision support. Results are model-derived from simulated inputs and not verified for real-world emergency deployment.",
        description="Simulation limitation disclaimer"
    )
