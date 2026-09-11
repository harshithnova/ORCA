"""
Unit tests for data freshness and validity helper (backend/services/freshness.py).

Tests require:
1. Valid current forecast -> fresh/valid
2. Expired forecast -> stale/invalid
3. Future valid_from -> not currently valid
4. Missing validity metadata -> fail-safe
5. Timezone-aware ISO timestamps
6. Naive timestamps (e.g. existing cached INCOIS data) handled safely
7. Both marine and weather must be fresh for is_data_fresh() to return True
"""

import unittest
from datetime import datetime, timezone

from backend.services.freshness import (
    check_forecast_validity,
    check_marine_and_weather_freshness,
    check_record_freshness,
    check_retrieval_freshness,
    is_data_fresh,
    parse_iso_datetime,
)


class TestFreshnessHelper(unittest.TestCase):
    """Test suite for deterministic data freshness and forecast validity."""

    def test_parse_iso_datetime_timezone_aware(self):
        """Timezone-aware ISO timestamps (Z or +offset) are parsed to UTC."""
        dt1 = parse_iso_datetime("2026-09-11T12:00:00Z")
        self.assertIsNotNone(dt1)
        self.assertEqual(dt1.tzinfo, timezone.utc)
        self.assertEqual(dt1.hour, 12)

        dt2 = parse_iso_datetime("2026-09-11T17:30:00+05:30")
        self.assertIsNotNone(dt2)
        self.assertEqual(dt2.tzinfo, timezone.utc)
        self.assertEqual(dt2.hour, 12)  # 17:30 - 5:30 = 12:00 UTC

    def test_parse_iso_datetime_naive_timestamp(self):
        """Naive ISO timestamp (as in cached INCOIS fixture) safely localizes to UTC."""
        dt = parse_iso_datetime("2026-09-11T00:00:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 9)
        self.assertEqual(dt.day, 11)

    def test_valid_current_forecast(self):
        """Forecast with valid_from <= target <= valid_to and fresh retrieval passes."""
        record = {
            "valid_from": "2026-09-11T00:00:00+00:00",
            "valid_to": "2026-09-12T00:00:00+00:00",
            "retrieved_at": "2026-09-11T06:00:00+00:00",
        }
        target_time = parse_iso_datetime("2026-09-11T12:00:00+00:00")
        current_time = parse_iso_datetime("2026-09-11T08:00:00+00:00")

        is_valid, msg = check_forecast_validity(record, target_time=target_time)
        self.assertTrue(is_valid)

        is_fresh, msg = check_retrieval_freshness(record, current_time=current_time)
        self.assertTrue(is_fresh)

        ok, _ = check_record_freshness(record, target_time=target_time, current_time=current_time)
        self.assertTrue(ok)

    def test_expired_forecast_is_stale_or_invalid(self):
        """Target time past valid_to must fail validity check."""
        record = {
            "valid_from": "2026-09-10T00:00:00+00:00",
            "valid_to": "2026-09-11T00:00:00+00:00",
            "retrieved_at": "2026-09-10T06:00:00+00:00",
        }
        target_time = parse_iso_datetime("2026-09-11T12:00:00+00:00")  # past valid_to

        is_valid, msg = check_forecast_validity(record, target_time=target_time)
        self.assertFalse(is_valid)
        self.assertIn("expired", msg.lower())

        ok, _ = check_record_freshness(record, target_time=target_time)
        self.assertFalse(ok)

    def test_future_valid_from_is_not_currently_valid(self):
        """Target time before valid_from must fail validity check."""
        record = {
            "valid_from": "2026-09-12T00:00:00+00:00",
            "valid_to": "2026-09-13T00:00:00+00:00",
            "retrieved_at": "2026-09-11T06:00:00+00:00",
        }
        target_time = parse_iso_datetime("2026-09-11T12:00:00+00:00")  # before valid_from

        is_valid, msg = check_forecast_validity(record, target_time=target_time)
        self.assertFalse(is_valid)
        self.assertIn("not yet valid", msg.lower())

    def test_missing_validity_metadata_fails_safe(self):
        """Record with missing or empty validity timestamps fails safe."""
        empty_record = {}
        is_valid, msg = check_forecast_validity(empty_record)
        self.assertFalse(is_valid)

        none_record = None
        is_valid, msg = check_forecast_validity(none_record)
        self.assertFalse(is_valid)

        record_no_timestamps = {"wave_height_m": 1.2, "source": "INCOIS"}
        is_valid, msg = check_forecast_validity(record_no_timestamps)
        self.assertFalse(is_valid)
        self.assertIn("missing", msg.lower())

    def test_naive_incois_fixture_validity(self):
        """Naive timestamp string from real INCOIS fixture is properly validated."""
        incois_record = {
            "valid_from": "2026-09-11T00:00:00",  # naive string
            "valid_to": None,
            "source": "INCOIS",
        }
        # Within the 24h window
        target_time = parse_iso_datetime("2026-09-11T14:00:00+00:00")
        is_valid, msg = check_forecast_validity(incois_record, target_time=target_time)
        self.assertTrue(is_valid)

        # Beyond the 24h window from valid_from
        target_time_late = parse_iso_datetime("2026-09-12T08:00:00+00:00")
        is_valid_late, _ = check_forecast_validity(incois_record, target_time=target_time_late)
        self.assertFalse(is_valid_late)

    def test_is_data_fresh_requires_both_domains(self):
        """is_data_fresh() returns False if either marine or weather is missing/stale."""
        marine = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-12T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
        }
        weather_stale = {
            "valid_from": "2026-09-09T00:00:00Z",
            "valid_to": "2026-09-10T00:00:00Z",
            "retrieved_at": "2026-09-09T04:00:00Z",
        }
        target = parse_iso_datetime("2026-09-11T10:00:00Z")
        current = parse_iso_datetime("2026-09-11T10:00:00Z")

        # Stale weather fails overall
        self.assertFalse(is_data_fresh(marine, weather_stale, target_time=target, current_time=current))

        # None weather fails overall
        self.assertFalse(is_data_fresh(marine, None, target_time=target, current_time=current))

        # Fresh weather passes
        weather_fresh = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-12T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
        }
        self.assertTrue(is_data_fresh(marine, weather_fresh, target_time=target, current_time=current))

        ok, details = check_marine_and_weather_freshness(marine, weather_fresh, target_time=target, current_time=current)
        self.assertTrue(ok)
        self.assertTrue(details["marine"]["valid"])
        self.assertTrue(details["weather"]["valid"])


if __name__ == "__main__":
    unittest.main()
