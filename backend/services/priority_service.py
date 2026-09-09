"""Coordination service executing multi-source data aggregation and priority ranking."""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.engines.priority_engine import PriorityEngine, default_priority_engine
from backend.models.priority_models import (
    PriorityLevel,
    PriorityResponse,
    PrioritySummary,
    ZonePriority,
)
from backend.services.flood_service import FloodService, default_flood_service
from backend.services.ml_service import MLService, default_ml_service


class PriorityServiceError(Exception):
    """Base exception for priority service errors."""
    pass


class PriorityService:
    """Coordinates flood and ML outputs to produce ranked operational action priorities."""

    def __init__(
        self,
        priority_engine: Optional[PriorityEngine] = None,
        flood_service: Optional[FloodService] = None,
        ml_service: Optional[MLService] = None,
    ):
        self.priority_engine = priority_engine or default_priority_engine
        self.flood_service = flood_service or default_flood_service
        self.ml_service = ml_service or default_ml_service

    def get_priorities(
        self,
        zone_id: Optional[str] = None,
        rainfall_override_mm_hr: Optional[float] = None,
    ) -> PriorityResponse:
        """
        Gathers live predictions and ranks zones according to intervention priority.
        """
        try:
            # 1. Fetch live physics baseline predictions
            flood_resp = self.flood_service.get_predictions(
                rainfall_override_mm_hr=rainfall_override_mm_hr,
                zone_id=zone_id,
            )

            if zone_id and not flood_resp.zones:
                raise KeyError(f"Catchment zone '{zone_id}' not found in flood monitoring network")

            # 2. Fetch ML predictions to supply hazard probabilities
            ml_by_zone: Dict[str, Dict] = {}
            try:
                ml_resp = self.ml_service.get_predictions(
                    rainfall_override_mm_hr=rainfall_override_mm_hr,
                    zone_id=zone_id,
                )
                for ml_p in ml_resp.predictions:
                    ml_by_zone[ml_p.zone_id] = ml_p.model_dump()
            except Exception:
                ml_by_zone = {}

            evaluated: List[ZonePriority] = []
            for z in flood_resp.zones:
                z_dict = z.model_dump()
                ml_dict = ml_by_zone.get(z.zone_id)
                p_item = self.priority_engine.evaluate_zone_priority(
                    zone_dict=z_dict,
                    ml_prediction=ml_dict,
                    rank=1,  # Rank will be assigned after sorting
                )
                evaluated.append(p_item)

            # 3. Sort descending by priority_score; tie-break deterministically by zone_id ascending
            evaluated.sort(key=lambda item: (-item.priority_score, item.zone_id))

            # 4. Assign 1-indexed ranks post-sorting
            for rank_idx, item in enumerate(evaluated, start=1):
                item.rank = rank_idx

            # 5. Compute summary statistics
            crit_cnt = sum(1 for p in evaluated if p.priority_level == PriorityLevel.CRITICAL)
            high_cnt = sum(1 for p in evaluated if p.priority_level == PriorityLevel.HIGH)
            med_cnt = sum(1 for p in evaluated if p.priority_level == PriorityLevel.MEDIUM)
            low_cnt = sum(1 for p in evaluated if p.priority_level == PriorityLevel.LOW)

            top_id = evaluated[0].zone_id if evaluated else None
            top_score = evaluated[0].priority_score if evaluated else 0.0

            summary = PrioritySummary(
                total_zones=len(evaluated),
                critical_count=crit_cnt,
                high_count=high_cnt,
                medium_count=med_cnt,
                low_count=low_cnt,
                top_priority_zone_id=top_id,
                highest_priority_score=top_score,
            )

            now_iso = datetime.now(timezone.utc).isoformat()

            return PriorityResponse(
                location=flood_resp.location,
                timestamp=now_iso,
                summary=summary,
                priorities=evaluated,
                data_provenance="DECISION PRIORITY DERIVED FROM MODEL-DERIVED FLOOD, DRAINAGE AND DEMO INPUTS",
                disclaimer=(
                    "Decision-support prototype. Action priorities are algorithmic recommendations based on "
                    "simulated hydraulic indicators, not official emergency dispatch authorizations."
                ),
            )

        except KeyError:
            raise
        except Exception as err:
            raise PriorityServiceError(f"Failed to generate action priorities: {err}") from err

    def get_zone_priority(
        self,
        zone_id: str,
        rainfall_override_mm_hr: Optional[float] = None,
    ) -> ZonePriority:
        """Retrieves priority evaluation for a single zone or raises KeyError."""
        resp = self.get_priorities(
            zone_id=zone_id,
            rainfall_override_mm_hr=rainfall_override_mm_hr,
        )
        if not resp.priorities:
            raise KeyError(f"Catchment zone '{zone_id}' not found in flood monitoring network")
        return resp.priorities[0]


# Global singleton instance
default_priority_service = PriorityService()
