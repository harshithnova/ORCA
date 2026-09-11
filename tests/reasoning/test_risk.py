"""
Unit tests for backend/reasoning/risk.py.
"""

import unittest

from backend.reasoning.risk import (
    calculate_hazard_risk,
    calculate_risk,
    get_risk_class,
    normalize_risk_linear,
)


class TestRisk(unittest.TestCase):
    def setUp(self):
        self.calm_marine = {
            "wave_height_m": 0.8,
            "wave_period_s": 8.0,
            "wind_speed_ms": 4.0,
        }
        self.calm_weather = {
            "wind_speed_ms": 4.0,
            "rainfall_mm": 0.0,
            "warning_level": "NONE",
        }

    def test_calm_conditions(self):
        """Under gentle, calm conditions, risk should be LOW."""
        res = calculate_risk(self.calm_marine, self.calm_weather)
        self.assertLessEqual(res["risk_score"], 20)
        self.assertEqual(res["risk_class"], "LOW")
        self.assertEqual(len(res["missing_critical_fields"]), 0)
        self.assertTrue(res["lightning_data_missing"])

    def test_severe_conditions(self):
        """Under dangerous wave, wind, and severe cyclone warning, risk should be elevated/high."""
        severe_marine = {
            "wave_height_m": 4.5,
            "wind_speed_ms": 22.0,
        }
        severe_weather = {
            "wind_speed_ms": 22.0,
            "rainfall_mm": 50.0,
            "warning_level": "CYCLONE_WARNING",
        }
        res = calculate_risk(severe_marine, severe_weather)
        # wave_risk=100 (0.30), wind_risk=100 (0.25), rain_risk=100 (0.15), hazard=100 (0.10) => 80
        self.assertGreaterEqual(res["risk_score"], 70)
        self.assertIn(res["risk_class"], ["HIGH", "SEVERE"])
        self.assertEqual(res["components"]["hazard_risk"], 100.0)

    def test_null_critical_field_reported(self):
        """When critical safety fields are missing, they must be recorded in missing_critical_fields."""
        missing_marine = {
            "wave_height_m": None,
            "wind_speed_ms": 5.0,
        }
        res = calculate_risk(missing_marine, self.calm_weather)
        self.assertIn("wave_height_m", res["missing_critical_fields"])

    def test_warning_level_hazard(self):
        """Test hazard risk sub-score derivation from warning levels."""
        self.assertEqual(calculate_hazard_risk("NONE"), 0.0)
        self.assertEqual(calculate_hazard_risk(None), 0.0)
        self.assertEqual(calculate_hazard_risk("CYCLONE_WARNING"), 100.0)
        self.assertEqual(calculate_hazard_risk("GALE_WARNING"), 100.0)
        self.assertEqual(calculate_hazard_risk("ADVISORY"), 50.0)

    def test_risk_class_boundaries(self):
        """Check classification thresholds."""
        self.assertEqual(get_risk_class(0), "LOW")
        self.assertEqual(get_risk_class(20), "LOW")
        self.assertEqual(get_risk_class(21), "MODERATE")
        self.assertEqual(get_risk_class(40), "MODERATE")
        self.assertEqual(get_risk_class(41), "ELEVATED")
        self.assertEqual(get_risk_class(60), "ELEVATED")
        self.assertEqual(get_risk_class(61), "HIGH")
        self.assertEqual(get_risk_class(80), "HIGH")
        self.assertEqual(get_risk_class(81), "SEVERE")
        self.assertEqual(get_risk_class(100), "SEVERE")

    def test_determinism(self):
        """Same inputs must produce exact same risk score."""
        res1 = calculate_risk(self.calm_marine, self.calm_weather)
        res2 = calculate_risk(self.calm_marine, self.calm_weather)
        self.assertEqual(res1, res2)


    def test_invalid_weights_raise_error(self):
        """Risk weights that do not sum to 1.0 must raise ValueError."""
        bad_config = {"weights": {
            "wave_risk": 0.50,
            "wind_risk": 0.50,
            "lightning_risk": 0.50,
            "rain_risk": 0.50,
            "hazard_risk": 0.50,
        }}
        with self.assertRaises(ValueError):
            calculate_risk(None, None, config=bad_config)

    def test_negative_weights_raise_error(self):
        """Negative risk weights must raise ValueError."""
        bad_config = {"weights": {
            "wave_risk": -0.30,
            "wind_risk": 0.55,
            "lightning_risk": 0.20,
            "rain_risk": 0.30,
            "hazard_risk": 0.25,
        }}
        with self.assertRaises(ValueError):
            calculate_risk(None, None, config=bad_config)

    def test_lightning_always_stubbed(self):
        """Lightning risk must be 0.0 and lightning_data_missing=True until P3 confirms field."""
        result = calculate_risk(
            {"wave_height_m": 1.0, "wind_speed_ms": 5.0},
            {"warning_level": "NONE", "rainfall_mm": 1.0},
        )
        self.assertEqual(result["components"]["lightning_risk"], 0.0)
        self.assertTrue(result["lightning_data_missing"])

    def test_unknown_warning_level_returns_nonzero(self):
        """An unrecognised warning_level must return a non-zero hazard risk (not silently safe)."""
        result = calculate_risk(
            {"wave_height_m": 1.0, "wind_speed_ms": 5.0},
            {"warning_level": "UNKNOWN_EXTREME_EVENT", "rainfall_mm": 1.0},
        )
        self.assertGreater(result["components"]["hazard_risk"], 0.0)


if __name__ == "__main__":
    unittest.main()
