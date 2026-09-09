"""Flood coordination service mediating between rainfall, terrain, drainage, and flood engine."""
from typing import Optional
from backend.engines.flood_engine import FloodEngine, default_flood_engine
from backend.models.flood_models import (
    FloodPredictionResponse,
    FloodRiskLevel,
    ZoneFloodPrediction,
)


class FloodServiceError(Exception):
    """Base exception for flood prediction service errors."""
    pass


class FloodService:
    """Coordinates hydrological inputs and executes flood prediction workflows."""

    def __init__(self, flood_engine: Optional[FloodEngine] = None):
        self.flood_engine = flood_engine or default_flood_engine

    def get_predictions(
        self,
        rainfall_override_mm_hr: Optional[float] = None,
        blockage_override_percent: Optional[float] = None,
        zone_id: Optional[str] = None,
        risk_level_filter: Optional[str] = None,
    ) -> FloodPredictionResponse:
        """Retrieves catchment-wide or filtered flood predictions."""
        risk_enum = None
        if risk_level_filter:
            try:
                risk_enum = FloodRiskLevel(risk_level_filter.strip().upper())
            except ValueError:
                raise ValueError(
                    f"Invalid risk_level: '{risk_level_filter}'. Allowed values: LOW, MODERATE, HIGH, SEVERE"
                )

        return self.flood_engine.generate_flood_prediction(
            rainfall_override_mm_hr=rainfall_override_mm_hr,
            blockage_override_percent=blockage_override_percent,
            zone_id=zone_id,
            risk_level_filter=risk_enum,
        )

    def get_zone_by_id(
        self,
        zone_id: str,
        rainfall_override_mm_hr: Optional[float] = None,
    ) -> Optional[ZoneFloodPrediction]:
        """Retrieves flood metrics for a specific zone."""
        response = self.get_predictions(
            rainfall_override_mm_hr=rainfall_override_mm_hr,
            zone_id=zone_id
        )
        if response.zones:
            return response.zones[0]
        return None


# Global singleton instance
default_flood_service = FloodService()
