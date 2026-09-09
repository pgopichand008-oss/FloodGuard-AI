"""API router for machine learning flood predictions and model operational status."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.models.ml_models import MLModelStatus, MLPredictionResponse
from backend.services.ml_service import MLServiceError, default_ml_service

router = APIRouter(prefix="/ml", tags=["Machine Learning Prediction Engine"])


@router.get(
    "/predict",
    response_model=MLPredictionResponse,
    summary="Get ML-driven flood depth, risk level, and hazard probability predictions",
    description="Invokes trained RandomForest ensemble models using live features from the rainfall, terrain, drainage, and flood pipeline. Complements the physics engine with probabilistic hazard assessment.",
)
def predict_flood_ml(
    zone_id: Optional[str] = Query(
        default=None,
        description="Filter ML predictions to a specific catchment zone ID (e.g. Z01)"
    ),
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Optional rainfall intensity override in mm/hr for scenario evaluation"
    ),
):
    """Execute ML flood depth and hazard probability inference across urban zones."""
    try:
        response = default_ml_service.get_predictions(
            rainfall_override_mm_hr=rainfall_mm_hr,
            zone_id=zone_id,
        )

        if zone_id and not response.predictions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catchment zone '{zone_id}' not found in ML prediction pipeline"
            )

        return response

    except HTTPException:
        raise
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err)
        )
    except MLServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML service execution error: {err}"
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in ML prediction engine: {err}"
        )


@router.get(
    "/status",
    response_model=MLModelStatus,
    summary="Get ML model status, features, and synthetic validation metrics",
    description="Returns metadata about the fitted RandomForest ensembles, including training samples, feature schema, and holdout validation scores (MAE, RMSE, R2, accuracy, F1).",
)
def get_ml_status():
    """Retrieve operational status and evaluation metrics for the ML models."""
    try:
        return default_ml_service.get_status()
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ML model status: {err}"
        )
