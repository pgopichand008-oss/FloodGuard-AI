"""Flood Propagation Engine modeling downstream and overland flood transmission across connected urban corridors."""
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.models.flood_models import FloodRiskLevel, ZoneFloodPrediction
from backend.models.propagation_models import (
    PropagationRelationship,
    PropagationSourceModel,
    PropagationStepModel,
    ZonePropagationResponse,
)


class PropagationEngine:
    """Calculates ordered flood propagation chains through drainage and illustrative road network connectivity."""

    # Illustrative urban road and corridor connectivity connecting adjacent catchment zones
    # Labeled explicitly: DEMO/ILLUSTRATIVE CONNECTIVITY based on catchment topology
    ILLUSTRATIVE_ZONE_CONNECTIVITY: Dict[str, List[Tuple[str, str]]] = {
        "Z01": [
            ("Z04", "Overland spillover from Station Road depression into connecting Hospital Access Road"),
            ("Z02", "Surface runoff conveyance along commercial arterial toward Market Junction"),
            ("Z08", "Drainage trunk backpressure propagating into Bus Route Corridor"),
            ("Z05", "Gravity runoff shedding into adjacent Riverbank Lane lowlands"),
        ],
        "Z02": [
            ("Z01", "Topographical drainage flow descending arterial toward Station Road"),
            ("Z04", "Connecting access link toward Hospital Access corridor"),
            ("Z03", "Upstream backpressure extending toward Main Street"),
            ("Z08", "Lateral street runoff spillover into Bus Route Corridor"),
        ],
        "Z03": [
            ("Z02", "Gravity drainage flow descending along Main Street to Market Junction"),
            ("Z07", "Overland shedding toward Central Park Sector"),
        ],
        "Z04": [
            ("Z01", "Surface spillover toward Station Road lowland depression"),
            ("Z05", "Lateral drainage overflow toward Riverbank Lane"),
            ("Z08", "Connecting road link to Bus Route Corridor"),
        ],
        "Z05": [
            ("Z01", "Lowland flood boundary retention connected with Station Road"),
            ("Z04", "Adjacent access corridor connection to Hospital Access Road"),
        ],
        "Z06": [
            ("Z03", "Downhill gravity surface shedding toward Main Street"),
            ("Z07", "Overland runoff shedding toward Central Park Sector"),
        ],
        "Z07": [
            ("Z08", "Overland drainage shedding toward Bus Route Corridor"),
            ("Z03", "Connecting corridor link with Main Street"),
        ],
        "Z08": [
            ("Z01", "Direct downstream conveyance toward Station Road trunk line"),
            ("Z04", "Connecting arterial road to Hospital Access corridor"),
            ("Z02", "Lateral road link to Market Junction"),
        ],
    }

    # Drainage node to zone mapping
    NODE_TO_ZONE: Dict[str, str] = {
        "N01": "Z05",
        "N02": "Z01",
        "N03": "Z04",
        "N04": "Z02",
        "N05": "Z08",
        "N07": "Z03",
        "N21": "Z01",  # Support N21 project concept alias -> Z01
    }

    ZONE_TO_NODE: Dict[str, str] = {
        "Z01": "N02",
        "Z02": "N04",
        "Z03": "N07",
        "Z04": "N03",
        "Z05": "N01",
        "Z08": "N05",
    }

    def resolve_zone_id(self, target_id: str) -> Optional[str]:
        """Resolves either zone_id (e.g. Z01) or node_id (e.g. N21, N02) to standard zone_id."""
        clean = target_id.strip().upper()
        if clean in self.ILLUSTRATIVE_ZONE_CONNECTIVITY:
            return clean
        if clean in self.NODE_TO_ZONE:
            return self.NODE_TO_ZONE[clean]
        return None

    def trace_propagation(
        self,
        source_zone_id: str,
        zone_predictions: Dict[str, ZoneFloodPrediction],
        max_hops: int = 4,
    ) -> ZonePropagationResponse:
        """
        Builds a deterministic, ordered flood propagation chain starting from the source zone.
        Traverses connected downstream/adjacent roads and populates actual flood metrics.
        """
        source_id = self.resolve_zone_id(source_zone_id)
        if not source_id or source_id not in zone_predictions:
            raise KeyError(f"Zone or node identifier '{source_zone_id}' not found in catchment network")

        source_zone = zone_predictions[source_id]
        source_node = self.ZONE_TO_NODE.get(source_id)

        source_model = PropagationSourceModel(
            node_id=source_node,
            zone_id=source_id,
            name=source_zone.name,
            risk=source_zone.risk_level,
            flood_depth_cm=source_zone.flood_depth_cm,
            drainage_utilization_percent=source_zone.drainage_utilization_percent,
            is_surcharged=source_zone.is_surcharged,
        )

        visited: Set[str] = {source_id}
        queue: deque = deque([(source_id, 1)])  # (current_zone_id, hop_level)
        steps: List[PropagationStepModel] = []

        while queue:
            curr_id, hop = queue.popleft()
            if hop > max_hops:
                continue

            neighbors = self.ILLUSTRATIVE_ZONE_CONNECTIVITY.get(curr_id, [])
            for neighbor_id, mechanism in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    n_zone = zone_predictions.get(neighbor_id)
                    if not n_zone:
                        continue

                    # Directly affected on first hop; downstream on subsequent hops
                    relationship = (
                        PropagationRelationship.DIRECTLY_AFFECTED.value
                        if hop == 1
                        else PropagationRelationship.DOWNSTREAM.value
                    )

                    step = PropagationStepModel(
                        order=len(steps) + 1,
                        zone_id=neighbor_id,
                        name=n_zone.name,
                        relationship=relationship,
                        risk=n_zone.risk_level,
                        flood_depth_cm=n_zone.flood_depth_cm,
                        elevation_m=n_zone.elevation_m,
                        mechanism=mechanism,
                    )
                    steps.append(step)
                    queue.append((neighbor_id, hop + 1))

        path = [source_zone.name] + [s.name for s in steps]

        return ZonePropagationResponse(
            zone_id=source_id,
            source=source_model,
            propagation=steps,
            affected_zone_count=len(steps),
            propagation_path=path,
            provenance="PROPAGATION DERIVED FROM DEMO-SIMULATED FLOOD AND DRAINAGE DATA",
            disclaimer=(
                "Illustrative flood propagation network for prototype decision support and visualization. "
                "Not based on certified 2D overland hydrodynamic modeling."
            ),
        )


# Global singleton instance
default_propagation_engine = PropagationEngine()
