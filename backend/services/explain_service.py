"""Coordination service mediating between Flood/ML engines and the WHY-FLOOD explainability engine."""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.engines.explain_engine import ExplainEngine, default_explain_engine
from backend.models.explain_models import ExplanationResponse, ZoneExplanation
from backend.services.flood_service import FloodService, default_flood_service
from backend.services.ml_service import MLService, default_ml_service


class ExplainServiceError(Exception):
    """Base exception for explainability service operations."""
    pass


class ExplainService:
    """Coordinates multi-engine data aggregation and generates structured WHY-FLOOD explanations."""

    def __init__(
        self,
        explain_engine: Optional[ExplainEngine] = None,
        flood_service: Optional[FloodService] = None,
        ml_service: Optional[MLService] = None,
    ):
        self.explain_engine = explain_engine or default_explain_engine
        self.flood_service = flood_service or default_flood_service
        self.ml_service = ml_service or default_ml_service

    def get_explanations(
        self,
        zone_id: Optional[str] = None,
        rainfall_override_mm_hr: Optional[float] = None,
    ) -> ExplanationResponse:
        """
        Gathers live physics and ML flood predictions and constructs explainability profiles.
        """
        try:
            # 1. Fetch live physics baseline predictions
            flood_resp = self.flood_service.get_predictions(
                rainfall_override_mm_hr=rainfall_override_mm_hr,
                zone_id=zone_id,
            )

            # 2. Fetch ML predictions to provide ensemble consensus insights
            ml_by_zone: Dict[str, Dict] = {}
            try:
                ml_resp = self.ml_service.get_predictions(
                    rainfall_override_mm_hr=rainfall_override_mm_hr,
                    zone_id=zone_id,
                )
                for ml_p in ml_resp.predictions:
                    ml_by_zone[ml_p.zone_id] = ml_p.model_dump()
            except Exception:
                # If ML fails or is unavailable, explanations continue using physics pipeline
                ml_by_zone = {}

            explanations: List[ZoneExplanation] = []
            causes_summary: Dict[str, int] = {}

            for zone in flood_resp.zones:
                zone_dict = zone.model_dump()
                ml_dict = ml_by_zone.get(zone.zone_id)
                exp = self.explain_engine.explain_zone(zone_dict, ml_dict)
                explanations.append(exp)

                causes_summary[exp.primary_cause] = causes_summary.get(exp.primary_cause, 0) + 1

            now_iso = datetime.now(timezone.utc).isoformat()

            return ExplanationResponse(
                location=flood_resp.location,
                timestamp=now_iso,
                total_zones_explained=len(explanations),
                primary_causes_summary=causes_summary,
                explanations=explanations,
                data_provenance="RULE-BASED EXPLANATION FROM MODEL-DERIVED AND DEMO-SIMULATED INPUTS",
                disclaimer=(
                    "Transparent rule-based explainability layer for operational decision support. "
                    "Explanations reflect model-derived and demo-simulated hydraulic indicators."
                ),
            )

        except Exception as err:
            raise ExplainServiceError(f"Failed to generate flood explanations: {err}") from err

    def get_zone_explanation(
        self,
        zone_id: str,
        rainfall_override_mm_hr: Optional[float] = None,
    ) -> ZoneExplanation:
        """Retrieves explanation for a single zone or raises KeyError if not found."""
        response = self.get_explanations(
            zone_id=zone_id,
            rainfall_override_mm_hr=rainfall_override_mm_hr,
        )
        if not response.explanations:
            raise KeyError(f"Catchment zone '{zone_id}' not found in flood monitoring network")
        return response.explanations[0]


# Global singleton instance
default_explain_service = ExplainService()
