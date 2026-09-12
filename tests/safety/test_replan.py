"""
Unit tests for deterministic replanning module (backend/safety/replan.py).

Tests verify:
1. Candidate ordering is preserved (nearest/highest priority first).
2. Evaluated candidates are never retried.
3. Candidate objects are not unexpectedly mutated.
4. Returns None when all candidates are exhausted.
5. Handles empty candidate list gracefully.
6. Audit log preserves safety evaluation history.
"""

import unittest

from backend.safety.replan import ReplanManager, select_next_candidate


class TestReplanModule(unittest.TestCase):
    """Test suite for deterministic replanning module."""

    def setUp(self):
        self.candidates = [
            {"id": "KOC-A", "name": "Candidate A", "distance_km": 15.2},
            {"id": "KOC-B", "name": "Candidate B", "distance_km": 21.0},
            {"id": "KOC-C", "name": "Candidate C", "distance_km": 32.5},
        ]

    def test_preserves_candidate_ordering(self):
        """Candidates are returned in their original ranking order."""
        manager = ReplanManager(self.candidates)
        first = manager.get_next_candidate()
        self.assertIsNotNone(first)
        self.assertEqual(first["id"], "KOC-A")

        manager.record_evaluation("KOC-A", "BLOCK", reason="Restricted zone")

        second = manager.get_next_candidate()
        self.assertIsNotNone(second)
        self.assertEqual(second["id"], "KOC-B")

        manager.record_evaluation("KOC-B", "BLOCK", reason="High risk")

        third = manager.get_next_candidate()
        self.assertIsNotNone(third)
        self.assertEqual(third["id"], "KOC-C")

    def test_never_retries_evaluated_candidate(self):
        """Candidate already in evaluated_ids is never returned again."""
        evaluated = {"KOC-A", "KOC-B"}
        next_cand = select_next_candidate(self.candidates, evaluated)
        self.assertIsNotNone(next_cand)
        self.assertEqual(next_cand["id"], "KOC-C")

        # Now evaluate KOC-C as well
        evaluated.add("KOC-C")
        self.assertIsNone(select_next_candidate(self.candidates, evaluated))

    def test_candidate_objects_not_mutated(self):
        """Original candidate objects in caller's list remain unmodified."""
        original_copy = [dict(c) for c in self.candidates]
        manager = ReplanManager(self.candidates)

        cand = manager.get_next_candidate()
        self.assertIsNotNone(cand)
        cand["custom_injected_key"] = "test"

        # The candidate returned next or in original list must NOT have custom_injected_key
        self.assertNotIn("custom_injected_key", self.candidates[0])
        self.assertEqual(self.candidates, original_copy)

    def test_exhausted_returns_none(self):
        """When all candidates have been evaluated, returns None."""
        manager = ReplanManager(self.candidates)
        self.assertFalse(manager.is_exhausted())
        self.assertEqual(manager.remaining_count, 3)

        for cand in self.candidates:
            cid = cand["id"]
            next_c = manager.get_next_candidate()
            self.assertEqual(next_c["id"], cid)
            manager.record_evaluation(cid, "BLOCK", reason="Blocked for test")

        self.assertTrue(manager.is_exhausted())
        self.assertEqual(manager.remaining_count, 0)
        self.assertIsNone(manager.get_next_candidate())

    def test_empty_candidate_list(self):
        """Empty candidate list immediately reports exhausted and returns None."""
        manager = ReplanManager([])
        self.assertTrue(manager.is_exhausted())
        self.assertIsNone(manager.get_next_candidate())
        self.assertEqual(manager.remaining_count, 0)
        self.assertEqual(manager.audit_log, [])

        self.assertIsNone(select_next_candidate([], set()))

    def test_audit_log_tracking(self):
        """Audit log preserves complete history of evaluated candidates and reasons."""
        manager = ReplanManager(self.candidates)
        manager.record_evaluation(
            "KOC-A",
            "BLOCK",
            blocking_reason="Intersects port channel",
            blocking_evidence=[{"check": "spatial_check", "value": "PORT_CHANNEL"}],
        )
        manager.record_evaluation(
            "KOC-B",
            "CAUTION",
            blocking_reason=None,
            blocking_evidence=[],
        )

        audit = manager.audit_log
        self.assertEqual(len(audit), 2)
        self.assertEqual(audit[0]["candidate_id"], "KOC-A")
        self.assertEqual(audit[0]["safety_status"], "BLOCK")
        self.assertEqual(audit[0]["blocking_reason"], "Intersects port channel")
        self.assertEqual(len(audit[0]["blocking_evidence"]), 1)

        self.assertEqual(audit[1]["candidate_id"], "KOC-B")
        self.assertEqual(audit[1]["safety_status"], "CAUTION")
        self.assertIsNone(audit[1]["blocking_reason"])


if __name__ == "__main__":
    unittest.main()
