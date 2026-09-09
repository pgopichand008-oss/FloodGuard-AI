"""Comprehensive automated test suite for Phase 11 Safe Routing Engine.

Verifies:
1. Routing API success (POST and GET)
2. Valid origin and destination mapping
3. Unknown origin -> 404
4. Unknown destination -> 404
5. Invalid request (negative rainfall) -> 422
6. Response schema adherence and metric completeness
7. Route contains valid, connected road edges
8. Deterministic results (repeat calls yield identical outputs)
9. Flood-aware route selection (choosing longer safe path over shorter flooded path)
10. Higher rainfall effects on route safety, depth, and cost
11. Drainage surcharge penalty impact
12. Conduit blockage penalty impact
13. Unsafe segment avoidance
14. Alternative corridor selection
15. No-safe-route handling when all corridors are submerged
16. Emergency mode behavior and clearance
17. Data provenance disclosure and Google Maps authority disclaimer
18. No duplicate / cyclic nodes along the path
19. Drainage node alias resolution (e.g. N02, N21 -> Z01)
20. Same origin and destination handling
"""
import pytest
from fastapi.testclient import TestClient

from backend.engines.routing_engine import RoutingEngine, default_routing_engine
from backend.main import app
from backend.models.flood_models import FloodRiskLevel
from backend.models.routing_models import (
    RouteResponse,
    RouteStatus,
    SegmentSafetyStatus,
)
from backend.services.flood_service import FloodService
from backend.services.routing_service import RoutingService, UnknownLocationError

client = TestClient(app)


class TestRoutingAPI:
    """API endpoint integration tests for POST /api/route and GET /api/route."""

    def test_routing_api_success_post(self):
        """Test POST /api/route computes a successful route."""
        payload = {
            "origin": "Z03",
            "destination": "Z05",
            "emergency": False,
        }
        resp = client.post("/api/route", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["origin"] == "Z03"
        assert data["destination"] == "Z05"
        assert data["origin_zone_id"] == "Z03"
        assert data["destination_zone_id"] == "Z05"
        assert data["status"] in ["SAFE_ROUTE", "CAUTION_ROUTE"]
        assert len(data["route"]) >= 2
        assert data["route"][0] == "Z03"
        assert data["route"][-1] == "Z05"
        assert data["total_distance_m"] > 0
        assert data["total_cost"] >= data["total_distance_m"]

    def test_routing_api_success_get(self):
        """Test GET /api/route computes a matching route."""
        resp = client.get("/api/route?origin=Z03&destination=Z05&emergency=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data["origin"] == "Z03"
        assert data["destination"] == "Z05"
        assert len(data["route"]) >= 2
        assert data["status"] in ["SAFE_ROUTE", "CAUTION_ROUTE"]

    def test_emergency_mode_api_flag_and_cost(self):
        """Test POST /api/route with emergency=True reflects emergency mode and discounted passable costs."""
        resp_std = client.post("/api/route", json={"origin": "Z03", "destination": "Z07", "emergency": False})
        resp_emerg = client.post("/api/route", json={"origin": "Z03", "destination": "Z07", "emergency": True})
        assert resp_std.status_code == 200
        assert resp_emerg.status_code == 200
        assert resp_emerg.json()["is_emergency"] is True
        assert resp_std.json()["is_emergency"] is False
        assert resp_emerg.json()["total_cost"] <= resp_std.json()["total_cost"]

    def test_unknown_origin_404(self):
        """Test that an unknown origin returns HTTP 404."""
        resp = client.post("/api/route", json={"origin": "Z99_UNKNOWN", "destination": "Z01"})
        assert resp.status_code == 404
        assert "Unknown origin location" in resp.json()["detail"]

    def test_unknown_destination_404(self):
        """Test that an unknown destination returns HTTP 404."""
        resp = client.post("/api/route", json={"origin": "Z01", "destination": "Z99_INVALID"})
        assert resp.status_code == 404
        assert "Unknown destination location" in resp.json()["detail"]

    def test_invalid_request_negative_rainfall_422(self):
        """Test that negative rainfall intensity triggers 422 Unprocessable Entity."""
        resp = client.post(
            "/api/route",
            json={"origin": "Z01", "destination": "Z04", "rainfall_mm_hr": -15.0},
        )
        assert resp.status_code == 422

    def test_node_alias_resolution(self):
        """Test that drainage node aliases (e.g. N21, N02 -> Z01, N01 -> Z05) resolve properly."""
        resp = client.post("/api/route", json={"origin": "N21", "destination": "N01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["origin_zone_id"] == "Z01"
        assert data["destination_zone_id"] == "Z05"
        assert data["route"][0] == "Z01"
        assert data["route"][-1] == "Z05"

    def test_same_origin_and_destination(self):
        """Test routing when origin equals destination."""
        resp = client.post("/api/route", json={"origin": "Z06", "destination": "Z06"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SAFE_ROUTE"
        assert data["route"] == ["Z06"]
        assert data["total_distance_m"] == 0.0
        assert data["total_cost"] == 0.0

    def test_route_response_schema_and_provenance(self):
        """Test that all required response fields, provenance, and mapping disclaimer are present."""
        resp = client.post("/api/route", json={"origin": "Z03", "destination": "Z04"})
        assert resp.status_code == 200
        data = resp.json()
        assert "origin" in data
        assert "destination" in data
        assert "status" in data
        assert "route" in data
        assert "route_names" in data
        assert "total_distance_m" in data
        assert "total_cost" in data
        assert "flood_risk" in data
        assert "max_flood_depth_cm" in data
        assert "avg_flood_depth_cm" in data
        assert "unsafe_segments_avoided" in data
        assert "segments" in data
        assert "is_emergency" in data
        assert "reason" in data
        assert "data_source" in data
        assert "provenance" in data
        assert "mapping_disclaimer" in data

        # Check explicit required disclosures
        assert "DEMO-SIMULATED DATA" in data["provenance"]
        assert "ILLUSTRATIVE CONNECTIVITY" in data["provenance"]
        assert "Google Maps" in data["mapping_disclaimer"]
        assert "determines flood safety using its own flood intelligence" in data["mapping_disclaimer"]


class TestRoutingEngineHydraulicsAndGraph:
    """Engine unit tests for flood-aware graph search, penalties, and safety cutoff behavior."""

    @pytest.fixture
    def setup_engine_and_service(self):
        engine = RoutingEngine()
        flood_svc = FloodService()
        routing_svc = RoutingService(routing_engine=engine, flood_service=flood_svc)
        return engine, flood_svc, routing_svc

    def test_route_connectivity_validity(self, setup_engine_and_service):
        """Test that every consecutive step in the generated route exists in the network graph."""
        engine, _, routing_svc = setup_engine_and_service
        resp = routing_svc.find_safe_route("Z03", "Z05")
        assert resp.status in [RouteStatus.SAFE_ROUTE, RouteStatus.CAUTION_ROUTE]
        route = resp.route
        assert len(route) >= 2

        # Verify each edge exists in engine.adjacency
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            neighbors = [nbr for nbr, _, _ in engine.adjacency[u]]
            assert v in neighbors, f"Edge ({u} -> {v}) does not exist in graph adjacency!"

    def test_no_cyclic_nodes(self, setup_engine_and_service):
        """Verify that routes do not contain duplicate nodes (no cycling)."""
        _, _, routing_svc = setup_engine_and_service
        resp = routing_svc.find_safe_route("Z06", "Z01")
        assert resp.status in [RouteStatus.SAFE_ROUTE, RouteStatus.CAUTION_ROUTE]
        assert len(resp.route) == len(set(resp.route)), f"Route has duplicate nodes: {resp.route}"

    def test_routing_determinism(self, setup_engine_and_service):
        """Verify that identical route requests yield exactly identical outputs."""
        _, _, routing_svc = setup_engine_and_service
        run1 = routing_svc.find_safe_route("Z03", "Z05", emergency=False)
        run2 = routing_svc.find_safe_route("Z03", "Z05", emergency=False)
        assert run1.route == run2.route
        assert run1.total_cost == run2.total_cost
        assert run1.total_distance_m == run2.total_distance_m
        assert run1.status == run2.status

    def test_flood_aware_route_selection_avoids_flooded_zone(self, setup_engine_and_service):
        """
        Verify that when a shorter physical route has high flood/surcharge,
        FloodGuard selects a safer alternative route.
        """
        engine, flood_svc, routing_svc = setup_engine_and_service

        # Base nominal predictions at low rainfall
        preds = {z.zone_id: z for z in flood_svc.get_predictions(rainfall_override_mm_hr=15.0).zones}

        # Baseline route from Z03 to Z05 passes through Z02 (shortest distance ~720m)
        res_baseline = engine.find_safe_route("Z03", "Z05", zone_predictions=preds)
        assert res_baseline.status in [RouteStatus.SAFE_ROUTE, RouteStatus.CAUTION_ROUTE]
        assert "Z02" in res_baseline.route

        # Artificially inundate Z02 (Market Junction) to 46 cm (SEVERE risk, surcharge)
        flooded_preds = dict(preds)
        z02_flooded = preds["Z02"].model_copy(
            update={
                "flood_depth_cm": 46.0,
                "peak_depth_cm": 52.0,
                "risk_level": FloodRiskLevel.SEVERE,
                "is_surcharged": True,
                "excess_flow_m3s": 2.5,
                "blockage_percent": 50.0,
            }
        )
        flooded_preds["Z02"] = z02_flooded

        res_flooded = engine.find_safe_route("Z03", "Z05", zone_predictions=flooded_preds)

        # The router must NOT route through Z02 because it is UNSAFE
        assert "Z02" not in res_flooded.route
        # Z02 must be recorded in unsafe_segments_avoided
        assert "Z02" in res_flooded.unsafe_segments_avoided
        # Route should take elevated bypass: Z03 -> Z07 -> Z08 -> Z04 -> Z05
        assert "Z07" in res_flooded.route or "Z08" in res_flooded.route

    def test_higher_rainfall_increases_route_cost_and_depth(self, setup_engine_and_service):
        """Verify that higher storm rainfall increases surface depth and navigation cost."""
        _, _, routing_svc = setup_engine_and_service

        route_low = routing_svc.find_safe_route("Z07", "Z08", rainfall_mm_hr=10.0)
        route_high = routing_svc.find_safe_route("Z07", "Z08", rainfall_mm_hr=50.0)

        assert route_high.max_flood_depth_cm >= route_low.max_flood_depth_cm
        assert route_high.total_cost > route_low.total_cost

    def test_blockage_penalty_impact(self, setup_engine_and_service):
        """Verify that conduit blockage increases segment traversal penalty."""
        engine, flood_svc, _ = setup_engine_and_service
        preds = {z.zone_id: z for z in flood_svc.get_predictions().zones}

        clean_z = preds["Z04"].model_copy(update={"blockage_percent": 0.0})
        blocked_z = preds["Z04"].model_copy(update={"blockage_percent": 60.0})

        pen_clean, _ = engine.calculate_segment_penalty(clean_z)
        pen_blocked, _ = engine.calculate_segment_penalty(blocked_z)

        assert pen_blocked > pen_clean

    def test_surcharge_penalty_impact(self, setup_engine_and_service):
        """Verify that drainage surcharge increases segment traversal penalty."""
        engine, flood_svc, _ = setup_engine_and_service
        preds = {z.zone_id: z for z in flood_svc.get_predictions().zones}

        normal_z = preds["Z01"].model_copy(update={"is_surcharged": False, "excess_flow_m3s": 0.0})
        surcharged_z = preds["Z01"].model_copy(update={"is_surcharged": True, "excess_flow_m3s": 1.2})

        pen_normal, _ = engine.calculate_segment_penalty(normal_z)
        pen_surcharged, _ = engine.calculate_segment_penalty(surcharged_z)

        assert pen_surcharged > pen_normal

    def test_no_safe_route_when_destination_submerged(self, setup_engine_and_service):
        """Verify NO_SAFE_ROUTE status when destination is submerged beyond safety threshold."""
        engine, flood_svc, _ = setup_engine_and_service
        preds = {z.zone_id: z for z in flood_svc.get_predictions().zones}

        # Submerge Z05 to 55 cm (SEVERE)
        preds["Z05"] = preds["Z05"].model_copy(
            update={"flood_depth_cm": 55.0, "risk_level": FloodRiskLevel.SEVERE}
        )

        resp = engine.find_safe_route("Z03", "Z05", zone_predictions=preds, emergency=False)
        assert resp.status == RouteStatus.NO_SAFE_ROUTE
        assert resp.route == []
        assert "submerged" in resp.reason or "inaccessible" in resp.reason
        assert "Z05" in resp.unsafe_segments_avoided

    def test_no_safe_route_when_origin_submerged(self, setup_engine_and_service):
        """Verify NO_SAFE_ROUTE status when origin is submerged beyond safety threshold."""
        engine, flood_svc, _ = setup_engine_and_service
        preds = {z.zone_id: z for z in flood_svc.get_predictions().zones}

        # Submerge Z01 to 60 cm (SEVERE)
        preds["Z01"] = preds["Z01"].model_copy(
            update={"flood_depth_cm": 60.0, "risk_level": FloodRiskLevel.SEVERE}
        )

        resp = engine.find_safe_route("Z01", "Z03", zone_predictions=preds, emergency=False)
        assert resp.status == RouteStatus.NO_SAFE_ROUTE
        assert resp.route == []
        assert "severely flooded" in resp.reason

    def test_emergency_mode_increased_clearance(self, setup_engine_and_service):
        """
        Verify that emergency mode allows high-clearance transit through moderate-high water (e.g. 35 cm),
        which would be impassable (UNSAFE) for standard passenger vehicles.
        """
        engine, flood_svc, _ = setup_engine_and_service
        preds = {z.zone_id: z for z in flood_svc.get_predictions().zones}

        # Set Z04 to 52 cm water (UNSAFE for standard vehicles >= 50 cm, but PASSABLE/CAUTION for emergency <= 60 cm)
        preds["Z04"] = preds["Z04"].model_copy(
            update={
                "flood_depth_cm": 52.0,
                "peak_depth_cm": 55.0,
                "risk_level": FloodRiskLevel.SEVERE,
                "is_surcharged": False,
            }
        )

        _, std_safety = engine.calculate_segment_penalty(preds["Z04"], is_emergency=False)
        _, emerg_safety = engine.calculate_segment_penalty(preds["Z04"], is_emergency=True)

        assert std_safety == SegmentSafetyStatus.UNSAFE
        assert emerg_safety == SegmentSafetyStatus.CAUTION

    def test_extreme_catchment_storm_causes_no_safe_route(self, setup_engine_and_service):
        """Verify that an extreme 200 mm/hr storm renders low-lying destination corridors inaccessible."""
        _, _, routing_svc = setup_engine_and_service
        resp = routing_svc.find_safe_route("Z06", "Z01", rainfall_mm_hr=200.0)
        # At 200 mm/hr, low-lying Station Road depression Z01 has deep inundation (54.8 cm) exceeding cutoff
        assert resp.status == RouteStatus.NO_SAFE_ROUTE
        assert resp.route == []
