"""
Unit tests for backend/gis/distance.py.
"""

import unittest
from backend.gis.distance import haversine_km, filter_by_radius


class TestDistance(unittest.TestCase):
    def test_same_point(self):
        """Distance between the exact same point should be 0.0."""
        dist = haversine_km(9.9312, 76.2673, 9.9312, 76.2673)
        self.assertEqual(dist, 0.0)

    def test_symmetry(self):
        """Distance(A, B) should equal Distance(B, A)."""
        dist_ab = haversine_km(9.9312, 76.2673, 10.05, 76.10)
        dist_ba = haversine_km(10.05, 76.10, 9.9312, 76.2673)
        self.assertAlmostEqual(dist_ab, dist_ba, places=4)

    def test_kochi_reference(self):
        """Test against known approximate distance."""
        # Distance from Kochi (9.9312, 76.2673) to a point ~22 km offshore West (9.9312, 76.0673)
        dist = haversine_km(9.9312, 76.2673, 9.9312, 76.0673)
        # 0.2 degrees longitude at ~10 deg latitude is approx 21.9 km
        self.assertTrue(21.0 <= dist <= 23.0, f"Expected approx 22 km, got {dist}")

    def test_filter_inside_radius(self):
        """Item within radius must be included with distance_km added."""
        items = [
            {"id": "near", "latitude": 9.95, "longitude": 76.25},
            {"id": "far", "latitude": 11.50, "longitude": 75.80},
        ]
        filtered = filter_by_radius(9.9312, 76.2673, items, max_km=15.0)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "near")
        self.assertIn("distance_km", filtered[0])
        self.assertLessEqual(filtered[0]["distance_km"], 15.0)

    def test_filter_outside_radius(self):
        """All items beyond max_km must be excluded."""
        items = [
            {"id": "far1", "latitude": 11.50, "longitude": 75.80},
            {"id": "far2", "latitude": 12.00, "longitude": 75.00},
        ]
        filtered = filter_by_radius(9.9312, 76.2673, items, max_km=10.0)
        self.assertEqual(len(filtered), 0)

    def test_filter_empty_list(self):
        """Empty list should return empty list."""
        filtered = filter_by_radius(9.9312, 76.2673, [], max_km=50.0)
        self.assertEqual(filtered, [])

    def test_filter_missing_coordinates(self):
        """Items missing lat or lon should be gracefully skipped."""
        items = [
            {"id": "valid", "latitude": 9.95, "longitude": 76.25},
            {"id": "missing_lon", "latitude": 9.95},
            {"id": "missing_lat", "longitude": 76.25},
        ]
        filtered = filter_by_radius(9.9312, 76.2673, items, max_km=15.0)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "valid")


if __name__ == "__main__":
    unittest.main()
