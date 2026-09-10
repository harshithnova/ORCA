"""
Unit tests for backend/reasoning/confidence.py.
"""

from datetime import datetime, timezone
import unittest

from backend.reasoning.confidence import (
    calculate_completeness,
    calculate_confidence,
    calculate_freshness,
    calculate_source_score,
)


class TestConfidence(unittest.TestCase):
    def setUp(self):
        self.marine_record = {
            "latitude": 9.90,
            "longitude": 76.10,
            "issued_at": "2026-09-08T00:00:00Z",
            "valid_from": "2026-09-08T06:00:00Z",
            "valid_to": "2026-09-08T18:00:00Z",
            "wave_height_m": 1.2,
            "wave_period_s": 7.5,
            "wind_speed_ms": 5.8,
            "wind_direction_deg": 240,
            "current_speed_ms": 0.4,
            "sst_c": 28.4,
            "chlorophyll_mg_m3": 0.35,
            "source": "INCOIS",
            "data_mode": "CACHED_OFFICIAL",
            "data_type": "FORECAST",
        }

        self.weather_record = {
            "latitude": 9.90,
            "longitude": 76.10,
            "issued_at": "2026-09-08T00:00:00Z",
            "valid_from": "2026-09-08T06:00:00Z",
            "valid_to": "2026-09-08T18:00:00Z",
            "wind_speed_ms": 6.0,
            "wind_direction_deg": 230,
            "rainfall_mm": 1.5,
            "visibility_km": 8,
            "warning_level": "NONE",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
            "data_type": "FORECAST",
        }

        self.query_time = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)

    def test_fresh_complete_official(self):
        """Fresh, 100% complete, cached official records should have high confidence."""
        res = calculate_confidence(
            self.marine_record, self.weather_record, self.query_time
        )
        self.assertGreaterEqual(res["confidence_score"], 0.85)
        self.assertEqual(res["components"]["freshness"], 1.0)
        self.assertEqual(res["components"]["completeness"], 1.0)
        self.assertEqual(res["components"]["source_score"], 1.0)
        self.assertEqual(len(res["missing_fields"]), 0)
        self.assertFalse(res["is_simulated"])

    def test_stale_data(self):
        """When query_time is well past valid_to, freshness drops significantly."""
        late_query_time = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)  # 18 hours past valid_to
        res = calculate_confidence(
            self.marine_record, self.weather_record, late_query_time
        )
        self.assertLess(res["components"]["freshness"], 0.5)
        self.assertLess(res["confidence_score"], 0.8)

    def test_missing_fields_reporting(self):
        """Missing fields must decrease completeness and be enumerated."""
        incomplete_marine = dict(self.marine_record)
        incomplete_marine["chlorophyll_mg_m3"] = None
        incomplete_marine["sst_c"] = None

        res = calculate_confidence(
            incomplete_marine, self.weather_record, self.query_time
        )
        self.assertLess(res["components"]["completeness"], 1.0)
        self.assertIn("chlorophyll_mg_m3", res["missing_fields"])
        self.assertIn("sst_c", res["missing_fields"])

    def test_simulated_mvp_source(self):
        """SIMULATED_MVP data_mode yields lower source score and sets is_simulated."""
        sim_marine = dict(self.marine_record)
        sim_marine["data_mode"] = "SIMULATED_MVP"

        res = calculate_confidence(
            sim_marine, self.weather_record, self.query_time
        )
        self.assertTrue(res["is_simulated"])
        self.assertLess(res["components"]["source_score"], 1.0)

    def test_bounds_clamping(self):
        """Confidence score must be clamped strictly within [0.0, 1.0]."""
        res = calculate_confidence(None, None, self.query_time)
        self.assertGreaterEqual(res["confidence_score"], 0.0)
        self.assertLessEqual(res["confidence_score"], 1.0)

    def test_determinism(self):
        """Identical inputs must produce identical confidence output."""
        res1 = calculate_confidence(
            self.marine_record, self.weather_record, self.query_time
        )
        res2 = calculate_confidence(
            self.marine_record, self.weather_record, self.query_time
        )
        self.assertEqual(res1, res2)


if __name__ == "__main__":
    unittest.main()
