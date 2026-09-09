"""Automated tests for Phase 5 integrated flood intelligence, depth calculations, and risk relationships."""
import unittest
from fastapi.testclient import TestClient

from backend.engines.flood_engine import FloodEngine
from backend.main import app
from backend.models.flood_models import FloodRiskLevel
from backend.services.flood_service import FloodService


class TestFloodAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_flood_success_and_contract_compatibility(self):
        """Verify GET /api/flood returns calculated flood intelligence and preserves baseline contract."""
        response = self.client.get("/api/flood")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # Baseline contract checks
        self.assertEqual(data["location"], "Demo Urban Area")
        self.assertIn("timestamp", data)
        self.assertIn("rainfall", data)
        self.assertIn("flood", data)
        self.assertIn("forecast", data)
        self.assertIsInstance(data["forecast"], list)
        self.assertGreater(len(data["forecast"]), 0)

        # Baseline flood dict contract
        self.assertIn("risk", data["flood"])
        self.assertIn(data["flood"]["risk"], ["LOW", "MODERATE", "HIGH", "SEVERE"])
        self.assertGreater(data["flood"]["peak_depth_cm"], 0)
        self.assertGreaterEqual(data["flood"]["affected_roads"], 1)

        # Extended Phase 5 intelligence checks
        self.assertEqual(data["data_type"], "MODEL-DERIVED FROM DEMO-SIMULATED INPUTS")
        self.assertIn("summary", data)
        self.assertIn("zones", data)
        self.assertEqual(len(data["zones"]), 8)

        # Provenance and methodology disclosures
        self.assertIn("physics-informed", data["methodology"].lower())
        self.assertGreater(len(data["assumptions"]), 0)
        self.assertIn("prototype flood intelligence", data["limitation_note"].lower())

    def test_get_flood_filter_by_zone(self):
        """Verify GET /api/flood?zone_id=Z01 filters to single street/zone."""
        response = self.client.get("/api/flood?zone_id=Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["zones"]), 1)
        zone = data["zones"][0]
        self.assertEqual(zone["zone_id"], "Z01")
        self.assertEqual(zone["name"], "Station Road")
        self.assertGreater(zone["flood_depth_cm"], 0.0)

    def test_get_flood_filter_by_risk_level(self):
        """Verify GET /api/flood?risk_level=HIGH filters to zones matching the risk level."""
        response = self.client.get("/api/flood?risk_level=HIGH")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        for zone in data["zones"]:
            self.assertEqual(zone["risk_level"], "HIGH")

    def test_get_flood_rainfall_override(self):
        """Verify rainfall_mm_hr query parameter dynamically alters flood depth."""
        res_low = self.client.get("/api/flood?rainfall_mm_hr=20.0&zone_id=Z01")
        res_high = self.client.get("/api/flood?rainfall_mm_hr=100.0&zone_id=Z01")

        self.assertEqual(res_low.status_code, 200)
        self.assertEqual(res_high.status_code, 200)

        depth_low = res_low.json()["zones"][0]["flood_depth_cm"]
        depth_high = res_high.json()["zones"][0]["flood_depth_cm"]
        self.assertGreater(depth_high, depth_low)

    def test_get_flood_nonexistent_zone_404(self):
        """Verify 404 is returned when filtering for an unknown zone ID."""
        response = self.client.get("/api/flood?zone_id=UNKNOWN_ZONE_99")
        self.assertEqual(response.status_code, 404)

    def test_get_flood_invalid_risk_level_422(self):
        """Verify 422 is returned when invalid risk level string is provided."""
        response = self.client.get("/api/flood?risk_level=EXTREME_DANGER")
        self.assertEqual(response.status_code, 422)


class TestFloodEngineHydraulicRelationships(unittest.TestCase):
    def setUp(self):
        self.engine = FloodEngine()

    def test_flood_engine_initialization(self):
        """Verify flood engine successfully initializes with dependencies."""
        self.assertIsNotNone(self.engine.rainfall_engine)
        self.assertIsNotNone(self.engine.terrain_engine)
        self.assertIsNotNone(self.engine.drainage_engine)

    def test_zero_rainfall_produces_zero_depth(self):
        """Relationship: When rainfall is 0.0 mm/hr, surface flood depth must be 0.0 cm."""
        resp = self.engine.generate_flood_prediction(rainfall_override_mm_hr=0.0)
        for zone in resp.zones:
            self.assertEqual(zone.flood_depth_cm, 0.0)
            self.assertEqual(zone.risk_level, FloodRiskLevel.LOW)
        self.assertEqual(resp.summary.max_flood_depth_cm, 0.0)
        self.assertEqual(resp.summary.low_risk_zones, len(resp.zones))

    def test_rainfall_depth_monotonicity(self):
        """Relationship: Higher rainfall must produce greater or equal flood depth."""
        zone_id = "Z01"
        resp_30 = self.engine.generate_flood_prediction(rainfall_override_mm_hr=30.0, zone_id=zone_id)
        resp_60 = self.engine.generate_flood_prediction(rainfall_override_mm_hr=60.0, zone_id=zone_id)
        resp_100 = self.engine.generate_flood_prediction(rainfall_override_mm_hr=100.0, zone_id=zone_id)

        depth_30 = resp_30.zones[0].flood_depth_cm
        depth_60 = resp_60.zones[0].flood_depth_cm
        depth_100 = resp_100.zones[0].flood_depth_cm

        self.assertLess(depth_30, depth_60)
        self.assertLess(depth_60, depth_100)

    def test_blockage_increases_flood_depth(self):
        """Relationship: Increasing pipe blockage must increase surface flood depth."""
        # Calculate depth with 0% blockage vs 50% blockage
        depth_unblocked = self.engine.calculate_zone_flood_depth(
            rainfall_mm_hr=80.0,
            flood_prone_index=0.80,
            accumulation_index=0.70,
            excess_flow_m3s=0.5,
            utilization_percent=85.0,
            blockage_percent=0.0,
        )
        depth_blocked = self.engine.calculate_zone_flood_depth(
            rainfall_mm_hr=80.0,
            flood_prone_index=0.80,
            accumulation_index=0.70,
            excess_flow_m3s=1.2,
            utilization_percent=130.0,
            blockage_percent=50.0,
        )
        self.assertGreater(depth_blocked, depth_unblocked)

    def test_surcharge_increases_flood_depth(self):
        """Relationship: Drainage surcharge overflow directly increases flood depth."""
        depth_no_excess = self.engine.calculate_zone_flood_depth(
            rainfall_mm_hr=80.0,
            flood_prone_index=0.75,
            accumulation_index=0.60,
            excess_flow_m3s=0.0,
            utilization_percent=80.0,
            blockage_percent=10.0,
        )
        depth_with_excess = self.engine.calculate_zone_flood_depth(
            rainfall_mm_hr=80.0,
            flood_prone_index=0.75,
            accumulation_index=0.60,
            excess_flow_m3s=1.5,
            utilization_percent=125.0,
            blockage_percent=10.0,
        )
        self.assertGreater(depth_with_excess, depth_no_excess)

    def test_low_lying_vs_elevated_vulnerability(self):
        """Relationship: Under identical storm intensity, low-lying terrain exhibits greater flood severity than hilltop."""
        resp = self.engine.generate_flood_prediction(rainfall_override_mm_hr=85.0)
        station_rd = next(z for z in resp.zones if z.name == "Station Road")
        hilltop = next(z for z in resp.zones if z.name == "Hilltop Avenue")

        self.assertTrue(station_rd.is_low_lying)
        self.assertFalse(hilltop.is_low_lying)
        self.assertGreater(station_rd.flood_depth_cm, hilltop.flood_depth_cm)
        self.assertIn(station_rd.risk_level, [FloodRiskLevel.HIGH, FloodRiskLevel.SEVERE])
        self.assertEqual(hilltop.risk_level, FloodRiskLevel.LOW)

    def test_risk_level_classification_rules(self):
        """Verify centralized risk classification boundaries."""
        # < 15 -> LOW
        self.assertEqual(FloodEngine.classify_flood_risk(0.0), FloodRiskLevel.LOW)
        self.assertEqual(FloodEngine.classify_flood_risk(14.9), FloodRiskLevel.LOW)

        # 15 - 30 -> MODERATE
        self.assertEqual(FloodEngine.classify_flood_risk(15.0), FloodRiskLevel.MODERATE)
        self.assertEqual(FloodEngine.classify_flood_risk(29.9), FloodRiskLevel.MODERATE)

        # 30 - 50 -> HIGH
        self.assertEqual(FloodEngine.classify_flood_risk(30.0), FloodRiskLevel.HIGH)
        self.assertEqual(FloodEngine.classify_flood_risk(49.9), FloodRiskLevel.HIGH)

        # >= 50 -> SEVERE
        self.assertEqual(FloodEngine.classify_flood_risk(50.0), FloodRiskLevel.SEVERE)
        self.assertEqual(FloodEngine.classify_flood_risk(85.0), FloodRiskLevel.SEVERE)

    def test_summary_metrics_consistency(self):
        """Verify summary counts match zone classification totals."""
        resp = self.engine.generate_flood_prediction()
        summary = resp.summary

        # Sum of categories must equal total zones
        cat_sum = (
            summary.low_risk_zones
            + summary.moderate_risk_zones
            + summary.high_risk_zones
            + summary.severe_risk_zones
        )
        self.assertEqual(cat_sum, summary.total_zones)
        self.assertEqual(summary.total_zones, len(resp.zones))

        # Max depth matches highest zone depth
        actual_max = max(z.peak_depth_cm for z in resp.zones)
        self.assertEqual(summary.max_flood_depth_cm, actual_max)

    def test_forecast_progression_sequence(self):
        """Verify 0-180 minute dynamic depth forecast sequence is produced."""
        resp = self.engine.generate_flood_prediction()
        self.assertEqual(len(resp.forecast), 7)
        minutes_seq = [fp.minutes for fp in resp.forecast]
        self.assertEqual(minutes_seq, [0, 30, 60, 90, 120, 150, 180])
        # Depth is positive during storm
        for fp in resp.forecast:
            self.assertGreater(fp.depth_cm, 0.0)


if __name__ == "__main__":
    unittest.main()
