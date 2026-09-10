"""
Unit tests for backend/gis/candidate_generator.py.
"""

import unittest
from backend.gis.candidate_generator import generate_candidates, load_candidate_fixtures


class TestCandidateGenerator(unittest.TestCase):
    def setUp(self):
        self.kochi_loc = {
            "name": "Kochi",
            "latitude": 9.9312,
            "longitude": 76.2673,
        }

    def test_load_candidate_fixtures(self):
        """Kochi candidate fixtures must load with 3 candidates."""
        fixtures = load_candidate_fixtures("Kochi")
        self.assertGreaterEqual(len(fixtures), 3)

    def test_candidates_within_radius(self):
        """With 25 km radius, closer candidates (A and B) should be returned, C (~32 km) excluded."""
        candidates = generate_candidates(self.kochi_loc, max_radius_km=25.0)
        cand_ids = [c["id"] for c in candidates]
        self.assertIn("KOC-A", cand_ids)
        self.assertIn("KOC-B", cand_ids)
        self.assertNotIn("KOC-C", cand_ids)

    def test_candidates_ordered_by_distance(self):
        """With 50 km radius, candidates must be sorted closest to furthest."""
        candidates = generate_candidates(self.kochi_loc, max_radius_km=50.0)
        self.assertEqual(len(candidates), 3)
        self.assertLess(candidates[0]["distance_km"], candidates[1]["distance_km"])
        self.assertLess(candidates[1]["distance_km"], candidates[2]["distance_km"])

    def test_small_radius_excludes_all(self):
        """A tiny search radius (e.g. 2 km) offshore from port should return no candidates."""
        candidates = generate_candidates(self.kochi_loc, max_radius_km=2.0)
        self.assertEqual(len(candidates), 0)

    def test_required_contract_fields(self):
        """Each candidate zone must satisfy DATA_CONTRACT.md fields."""
        candidates = generate_candidates(self.kochi_loc, max_radius_km=50.0)
        for c in candidates:
            self.assertIn("id", c)
            self.assertIn("name", c)
            self.assertIn("latitude", c)
            self.assertIn("longitude", c)
            self.assertIn("geometry", c)
            self.assertIn("region", c)
            self.assertIn("active", c)
            self.assertIn("data_mode", c)
            self.assertIn("distance_km", c)

    def test_simulated_mvp_label(self):
        """Synthetic fixture records must be explicitly labelled SIMULATED_MVP."""
        candidates = generate_candidates(self.kochi_loc, max_radius_km=50.0)
        for c in candidates:
            self.assertEqual(c["data_mode"], "SIMULATED_MVP")

    def test_determinism(self):
        """Same input returns exact same output."""
        res1 = generate_candidates(self.kochi_loc, max_radius_km=30.0)
        res2 = generate_candidates(self.kochi_loc, max_radius_km=30.0)
        self.assertEqual(res1, res2)

    def test_unknown_region_does_not_fallback_to_kochi(self):
        """
        A request for an unknown region (e.g. Mumbai, for which no fixture
        exists) must return an empty list. It must NOT silently fall back
        to Kochi candidates, which would be a wrong recommendation.
        """
        candidates = generate_candidates(
            location={
                "name": "Mumbai",
                "latitude": 19.07,
                "longitude": 72.87,
            },
            max_radius_km=50.0,
        )
        self.assertEqual(candidates, [])

    def test_time_window_does_not_mutate_fixture(self):
        """
        Attaching a time_window must not modify the underlying fixture
        dicts. A subsequent call without time_window should return
        candidates that have no time_window key.
        """
        tw = {"valid_from": "2026-09-08T06:00:00Z", "valid_to": "2026-09-08T12:00:00Z"}
        generate_candidates(self.kochi_loc, time_window=tw, max_radius_km=50.0)
        # Second call without time_window
        candidates = generate_candidates(self.kochi_loc, max_radius_km=50.0)
        for c in candidates:
            self.assertNotIn("time_window", c)


if __name__ == "__main__":
    unittest.main()
