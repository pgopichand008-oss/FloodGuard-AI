"""Automated test suite for Phase 9 Action Priority and Decision Engine."""
import unittest
from fastapi.testclient import TestClient

from backend.engines.priority_engine import PriorityEngine
from backend.main import app
from backend.models.flood_models import FloodRiskLevel
from backend.models.priority_models import PriorityLevel
from backend.services.priority_service import PriorityService


class TestPriorityAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_priorities_endpoint_success(self):
        """Verify GET /api/priorities returns 200 and evaluates all catchment zones."""
        response = self.client.get("/api/priorities")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["summary"]["total_zones"], 8)
        self.assertEqual(len(data["priorities"]), 8)
        self.assertEqual(
            data["data_provenance"],
            "DECISION PRIORITY DERIVED FROM MODEL-DERIVED FLOOD, DRAINAGE AND DEMO INPUTS"
        )
        self.assertIn("disclaimer", data)

        # 1. Verify descending sort order of priority scores
        scores = [p["priority_score"] for p in data["priorities"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

        # 2. Verify ranks are strictly 1 through N
        ranks = [p["rank"] for p in data["priorities"]]
        self.assertEqual(ranks, list(range(1, 9)))

        # 3. Verify individual zone priority structure
        for p in data["priorities"]:
            self.assertIn("zone_id", p)
            self.assertIn("zone_name", p)
            self.assertGreaterEqual(p["priority_score"], 0.0)
            self.assertLessEqual(p["priority_score"], 100.0)
            self.assertIn(p["priority_level"], ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
            self.assertTrue(len(p["recommended_action"]) > 0)
            self.assertTrue(len(p["reason"]) > 0)
            self.assertIn("score_breakdown", p)

    def test_get_priorities_filter_by_zone(self):
        """Verify GET /api/priorities?zone_id=Z01 filters to single requested zone."""
        response = self.client.get("/api/priorities?zone_id=Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["summary"]["total_zones"], 1)
        self.assertEqual(len(data["priorities"]), 1)
        self.assertEqual(data["priorities"][0]["zone_id"], "Z01")
        self.assertEqual(data["priorities"][0]["zone_name"], "Station Road")

    def test_get_zone_priority_path_endpoint(self):
        """Verify GET /api/priorities/{zone_id} returns ZonePriority directly."""
        response = self.client.get("/api/priorities/Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["zone_id"], "Z01")
        self.assertEqual(data["zone_name"], "Station Road")
        self.assertIn(data["priority_level"], ["HIGH", "CRITICAL"])
        self.assertGreater(data["priority_score"], 60.0)
        self.assertIn("Station Road", data["reason"])

    def test_get_priorities_nonexistent_zone_query_404(self):
        """Verify 404 when querying unknown zone via query parameter."""
        response = self.client.get("/api/priorities?zone_id=UNKNOWN_ZONE_999")
        self.assertEqual(response.status_code, 404)

    def test_get_zone_priority_nonexistent_zone_path_404(self):
        """Verify 404 when querying unknown zone via path parameter."""
        response = self.client.get("/api/priorities/UNKNOWN_ZONE_999")
        self.assertEqual(response.status_code, 404)

    def test_get_priorities_rainfall_override(self):
        """Verify scenario rainfall override changes priority scores."""
        res_light = self.client.get("/api/priorities/Z01?rainfall_mm_hr=20.0")
        res_heavy = self.client.get("/api/priorities/Z01?rainfall_mm_hr=120.0")

        self.assertEqual(res_light.status_code, 200)
        self.assertEqual(res_heavy.status_code, 200)

        score_light = res_light.json()["priority_score"]
        score_heavy = res_heavy.json()["priority_score"]
        self.assertGreater(score_heavy, score_light)


class TestPriorityEngineDeterminismAndHydraulics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = PriorityEngine()

    def test_score_determinism(self):
        """Verify priority scoring is 100% deterministic given identical inputs."""
        sample_zone = {
            "zone_id": "Z01",
            "name": "Station Road",
            "flood_depth_cm": 38.9,
            "risk_level": FloodRiskLevel.HIGH,
            "drainage_utilization_percent": 133.3,
            "blockage_percent": 30.0,
            "excess_flow_m3s": 1.05,
            "is_surcharged": True,
            "is_low_lying": True,
            "elevation_m": 12.4,
            "slope_percent": 0.5,
            "peak_depth_cm": 45.0,
            "rainfall_intensity_mm_hr": 86.0,
        }

        p1 = self.engine.evaluate_zone_priority(sample_zone)
        p2 = self.engine.evaluate_zone_priority(sample_zone)

        self.assertEqual(p1.priority_score, p2.priority_score)
        self.assertEqual(p1.priority_level, p2.priority_level)
        self.assertEqual(p1.recommended_action, p2.recommended_action)
        self.assertEqual(p1.reason, p2.reason)

    def test_higher_flood_depth_increases_priority_score(self):
        """Dynamic relationship: Higher flood depth produces higher priority score."""
        base_zone = {
            "zone_id": "Z_TEST",
            "name": "Test Corridor",
            "risk_level": FloodRiskLevel.MODERATE,
            "drainage_utilization_percent": 70.0,
            "blockage_percent": 10.0,
            "excess_flow_m3s": 0.0,
            "is_surcharged": False,
            "is_low_lying": False,
            "elevation_m": 22.0,
            "slope_percent": 1.8,
            "rainfall_intensity_mm_hr": 60.0,
        }

        z_shallow = dict(base_zone, flood_depth_cm=8.0, risk_level=FloodRiskLevel.LOW)
        z_deep = dict(base_zone, flood_depth_cm=48.0, risk_level=FloodRiskLevel.HIGH)

        p_shallow = self.engine.evaluate_zone_priority(z_shallow)
        p_deep = self.engine.evaluate_zone_priority(z_deep)

        self.assertGreater(p_deep.priority_score, p_shallow.priority_score)
        self.assertGreater(p_deep.score_breakdown["flood_depth"], p_shallow.score_breakdown["flood_depth"])

    def test_higher_drainage_utilization_and_surcharge_increases_priority(self):
        """Dynamic relationship: Conduit surcharge overflow substantially elevates priority."""
        base_zone = {
            "zone_id": "Z_TEST",
            "name": "Test Corridor",
            "flood_depth_cm": 20.0,
            "risk_level": FloodRiskLevel.MODERATE,
            "blockage_percent": 15.0,
            "is_low_lying": True,
            "elevation_m": 14.0,
            "slope_percent": 0.8,
            "rainfall_intensity_mm_hr": 70.0,
        }

        z_normal = dict(base_zone, drainage_utilization_percent=50.0, excess_flow_m3s=0.0, is_surcharged=False)
        z_surcharged = dict(base_zone, drainage_utilization_percent=140.0, excess_flow_m3s=1.2, is_surcharged=True)

        p_normal = self.engine.evaluate_zone_priority(z_normal)
        p_surcharged = self.engine.evaluate_zone_priority(z_surcharged)

        self.assertGreater(p_surcharged.priority_score, p_normal.priority_score)
        self.assertGreater(
            p_surcharged.score_breakdown["drainage_overload"],
            p_normal.score_breakdown["drainage_overload"]
        )

    def test_higher_blockage_increases_priority_score(self):
        """Dynamic relationship: Higher conduit blockage increases infrastructure priority component."""
        base_zone = {
            "zone_id": "Z_TEST",
            "name": "Test Corridor",
            "flood_depth_cm": 15.0,
            "risk_level": FloodRiskLevel.MODERATE,
            "drainage_utilization_percent": 75.0,
            "excess_flow_m3s": 0.0,
            "is_surcharged": False,
            "is_low_lying": True,
            "elevation_m": 15.0,
            "slope_percent": 1.0,
            "rainfall_intensity_mm_hr": 60.0,
        }

        z_clean = dict(base_zone, blockage_percent=0.0)
        z_blocked = dict(base_zone, blockage_percent=60.0)

        p_clean = self.engine.evaluate_zone_priority(z_clean)
        p_blocked = self.engine.evaluate_zone_priority(z_blocked)

        self.assertGreater(p_blocked.priority_score, p_clean.priority_score)
        self.assertGreater(p_blocked.score_breakdown["blockage"], p_clean.score_breakdown["blockage"])

    def test_priority_level_threshold_consistency(self):
        """Verify priority levels match defined score boundaries."""
        self.assertEqual(self.engine.classify_priority_level(85.0), PriorityLevel.CRITICAL)
        self.assertEqual(self.engine.classify_priority_level(75.0), PriorityLevel.CRITICAL)
        self.assertEqual(self.engine.classify_priority_level(65.0), PriorityLevel.HIGH)
        self.assertEqual(self.engine.classify_priority_level(50.0), PriorityLevel.HIGH)
        self.assertEqual(self.engine.classify_priority_level(40.0), PriorityLevel.MEDIUM)
        self.assertEqual(self.engine.classify_priority_level(25.0), PriorityLevel.MEDIUM)
        self.assertEqual(self.engine.classify_priority_level(15.0), PriorityLevel.LOW)
        self.assertEqual(self.engine.classify_priority_level(0.0), PriorityLevel.LOW)

    def test_actions_differ_by_hydraulic_condition(self):
        """Verify that recommended actions are dynamic and condition-specific."""
        service = PriorityService()
        resp = service.get_priorities()

        actions = [p.recommended_action for p in resp.priorities]
        # Should contain multiple distinct recommendations across the catchment
        unique_actions = set(actions)
        self.assertGreaterEqual(len(unique_actions), 3)

        # Station Road with surcharge and blockage should recommend jetting / desilting
        station_rd = next(p for p in resp.priorities if p.zone_id == "Z01")
        self.assertIn("jetting", station_rd.recommended_action.lower())

        # Hilltop Avenue with nominal condition should recommend routine monitoring
        hilltop = next(p for p in resp.priorities if p.zone_name == "Hilltop Avenue")
        self.assertIn("monitoring", hilltop.recommended_action.lower())


if __name__ == "__main__":
    unittest.main()
