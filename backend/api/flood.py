"""API router for urban flood prediction and real-time hazard intelligence."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.flood_models import FloodPredictionResponse
from backend.services.flood_service import (
    FloodServiceError,
    default_flood_service,
)

router = APIRouter(tags=["Flood Intelligence"])


@router.get(
    "/flood",
    response_model=FloodPredictionResponse,
    summary="Get integrated urban flood prediction, depth calculations, and risk levels",
    description="Couples rainfall nowcasting, terrain runoff, and drainage surcharge to calculate street-level flood depths, hazard risk levels, and operational summary.",
)
def get_flood_prediction(
    zone_id: Optional[str] = Query(
        default=None,
        description="Filter results to a specific catchment zone ID (e.g. Z01)"
    ),
    risk_level: Optional[str] = Query(
        default=None,
        description="Filter zones by calculated risk level: LOW, MODERATE, HIGH, or SEVERE"
    ),
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional override for rainfall intensity in mm/hr (defaults to current nowcast rate)"
    ),
):
    """Calculate and retrieve street-level flood depths and catchment hazard overview."""
    try:
        response = default_flood_service.get_predictions(
            rainfall_override_mm_hr=rainfall_mm_hr,
            zone_id=zone_id,
            risk_level_filter=risk_level,
        )

        if zone_id and not response.zones:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catchment zone '{zone_id}' not found in flood analysis"
            )

        return response

    except HTTPException:
        raise
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err)
        )
    except FloodServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal flood intelligence calculation error: {err}"
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in flood engine: {err}"
        )
