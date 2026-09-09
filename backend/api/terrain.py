"""API endpoints for terrain characteristics and surface runoff calculations."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.engines.terrain_engine import (
    TerrainEngine,
    default_terrain_engine,
)
from backend.models.terrain_models import (
    RunoffCalculationRequest,
    RunoffOverviewResponse,
    TerrainOverviewResponse,
)
from backend.services.terrain_service import (
    InvalidTerrainDataFormatError,
    TerrainFileNotFoundError,
    TerrainServiceError,
)

router = APIRouter(tags=["Terrain & Surface Runoff"])


@router.get(
    "/terrain",
    response_model=TerrainOverviewResponse,
    summary="Get digital elevation model (DEM) and catchment zones",
    description="Returns urban terrain elevation, slope, flow accumulation, imperviousness, and low-lying status. Labeled as DEMO-SIMULATED data.",
)
def get_terrain_zones():
    """Retrieve all delineated catchment zones and terrain characteristics."""
    try:
        return default_terrain_engine.get_terrain_overview()
    except TerrainFileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terrain dataset not found: {err}"
        )
    except (InvalidTerrainDataFormatError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid terrain data structure: {err}"
        )
    except TerrainServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing terrain data: {err}"
        )


@router.get(
    "/runoff",
    response_model=RunoffOverviewResponse,
    summary="Calculate surface runoff across catchment zones",
    description="Computes Rational Method surface runoff (m3/s and mm/hr), runoff tendency, and accumulation vulnerability based on current or custom rainfall intensity.",
)
def calculate_runoff(
    rainfall_mm_hr: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=500.0,
        description="Override rainfall intensity in mm/hr (defaults to current live/demo rainfall)"
    ),
    zone_id: Optional[str] = Query(
        default=None,
        description="Optional single zone ID to evaluate (e.g. Z01)"
    )
):
    """Calculate zone-by-zone surface runoff and vulnerability indices."""
    try:
        target_zones = [zone_id] if zone_id else None
        return default_terrain_engine.calculate_catchment_runoff(
            rainfall_intensity_mm_hr=rainfall_mm_hr,
            zone_ids=target_zones
        )
    except TerrainFileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terrain dataset not found: {err}"
        )
    except (InvalidTerrainDataFormatError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid runoff calculation input: {err}"
        )
    except TerrainServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error calculating runoff: {err}"
        )


@router.post(
    "/runoff",
    response_model=RunoffOverviewResponse,
    summary="Calculate surface runoff with scenario parameters",
    description="POST endpoint for evaluating custom scenario inputs including rainfall intensity overrides and specific zone subsets.",
)
def calculate_runoff_scenario(payload: RunoffCalculationRequest):
    """Execute scenario-based surface runoff calculation."""
    try:
        return default_terrain_engine.calculate_catchment_runoff(
            rainfall_intensity_mm_hr=payload.rainfall_intensity_mm_hr,
            zone_ids=payload.zone_ids
        )
    except TerrainFileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terrain dataset not found: {err}"
        )
    except (InvalidTerrainDataFormatError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid runoff scenario payload: {err}"
        )
    except TerrainServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing runoff scenario: {err}"
        )
