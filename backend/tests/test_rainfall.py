"""Automated unit and integration tests for rainfall monitoring and forecast engine."""
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.engines.rainfall_engine import RainfallEngine
from backend.main import app
from backend.models.rainfall_models import RainfallPoint
from backend.services.rainfall_service import (
    InvalidRainfallDataFormatError,
    RainfallFileNotFoundError,
    RainfallService,
)


class TestRainfallAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_current_rainfall_success(self):
        """Verify GET /api/rainfall returns current intensity, trend, and demo disclaimer."""
        response = self.client.get("/api/rainfall")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["location"], "Demo Urban Area")
        self.assertEqual(data["unit"], "mm/hr")
        self.assertEqual(data["data_type"], "DEMO-SIMULATED")
        self.assertEqual(data["current_intensity_mm_per_hr"], 86.0)
        self.assertEqual(data["peak_intensity_mm_per_hr"], 102.0)
        self.assertEqual(data["trend"], "increasing")
        self.assertIn("not a live radar observation", data["source_note"].lower())
        self.assertIsInstance(data["recent_observations"], list)
        self.assertGreaterEqual(len(data["recent_observations"]), 1)

    def test_get_forecast_default_horizon(self):
        """Verify GET /api/forecast returns 0-3 hour (180 min) nowcast series with 30m steps."""
        response = self.client.get("/api/forecast")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["location"], "Demo Urban Area")
        self.assertEqual(data["unit"], "mm/hr")
        self.assertEqual(data["data_type"], "DEMO-SIMULATED")
        self.assertEqual(data["forecast_horizon_minutes"], 180)
        self.assertEqual(data["time_step_minutes"], 30)
        self.assertIn("not live meteorological radar", data["source_note"].lower())

        series = data["forecast_series"]
        self.assertEqual(len(series), 7)

        # Expected demo curve: 86, 91, 96, 102, 98, 87, 74
        expected_intensities = [86.0, 91.0, 96.0, 102.0, 98.0, 87.0, 74.0]
        for i, pt in enumerate(series):
            self.assertEqual(pt["offset_minutes"], i * 30)
            self.assertEqual(pt["intensity_mm_per_hr"], expected_intensities[i])

        self.assertEqual(data["peak_forecast_intensity_mm_per_hr"], 102.0)
        self.assertEqual(data["peak_forecast_offset_minutes"], 90)

    def test_get_forecast_custom_horizon(self):
        """Verify GET /api/forecast responds to custom horizon parameter."""
        response = self.client.get("/api/forecast?horizon_minutes=60")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["forecast_horizon_minutes"], 60)
        self.assertEqual(len(data["forecast_series"]), 3)  # 0, 30, 60 mins


class TestRainfallEngineAndService(unittest.TestCase):
    def test_pydantic_validation_rules(self):
        """Ensure rainfall values outside realistic physical bounds are rejected."""
        # Valid point
        pt = RainfallPoint(offset_minutes=0, intensity_mm_per_hr=50.0)
        self.assertEqual(pt.intensity_mm_per_hr, 50.0)

        # Negative intensity rejected
        with self.assertRaises(ValidationError):
            RainfallPoint(offset_minutes=0, intensity_mm_per_hr=-5.0)

        # Extreme impossible intensity (> 500 mm/hr) rejected
        with self.assertRaises(ValidationError):
            RainfallPoint(offset_minutes=0, intensity_mm_per_hr=600.0)

    def test_linear_interpolation(self):
        """Verify linear interpolation calculates correct rainfall between discrete steps."""
        engine = RainfallEngine()
        # Between 0 min (86 mm/hr) and 30 min (91 mm/hr), at 15 min -> 88.5 mm/hr
        midpoint_intensity = engine.interpolate_intensity(15)
        self.assertAlmostEqual(midpoint_intensity, 88.5, places=2)

        # At boundary
        self.assertEqual(engine.interpolate_intensity(0), 86.0)
        self.assertEqual(engine.interpolate_intensity(90), 102.0)

    def test_missing_dataset_error_handling(self):
        """Verify RainfallFileNotFoundError is raised when dataset file is missing."""
        missing_service = RainfallService(data_file_path=Path("non_existent_rainfall_file.json"))
        engine = RainfallEngine(service=missing_service)

        with self.assertRaises(RainfallFileNotFoundError):
            engine.get_current_rainfall()

    def test_corrupted_dataset_error_handling(self):
        """Verify InvalidRainfallDataFormatError is raised when JSON structure is invalid."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tf:
            tf.write('{"invalid": true}')
            temp_path = Path(tf.name)

        try:
            corrupt_service = RainfallService(data_file_path=temp_path)
            engine = RainfallEngine(service=corrupt_service)

            with self.assertRaises(InvalidRainfallDataFormatError):
                engine.get_current_rainfall()
        finally:
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
