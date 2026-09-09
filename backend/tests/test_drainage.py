"""Automated unit and integration tests for urban drainage network intelligence, capacity, utilization, and surcharge."""
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.engines.drainage_engine import DrainageEngine
from backend.main import app
from backend.models.drainage_models import DrainStatus
from backend.services.drainage_service import (
    DrainageFileNotFoundError,
    DrainageService,
    InvalidDrainageDataFormatError,
)


class TestDrainageHydraulicsAndEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DrainageEngine()

    def test_status_threshold_rules(self):
        """Verify centralized utilization status classification rules."""
        # < 70% -> NORMAL
        self.assertEqual(DrainageEngine.classify_drain_status(0.0), DrainStatus.NORMAL)
        self.assertEqual(DrainageEngine.classify_drain_status(69.9), DrainStatus.NORMAL)

        # 70% - 90% -> WARNING
        self.assertEqual(DrainageEngine.classify_drain_status(70.0), DrainStatus.WARNING)
        self.assertEqual(DrainageEngine.classify_drain_status(89.9), DrainStatus.WARNING)

        # 90% - 100% -> CRITICAL
        self.assertEqual(DrainageEngine.classify_drain_status(90.0), DrainStatus.CRITICAL)
        self.assertEqual(DrainageEngine.classify_drain_status(100.0), DrainStatus.CRITICAL)

        # > 100% -> SURCHARGED
        self.assertEqual(DrainageEngine.classify_drain_status(100.1), DrainStatus.SURCHARGED)
        self.assertEqual(DrainageEngine.classify_drain_status(150.0), DrainStatus.SURCHARGED)

    def test_effective_capacity_calculation(self):
        """Verify effective capacity formula: C * (1 - blockage / 100)."""
        # 0% blockage -> 100% capacity
        self.assertEqual(DrainageEngine.calculate_effective_capacity(10.0, 0.0), 10.0)

        # 30% blockage -> 70% capacity
        self.assertEqual(DrainageEngine.calculate_effective_capacity(10.0, 30.0), 7.0)

        # 100% blockage -> 0% capacity
        self.assertEqual(DrainageEngine.calculate_effective_capacity(10.0, 100.0), 0.0)

    def test_utilization_and_division_by_zero(self):
        """Verify utilization calculation and division-by-zero protection."""
        # Standard: 8 m3/s over 7 m3/s -> 114.29%
        util = DrainageEngine.calculate_utilization(8.0, 7.0)
        self.assertEqual(util, 114.29)

        # Zero flow over positive capacity -> 0%
        self.assertEqual(DrainageEngine.calculate_utilization(0.0, 5.0), 0.0)

        # Flow through zero capacity conduit -> 999.9% (SURCHARGED)
        self.assertEqual(DrainageEngine.calculate_utilization(2.0, 0.0), 999.9)

        # Zero flow through zero capacity conduit -> 0%
        self.assertEqual(DrainageEngine.calculate_utilization(0.0, 0.0), 0.0)

    def test_excess_flow_calculation(self):
        """Verify uncontained surcharge volume: max(flow - effective_cap, 0)."""
        # Surcharged case: 8.0 - 7.0 = 1.0 m3/s
        self.assertEqual(DrainageEngine.calculate_excess_flow(8.0, 7.0), 1.0)

        # Contained case: 5.0 - 7.0 = 0.0 m3/s
        self.assertEqual(DrainageEngine.calculate_excess_flow(5.0, 7.0), 0.0)

    def test_graph_construction_and_topology(self):
        """Verify directed graph builds with expected nodes, edges, and connectivity."""
        g = self.engine.build_graph()
        self.assertEqual(g.number_of_nodes(), 7)
        self.assertEqual(g.number_of_edges(), 6)

        # Verify upstream / downstream relationships
        # E01 is N07 -> N04, so predecessors of N04 includes N07
        self.assertIn("N07", list(g.predecessors("N04")))
        # Successors of N04 includes N03
        self.assertIn("N03", list(g.successors("N04")))

    def test_blockage_induced_surcharge(self):
        """Verify specific edge E03 blockage drives conduit into SURCHARGED status."""
        metrics = self.engine.evaluate_edge_metrics("E03")
        # Capacity 4.5, Blockage 30% -> Effective Cap 3.15, Flow 4.2
        self.assertEqual(metrics.capacity_m3s, 4.5)
        self.assertEqual(metrics.blockage_percent, 30.0)
        self.assertEqual(metrics.effective_capacity_m3s, 3.15)
        self.assertEqual(metrics.current_flow_m3s, 4.2)
        self.assertGreater(metrics.utilization_percent, 100.0)
        self.assertEqual(metrics.status, DrainStatus.SURCHARGED)
        self.assertTrue(metrics.is_surcharged)
        self.assertAlmostEqual(metrics.excess_flow_m3s, 1.05, places=2)

    def test_node_surcharge_evaluation(self):
        """Verify node metrics reflect arriving flow and connected conduit surcharge."""
        # N02 receives inflow from N03 and N05 and discharges to N06
        n02_metrics = self.engine.evaluate_node_metrics("N02")
        self.assertEqual(n02_metrics.node_id, "N02")
        self.assertGreater(n02_metrics.inflow_m3s, 0.0)
        # E06 is surcharged (Station Road trunk), so N02 should be surcharged
        self.assertTrue(n02_metrics.is_surcharged)
        self.assertEqual(n02_metrics.status, DrainStatus.SURCHARGED)

    def test_missing_dataset_handling(self):
        """Verify DrainageFileNotFoundError when dataset is missing."""
        bad_service = DrainageService(data_file_path=Path("non_existent_drainage.json"))
        engine = DrainageEngine(service=bad_service)
        with self.assertRaises(DrainageFileNotFoundError):
            engine.evaluate_entire_network()

    def test_corrupted_dataset_handling(self):
        """Verify InvalidDrainageDataFormatError on corrupted JSON or missing fields."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tf:
            tf.write('{"nodes": "not a list"}')
            temp_path = Path(tf.name)

        try:
            bad_service = DrainageService(data_file_path=temp_path)
            with self.assertRaises(InvalidDrainageDataFormatError):
                bad_service.load_dataset()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_edge_referencing_nonexistent_node(self):
        """Verify graph validation catches edge referencing invalid node."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tf:
            data = {
                "nodes": [{"node_id": "N01", "name": "Node 1", "latitude": 0, "longitude": 0, "elevation_m": 10, "type": "inlet"}],
                "edges": [{"edge_id": "E01", "from_node": "N01", "to_node": "NON_EXISTENT", "capacity_m3s": 2, "current_flow_m3s": 1, "length_m": 50}]
            }
            json.dump(data, tf)
            temp_path = Path(tf.name)

        try:
            bad_service = DrainageService(data_file_path=temp_path)
            engine = DrainageEngine(service=bad_service)
            with self.assertRaises(InvalidDrainageDataFormatError):
                engine.build_graph()
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestDrainageAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_drainage_full_network(self):
        """Verify GET /api/drainage returns complete network, summary, and demo labels."""
        response = self.client.get("/api/drainage")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["location"], "Demo Urban Area")
        self.assertEqual(data["data_type"], "DEMO-SIMULATED")
        self.assertIn("synthetic urban drainage", data["source_note"].lower())
        self.assertIn("drainage-capacity", data["limitation_note"].lower())

        summary = data["summary"]
        self.assertEqual(summary["total_nodes"], 7)
        self.assertEqual(summary["total_edges"], 6)
        self.assertGreater(summary["surcharged_drains"], 0)
        self.assertGreater(summary["max_utilization_percent"], 100.0)

        # Verify sum of categories equals total edges
        cat_sum = (
            summary["normal_drains"]
            + summary["warning_drains"]
            + summary["critical_drains"]
            + summary["surcharged_drains"]
        )
        self.assertEqual(cat_sum, summary["total_edges"])

        # Check drains list
        self.assertEqual(len(data["drains"]), 6)
        e03 = next(d for d in data["drains"] if d["edge_id"] == "E03")
        self.assertEqual(e03["status"], "SURCHARGED")
        self.assertTrue(e03["is_surcharged"])

    def test_get_drainage_filter_by_node(self):
        """Verify GET /api/drainage?node_id=N02 returns node and connected conduits."""
        response = self.client.get("/api/drainage?node_id=N02")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["nodes"]), 1)
        self.assertEqual(data["nodes"][0]["node_id"], "N02")

        # Conduits connected to N02: E03 (to N02), E04 (to N02), E06 (from N02)
        edge_ids = [d["edge_id"] for d in data["drains"]]
        self.assertIn("E03", edge_ids)
        self.assertIn("E04", edge_ids)
        self.assertIn("E06", edge_ids)

    def test_get_drainage_filter_by_edge(self):
        """Verify GET /api/drainage?edge_id=E03 returns single conduit."""
        response = self.client.get("/api/drainage?edge_id=E03")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["drains"]), 1)
        self.assertEqual(data["drains"][0]["edge_id"], "E03")
        self.assertEqual(data["drains"][0]["street_name"], "Hospital Access Road")

    def test_get_drainage_filter_by_status(self):
        """Verify GET /api/drainage?status_filter=SURCHARGED returns only surcharged conduits."""
        response = self.client.get("/api/drainage?status_filter=SURCHARGED")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertGreater(len(data["drains"]), 0)
        for drain in data["drains"]:
            self.assertEqual(drain["status"], "SURCHARGED")

    def test_get_drainage_nonexistent_node_404(self):
        """Verify 404 is returned when filtering for an unknown node ID."""
        response = self.client.get("/api/drainage?node_id=UNKNOWN99")
        self.assertEqual(response.status_code, 404)

    def test_get_drainage_nonexistent_edge_404(self):
        """Verify 404 is returned when filtering for an unknown edge ID."""
        response = self.client.get("/api/drainage?edge_id=EDGE99")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
