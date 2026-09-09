"""API endpoints for rainfall monitoring and 0-3 hour nowcast forecasts."""
from fastapi import APIRouter, HTTPException, Query, status
from backend.engines.rainfall_engine import (
    RainfallEngine,
    default_rainfall_engine,
)
from backend.models.rainfall_models import (
    CurrentRainfallResponse,
    ForecastResponse,
)
from backend.services.rainfall_service import (
    InvalidRainfallDataFormatError,
    RainfallFileNotFoundError,
    RainfallServiceError,
)

router = APIRouter(tags=["Rainfall & Forecast"])


@router.get(
    "/rainfall",
    response_model=CurrentRainfallResponse,
    summary="Get current rainfall intensity and recent observation series",
    description="Returns current rainfall intensity (mm/hr), observation series, and short-term trend. Clearly distinguishes demo data from real observations.",
)
def get_current_rainfall():
    """Retrieve the current rainfall state and trend."""
    try:
        return default_rainfall_engine.get_current_rainfall()
    except RainfallFileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rainfall dataset not found: {err}"
        )
    except (InvalidRainfallDataFormatError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid rainfall data structure: {err}"
        )
    except RainfallServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing rainfall data: {err}"
        )


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get 0-3 hour nowcast rainfall forecast",
    description="Returns the 0-3 hour rainfall forecast series with 30-minute time intervals, peak intensity, and arrival offset. Labeled as DEMO-SIMULATED prototype data.",
)
def get_rainfall_forecast(
    horizon_minutes: int = Query(
        default=180,
        ge=30,
        le=360,
        description="Forecast horizon in minutes (default 180 mins / 3 hours)"
    )
):
    """Retrieve the nowcast rainfall forecast up to the requested horizon."""
    try:
        return default_rainfall_engine.get_forecast(horizon_minutes=horizon_minutes)
    except RainfallFileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rainfall forecast dataset not found: {err}"
        )
    except (InvalidRainfallDataFormatError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid forecast data structure: {err}"
        )
    except RainfallServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error generating rainfall forecast: {err}"
        )
