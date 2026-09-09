"""Pydantic data models for rainfall observations, nowcasting, and forecasts."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    REAL_OBSERVATION = "REAL_OBSERVATION"
    DEMO_SIMULATED = "DEMO-SIMULATED"
    SYNTHETIC_ML = "SYNTHETIC_ML"
    ILLUSTRATIVE = "ILLUSTRATIVE"


class RainfallPoint(BaseModel):
    """Represents rainfall intensity at a relative time offset."""
    offset_minutes: int = Field(..., ge=0, description="Time offset in minutes from generation timestamp")
    intensity_mm_per_hr: float = Field(..., ge=0.0, le=500.0, description="Rainfall intensity in mm/hr")
    timestamp: Optional[str] = Field(None, description="ISO-8601 formatted timestamp if available")


class CurrentRainfallResponse(BaseModel):
    """Response model for current rainfall observations and trend."""
    location: str = Field(..., description="Target urban area or catchment location")
    unit: str = Field(default="mm/hr", description="Measurement unit for rainfall rate")
    data_type: str = Field(default=DataSourceType.DEMO_SIMULATED.value, description="Classification of data origin")
    generated_at: str = Field(..., description="ISO timestamp when observation was recorded or simulated")
    current_intensity_mm_per_hr: float = Field(..., ge=0.0, description="Latest observed/simulated rainfall intensity")
    peak_intensity_mm_per_hr: float = Field(..., ge=0.0, description="Peak intensity observed across the current window")
    trend: str = Field(..., description="Rainfall trend direction: increasing, decreasing, peak, or stable")
    recent_observations: List[RainfallPoint] = Field(default_factory=list, description="Recent observation sequence")
    source_note: str = Field(
        default="Demo simulated data for prototyping; not a live radar observation.",
        description="Explicit provenance disclaimer"
    )


class ForecastResponse(BaseModel):
    """Response model for 0-3 hour nowcast rainfall forecast."""
    location: str = Field(..., description="Target urban area or catchment location")
    unit: str = Field(default="mm/hr", description="Measurement unit for rainfall rate")
    data_type: str = Field(default=DataSourceType.DEMO_SIMULATED.value, description="Classification of data origin")
    generated_at: str = Field(..., description="ISO timestamp when forecast was generated")
    forecast_horizon_minutes: int = Field(default=180, description="Forecast window span in minutes (e.g. 180 = 3 hours)")
    time_step_minutes: int = Field(default=30, description="Time step delta between forecast intervals")
    forecast_series: List[RainfallPoint] = Field(..., description="Nowcast forecast points across horizon")
    peak_forecast_intensity_mm_per_hr: float = Field(..., ge=0.0, description="Maximum predicted rainfall intensity")
    peak_forecast_offset_minutes: int = Field(..., ge=0, description="Offset in minutes when peak intensity occurs")
    source_note: str = Field(
        default="Demo simulated nowcast curve for prototyping; not live meteorological radar output.",
        description="Explicit provenance disclaimer"
    )
