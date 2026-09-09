"""Flood-Aware Safe Routing Engine for FloodGuard AI.

Calculates deterministic, multi-criteria route safety and navigation costs across
urban corridors by evaluating real-time hydraulic conditions (depth, risk, surcharge, blockage).
"""
import heapq
from typing import Dict, List, Optional, Set, Tuple

from backend.models.flood_models import FloodRiskLevel, ZoneFloodPrediction
from backend.models.routing_models import (
    RouteResponse,
    RouteSegmentDetail,
    RouteStatus,
    SegmentSafetyStatus,
)


class RoutingEngine:
    """Computes flood-safe routes using graph traversal and multi-parameter hydraulic penalties."""

    # Illustrative urban road network connecting adjacent catchment zones
    # (zone_u, zone_v, base_distance_meters, corridor_name)
    # Labeled explicitly: DEMO-SIMULATED DATA and ILLUSTRATIVE CONNECTIVITY
    ROAD_NETWORK_EDGES: List[Tuple[str, str, float, str]] = [
        ("Z03", "Z02", 180.0, "Main Street - Market Junction Arterial"),
        ("Z02", "Z01", 300.0, "Market Junction - Station Road Commercial Link"),
        ("Z01", "Z04", 250.0, "Station Road - Hospital Access Connector"),
        ("Z04", "Z02", 220.0, "Hospital Access - Market Junction Boulevard"),
        ("Z01", "Z05", 350.0, "Station Road - Riverbank Lane Way"),
        ("Z04", "Z05", 320.0, "Hospital Access - Riverbank Cut-through"),
        ("Z01", "Z08", 190.0, "Station Road - Bus Route Corridor"),
        ("Z02", "Z08", 260.0, "Market Junction - Bus Route Link"),
        ("Z04", "Z08", 240.0, "Hospital Access - Bus Route Crossway"),
        ("Z03", "Z06", 450.0, "Main Street - Hilltop Avenue Incline"),
        ("Z06", "Z07", 400.0, "Hilltop Avenue - Central Park Ridge"),
        ("Z03", "Z07", 280.0, "Main Street - Central Park Bypass"),
        ("Z07", "Z08", 310.0, "Central Park - Bus Route Connector"),
    ]

    # Drainage node to zone mapping (reused from drainage and propagation specifications)
    NODE_TO_ZONE: Dict[str, str] = {
        "N01": "Z05",
        "N02": "Z01",
        "N03": "Z04",
        "N04": "Z02",
        "N05": "Z08",
        "N07": "Z03",
        "N21": "Z01",  # Support N21 project concept alias -> Z01 Station Road
    }

    # All recognized zones
    KNOWN_ZONES: Set[str] = {
        "Z01", "Z02", "Z03", "Z04", "Z05", "Z06", "Z07", "Z08"
    }

    # Passability thresholds (in cm)
    STANDARD_UNSAFE_DEPTH_CM = 50.0    # >= 50 cm corresponds to SEVERE flood depth
    EMERGENCY_UNSAFE_DEPTH_CM = 60.0   # High-clearance rescue vehicles can ford deeper water

    def __init__(self):
        # Build adjacency graph
        self.adjacency: Dict[str, List[Tuple[str, float, str]]] = {z: [] for z in self.KNOWN_ZONES}
        for u, v, dist, name in self.ROAD_NETWORK_EDGES:
            self.adjacency[u].append((v, dist, name))
            self.adjacency[v].append((u, dist, name))

    def resolve_zone_id(self, identifier: str) -> Optional[str]:
        """Resolves zone ID or drainage node alias to standard uppercase zone ID."""
        clean = identifier.strip().upper()
        if clean in self.KNOWN_ZONES:
            return clean
        if clean in self.NODE_TO_ZONE:
            return self.NODE_TO_ZONE[clean]
        return None

    def calculate_segment_penalty(
        self,
        zone_pred: ZoneFloodPrediction,
        is_emergency: bool = False,
    ) -> Tuple[float, SegmentSafetyStatus]:
        """
        Calculates deterministic hydraulic safety penalty and passability for entering a zone.
        
        Cost Formulation:
          penalty = flood_depth_penalty + risk_level_penalty + surcharge_penalty 
                    + utilization_penalty + blockage_penalty
        """
        depth = zone_pred.flood_depth_cm
        risk = zone_pred.risk_level
        surcharged = zone_pred.is_surcharged
        excess = zone_pred.excess_flow_m3s
        util = zone_pred.drainage_utilization_percent
        blockage = zone_pred.blockage_percent

        cutoff_depth = self.EMERGENCY_UNSAFE_DEPTH_CM if is_emergency else self.STANDARD_UNSAFE_DEPTH_CM
        severe_risk_cutoff = 55.0 if is_emergency else 45.0
        excess_cutoff = 3.0 if is_emergency else 2.0

        # 1. Determine Passability Status
        # A segment is UNSAFE (impassable) if flood depth reaches severe cutoff or extreme surcharge
        if depth >= cutoff_depth or (risk == FloodRiskLevel.SEVERE and depth >= severe_risk_cutoff) or (surcharged and excess >= excess_cutoff):
            safety_status = SegmentSafetyStatus.UNSAFE
        elif depth >= 15.0 or risk in (FloodRiskLevel.MODERATE, FloodRiskLevel.HIGH, FloodRiskLevel.SEVERE) or surcharged or blockage >= 25.0:
            safety_status = SegmentSafetyStatus.CAUTION
        else:
            safety_status = SegmentSafetyStatus.PASSABLE

        # 2. Flood Depth Penalty
        if depth < 5.0:
            depth_pen = 0.0
        elif depth < 15.0:
            depth_pen = depth * 10.0
        elif depth < 30.0:
            depth_pen = 300.0 + (depth - 15.0) * 40.0
        elif depth < 50.0:
            depth_pen = 1500.0 + (depth - 30.0) * 100.0
        else:
            depth_pen = 8000.0 + (depth - 50.0) * 200.0

        # 3. Categorical Risk Penalty
        risk_pen_map = {
            FloodRiskLevel.LOW: 0.0,
            FloodRiskLevel.MODERATE: 200.0,
            FloodRiskLevel.HIGH: 1000.0,
            FloodRiskLevel.SEVERE: 3500.0,
        }
        risk_pen = risk_pen_map.get(risk, 0.0)

        # 4. Drainage Surcharge & Overflow Penalty
        if surcharged:
            surcharge_pen = 400.0 + min(2000.0, excess * 500.0)
        else:
            surcharge_pen = 0.0

        # 5. Conduit Utilization Penalty (> 75%)
        if util > 75.0:
            util_pen = (util - 75.0) * 6.0
        else:
            util_pen = 0.0

        # 6. Blockage Impediment Penalty (> 10%)
        if blockage > 10.0:
            blockage_pen = blockage * 4.0
        else:
            blockage_pen = 0.0

        total_penalty = depth_pen + risk_pen + surcharge_pen + util_pen + blockage_pen

        # In emergency mode, discount passable corridors to prioritize swift response
        if is_emergency:
            if safety_status == SegmentSafetyStatus.PASSABLE:
                total_penalty *= 0.5
            elif safety_status == SegmentSafetyStatus.UNSAFE:
                total_penalty += 15000.0

        return total_penalty, safety_status

    def _dijkstra_search(
        self,
        origin: str,
        destination: str,
        zone_predictions: Dict[str, ZoneFloodPrediction],
        is_emergency: bool,
        allow_unsafe: bool = False,
    ) -> Optional[Tuple[List[str], float, float]]:
        """
        Dijkstra's shortest path minimizing flood-aware navigation cost.
        Returns: (path, total_cost, total_distance) or None if unreachable.
        """
        # Priority queue entries: (cost, distance, current_node, path)
        pq: List[Tuple[float, float, str, List[str]]] = [(0.0, 0.0, origin, [origin])]
        best_cost: Dict[str, float] = {origin: 0.0}

        while pq:
            cost, dist, u, path = heapq.heappop(pq)

            if u == destination:
                return path, cost, dist

            if cost > best_cost.get(u, float("inf")):
                continue

            for v, road_dist, _ in self.adjacency.get(u, []):
                if v in path:
                    continue  # Prevent cycles

                pred_v = zone_predictions.get(v)
                if not pred_v:
                    continue

                penalty, safety = self.calculate_segment_penalty(pred_v, is_emergency=is_emergency)

                if not allow_unsafe and safety == SegmentSafetyStatus.UNSAFE and v != destination:
                    continue  # Exclude unsafe intermediate zones

                step_cost = road_dist + penalty
                new_cost = cost + step_cost
                new_dist = dist + road_dist

                if new_cost < best_cost.get(v, float("inf")):
                    best_cost[v] = new_cost
                    heapq.heappush(pq, (new_cost, new_dist, v, path + [v]))

        return None

    def _unconstrained_shortest_path(
        self,
        origin: str,
        destination: str,
    ) -> Optional[Tuple[List[str], float]]:
        """Computes baseline nominal road distance path without flood penalties."""
        pq: List[Tuple[float, str, List[str]]] = [(0.0, origin, [origin])]
        best_dist: Dict[str, float] = {origin: 0.0}

        while pq:
            dist, u, path = heapq.heappop(pq)
            if u == destination:
                return path, dist

            if dist > best_dist.get(u, float("inf")):
                continue

            for v, road_dist, _ in self.adjacency.get(u, []):
                if v in path:
                    continue
                new_dist = dist + road_dist
                if new_dist < best_dist.get(v, float("inf")):
                    best_dist[v] = new_dist
                    heapq.heappush(pq, (new_dist, v, path + [v]))

        return None

    def find_safe_route(
        self,
        origin_id: str,
        destination_id: str,
        zone_predictions: Dict[str, ZoneFloodPrediction],
        emergency: bool = False,
    ) -> RouteResponse:
        """
        Executes flood-aware routing between origin and destination.
        Selects safest practical path, avoiding flooded and surcharging corridors.
        """
        resolved_origin = self.resolve_zone_id(origin_id)
        resolved_dest = self.resolve_zone_id(destination_id)

        if not resolved_origin:
            raise KeyError(f"Unknown origin location: '{origin_id}'.")
        if not resolved_dest:
            raise KeyError(f"Unknown destination location: '{destination_id}'.")

        origin_pred = zone_predictions[resolved_origin]
        dest_pred = zone_predictions[resolved_dest]

        cutoff_depth = self.EMERGENCY_UNSAFE_DEPTH_CM if emergency else self.STANDARD_UNSAFE_DEPTH_CM

        # Case 1: Origin and Destination are identical
        if resolved_origin == resolved_dest:
            _, safety = self.calculate_segment_penalty(origin_pred, is_emergency=emergency)
            status = RouteStatus.SAFE_ROUTE if safety == SegmentSafetyStatus.PASSABLE else (
                RouteStatus.CAUTION_ROUTE if safety == SegmentSafetyStatus.CAUTION else RouteStatus.NO_SAFE_ROUTE
            )
            reason = (
                f"Origin and destination are the same zone ({origin_pred.name}). "
                + (f"Current depth: {origin_pred.flood_depth_cm} cm." if status != RouteStatus.NO_SAFE_ROUTE else
                   f"Zone is submerged with {origin_pred.flood_depth_cm} cm water; navigation is unsafe.")
            )
            return RouteResponse(
                origin=origin_id,
                destination=destination_id,
                origin_zone_id=resolved_origin,
                destination_zone_id=resolved_dest,
                status=status,
                route=[resolved_origin] if status != RouteStatus.NO_SAFE_ROUTE else [],
                route_names=[origin_pred.name] if status != RouteStatus.NO_SAFE_ROUTE else [],
                total_distance_m=0.0,
                total_cost=0.0,
                flood_risk=origin_pred.risk_level,
                max_flood_depth_cm=origin_pred.flood_depth_cm,
                avg_flood_depth_cm=origin_pred.flood_depth_cm,
                unsafe_segments_avoided=[],
                segments=[],
                is_emergency=emergency,
                reason=reason,
            )

        # Baseline shortest unconstrained path for comparison
        unconstrained = self._unconstrained_shortest_path(resolved_origin, resolved_dest)
        shortest_path_nodes = unconstrained[0] if unconstrained else []

        # Find unsafe zones in catchment
        unsafe_zones_in_network: Set[str] = set()
        for z_id, z_pred in zone_predictions.items():
            _, z_safety = self.calculate_segment_penalty(z_pred, is_emergency=emergency)
            if z_safety == SegmentSafetyStatus.UNSAFE:
                unsafe_zones_in_network.add(z_id)

        # Check if origin or destination is severely flooded beyond safe cutoff
        if origin_pred.flood_depth_cm >= cutoff_depth or (origin_pred.risk_level == FloodRiskLevel.SEVERE and origin_pred.flood_depth_cm >= 45.0):
            return RouteResponse(
                origin=origin_id,
                destination=destination_id,
                origin_zone_id=resolved_origin,
                destination_zone_id=resolved_dest,
                status=RouteStatus.NO_SAFE_ROUTE,
                route=[],
                route_names=[],
                total_distance_m=0.0,
                total_cost=0.0,
                flood_risk=origin_pred.risk_level,
                max_flood_depth_cm=origin_pred.flood_depth_cm,
                avg_flood_depth_cm=origin_pred.flood_depth_cm,
                unsafe_segments_avoided=sorted(list(unsafe_zones_in_network)),
                segments=[],
                is_emergency=emergency,
                reason=(
                    f"Origin zone '{origin_pred.name}' ({resolved_origin}) is severely flooded "
                    f"({origin_pred.flood_depth_cm} cm >= cutoff {cutoff_depth} cm). Navigation cannot safely begin."
                ),
            )

        if dest_pred.flood_depth_cm >= cutoff_depth or (dest_pred.risk_level == FloodRiskLevel.SEVERE and dest_pred.flood_depth_cm >= 45.0):
            return RouteResponse(
                origin=origin_id,
                destination=destination_id,
                origin_zone_id=resolved_origin,
                destination_zone_id=resolved_dest,
                status=RouteStatus.NO_SAFE_ROUTE,
                route=[],
                route_names=[],
                total_distance_m=0.0,
                total_cost=0.0,
                flood_risk=dest_pred.risk_level,
                max_flood_depth_cm=dest_pred.flood_depth_cm,
                avg_flood_depth_cm=dest_pred.flood_depth_cm,
                unsafe_segments_avoided=sorted(list(unsafe_zones_in_network)),
                segments=[],
                is_emergency=emergency,
                reason=(
                    f"Destination zone '{dest_pred.name}' ({resolved_dest}) is submerged under "
                    f"{dest_pred.flood_depth_cm} cm water (exceeds safety threshold {cutoff_depth} cm). Route inaccessible."
                ),
            )

        # Step 1: Attempt to find route strictly avoiding UNSAFE corridors
        res = self._dijkstra_search(
            origin=resolved_origin,
            destination=resolved_dest,
            zone_predictions=zone_predictions,
            is_emergency=emergency,
            allow_unsafe=False,
        )

        # If no safe route exists without traversing unsafe corridors
        if not res:
            return RouteResponse(
                origin=origin_id,
                destination=destination_id,
                origin_zone_id=resolved_origin,
                destination_zone_id=resolved_dest,
                status=RouteStatus.NO_SAFE_ROUTE,
                route=[],
                route_names=[],
                total_distance_m=0.0,
                total_cost=0.0,
                flood_risk=FloodRiskLevel.SEVERE,
                max_flood_depth_cm=max(origin_pred.flood_depth_cm, dest_pred.flood_depth_cm),
                avg_flood_depth_cm=round((origin_pred.flood_depth_cm + dest_pred.flood_depth_cm) / 2.0, 1),
                unsafe_segments_avoided=sorted(list(unsafe_zones_in_network)),
                segments=[],
                is_emergency=emergency,
                reason="All available paths between origin and destination contain impassable flood or surcharge conditions.",
            )

        path_nodes, total_cost, total_dist = res

        # Build detailed segment metrics
        segments: List[RouteSegmentDetail] = []
        depths_on_route: List[float] = [origin_pred.flood_depth_cm]
        risks_on_route: List[FloodRiskLevel] = [origin_pred.risk_level]

        for i in range(len(path_nodes) - 1):
            u_id = path_nodes[i]
            v_id = path_nodes[i + 1]
            pred_v = zone_predictions[v_id]
            depths_on_route.append(pred_v.flood_depth_cm)
            risks_on_route.append(pred_v.risk_level)

            # Find edge distance and street name
            e_dist = 0.0
            e_name = f"{u_id} to {v_id}"
            for neighbor, d, nm in self.adjacency.get(u_id, []):
                if neighbor == v_id:
                    e_dist = d
                    e_name = nm
                    break

            pen, seg_safety = self.calculate_segment_penalty(pred_v, is_emergency=emergency)
            seg_cost = e_dist + pen

            segments.append(
                RouteSegmentDetail(
                    from_zone_id=u_id,
                    to_zone_id=v_id,
                    street_name=e_name,
                    distance_m=round(e_dist, 1),
                    flood_depth_cm=pred_v.flood_depth_cm,
                    risk_level=pred_v.risk_level,
                    is_surcharged=pred_v.is_surcharged,
                    drainage_utilization_percent=pred_v.drainage_utilization_percent,
                    blockage_percent=pred_v.blockage_percent,
                    segment_cost=round(seg_cost, 1),
                    safety_status=seg_safety,
                )
            )

        # Calculate summary metrics
        max_depth = max(depths_on_route)
        avg_depth = round(sum(depths_on_route) / len(depths_on_route), 1)

        # Categorical risk hierarchy: SEVERE > HIGH > MODERATE > LOW
        risk_priority = [FloodRiskLevel.LOW, FloodRiskLevel.MODERATE, FloodRiskLevel.HIGH, FloodRiskLevel.SEVERE]
        max_risk = max(risks_on_route, key=lambda r: risk_priority.index(r))

        # Overall route status
        has_caution = any(s.safety_status == SegmentSafetyStatus.CAUTION for s in segments) or (
            origin_pred.flood_depth_cm >= 15.0 or origin_pred.risk_level != FloodRiskLevel.LOW
        )
        route_status = RouteStatus.CAUTION_ROUTE if has_caution else RouteStatus.SAFE_ROUTE

        # Identify which unsafe or high-risk corridors were avoided relative to shortest unconstrained path
        avoided_unsafe = [
            node for node in shortest_path_nodes
            if node not in path_nodes and (
                node in unsafe_zones_in_network or
                zone_predictions[node].risk_level in (FloodRiskLevel.HIGH, FloodRiskLevel.SEVERE) or
                zone_predictions[node].is_surcharged
            )
        ]

        route_names = [zone_predictions[zid].name for zid in path_nodes]

        # Formulate clear rationale
        if avoided_unsafe:
            avoided_str = ", ".join(f"{zone_predictions[z].name} ({z})" for z in avoided_unsafe)
            reason = (
                f"FloodGuard selected an alternative safe route via {len(path_nodes)} zones, "
                f"successfully avoiding high-risk flooded corridors: {avoided_str}."
            )
        elif route_status == RouteStatus.CAUTION_ROUTE:
            reason = (
                f"Route is passable with caution (maximum depth: {max_depth} cm, peak risk: {max_risk.value}). "
                f"Drivers should proceed slowly through minor ponding zones."
            )
        else:
            reason = (
                f"Clear flood-safe route verified across {len(path_nodes)} zones. "
                f"Maximum surface depth is {max_depth} cm with nominal drainage capacity."
            )

        return RouteResponse(
            origin=origin_id,
            destination=destination_id,
            origin_zone_id=resolved_origin,
            destination_zone_id=resolved_dest,
            status=route_status,
            route=path_nodes,
            route_names=route_names,
            total_distance_m=round(total_dist, 1),
            total_cost=round(total_cost, 1),
            flood_risk=max_risk,
            max_flood_depth_cm=round(max_depth, 1),
            avg_flood_depth_cm=avg_depth,
            unsafe_segments_avoided=avoided_unsafe,
            segments=segments,
            is_emergency=emergency,
            reason=reason,
        )


default_routing_engine = RoutingEngine()
