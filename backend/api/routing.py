"""FastAPI endpoints for flood-aware safe routing across urban catchment corridors."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.routing_models import RouteRequest, RouteResponse
from backend.services.routing_service import (
    UnknownLocationError,
    default_routing_service,
)

router = APIRouter(
    prefix="/route",
    tags=["Safe Routing Engine"],
)


@router.post(
    "",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Flood-Aware Safe Route",
    description=(
        "Calculates the safest practical route between origin and destination based on real-time "
        "flood depth, risk level, drainage surcharge, and blockage. Avoids impassable flooded corridors."
    ),
)
def compute_safe_route_post(request: RouteRequest) -> RouteResponse:
    """Finds optimal flood-safe route using POST body parameters."""
    try:
        return default_routing_service.find_safe_route(
            origin=request.origin,
            destination=request.destination,
            emergency=request.emergency,
            rainfall_mm_hr=request.rainfall_mm_hr,
        )
    except UnknownLocationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing failure: {exc}",
        ) from exc


@router.get(
    "",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Flood-Aware Safe Route (GET Query)",
    description="Convenience GET endpoint to query flood-safe routes with URL parameters.",
)
def compute_safe_route_get(
    origin: str = Query(..., description="Origin zone or drainage node ID (e.g. Z01, Z03, N02)"),
    destination: str = Query(..., description="Destination zone or drainage node ID (e.g. Z05, Z08, N01)"),
    emergency: bool = Query(default=False, description="Enable emergency vehicle routing prioritization"),
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        description="Optional scenario rainfall intensity override in mm/hr",
    ),
) -> RouteResponse:
    """Finds optimal flood-safe route using GET query parameters."""
    try:
        return default_routing_service.find_safe_route(
            origin=origin,
            destination=destination,
            emergency=emergency,
            rainfall_mm_hr=rainfall_mm_hr,
        )
    except UnknownLocationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing failure: {exc}",
        ) from exc
