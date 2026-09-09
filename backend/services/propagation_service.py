"""Coordination service executing flood propagation traces across connected corridors."""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.engines.propagation_engine import PropagationEngine, default_propagation_engine
from backend.models.propagation_models import CatchmentPropagationResponse, ZonePropagationResponse
from backend.services.flood_service import FloodService, default_flood_service


class PropagationServiceError(Exception):
    """Base exception for propagation service errors."""
    pass


class PropagationService:
    """Coordinates flood predictions and traces hydraulic propagation paths."""

    def __init__(
        self,
        propagation_engine: Optional[PropagationEngine] = None,
        flood_service: Optional[FloodService] = None,
    ):
        self.propagation_engine = propagation_engine or default_propagation_engine
        self.flood_service = flood_service or default_flood_service

    def get_zone_propagation(
        self,
        zone_id: str,
        rainfall_override_mm_hr: Optional[float] = None,
    ) -> ZonePropagationResponse:
        """Traces flood propagation originating from a specific zone or node."""
        try:
            flood_resp = self.flood_service.get_predictions(
                rainfall_override_mm_hr=rainfall_override_mm_hr
            )
            zone_map = {z.zone_id: z for z in flood_resp.zones}

            return self.propagation_engine.trace_propagation(
                source_zone_id=zone_id,
                zone_predictions=zone_map,
            )
        except KeyError:
            raise
        except Exception as err:
            raise PropagationServiceError(f"Failed to trace zone propagation: {err}") from err

    def get_catchment_propagation(
        self,
        rainfall_override_mm_hr: Optional[float] = None,
    ) -> CatchmentPropagationResponse:
        """Evaluates flood propagation starting from all active zones in the catchment."""
        try:
            flood_resp = self.flood_service.get_predictions(
                rainfall_override_mm_hr=rainfall_override_mm_hr
            )
            zone_map = {z.zone_id: z for z in flood_resp.zones}

            chains: List[ZonePropagationResponse] = []
            for z in flood_resp.zones:
                chain = self.propagation_engine.trace_propagation(
                    source_zone_id=z.zone_id,
                    zone_predictions=zone_map,
                )
                chains.append(chain)

            now_iso = datetime.now(timezone.utc).isoformat()

            return CatchmentPropagationResponse(
                location=flood_resp.location,
                timestamp=now_iso,
                total_sources=len(chains),
                propagations=chains,
                provenance="PROPAGATION DERIVED FROM DEMO-SIMULATED FLOOD AND DRAINAGE DATA",
                disclaimer=(
                    "Illustrative flood propagation network for prototype decision support and visualization. "
                    "Not based on certified 2D overland hydrodynamic modeling."
                ),
            )
        except Exception as err:
            raise PropagationServiceError(f"Failed to generate catchment propagation: {err}") from err


# Global singleton instance
default_propagation_service = PropagationService()
