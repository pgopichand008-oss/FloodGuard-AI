"""Automated tests for terrain characteristics, DEM zones, and surface runoff engine."""
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.engines.terrain_engine import TerrainEngine
from backend.main import app
from backend.models.terrain_models import RunoffTendency, TerrainZoneModel
from backend.services.terrain_service import (
    InvalidTerrainDataFormatError,
    TerrainFileNotFoundError,
    TerrainService,
)


class TestTerrainAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_terrain_endpoint_success(self):
        """Verify GET /api/terrain returns registered DEM zones and attributes."""
        response = self.client.get("/api/terrain")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["location"], "Demo Urban Area")
        self.assertEqual(data["data_type"], "DEMO-SIMULATED")
        self.assertEqual(data["zone_count"], 8)
        self.assertIn("synthetic digital elevation model", data["source_note"].lower())

        zone_names = [z["name"] for z in data["zones"]]
        self.assertIn("Station Road", zone_names)
        self.assertIn("Market Junction", zone_names)
        self.assertIn("Hilltop Avenue", zone_names)
        self.assertIn("Riverbank Lane", zone_names)

        # Verify low-lying flag on Station Road
        station_rd = next(z for z in data["zones"] if z["name"] == "Station Road")
        self.assertTrue(station_rd["is_low_lying"])
        self.assertLess(station_rd["elevation_m"], 15.0)

    def test_get_runoff_default_rainfall(self):
        """Verify GET /api/runoff uses current rainfall from RainfallEngine and returns Rational runoff."""
        response = self.client.get("/api/runoff")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["data_type"], "DEMO-SIMULATED")
        self.assertEqual(data["rainfall_intensity_used_mm_hr"], 86.0)
        self.assertIn("Rational Method", data["methodology"])
        self.assertGreater(len(data["assumptions"]), 0)
        self.assertEqual(len(data["results"]), 8)
        self.assertGreater(data["total_discharge_m3_s"], 0.0)
        self.assertGreater(len(data["highest_risk_zones"]), 0)

        # Check Station Road calculated metrics
        station_res = next(r for r in data["results"] if r["name"] == "Station Road")
        self.assertGreaterEqual(station_res["runoff_coefficient_c"], 0.80)
        self.assertEqual(station_res["runoff_tendency"], "HIGH")
        self.assertGreater(station_res["flood_prone_index"], 0.70)

    def test_get_runoff_custom_rainfall_override(self):
        """Verify GET /api/runoff with custom rainfall_mm_hr query parameter."""
        response = self.client.get("/api/runoff?rainfall_mm_hr=40.0")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["rainfall_intensity_used_mm_hr"], 40.0)
        station_res = next(r for r in data["results"] if r["name"] == "Station Road")
        # Runoff rate = C * 40.0
        expected_rate = round(station_res["runoff_coefficient_c"] * 40.0, 2)
        self.assertEqual(station_res["runoff_rate_mm_hr"], expected_rate)

    def test_get_runoff_single_zone_filter(self):
        """Verify GET /api/runoff with zone_id query filter."""
        response = self.client.get("/api/runoff?zone_id=Z01")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["zone_id"], "Z01")
        self.assertEqual(data["results"][0]["name"], "Station Road")

    def test_post_runoff_scenario_calculation(self):
        """Verify POST /api/runoff scenario evaluation endpoint."""
        payload = {
            "rainfall_intensity_mm_hr": 100.0,
            "zone_ids": ["Z01", "Z06"]
        }
        response = self.client.post("/api/runoff", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["rainfall_intensity_used_mm_hr"], 100.0)
        self.assertEqual(len(data["results"]), 2)
        zone_ids = [r["zone_id"] for r in data["results"]]
        self.assertIn("Z01", zone_ids)
        self.assertIn("Z06", zone_ids)

    def test_runoff_negative_rainfall_validation(self):
        """Verify negative rainfall intensity is rejected with HTTP 422."""
        response = self.client.get("/api/runoff?rainfall_mm_hr=-10.0")
        self.assertEqual(response.status_code, 422)


class TestTerrainEngineAndService(unittest.TestCase):
    def setUp(self):
        self.engine = TerrainEngine()

    def test_runoff_coefficient_calculation(self):
        """Verify runoff coefficient formula bounds and sensitivity."""
        # Highly impervious and steep
        c_high = self.engine.calculate_runoff_coefficient(imperviousness=0.95, slope_percent=5.0)
        self.assertLessEqual(c_high, 0.98)
        self.assertGreaterEqual(c_high, 0.85)

        # Highly permeable (park/vegetated)
        c_low = self.engine.calculate_runoff_coefficient(imperviousness=0.10, slope_percent=1.0)
        self.assertGreaterEqual(c_low, 0.15)
        self.assertLessEqual(c_low, 0.35)

    def test_zero_rainfall_discharge(self):
        """Verify zero rainfall generates zero discharge and LOW tendency."""
        sample_zone = TerrainZoneModel(
            zone_id="TEST01",
            name="Test Zone",
            elevation_m=15.0,
            slope_percent=1.0,
            flow_accumulation=1000,
            imperviousness=0.85,
            area_hectares=2.5,
            is_low_lying=True
        )
        res = self.engine.calculate_zone_runoff(sample_zone, rainfall_intensity_mm_hr=0.0)
        self.assertEqual(res.runoff_rate_mm_hr, 0.0)
        self.assertEqual(res.peak_discharge_m3_s, 0.0)
        self.assertEqual(res.runoff_tendency, RunoffTendency.LOW)

    def test_rational_method_formula_exactness(self):
        """Verify Q = (C * I * A) / 360 metric calculation."""
        # Zone with known area
        sample_zone = TerrainZoneModel(
            zone_id="TEST02",
            name="Formula Test Zone",
            elevation_m=20.0,
            slope_percent=0.0,
            flow_accumulation=500,
            imperviousness=0.80,
            area_hectares=3.6,
            is_low_lying=False
        )
        c = self.engine.calculate_runoff_coefficient(0.80, 0.0)
        # Expected Q = (c * 100 * 3.6) / 360 = c
        res = self.engine.calculate_zone_runoff(sample_zone, rainfall_intensity_mm_hr=100.0)
        expected_q = round((c * 100.0 * 3.6) / 360.0, 4)
        self.assertEqual(res.peak_discharge_m3_s, expected_q)

    def test_low_lying_vs_hilltop_vulnerability(self):
        """Verify low-lying terrain exhibits significantly higher vulnerability than elevated slope."""
        low_zone = TerrainZoneModel(
            zone_id="LOW",
            name="Low Basin",
            elevation_m=11.0,
            slope_percent=0.3,
            flow_accumulation=2200,
            imperviousness=0.90,
            area_hectares=3.0,
            is_low_lying=True
        )
        hill_zone = TerrainZoneModel(
            zone_id="HILL",
            name="Hill Crest",
            elevation_m=39.0,
            slope_percent=6.0,
            flow_accumulation=100,
            imperviousness=0.50,
            area_hectares=3.0,
            is_low_lying=False
        )
        low_res = self.engine.calculate_zone_runoff(low_zone, rainfall_intensity_mm_hr=80.0)
        hill_res = self.engine.calculate_zone_runoff(hill_zone, rainfall_intensity_mm_hr=80.0)

        self.assertGreater(low_res.flood_prone_index, hill_res.flood_prone_index)
        self.assertGreater(low_res.accumulation_index, hill_res.accumulation_index)
        self.assertGreater(low_res.runoff_rate_mm_hr, hill_res.runoff_rate_mm_hr)

    def test_missing_terrain_dataset(self):
        """Verify TerrainFileNotFoundError on missing file."""
        missing_service = TerrainService(data_file_path=Path("non_existent_terrain_file.json"))
        with self.assertRaises(TerrainFileNotFoundError):
            missing_service.load_dataset()

    def test_corrupted_terrain_dataset(self):
        """Verify InvalidTerrainDataFormatError on corrupt JSON."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tf:
            tf.write('{"zones": "not a list"}')
            temp_path = Path(tf.name)

        try:
            corrupt_service = TerrainService(data_file_path=temp_path)
            with self.assertRaises(InvalidTerrainDataFormatError):
                corrupt_service.load_dataset()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_terrain_service_zone_queries(self):
        """Verify get_zone_by_id and get_low_lying_zones query helpers."""
        service = TerrainService()
        z = service.get_zone_by_id("Z01")
        self.assertIsNotNone(z)
        self.assertEqual(z.name, "Station Road")

        unknown = service.get_zone_by_id("NON_EXISTENT")
        self.assertIsNone(unknown)

        low_lying = service.get_low_lying_zones()
        self.assertGreaterEqual(len(low_lying), 1)
        for zone in low_lying:
            self.assertTrue(zone.is_low_lying)


if __name__ == "__main__":
    unittest.main()
