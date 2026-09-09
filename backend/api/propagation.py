"""FastAPI router for Phase 10 Flood Propagation Engine."""
from typing import Optional, Union
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.propagation_models import CatchmentPropagationResponse, ZonePropagationResponse
from backend.services.propagation_service import PropagationServiceError, default_propagation_service

router = APIRouter(prefix="/propagation", tags=["Flood Propagation Engine"])


@router.get(
    "",
    response_model=Union[ZonePropagationResponse, CatchmentPropagationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get flood propagation chains across connected corridors",
    description=(
        "Traces sequential flood propagation through connected drainage and road corridors. "
        "Returns either the propagation chain originating from a specified zone/node, "
        "or catchment-wide propagation networks across all zones."
    ),
)
def get_propagation(
    zone_id: Optional[str] = Query(
        default=None,
        description="Optional origin zone ID (e.g. Z01) or drainage node ID (e.g. N02, N21) to trace"
    ),
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional rainfall intensity override in mm/hr for scenario evaluation"
    ),
):
    """Retrieve flood propagation pathways starting from a specific zone or across all zones."""
    try:
        if zone_id:
            return default_propagation_service.get_zone_propagation(
                zone_id=zone_id,
                rainfall_override_mm_hr=rainfall_mm_hr,
            )
        return default_propagation_service.get_catchment_propagation(
            rainfall_override_mm_hr=rainfall_mm_hr
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err).strip("'\"")
        )
    except PropagationServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in propagation engine: {err}"
        )


@router.get(
    "/{zone_id}",
    response_model=ZonePropagationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get flood propagation chain for an individual zone",
    description="Returns sequential corridor traversal, affected zone depths, and hydraulic transmission mechanisms.",
)
def get_zone_propagation(
    zone_id: str,
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional rainfall intensity override in mm/hr"
    ),
):
    """Retrieve propagation chain for a specific zone."""
    try:
        return default_propagation_service.get_zone_propagation(
            zone_id=zone_id,
            rainfall_override_mm_hr=rainfall_mm_hr,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err).strip("'\"")
        )
    except PropagationServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in zone propagation: {err}"
        )
