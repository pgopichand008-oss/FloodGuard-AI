"""Automated test suite for Phase 7 WHY-FLOOD explainability engine, factor attribution, and API endpoints."""
import unittest
from fastapi.testclient import TestClient

from backend.engines.explain_engine import ExplainEngine
from backend.main import app
from backend.models.explain_models import (
    ContributionLevel,
    FactorSeverity,
    ZoneExplanation,
)
from backend.models.flood_models import FloodRiskLevel
from backend.services.explain_service import ExplainService


class TestExplainAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_explanations_full_catchment(self):
        """Verify GET /api/explanations returns structured explanations for all 8 zones."""
        response = self.client.get("/api/explanations")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_zones_explained"], 8)
        self.assertEqual(len(data["explanations"]), 8)
        self.assertEqual(
            data["data_provenance"],
            "RULE-BASED EXPLANATION FROM MODEL-DERIVED AND DEMO-SIMULATED INPUTS"
        )
        self.assertIn("disclaimer", data)
        self.assertIn("primary_causes_summary", data)
        self.assertGreater(len(data["primary_causes_summary"]), 0)

        # Inspect individual zone explanation contract
        for exp in data["explanations"]:
            self.assertIn("zone_id", exp)
            self.assertIn("name", exp)
            self.assertIn("risk_level", exp)
            self.assertGreaterEqual(exp["flood_depth_cm"], 0.0)
            self.assertTrue(len(exp["primary_cause"]) > 0)
            self.assertTrue(len(exp["summary_explanation"]) > 0)
            self.assertGreaterEqual(len(exp["contributing_factors"]), 5)
            self.assertIn("evidence", exp)
            self.assertIn("data_provenance", exp)

            # Check contributing factor structure
            for factor in exp["contributing_factors"]:
                self.assertIn("factor", factor)
                self.assertIn(factor["severity"], ["NEGLIGIBLE", "MODERATE", "HIGH", "CRITICAL"])
                self.assertIn(factor["contribution"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])
                self.assertGreaterEqual(factor["contribution_score"], 0.0)
                self.assertLessEqual(factor["contribution_score"], 1.0)
                self.assertTrue(len(factor["explanation"]) > 0)

    def test_get_explanations_filter_by_zone(self):
        """Verify GET /api/explanations?zone_id=Z01 filters to single requested zone."""
        response = self.client.get("/api/explanations?zone_id=Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_zones_explained"], 1)
        self.assertEqual(len(data["explanations"]), 1)
        exp = data["explanations"][0]
        self.assertEqual(exp["zone_id"], "Z01")
        self.assertEqual(exp["name"], "Station Road")
        self.assertIn("Surcharge", exp["primary_cause"])

    def test_get_zone_explanation_path_endpoint(self):
        """Verify GET /api/explanations/{zone_id} returns ZoneExplanation directly."""
        response = self.client.get("/api/explanations/Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["zone_id"], "Z01")
        self.assertEqual(data["name"], "Station Road")
        self.assertEqual(data["risk_level"], "HIGH")
        self.assertGreaterEqual(data["flood_depth_cm"], 30.0)
        self.assertIn("Surcharge", data["primary_cause"])
        self.assertTrue(len(data["summary_explanation"]) > 0)
        self.assertIn("Station Road", data["summary_explanation"])

    def test_get_explanations_nonexistent_zone_query_404(self):
        """Verify 404 when querying unknown zone_id via query parameter."""
        response = self.client.get("/api/explanations?zone_id=NONEXISTENT_ZONE_999")
        self.assertEqual(response.status_code, 404)

    def test_get_zone_explanation_nonexistent_zone_path_404(self):
        """Verify 404 when querying unknown zone_id via path parameter."""
        response = self.client.get("/api/explanations/NONEXISTENT_ZONE_999")
        self.assertEqual(response.status_code, 404)

    def test_get_explanations_rainfall_override(self):
        """Verify rainfall_mm_hr override modifies explanation factors and text."""
        res_dry = self.client.get("/api/explanations/Z01?rainfall_mm_hr=10.0")
        res_deluge = self.client.get("/api/explanations/Z01?rainfall_mm_hr=130.0")

        self.assertEqual(res_dry.status_code, 200)
        self.assertEqual(res_deluge.status_code, 200)

        dry_factors = {f["factor"]: f for f in res_dry.json()["contributing_factors"]}
        deluge_factors = {f["factor"]: f for f in res_deluge.json()["contributing_factors"]}

        self.assertLess(
            dry_factors["Rainfall Intensity"]["contribution_score"],
            deluge_factors["Rainfall Intensity"]["contribution_score"]
        )


class TestExplainEngineHydraulicAttribution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ExplainEngine()

    def test_engine_initialization(self):
        """Verify engine initialization and threshold definitions."""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.RAINFALL_THRESHOLD_CRITICAL_MM_HR, 80.0)
        self.assertEqual(self.engine.UTILIZATION_THRESHOLD_CRITICAL_PCT, 100.0)

    def test_rainfall_factor_dynamic_responsiveness(self):
        """Dynamic test: Increasing rainfall intensity systematically increases contribution score."""
        f_dry = self.engine.evaluate_rainfall_factor(0.0)
        f_light = self.engine.evaluate_rainfall_factor(15.0)
        f_moderate = self.engine.evaluate_rainfall_factor(35.0)
        f_heavy = self.engine.evaluate_rainfall_factor(65.0)
        f_torrential = self.engine.evaluate_rainfall_factor(110.0)

        self.assertEqual(f_dry.contribution_score, 0.0)
        self.assertLess(f_light.contribution_score, f_moderate.contribution_score)
        self.assertLess(f_moderate.contribution_score, f_heavy.contribution_score)
        self.assertLess(f_heavy.contribution_score, f_torrential.contribution_score)
        self.assertEqual(f_torrential.severity, FactorSeverity.CRITICAL)

    def test_drainage_utilization_responsiveness(self):
        """Dynamic test: Higher pipe utilization produces higher contribution score and severity."""
        f_idle = self.engine.evaluate_drainage_utilization_factor(25.0)
        f_moderate = self.engine.evaluate_drainage_utilization_factor(70.0)
        f_stressed = self.engine.evaluate_drainage_utilization_factor(92.0)
        f_overloaded = self.engine.evaluate_drainage_utilization_factor(135.0)

        self.assertLess(f_idle.contribution_score, f_moderate.contribution_score)
        self.assertLess(f_moderate.contribution_score, f_stressed.contribution_score)
        self.assertLess(f_stressed.contribution_score, f_overloaded.contribution_score)
        self.assertEqual(f_overloaded.severity, FactorSeverity.CRITICAL)
        self.assertEqual(f_overloaded.contribution, ContributionLevel.CRITICAL)

    def test_surcharge_dominance(self):
        """Dynamic test: Active conduit surcharge produces high/critical contribution score."""
        f_contained = self.engine.evaluate_surcharge_factor(0.0, is_surcharged=False)
        f_minor = self.engine.evaluate_surcharge_factor(0.05, is_surcharged=True)
        f_severe = self.engine.evaluate_surcharge_factor(1.20, is_surcharged=True)

        self.assertEqual(f_contained.contribution_score, 0.0)
        self.assertGreater(f_minor.contribution_score, 0.3)
        self.assertGreaterEqual(f_severe.contribution_score, 0.85)
        self.assertEqual(f_severe.severity, FactorSeverity.CRITICAL)

    def test_blockage_responsiveness(self):
        """Dynamic test: Increasing conduit blockage percentage increases attribution score."""
        f_clear = self.engine.evaluate_blockage_factor(0.0)
        f_choked = self.engine.evaluate_blockage_factor(40.0)

        self.assertEqual(f_clear.contribution_score, 0.0)
        self.assertGreaterEqual(f_choked.contribution_score, 0.80)
        self.assertEqual(f_choked.severity, FactorSeverity.CRITICAL)

    def test_terrain_elevation_and_depression_responsiveness(self):
        """Dynamic test: Low-lying depression scores higher terrain contribution than elevated hilltops."""
        f_low_lying = self.engine.evaluate_terrain_factor(elevation_m=11.5, slope_pct=0.4, is_low_lying=True)
        f_hilltop = self.engine.evaluate_terrain_factor(elevation_m=42.0, slope_pct=5.5, is_low_lying=False)

        self.assertGreater(f_low_lying.contribution_score, f_hilltop.contribution_score)
        self.assertIn("depression", f_low_lying.explanation.lower())
        self.assertIn("shedding", f_hilltop.explanation.lower())

    def test_zero_rainfall_or_minimal_inundation_explanation(self):
        """Dynamic test: Nominal conditions produce appropriate minimal inundation cause."""
        nominal_zone = {
            "zone_id": "Z99",
            "name": "High Meadow",
            "elevation_m": 45.0,
            "slope_percent": 4.0,
            "is_low_lying": False,
            "rainfall_intensity_mm_hr": 0.0,
            "runoff_discharge_m3s": 0.0,
            "drainage_capacity_m3s": 4.0,
            "drainage_effective_capacity_m3s": 4.0,
            "drainage_utilization_percent": 0.0,
            "blockage_percent": 0.0,
            "excess_flow_m3s": 0.0,
            "is_surcharged": False,
            "flood_depth_cm": 0.0,
            "risk_level": FloodRiskLevel.LOW,
        }

        exp = self.engine.explain_zone(nominal_zone)
        self.assertIn("Nominal", exp.primary_cause)
        self.assertIn("LOW", exp.summary_explanation)
        self.assertEqual(exp.flood_depth_cm, 0.0)

    def test_primary_causes_vary_across_zones(self):
        """Verify that primary causes are dynamically differentiated across different urban zones."""
        service = ExplainService()
        response = service.get_explanations()

        station_road = next(z for z in response.explanations if z.name == "Station Road")
        hilltop = next(z for z in response.explanations if z.name == "Hilltop Avenue")

        self.assertNotEqual(station_road.primary_cause, hilltop.primary_cause)
        self.assertIn("Surcharge", station_road.primary_cause)
        self.assertIn("Runoff Shedding", hilltop.primary_cause)


if __name__ == "__main__":
    unittest.main()
