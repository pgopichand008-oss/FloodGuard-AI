"""FastAPI router for Phase 8 WHAT-IF flood simulation."""
from fastapi import APIRouter, HTTPException, status

from backend.models.simulation_models import SimulationRequest, SimulationResponse
from backend.services.simulation_service import SimulationServiceError, default_simulation_service

router = APIRouter(prefix="/simulate", tags=["WHAT-IF Flood Simulation"])


@router.post(
    "",
    response_model=SimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute WHAT-IF flood scenario simulation",
    description=(
        "Simulates urban catchment flood conditions under altered rainfall intensity, drainage blockage, "
        "or combined storm scenarios. Directly compares baseline vs simulated conditions per zone "
        "and computes hydraulic depth deltas, risk transitions, and impact classifications."
    ),
)
def simulate_flood_scenario(request: SimulationRequest):
    """Execute dynamic WHAT-IF simulation comparing baseline vs scenario conditions."""
    try:
        return default_simulation_service.simulate(request)
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err).strip("'\"")
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err)
        )
    except SimulationServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error executing simulation: {err}"
        )
