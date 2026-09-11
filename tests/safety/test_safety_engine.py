"""
Unit tests for backend/safety/safety_engine.py.
Directly maps to ORCA TEST_PLAN.md (T1, T2, T3, T4, T5, T6, T12).
"""

import unittest
from backend.safety.safety_engine import evaluate_safety


class TestSafetyEngine(unittest.TestCase):
    def setUp(self):
        self.safe_candidate = {
            "id": "KOC-A",
            "name": "Candidate A",
            "spatial_blocked": False,
        }
        self.safe_risk = {
            "risk_score": 18,
            "risk_class": "LOW",
            "missing_critical_fields": [],
        }
        self.safe_weather = {
            "warning_level": "NONE",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }

    def test_T1_normal_safe_case(self):
        """T1: Normal safe forecast and valid candidate -> SAFE."""
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=self.safe_risk,
            weather_record=self.safe_weather,
            data_freshness_ok=True,
        )
        self.assertEqual(res["safety_status"], "SAFE")
        self.assertIsNone(res["blocking_reason"])
        self.assertEqual(len(res["blocking_evidence"]), 0)

    def test_T2_high_risk_blocked(self):
        """T2: Risk score exceeds configured threshold -> BLOCK."""
        high_risk = {
            "risk_score": 68,
            "risk_class": "HIGH",
            "missing_critical_fields": [],
        }
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=high_risk,
            weather_record=self.safe_weather,
            data_freshness_ok=True,
        )
        self.assertEqual(res["safety_status"], "BLOCK")
        self.assertIn("exceeds configured limit", res["blocking_reason"])
        self.assertGreater(len(res["blocking_evidence"]), 0)

    def test_T3_restricted_zone_block(self):
        """T3: Candidate geometry intersects restricted zone -> BLOCK regardless of low risk."""
        blocked_cand = {
            "id": "KOC-RESTRICTED",
            "spatial_blocked": True,
            "blocking_reason": "Intersects naval exercise zone",
            "zone_source": "SIMULATED_MVP",
        }
        res = evaluate_safety(
            candidate=blocked_cand,
            risk_result=self.safe_risk,
            weather_record=self.safe_weather,
            data_freshness_ok=True,
        )
        self.assertEqual(res["safety_status"], "BLOCK")
        self.assertEqual(res["checks_performed"]["restricted_zone_check"], "BLOCK")
        self.assertIn("naval exercise zone", res["blocking_reason"])

    def test_T4_official_warning_block(self):
        """T4: Authoritative blocking warning -> BLOCK with source provenance."""
        warning_weather = {
            "warning_level": "CYCLONE_WARNING",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=self.safe_risk,
            weather_record=warning_weather,
            data_freshness_ok=True,
        )
        self.assertEqual(res["safety_status"], "BLOCK")
        self.assertEqual(res["checks_performed"]["official_warning_check"], "BLOCK")
        self.assertIn("CYCLONE_WARNING", res["blocking_reason"])
        self.assertEqual(res["blocking_evidence"][0]["source"], "IMD")

    def test_T5_missing_critical_data_fails_safe(self):
        """T5: Critical safety parameter unavailable -> Fail safe, never false SAFE."""
        missing_risk = {
            "risk_score": 0,
            "risk_class": "LOW",
            "missing_critical_fields": ["wave_height_m"],
        }
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=missing_risk,
            weather_record=self.safe_weather,
            data_freshness_ok=True,
        )
        self.assertEqual(res["safety_status"], "BLOCK")
        self.assertEqual(res["checks_performed"]["missing_critical_data_check"], "BLOCK")
        self.assertIn("wave_height_m", res["blocking_reason"])

    def test_T6_stale_critical_data_fails_safe(self):
        """T6: Critical safety record outside freshness window -> Fail safe BLOCK."""
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=self.safe_risk,
            weather_record=self.safe_weather,
            data_freshness_ok=False,
        )
        self.assertEqual(res["safety_status"], "BLOCK")
        self.assertEqual(res["checks_performed"]["stale_data_check"], "BLOCK")
        self.assertIn("stale data", res["blocking_reason"])

    def test_caution_range(self):
        """Risk in moderate/elevated range triggers CAUTION."""
        caution_risk = {
            "risk_score": 48,
            "risk_class": "ELEVATED",
            "missing_critical_fields": [],
        }
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=caution_risk,
            weather_record=self.safe_weather,
            data_freshness_ok=True,
        )
        self.assertEqual(res["safety_status"], "CAUTION")
        self.assertIsNone(res["blocking_reason"])

    def test_T12_determinism(self):
        """T12: Identical inputs produce identical safety outputs."""
        res1 = evaluate_safety(
            self.safe_candidate, self.safe_risk, weather_record=self.safe_weather
        )
        res2 = evaluate_safety(
            self.safe_candidate, self.safe_risk, weather_record=self.safe_weather
        )
        self.assertEqual(res1, res2)



    def test_unknown_warning_level_fails_safe_to_caution(self):
        """Unknown/unrecognized warning level (e.g. 'Hot Day') must NOT produce clean SAFE."""
        unknown_weather = {
            "warning_level": "Hot Day",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=self.safe_risk,
            weather_record=unknown_weather,
            data_freshness_ok=True,
        )
        self.assertNotEqual(res["safety_status"], "SAFE")
        self.assertEqual(res["safety_status"], "CAUTION")

    def test_unknown_warning_preserves_original_value_in_evidence(self):
        """Original unrecognized warning string is preserved in evidence."""
        unknown_weather = {
            "warning_level": "Hot Day",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=self.safe_risk,
            weather_record=unknown_weather,
            data_freshness_ok=True,
        )
        evidence = res["blocking_evidence"]
        self.assertGreater(len(evidence), 0)
        warning_entries = [e for e in evidence if e.get("parameter") == "warning_level"]
        self.assertEqual(len(warning_entries), 1)
        self.assertEqual(warning_entries[0]["value"], "Hot Day")

    def test_known_caution_warning_produces_caution(self):
        """Known caution warning level (e.g. 'YELLOW_ALERT') produces CAUTION."""
        caution_weather = {
            "warning_level": "YELLOW_ALERT",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }
        res = evaluate_safety(
            candidate=self.safe_candidate,
            risk_result=self.safe_risk,
            weather_record=caution_weather,
            data_freshness_ok=True,
        )
        self.assertEqual(res["safety_status"], "CAUTION")
        self.assertEqual(res["checks_performed"]["caution_warning_check"], "CAUTION")
        self.assertEqual(res["blocking_evidence"][0]["value"], "YELLOW_ALERT")


if __name__ == "__main__":
    unittest.main()
