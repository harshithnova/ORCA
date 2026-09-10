"""
Unit tests for backend/gis/spatial_filter.py.
"""

import unittest
from backend.gis.spatial_filter import apply_spatial_filter, check_candidate_intersection


class TestSpatialFilter(unittest.TestCase):
    def setUp(self):
        # Restricted polygon: [10.0, 10.0] to [20.0, 20.0]
        self.restricted_zones = [
            {
                "id": "RZ-TEST-01",
                "name": "Naval Firing Range",
                "source": "SIMULATED_MVP",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [10.0, 10.0],
                            [20.0, 10.0],
                            [20.0, 20.0],
                            [10.0, 20.0],
                            [10.0, 10.0],
                        ]
                    ],
                },
            }
        ]

    def test_candidate_inside_restricted_zone(self):
        """Candidate entirely inside restricted zone must be blocked."""
        candidates = [
            {
                "id": "CAND-INSIDE",
                "name": "Inside Candidate",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [12.0, 12.0],
                            [15.0, 12.0],
                            [15.0, 15.0],
                            [12.0, 15.0],
                            [12.0, 12.0],
                        ]
                    ],
                },
            }
        ]
        passed, blocked = apply_spatial_filter(candidates, self.restricted_zones)
        self.assertEqual(len(passed), 0)
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["status"], "BLOCK")
        self.assertTrue(blocked[0]["spatial_blocked"])
        self.assertIn("RZ-TEST-01", blocked[0]["blocking_reason"])

    def test_candidate_outside_restricted_zone(self):
        """Candidate completely outside restricted zone must pass."""
        candidates = [
            {
                "id": "CAND-OUTSIDE",
                "name": "Safe Outside Candidate",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [1.0, 1.0],
                            [2.0, 1.0],
                            [2.0, 2.0],
                            [1.0, 2.0],
                            [1.0, 1.0],
                        ]
                    ],
                },
            }
        ]
        passed, blocked = apply_spatial_filter(candidates, self.restricted_zones)
        self.assertEqual(len(passed), 1)
        self.assertEqual(len(blocked), 0)
        self.assertFalse(passed[0]["spatial_blocked"])

    def test_candidate_overlapping_boundary(self):
        """Candidate partially overlapping the boundary must be blocked."""
        candidates = [
            {
                "id": "CAND-OVERLAP",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [9.0, 9.0],
                            [11.0, 9.0],
                            [11.0, 11.0],
                            [9.0, 11.0],
                            [9.0, 9.0],
                        ]
                    ],
                },
            }
        ]
        passed, blocked = apply_spatial_filter(candidates, self.restricted_zones)
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["status"], "BLOCK")

    def test_no_restricted_zones(self):
        """If there are no restricted zones, all candidates must pass."""
        candidates = [
            {"id": "C1", "geometry": {"type": "Point", "coordinates": [5.0, 5.0]}},
            {"id": "C2", "geometry": {"type": "Point", "coordinates": [6.0, 6.0]}},
        ]
        passed, blocked = apply_spatial_filter(candidates, [])
        self.assertEqual(len(passed), 2)
        self.assertEqual(len(blocked), 0)

    def test_malformed_geometry_fails_safe(self):
        """Invalid geometry must fail-safe to blocked rather than passing quietly."""
        candidates = [
            {"id": "C_BAD", "geometry": "not-a-geometry"}
        ]
        passed, blocked = apply_spatial_filter(candidates, self.restricted_zones)
        self.assertEqual(len(passed), 0)
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
