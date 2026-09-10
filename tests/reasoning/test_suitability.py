"""
Unit tests for backend/reasoning/suitability.py.
"""

import unittest

from backend.reasoning.suitability import (
    calculate_suitability,
    get_suitability_class,
    normalize_linear,
    normalize_sst,
)


class TestSuitability(unittest.TestCase):
    def setUp(self):
        self.ideal_marine = {
            "wave_height_m": 0.8,
            "wave_period_s": 8.0,
            "sst_c": 28.0,
            "chlorophyll_mg_m3": 0.60,
            "wind_speed_ms": 3.5,
        }
        self.ideal_weather = {
            "wind_speed_ms": 3.5,
            "rainfall_mm": 0.0,
        }

    def test_all_ideal_conditions(self):
        """When all conditions are optimal and PFZ=100, suitability should be EXCELLENT (~100)."""
        res = calculate_suitability(
            self.ideal_marine, self.ideal_weather, pfz_signal=100.0
        )
        self.assertGreaterEqual(res["suitability_score"], 90)
        self.assertEqual(res["suitability_class"], "EXCELLENT")
        self.assertFalse(res["pfz_fallback_used"])
        self.assertTrue(res["is_prototype"])
        self.assertEqual(len(res["missing_fields"]), 0)

    def test_all_poor_conditions(self):
        """When conditions are rough/unsuitable, suitability should be POOR."""
        poor_marine = {
            "wave_height_m": 4.0,
            "wave_period_s": 4.0,
            "sst_c": 35.0,  # far from 28
            "chlorophyll_mg_m3": 0.01,
            "wind_speed_ms": 18.0,
        }
        poor_weather = {
            "wind_speed_ms": 18.0,
            "rainfall_mm": 50.0,
        }
        res = calculate_suitability(poor_marine, poor_weather, pfz_signal=0.0)
        self.assertLessEqual(res["suitability_score"], 20)
        self.assertEqual(res["suitability_class"], "POOR")

    def test_pfz_unavailable_fallback(self):
        """If official PFZ signal is None, fallback must be used and flagged."""
        res = calculate_suitability(
            self.ideal_marine, self.ideal_weather, pfz_signal=None
        )
        self.assertTrue(res["pfz_fallback_used"])
        self.assertEqual(res["components"]["pfz_signal"], 0.0)
        # Without PFZ (weight 0.35), maximum possible score from the remaining 0.65 is ~65
        self.assertLessEqual(res["suitability_score"], 65)

    def test_missing_fields_reporting(self):
        """Missing parameters must be recorded in missing_fields."""
        incomplete_marine = {
            "wave_height_m": 1.0,
            "sst_c": None,
            "chlorophyll_mg_m3": None,
        }
        res = calculate_suitability(
            incomplete_marine, self.ideal_weather, pfz_signal=50.0
        )
        self.assertIn("sst_c", res["missing_fields"])
        self.assertIn("chlorophyll_mg_m3", res["missing_fields"])

    def test_class_boundaries(self):
        """Check classification thresholds."""
        self.assertEqual(get_suitability_class(0), "POOR")
        self.assertEqual(get_suitability_class(20), "POOR")
        self.assertEqual(get_suitability_class(21), "FAIR")
        self.assertEqual(get_suitability_class(40), "FAIR")
        self.assertEqual(get_suitability_class(41), "GOOD")
        self.assertEqual(get_suitability_class(60), "GOOD")
        self.assertEqual(get_suitability_class(61), "VERY GOOD")
        self.assertEqual(get_suitability_class(80), "VERY GOOD")
        self.assertEqual(get_suitability_class(81), "EXCELLENT")
        self.assertEqual(get_suitability_class(100), "EXCELLENT")

    def test_determinism(self):
        """Same inputs must produce exact same suitability score."""
        res1 = calculate_suitability(
            self.ideal_marine, self.ideal_weather, pfz_signal=80.0
        )
        res2 = calculate_suitability(
            self.ideal_marine, self.ideal_weather, pfz_signal=80.0
        )
        self.assertEqual(res1, res2)


if __name__ == "__main__":
    unittest.main()
