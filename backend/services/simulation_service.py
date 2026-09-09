"""Coordination service executing WHAT-IF scenario simulations and managing business workflow."""
from typing import Optional

from backend.engines.simulation_engine import SimulationEngine, default_simulation_engine
from backend.models.simulation_models import SimulationRequest, SimulationResponse


class SimulationServiceError(Exception):
    """Base exception for simulation service errors."""
    pass


class SimulationService:
    """Service mediating scenario simulation execution."""

    def __init__(self, simulation_engine: Optional[SimulationEngine] = None):
        self.simulation_engine = simulation_engine or default_simulation_engine

    def simulate(self, request: SimulationRequest) -> SimulationResponse:
        """Executes what-if scenario comparison based on request specification."""
        try:
            return self.simulation_engine.run_simulation(
                rainfall_mm_hr=request.rainfall_mm_hr,
                blockage_percent=request.blockage_percent,
                zone_id=request.zone_id,
            )
        except KeyError as err:
            # Propagate zone not found error
            raise
        except Exception as err:
            raise SimulationServiceError(f"Simulation execution failed: {err}") from err


# Global singleton instance
default_simulation_service = SimulationService()
