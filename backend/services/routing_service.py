"""Routing service coordinating flood intelligence and the flood-aware routing engine."""
from typing import Dict, Optional

from backend.engines.routing_engine import RoutingEngine, default_routing_engine
from backend.models.flood_models import ZoneFloodPrediction
from backend.models.routing_models import RouteRequest, RouteResponse
from backend.services.flood_service import FloodService


class RoutingServiceError(Exception):
    """Base exception for routing service errors."""
    pass


class UnknownLocationError(RoutingServiceError):
    """Raised when origin or destination cannot be resolved to a known zone or node."""
    pass


class RoutingService:
    """Coordinates flood predictions and executes safe pathfinding."""

    def __init__(
        self,
        routing_engine: Optional[RoutingEngine] = None,
        flood_service: Optional[FloodService] = None,
    ):
        self.routing_engine = routing_engine or default_routing_engine
        self.flood_service = flood_service or FloodService()

    def find_safe_route(
        self,
        origin: str,
        destination: str,
        emergency: bool = False,
        rainfall_mm_hr: Optional[float] = None,
    ) -> RouteResponse:
        """
        Gathers live hydraulic flood metrics and determines safest navigation path.
        """
        # Validate origin & destination resolution
        resolved_origin = self.routing_engine.resolve_zone_id(origin)
        if not resolved_origin:
            raise UnknownLocationError(
                f"Unknown origin location: '{origin}'. Must be a valid zone ID (Z01-Z08) or drainage node (N01-N07, N21)."
            )

        resolved_dest = self.routing_engine.resolve_zone_id(destination)
        if not resolved_dest:
            raise UnknownLocationError(
                f"Unknown destination location: '{destination}'. Must be a valid zone ID (Z01-Z08) or drainage node (N01-N07, N21)."
            )

        # Retrieve live hydraulic predictions from FloodService under current or scenario rainfall
        flood_pred_resp = self.flood_service.get_predictions(
            rainfall_override_mm_hr=rainfall_mm_hr
        )
        zone_map: Dict[str, ZoneFloodPrediction] = {
            z.zone_id: z for z in flood_pred_resp.zones
        }

        # Execute routing algorithm
        return self.routing_engine.find_safe_route(
            origin_id=origin,
            destination_id=destination,
            zone_predictions=zone_map,
            emergency=emergency,
        )


default_routing_service = RoutingService()
