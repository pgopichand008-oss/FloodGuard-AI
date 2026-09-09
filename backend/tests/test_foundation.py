"""Automated tests for backend foundation and baseline endpoints."""
import unittest
from fastapi.testclient import TestClient

from backend.main import app


class TestBackendFoundation(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("status"), "online")
        self.assertEqual(payload.get("name"), "FloodGuard AI API")

    def test_health_check_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("status"), "ok")
        self.assertEqual(payload.get("version"), "0.1.0")
        self.assertIn("message", payload)

    def test_flood_baseline_endpoint(self):
        response = self.client.get("/api/flood")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("location", payload)
        self.assertIn("timestamp", payload)
        self.assertIn("rainfall", payload)
        self.assertIn("flood", payload)
        self.assertIn("forecast", payload)
        self.assertEqual(payload["location"], "Demo Urban Area")
        self.assertEqual(payload["flood"]["risk"], "HIGH")
        self.assertIsInstance(payload["forecast"], list)
        self.assertGreater(len(payload["forecast"]), 0)


if __name__ == "__main__":
    unittest.main()
