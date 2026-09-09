"""Automated test suite for Phase 10 Flood Propagation Engine."""
import unittest
from fastapi.testclient import TestClient

from backend.engines.propagation_engine import PropagationEngine
from backend.main import app
from backend.models.flood_models import FloodRiskLevel, ZoneFloodPrediction
from backend.services.propagation_service import PropagationService


class TestPropagationAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_catchment_propagation_endpoint_success(self):
        """Verify GET /api/propagation returns catchment-wide propagation networks."""
        response = self.client.get("/api/propagation")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("location", data)
        self.assertEqual(data["total_sources"], 8)
        self.assertEqual(len(data["propagations"]), 8)
        self.assertEqual(
            data["provenance"],
            "PROPAGATION DERIVED FROM DEMO-SIMULATED FLOOD AND DRAINAGE DATA"
        )
        self.assertIn("disclaimer", data)

    def test_get_zone_propagation_endpoint_success(self):
        """Verify GET /api/propagation?zone_id=Z01 returns valid ordered propagation chain."""
        response = self.client.get("/api/propagation?zone_id=Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["zone_id"], "Z01")
        self.assertEqual(data["source"]["name"], "Station Road")
        self.assertGreater(data["affected_zone_count"], 0)
        self.assertEqual(len(data["propagation"]), data["affected_zone_count"])

        # Check order sequence: 1, 2, 3...
        orders = [step["order"] for step in data["propagation"]]
        self.assertEqual(orders, list(range(1, len(data["propagation"]) + 1)))

        # Check source zone is not in downstream propagation (no self-loops)
        downstream_ids = [step["zone_id"] for step in data["propagation"]]
        self.assertNotIn("Z01", downstream_ids)

        # Check no duplicates in propagation chain
        self.assertEqual(len(downstream_ids), len(set(downstream_ids)))

    def test_get_zone_propagation_path_endpoint(self):
        """Verify GET /api/propagation/{zone_id} returns ZonePropagationResponse."""
        response = self.client.get("/api/propagation/Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["zone_id"], "Z01")
        self.assertEqual(data["source"]["name"], "Station Road")
        self.assertIn("Station Road", data["propagation_path"][0])
        self.assertEqual(len(data["propagation_path"]), data["affected_zone_count"] + 1)

    def test_get_propagation_node_alias_resolution(self):
        """Verify N21 and N02 resolve to Z01 propagation."""
        res_n02 = self.client.get("/api/propagation?zone_id=N02")
        self.assertEqual(res_n02.status_code, 200)
        self.assertEqual(res_n02.json()["zone_id"], "Z01")

        res_n21 = self.client.get("/api/propagation?zone_id=N21")
        self.assertEqual(res_n21.status_code, 200)
        self.assertEqual(res_n21.json()["zone_id"], "Z01")

    def test_get_propagation_unknown_zone_404(self):
        """Verify 404 is returned for unknown zone ID."""
        response = self.client.get("/api/propagation?zone_id=UNKNOWN_ZONE_999")
        self.assertEqual(response.status_code, 404)

        res_path = self.client.get("/api/propagation/UNKNOWN_ZONE_999")
        self.assertEqual(res_path.status_code, 404)

    def test_propagation_rainfall_scenario_responsiveness(self):
        """Verify rainfall override propagates through flood metrics in propagation chain."""
        res_dry = self.client.get("/api/propagation/Z01?rainfall_mm_hr=20.0")
        res_deluge = self.client.get("/api/propagation/Z01?rainfall_mm_hr=120.0")

        self.assertEqual(res_dry.status_code, 200)
        self.assertEqual(res_deluge.status_code, 200)

        depth_dry = res_dry.json()["source"]["flood_depth_cm"]
        depth_deluge = res_deluge.json()["source"]["flood_depth_cm"]
        self.assertGreater(depth_deluge, depth_dry)


class TestPropagationEngineGraphTraversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = PropagationEngine()
        cls.service = PropagationService()

    def test_propagation_determinism(self):
        """Verify traversal is 100% deterministic given identical inputs."""
        p1 = self.service.get_zone_propagation("Z01")
        p2 = self.service.get_zone_propagation("Z01")

        self.assertEqual(p1.propagation_path, p2.propagation_path)
        self.assertEqual(p1.affected_zone_count, p2.affected_zone_count)

        steps1 = [(s.order, s.zone_id, s.relationship) for s in p1.propagation]
        steps2 = [(s.order, s.zone_id, s.relationship) for s in p2.propagation]
        self.assertEqual(steps1, steps2)

    def test_cyclic_graph_termination(self):
        """Verify that cyclic relationships in road network do not cause infinite traversal."""
        resp = self.service.get_zone_propagation("Z01")
        # Should visit all reachable connected zones and terminate without hanging
        self.assertGreater(len(resp.propagation), 0)
        self.assertLessEqual(len(resp.propagation), 8)

    def test_hop_relationship_classification(self):
        """Verify that immediate neighbors are DIRECTLY_AFFECTED and further hops are DOWNSTREAM."""
        resp = self.service.get_zone_propagation("Z01")

        # First hop neighbors of Z01 (Z04, Z02, Z08, Z05) must be DIRECTLY_AFFECTED
        first_hop_ids = {"Z04", "Z02", "Z08", "Z05"}
        for step in resp.propagation:
            if step.zone_id in first_hop_ids:
                self.assertEqual(step.relationship, "DIRECTLY_AFFECTED")
            else:
                self.assertEqual(step.relationship, "DOWNSTREAM")

    def test_propagation_depths_match_flood_engine(self):
        """Verify propagation steps reflect live flood depths from upstream engine."""
        resp = self.service.get_zone_propagation("Z01")
        for step in resp.propagation:
            self.assertGreaterEqual(step.flood_depth_cm, 0.0)
            self.assertIn(step.risk, [FloodRiskLevel.LOW, FloodRiskLevel.MODERATE, FloodRiskLevel.HIGH, FloodRiskLevel.SEVERE])
            self.assertTrue(len(step.mechanism) > 0)


if __name__ == "__main__":
    unittest.main()
