"""
Unit tests for backend/services/data_service.py.

Verifies:
1. Kochi INCOIS record loads.
2. Kochi IMD record loads.
3. Restricted zones load.
4. Missing/null fields remain None.
5. Missing file produces an explicit error (FileNotFoundError).
6. Loaded data contains source/data_mode/data_type metadata.
7. Loading the same data twice is deterministic.
"""

import unittest
from pathlib import Path

from backend.services.data_service import (
    load_marine_record,
    load_restricted_zones,
    load_weather_record,
)


class TestDataService(unittest.TestCase):
    """Test suite for cached data service loader."""

    def test_load_kochi_incois_record(self):
        """Kochi INCOIS marine record loads successfully and returns dict."""
        record = load_marine_record("Kochi")
        self.assertIsInstance(record, dict)
        self.assertEqual(record.get("source"), "INCOIS")
        self.assertIn("wave_height_m", record)
        self.assertIn("wind_speed_ms", record)

    def test_load_kochi_imd_record(self):
        """Kochi IMD weather record loads successfully and returns dict."""
        record = load_weather_record("Kochi")
        self.assertIsInstance(record, dict)
        self.assertEqual(record.get("source"), "IMD")
        self.assertIn("warning_level", record)
        self.assertIn("weather_condition", record)

    def test_load_restricted_zones(self):
        """Restricted zones fixture loads successfully and returns non-empty list."""
        zones = load_restricted_zones()
        self.assertIsInstance(zones, list)
        self.assertGreater(len(zones), 0)
        zone = zones[0]
        self.assertIn("id", zone)
        self.assertIn("geometry", zone)
        self.assertIn("restriction_type", zone)

    def test_null_fields_remain_none(self):
        """
        Missing / null fields in raw files must strictly remain None.
        Must NOT be replaced with 0 or synthetic fallbacks.
        """
        marine = load_marine_record("Kochi")
        # In kochi_incois.json, sst_c, chlorophyll_mg_m3, current_speed_ms are null
        self.assertIsNone(marine.get("sst_c"))
        self.assertIsNone(marine.get("chlorophyll_mg_m3"))
        self.assertIsNone(marine.get("current_speed_ms"))

        weather = load_weather_record("Kochi")
        # In kochi_imd.json, rainfall_mm, visibility_km, wave_height_m are null
        self.assertIsNone(weather.get("rainfall_mm"))
        self.assertIsNone(weather.get("visibility_km"))
        self.assertIsNone(weather.get("wave_height_m"))

    def test_missing_file_raises_explicit_error(self):
        """Requesting an unavailable region or file must raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_marine_record("NonExistentRegion_12345")

        with self.assertRaises(FileNotFoundError):
            load_weather_record("NonExistentRegion_12345")

        with self.assertRaises(FileNotFoundError):
            load_restricted_zones(file_path="non_existent_path.json")

    def test_metadata_fields_present(self):
        """Records must contain required metadata: source, data_mode, data_type."""
        marine = load_marine_record("Kochi")
        self.assertEqual(marine.get("data_mode"), "CACHED_OFFICIAL")
        self.assertEqual(marine.get("data_type"), "FORECAST")
        self.assertEqual(marine.get("source"), "INCOIS")

        weather = load_weather_record("Kochi")
        self.assertEqual(weather.get("data_mode"), "CACHED_OFFICIAL")
        self.assertEqual(weather.get("data_type"), "FORECAST")
        self.assertEqual(weather.get("source"), "IMD")

        zones = load_restricted_zones()
        self.assertTrue(any("source" in z for z in zones))

    def test_deterministic_loading(self):
        """Loading data multiple times produces identical content."""
        marine_1 = load_marine_record("Kochi")
        marine_2 = load_marine_record("Kochi")
        self.assertEqual(marine_1, marine_2)

        weather_1 = load_weather_record("Kochi")
        weather_2 = load_weather_record("Kochi")
        self.assertEqual(weather_1, weather_2)

        zones_1 = load_restricted_zones()
        zones_2 = load_restricted_zones()
        self.assertEqual(zones_1, zones_2)


if __name__ == "__main__":
    unittest.main()
