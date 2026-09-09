"""Automated test suite for Phase 8 WHAT-IF flood simulation, scenario validation, and dynamic hydraulic comparison."""
import unittest
from fastapi.testclient import TestClient

from backend.engines.simulation_engine import SimulationEngine
from backend.main import app
from backend.models.simulation_models import (
    SimulationImpact,
    SimulationRequest,
)


class TestSimulationAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_simulation_endpoint_success_full_catchment(self):
        """Verify POST /api/simulate returns 200 and evaluates all 8 catchment zones."""
        payload = {"rainfall_mm_hr": 100.0}
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("scenario_name", data)
        self.assertIn("summary", data)
        self.assertEqual(data["summary"]["total_zones_simulated"], 8)
        self.assertEqual(len(data["results"]), 8)
        self.assertEqual(
            data["data_provenance"],
            "SCENARIO SIMULATION USING MODEL-DERIVED FLOOD AND DEMO INPUTS"
        )
        self.assertIn("disclaimer", data)

        # Validate zone comparison fields
        for res in data["results"]:
            self.assertIn("zone_id", res)
            self.assertIn("name", res)
            self.assertIn("baseline_flood_depth_cm", res)
            self.assertIn("simulated_flood_depth_cm", res)
            self.assertIn("depth_change_cm", res)
            self.assertIn("baseline_risk_level", res)
            self.assertIn("simulated_risk_level", res)
            self.assertIn("impact", res)
            self.assertIn(res["impact"], ["IMPROVED", "UNCHANGED", "WORSENED"])

            # Verify depth change formula exactness
            expected_change = round(res["simulated_flood_depth_cm"] - res["baseline_flood_depth_cm"], 1)
            self.assertAlmostEqual(res["depth_change_cm"], expected_change, places=1)

    def test_simulation_filter_by_zone(self):
        """Verify simulation restricted to a single zone."""
        payload = {"rainfall_mm_hr": 120.0, "zone_id": "Z01"}
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["summary"]["total_zones_simulated"], 1)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["zone_id"], "Z01")
        self.assertEqual(data["results"][0]["name"], "Station Road")

    def test_simulation_nonexistent_zone_404(self):
        """Verify 404 is returned when specifying an unknown zone ID."""
        payload = {"rainfall_mm_hr": 100.0, "zone_id": "UNKNOWN_ZONE_999"}
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_validation_negative_rainfall_422(self):
        """Verify 422 returned for negative rainfall."""
        payload = {"rainfall_mm_hr": -15.0}
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_validation_blockage_below_zero_422(self):
        """Verify 422 returned for negative blockage."""
        payload = {"blockage_percent": -5.0}
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_validation_blockage_above_100_422(self):
        """Verify 422 returned for blockage > 100."""
        payload = {"blockage_percent": 120.0}
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_validation_missing_simulation_parameters_422(self):
        """Verify 422 returned when no scenario parameters are provided."""
        # Empty payload
        res1 = self.client.post("/api/simulate", json={})
        self.assertEqual(res1.status_code, 422)

        # Only zone_id supplied without any scenario changes
        res2 = self.client.post("/api/simulate", json={"zone_id": "Z01"})
        self.assertEqual(res2.status_code, 422)

    def test_combined_scenario_execution(self):
        """Verify simultaneous rainfall and blockage scenario execution."""
        payload = {"rainfall_mm_hr": 120.0, "blockage_percent": 50.0}
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("Combined scenario", data["scenario_name"])
        self.assertEqual(data["parameters_applied"]["rainfall_mm_hr"], 120.0)
        self.assertEqual(data["parameters_applied"]["blockage_percent"], 50.0)

        # Station Road (Z01) should experience higher flood depth under combined heavy stress
        station_rd = next(r for r in data["results"] if r["zone_id"] == "Z01")
        self.assertGreater(station_rd["simulated_flood_depth_cm"], station_rd["baseline_flood_depth_cm"])
        self.assertEqual(station_rd["impact"], "WORSENED")


class TestSimulationEngineHydraulics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = SimulationEngine()

    def test_higher_rainfall_increases_depth_monotonically(self):
        """Dynamic hydraulic test: Increasing rainfall intensity systematically increases flood depths."""
        resp_moderate = self.engine.run_simulation(rainfall_mm_hr=40.0, zone_id="Z01")
        resp_deluge = self.engine.run_simulation(rainfall_mm_hr=120.0, zone_id="Z01")

        depth_mod = resp_moderate.results[0].simulated_flood_depth_cm
        depth_deluge = resp_deluge.results[0].simulated_flood_depth_cm

        self.assertGreater(depth_deluge, depth_mod)
        self.assertGreater(resp_deluge.results[0].depth_change_cm, resp_moderate.results[0].depth_change_cm)

    def test_higher_blockage_worsens_drainage_and_flood_conditions(self):
        """Dynamic hydraulic test: Increasing blockage reduces effective capacity and worsens inundation."""
        resp_clear = self.engine.run_simulation(blockage_percent=0.0, zone_id="Z01")
        resp_choked = self.engine.run_simulation(blockage_percent=60.0, zone_id="Z01")

        z_clear = resp_clear.results[0]
        z_choked = resp_choked.results[0]

        # Effective capacity lower and depth higher under 60% blockage
        self.assertGreater(z_choked.simulated_drainage_utilization_percent, z_clear.simulated_drainage_utilization_percent)
        self.assertGreater(z_choked.simulated_flood_depth_cm, z_clear.simulated_flood_depth_cm)

    def test_drainage_clearing_scenario_improves_conditions(self):
        """Dynamic hydraulic test: 0% blockage scenario improves or maintains conditions compared to blocked baseline."""
        # Baseline Z01 has 30% blockage
        resp = self.engine.run_simulation(blockage_percent=0.0, zone_id="Z01")
        z01 = resp.results[0]

        # Clearing blockage to 0% should reduce flood depth and excess flow
        self.assertLess(z01.simulated_flood_depth_cm, z01.baseline_flood_depth_cm)
        self.assertEqual(z01.impact, SimulationImpact.IMPROVED)
        self.assertLess(z01.simulated_excess_flow_m3s, z01.baseline_excess_flow_m3s)

    def test_different_scenarios_produce_distinct_results(self):
        """Verify different scenarios produce dynamically distinct simulation results."""
        resp_a = self.engine.run_simulation(rainfall_mm_hr=70.0)
        resp_b = self.engine.run_simulation(rainfall_mm_hr=130.0)

        depths_a = [z.simulated_flood_depth_cm for z in resp_a.results]
        depths_b = [z.simulated_flood_depth_cm for z in resp_b.results]

        self.assertNotEqual(depths_a, depths_b)
        self.assertNotEqual(resp_a.summary.avg_depth_change_cm, resp_b.summary.avg_depth_change_cm)

    def test_depth_change_exactness(self):
        """Verify exact calculation: depth_change_cm = simulated_depth - baseline_depth."""
        resp = self.engine.run_simulation(rainfall_mm_hr=110.0, blockage_percent=40.0)
        for z in resp.results:
            calc_diff = round(z.simulated_flood_depth_cm - z.baseline_flood_depth_cm, 1)
            self.assertEqual(z.depth_change_cm, calc_diff)


if __name__ == "__main__":
    unittest.main()
