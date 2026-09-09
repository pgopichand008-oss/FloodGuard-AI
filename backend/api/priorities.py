"""FastAPI router for Phase 9 Action Priority and Decision Engine."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.priority_models import PriorityResponse, ZonePriority
from backend.services.priority_service import PriorityServiceError, default_priority_service

router = APIRouter(prefix="/priorities", tags=["Action Priority Decision Engine"])


@router.get(
    "",
    response_model=PriorityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ranked action priorities across catchment zones",
    description=(
        "Evaluates multi-criteria action priorities across urban zones by integrating flood inundation depth, "
        "pipe surcharge rate, conduit utilization, debris blockage, and ML hazard probabilities. "
        "Returns zones ordered descending by urgency to support field intervention dispatch."
    ),
)
def get_priorities(
    zone_id: Optional[str] = Query(
        default=None,
        description="Filter priority assessment to a specific catchment zone ID (e.g. Z01)"
    ),
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional rainfall intensity override in mm/hr for scenario-based prioritization"
    ),
):
    """Retrieve ranked intervention priorities across urban zones."""
    try:
        return default_priority_service.get_priorities(
            zone_id=zone_id,
            rainfall_override_mm_hr=rainfall_mm_hr,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err).strip("'\"")
        )
    except PriorityServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in priority engine: {err}"
        )


@router.get(
    "/{zone_id}",
    response_model=ZonePriority,
    status_code=status.HTTP_200_OK,
    summary="Get action priority evaluation for a single zone",
    description="Returns detailed score breakdown, assigned priority level, and recommended action for a specific zone.",
)
def get_zone_priority(
    zone_id: str,
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional rainfall intensity override in mm/hr"
    ),
):
    """Retrieve action priority for a specific zone."""
    try:
        return default_priority_service.get_zone_priority(
            zone_id=zone_id,
            rainfall_override_mm_hr=rainfall_mm_hr,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err).strip("'\"")
        )
    except PriorityServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in zone priority evaluation: {err}"
        )
