"""Automated tests for Phase 6 machine learning prediction engine, model training, and API endpoints."""
import unittest
from fastapi.testclient import TestClient

from backend.engines.ml_engine import MLEngine
from backend.main import app
from backend.models.flood_models import FloodRiskLevel
from backend.services.ml_service import MLService


class TestMLAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_ml_status_endpoint(self):
        """Verify GET /api/ml/status returns loaded status, features, and synthetic validation scores."""
        response = self.client.get("/api/ml/status")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["model_loaded"])
        self.assertIn("RandomForest", data["model_type"])
        self.assertGreater(data["training_samples"], 100)
        self.assertEqual(len(data["features"]), 15)
        self.assertEqual(data["data_provenance"], "SYNTHETIC ML TRAINING DATA")
        self.assertIn("synthetic", data["disclaimer"].lower())

        # Check validation metrics
        metrics = data["validation_metrics"]
        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("r2_score", metrics)
        self.assertIn("classification_accuracy", metrics)
        self.assertIn("f1_score", metrics)
        self.assertGreater(metrics["r2_score"], 0.85)

    def test_get_ml_predict_full_catchment(self):
        """Verify GET /api/ml/predict returns zone predictions, probabilities, and confidence."""
        response = self.client.get("/api/ml/predict")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["data_type"], "ML-DERIVED FROM SYNTHETICALLY TRAINED MODEL USING DEMO-SIMULATED INPUTS")
        self.assertEqual(data["total_zones_predicted"], 8)
        self.assertEqual(len(data["predictions"]), 8)
        self.assertEqual(len(data["features_used"]), 15)

        for pred in data["predictions"]:
            self.assertGreaterEqual(pred["predicted_flood_depth_cm"], 0.0)
            self.assertIn(pred["predicted_risk_level"], ["LOW", "MODERATE", "HIGH", "SEVERE"])
            self.assertGreaterEqual(pred["flood_probability"], 0.0)
            self.assertLessEqual(pred["flood_probability"], 1.0)
            self.assertGreaterEqual(pred["model_confidence"], 0.0)
            self.assertLessEqual(pred["model_confidence"], 1.0)
            self.assertIn("delta_depth_cm", pred)

    def test_get_ml_predict_filter_by_zone(self):
        """Verify GET /api/ml/predict?zone_id=Z01 returns prediction for specific zone."""
        response = self.client.get("/api/ml/predict?zone_id=Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["predictions"]), 1)
        pred = data["predictions"][0]
        self.assertEqual(pred["zone_id"], "Z01")
        self.assertEqual(pred["name"], "Station Road")

    def test_get_ml_predict_rainfall_override(self):
        """Verify rainfall_mm_hr query parameter affects ML predicted depth."""
        res_low = self.client.get("/api/ml/predict?rainfall_mm_hr=20.0&zone_id=Z01")
        res_high = self.client.get("/api/ml/predict?rainfall_mm_hr=100.0&zone_id=Z01")

        self.assertEqual(res_low.status_code, 200)
        self.assertEqual(res_high.status_code, 200)

        depth_low = res_low.json()["predictions"][0]["predicted_flood_depth_cm"]
        depth_high = res_high.json()["predictions"][0]["predicted_flood_depth_cm"]
        self.assertGreater(depth_high, depth_low)

    def test_get_ml_predict_nonexistent_zone_404(self):
        """Verify 404 is returned when filtering for an unknown zone ID."""
        response = self.client.get("/api/ml/predict?zone_id=UNKNOWN_ZONE_99")
        self.assertEqual(response.status_code, 404)


class TestMLEngineAndHydraulicRelationships(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = MLEngine(random_state=42, auto_train=True)

    def test_engine_initialization_and_training(self):
        """Verify model training and synthetic data dimensions."""
        self.assertTrue(self.engine._is_trained)
        self.assertIsNotNone(self.engine.regressor)
        self.assertIsNotNone(self.engine.classifier)
        self.assertEqual(self.engine.training_samples_count, 600)

    def test_training_reproducibility(self):
        """Verify fixed random seed produces identical predictions."""
        engine_a = MLEngine(random_state=42, auto_train=True)
        engine_b = MLEngine(random_state=42, auto_train=True)

        sample_features = {
            "rainfall_intensity_mm_hr": 80.0,
            "forecast_peak_rainfall_mm_hr": 95.0,
            "elevation_m": 12.0,
            "slope_percent": 0.6,
            "flow_accumulation": 1800.0,
            "imperviousness": 0.88,
            "runoff_coefficient_c": 0.85,
            "runoff_discharge_m3_s": 0.8,
            "is_low_lying": 1.0,
            "drainage_capacity_m3s": 4.0,
            "drainage_effective_capacity_m3s": 3.0,
            "drainage_utilization_percent": 110.0,
            "blockage_percent": 25.0,
            "excess_flow_m3s": 0.4,
            "physics_flood_depth_cm": 35.0,
        }

        pred_a = engine_a.predict_zone(sample_features)
        pred_b = engine_b.predict_zone(sample_features)
        self.assertEqual(pred_a[0], pred_b[0])
        self.assertEqual(pred_a[1], pred_b[1])
        self.assertEqual(pred_a[2], pred_b[2])

    def test_zero_rainfall_produces_zero_prediction(self):
        """Relationship: Zero rainfall must yield zero predicted flood depth."""
        zero_features = {
            "rainfall_intensity_mm_hr": 0.0,
            "forecast_peak_rainfall_mm_hr": 0.0,
            "elevation_m": 12.0,
            "slope_percent": 0.6,
            "flow_accumulation": 1800.0,
            "imperviousness": 0.88,
            "runoff_coefficient_c": 0.85,
            "runoff_discharge_m3_s": 0.0,
            "is_low_lying": 1.0,
            "drainage_capacity_m3s": 4.0,
            "drainage_effective_capacity_m3s": 4.0,
            "drainage_utilization_percent": 0.0,
            "blockage_percent": 0.0,
            "excess_flow_m3s": 0.0,
            "physics_flood_depth_cm": 0.0,
        }
        depth, risk, prob, conf = self.engine.predict_zone(zero_features)
        self.assertEqual(depth, 0.0)
        self.assertEqual(risk, FloodRiskLevel.LOW)
        self.assertEqual(prob, 0.0)

    def test_rainfall_depth_monotonicity(self):
        """Relationship: Higher rainfall generally produces higher ML predicted flood depth."""
        base_features = {
            "forecast_peak_rainfall_mm_hr": 100.0,
            "elevation_m": 12.0,
            "slope_percent": 0.6,
            "flow_accumulation": 1800.0,
            "imperviousness": 0.88,
            "runoff_coefficient_c": 0.85,
            "runoff_discharge_m3_s": 0.6,
            "is_low_lying": 1.0,
            "drainage_capacity_m3s": 4.0,
            "drainage_effective_capacity_m3s": 3.0,
            "drainage_utilization_percent": 90.0,
            "blockage_percent": 15.0,
            "excess_flow_m3s": 0.1,
            "physics_flood_depth_cm": 20.0,
        }

        f_light = dict(base_features, rainfall_intensity_mm_hr=25.0, physics_flood_depth_cm=8.0)
        f_medium = dict(base_features, rainfall_intensity_mm_hr=60.0, physics_flood_depth_cm=22.0)
        f_heavy = dict(base_features, rainfall_intensity_mm_hr=110.0, physics_flood_depth_cm=45.0)

        depth_light, _, _, _ = self.engine.predict_zone(f_light)
        depth_medium, _, _, _ = self.engine.predict_zone(f_medium)
        depth_heavy, _, _, _ = self.engine.predict_zone(f_heavy)

        self.assertLess(depth_light, depth_medium)
        self.assertLess(depth_medium, depth_heavy)

    def test_blockage_and_surcharge_increases_risk(self):
        """Relationship: Higher drainage blockage and surcharge increases predicted hazard."""
        f_clean = {
            "rainfall_intensity_mm_hr": 75.0,
            "forecast_peak_rainfall_mm_hr": 85.0,
            "elevation_m": 14.0,
            "slope_percent": 1.0,
            "flow_accumulation": 1200.0,
            "imperviousness": 0.80,
            "runoff_coefficient_c": 0.80,
            "runoff_discharge_m3_s": 0.5,
            "is_low_lying": 1.0,
            "drainage_capacity_m3s": 4.5,
            "drainage_effective_capacity_m3s": 4.5,
            "drainage_utilization_percent": 60.0,
            "blockage_percent": 0.0,
            "excess_flow_m3s": 0.0,
            "physics_flood_depth_cm": 14.0,
        }
        f_choked = {
            "rainfall_intensity_mm_hr": 75.0,
            "forecast_peak_rainfall_mm_hr": 85.0,
            "elevation_m": 14.0,
            "slope_percent": 1.0,
            "flow_accumulation": 1200.0,
            "imperviousness": 0.80,
            "runoff_coefficient_c": 0.80,
            "runoff_discharge_m3_s": 0.5,
            "is_low_lying": 1.0,
            "drainage_capacity_m3s": 4.5,
            "drainage_effective_capacity_m3s": 2.25,
            "drainage_utilization_percent": 135.0,
            "blockage_percent": 50.0,
            "excess_flow_m3s": 1.2,
            "physics_flood_depth_cm": 38.0,
        }

        depth_clean, _, prob_clean, _ = self.engine.predict_zone(f_clean)
        depth_choked, _, prob_choked, _ = self.engine.predict_zone(f_choked)

        self.assertGreater(depth_choked, depth_clean)
        self.assertGreaterEqual(prob_choked, prob_clean)

    def test_low_lying_vs_elevated_vulnerability(self):
        """Relationship: Low-lying zones predict higher flood depth and hazard probability than elevated slopes."""
        service = MLService(ml_engine=self.engine)
        resp = service.get_predictions(rainfall_override_mm_hr=85.0)

        station_rd = next(z for z in resp.predictions if z.name == "Station Road")
        hilltop = next(z for z in resp.predictions if z.name == "Hilltop Avenue")

        self.assertGreater(station_rd.predicted_flood_depth_cm, hilltop.predicted_flood_depth_cm)
        self.assertGreater(station_rd.flood_probability, hilltop.flood_probability)
        self.assertIn(station_rd.predicted_risk_level, [FloodRiskLevel.HIGH, FloodRiskLevel.SEVERE])
        self.assertEqual(hilltop.predicted_risk_level, FloodRiskLevel.LOW)


if __name__ == "__main__":
    unittest.main()
