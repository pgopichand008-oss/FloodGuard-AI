"""FastAPI router for WHY-FLOOD explainability, factor attribution, and operational reasoning."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.explain_models import ExplanationResponse, ZoneExplanation
from backend.services.explain_service import ExplainServiceError, default_explain_service

router = APIRouter(prefix="/explanations", tags=["WHY-FLOOD Explainability Engine"])


@router.get(
    "",
    response_model=ExplanationResponse,
    summary="Get multi-factor WHY-FLOOD explanations across urban catchment zones",
    description=(
        "Returns transparent, rule-based attribution scoring explaining WHY each zone faces flood risk. "
        "Evaluates rainfall intensity, terrain depression, runoff discharge, drainage capacity utilization, "
        "conduit blockage, and surcharge overflow, complemented by ML model insights."
    ),
)
def get_explanations(
    zone_id: Optional[str] = Query(
        default=None,
        description="Filter explanations to a specific catchment zone ID (e.g. Z01)"
    ),
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional rainfall intensity override in mm/hr for scenario-based explanation"
    ),
):
    """Retrieve structured factor attribution and primary cause reasoning across zones."""
    try:
        response = default_explain_service.get_explanations(
            zone_id=zone_id,
            rainfall_override_mm_hr=rainfall_mm_hr,
        )

        if zone_id and not response.explanations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catchment zone '{zone_id}' not found in flood network"
            )

        return response

    except HTTPException:
        raise
    except ExplainServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in explainability engine: {err}"
        )


@router.get(
    "/{zone_id}",
    response_model=ZoneExplanation,
    summary="Get detailed WHY-FLOOD explainability profile for an individual zone",
    description="Returns fine-grained contributing factors, evidence metrics, and primary cause for a single zone ID.",
)
def get_zone_explanation(
    zone_id: str,
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional rainfall intensity override in mm/hr"
    ),
):
    """Retrieve detailed explainability analysis for a specific zone."""
    try:
        return default_explain_service.get_zone_explanation(
            zone_id=zone_id,
            rainfall_override_mm_hr=rainfall_mm_hr,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
    except ExplainServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in zone explainability: {err}"
        )
