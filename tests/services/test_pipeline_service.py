"""
Unit and integration tests for deterministic pipeline service (backend/services/pipeline_service.py).

Tests:
1. 'tomorrow morning' resolves to next calendar day (deterministic reference datetime).
2. 'today morning' resolves to current calendar day (deterministic reference datetime).
3. Explicit unsupported region returns NO_SAFE_RECOMMENDATION (never silently Kochi).
4. Real cached Kochi query never claims SAFE unless freshness/forecast validity passes.
5. Controlled BLOCK -> replan to next candidate.
6. Controlled CAUTION -> no replan.
7. All candidates blocked -> NO_SAFE_RECOMMENDATION.
8. Missing critical safety data -> fails safe to NO_SAFE_RECOMMENDATION.
9. Freshness failure -> fails safe to NO_SAFE_RECOMMENDATION.
10. Output matches ReasonResponse Pydantic schema.
11. Evidence preserves source/data_mode provenance.
12. Deterministic repeated calls produce identical results.
"""

import unittest
from datetime import datetime, timezone

from backend.api.schemas import ReasonResponse
from backend.services.pipeline_service import (
    PipelineRequest,
    parse_query_mvp,
    run_pipeline,
)


class TestPipelineService(unittest.TestCase):
    """Test suite for end-to-end reasoning and safety pipeline."""

    def setUp(self):
        # Deterministic fixed reference datetime for testing: 2026-09-11 10:00:00 UTC (15:30 IST)
        self.fixed_ref_time = datetime(2026, 9, 11, 10, 0, 0, tzinfo=timezone.utc)

        # Base synthetic candidate zones for controlled pipeline unit tests
        self.candidate_a = {
            "id": "TEST-A",
            "name": "Candidate A",
            "latitude": 9.88,
            "longitude": 76.12,
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.08, 9.85], [76.16, 9.85], [76.16, 9.91], [76.08, 9.91], [76.08, 9.85]]],
            },
            "region": "Kochi",
            "active": True,
        }
        self.candidate_b = {
            "id": "TEST-B",
            "name": "Candidate B",
            "latitude": 9.95,
            "longitude": 76.08,
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.04, 9.92], [76.12, 9.92], [76.12, 9.98], [76.04, 9.98], [76.04, 9.92]]],
            },
            "region": "Kochi",
            "active": True,
        }
        # A test restricted zone covering Candidate A only
        self.restricted_zone_a = [{
            "id": "RZ-TEST-A",
            "name": "Test Restricted Zone A",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[76.05, 9.80], [76.20, 9.80], [76.20, 9.91], [76.05, 9.91], [76.05, 9.80]]],
            },
            "restriction_type": "NAVAL_BASE",
            "source": "SIMULATED_MVP",
        }]

    def test_tomorrow_morning_resolves_to_next_calendar_day(self):
        """'tomorrow morning' resolves to next calendar day in IST (06:00 - 12:00 IST)."""
        parsed = parse_query_mvp("Find safe zone near Kochi tomorrow morning", now=self.fixed_ref_time)
        tw = parsed["time_window"]
        self.assertEqual(tw["valid_from"], "2026-09-12T06:00:00+05:30")
        self.assertEqual(tw["valid_to"], "2026-09-12T12:00:00+05:30")

    def test_today_morning_resolves_to_current_calendar_day(self):
        """'today morning' resolves to current calendar day in IST (06:00 - 12:00 IST)."""
        parsed = parse_query_mvp("Find safe zone near Kochi today morning", now=self.fixed_ref_time)
        tw = parsed["time_window"]
        self.assertEqual(tw["valid_from"], "2026-09-11T06:00:00+05:30")
        self.assertEqual(tw["valid_to"], "2026-09-11T12:00:00+05:30")

    def test_unknown_region_does_not_silently_become_kochi(self):
        """Query for Mumbai returns NO_SAFE_RECOMMENDATION, never silently Kochi."""
        req = PipelineRequest(query="Find a safe fishing zone near Mumbai tomorrow morning.")
        res = run_pipeline(req)

        self.assertEqual(res.status, "NO_SAFE_RECOMMENDATION")
        self.assertEqual(res.location.name, "Mumbai")
        self.assertIsNone(res.recommendation)
        self.assertIn("Mumbai", res.evidence[0]["reason"])

    def test_real_cached_kochi_query_never_claims_safe_without_valid_coverage(self):
        """
        Real cached Kochi query validates safety contract:
        - Real cached IMD data ends 2026-09-12T00:00:00Z (05:30 IST).
        - 'tomorrow morning' (06:00 - 12:00 IST) is past the forecast validity.
        - Fails safe to NO_SAFE_RECOMMENDATION instead of fabricating coverage or claiming SAFE.
        """
        req = PipelineRequest(query="Find a suitable and safe fishing zone near Kochi tomorrow morning.")
        res = run_pipeline(req, current_time=self.fixed_ref_time)

        self.assertIsInstance(res, ReasonResponse)
        self.assertEqual(res.location.name, "Kochi")
        self.assertEqual(res.requested_time.valid_from, "2026-09-12T06:00:00+05:30")
        self.assertNotEqual(res.status, "SAFE")
        self.assertEqual(res.status, "NO_SAFE_RECOMMENDATION")
        self.assertIsNone(res.recommendation)
        self.assertGreater(len(res.evidence), 0)

    def test_restricted_candidate_is_blocked_and_replanned(self):
        """Candidate A in restricted zone is blocked; pipeline replans to Candidate B."""
        req = PipelineRequest(query="Find safe fishing zone near Kochi")
        marine = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wave_height_m": 0.8,
            "wind_speed_ms": 3.0,
            "source": "INCOIS",
            "data_mode": "CACHED_OFFICIAL",
        }
        weather = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wind_speed_ms": 3.0,
            "warning_level": "NONE",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }
        # Candidate A is covered by self.restricted_zone_a, B is not
        res = run_pipeline(
            req,
            marine_record=marine,
            weather_record=weather,
            restricted_zones=self.restricted_zone_a,
            candidates=[self.candidate_a, self.candidate_b],
            current_time=datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(res.status, "SAFE")
        # Candidate A was blocked, so Candidate B was recommended
        self.assertEqual(res.recommendation.zone_id, "TEST-B")

    def test_caution_does_not_trigger_replan(self):
        """CAUTION is an acceptable recommendation and must NOT replan."""
        req = PipelineRequest(query="Find safe fishing zone near Kochi")
        marine = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wave_height_m": 0.8,
            "wind_speed_ms": 3.0,
            "source": "INCOIS",
            "data_mode": "CACHED_OFFICIAL",
        }
        # Yellow alert is a known CAUTION warning
        weather = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wind_speed_ms": 3.0,
            "warning_level": "YELLOW_ALERT",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }
        res = run_pipeline(
            req,
            marine_record=marine,
            weather_record=weather,
            restricted_zones=[],
            candidates=[self.candidate_a, self.candidate_b],
            current_time=datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(res.status, "CAUTION")
        # First candidate is accepted with CAUTION; no replan to B
        self.assertEqual(res.recommendation.zone_id, "TEST-A")

    def test_all_candidates_blocked_returns_no_safe_recommendation(self):
        """When all candidate zones are blocked, returns NO_SAFE_RECOMMENDATION."""
        req = PipelineRequest(query="Find safe fishing zone near Kochi")
        marine = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wave_height_m": 0.8,
            "wind_speed_ms": 3.0,
        }
        weather = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wind_speed_ms": 3.0,
            "warning_level": "CYCLONE_WARNING",  # Hard BLOCK for all
            "source": "IMD",
        }
        res = run_pipeline(
            req,
            marine_record=marine,
            weather_record=weather,
            restricted_zones=[],
            candidates=[self.candidate_a, self.candidate_b],
            current_time=datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(res.status, "NO_SAFE_RECOMMENDATION")
        self.assertIsNone(res.recommendation)
        # Evidence contains audit log of both blocked candidates
        self.assertEqual(len(res.evidence), 2)
        self.assertEqual(res.evidence[0]["candidate_id"], "TEST-A")
        self.assertEqual(res.evidence[1]["candidate_id"], "TEST-B")

    def test_missing_critical_safety_data_fails_safe(self):
        """Missing wave_height_m must never claim SAFE."""
        req = PipelineRequest(query="Find safe fishing zone near Kochi")
        marine_missing_wave = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wave_height_m": None,  # Critical missing
            "wind_speed_ms": 3.0,
        }
        weather = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wind_speed_ms": 3.0,
            "warning_level": "NONE",
        }
        res = run_pipeline(
            req,
            marine_record=marine_missing_wave,
            weather_record=weather,
            restricted_zones=[],
            candidates=[self.candidate_a],
            current_time=datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc),
        )

        self.assertNotEqual(res.status, "SAFE")
        self.assertEqual(res.status, "NO_SAFE_RECOMMENDATION")
        self.assertIn("Critical safety data missing", res.evidence[0]["reason"])

    def test_freshness_failure_fails_safe(self):
        """Stale / expired forecast must never produce SAFE."""
        req = PipelineRequest(query="Find safe fishing zone near Kochi")
        marine_stale = {
            "valid_from": "2026-09-01T00:00:00Z",
            "valid_to": "2026-09-02T00:00:00Z",
            "retrieved_at": "2026-09-01T04:00:00Z",
            "wave_height_m": 0.8,
            "wind_speed_ms": 3.0,
        }
        weather = {
            "valid_from": "2026-09-01T00:00:00Z",
            "valid_to": "2026-09-02T00:00:00Z",
            "retrieved_at": "2026-09-01T04:00:00Z",
            "wind_speed_ms": 3.0,
            "warning_level": "NONE",
        }
        # Query target time is 2026-09-12 (well past valid_to 2026-09-02)
        res = run_pipeline(
            req,
            marine_record=marine_stale,
            weather_record=weather,
            restricted_zones=[],
            candidates=[self.candidate_a],
            current_time=self.fixed_ref_time,
        )

        self.assertNotEqual(res.status, "SAFE")
        self.assertEqual(res.status, "NO_SAFE_RECOMMENDATION")

    def test_response_matches_reason_response_schema(self):
        """Output dictionary parses into ReasonResponse without validation errors."""
        req = PipelineRequest(query="Find safe fishing zone near Kochi tomorrow morning")
        res = run_pipeline(req, current_time=self.fixed_ref_time)

        # Validate by dumping and reloading into ReasonResponse
        res_dict = res.model_dump()
        validated = ReasonResponse.model_validate(res_dict)
        self.assertEqual(validated.query, req.query)
        self.assertIn(validated.status, ["SAFE", "CAUTION", "BLOCK", "NO_SAFE_RECOMMENDATION"])

    def test_evidence_preserves_provenance(self):
        """Evidence contains source, data_mode, and valid_from metadata when data is evaluated."""
        # Test with injected data covering target window
        marine = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wave_height_m": 0.8,
            "wind_speed_ms": 3.0,
            "source": "INCOIS",
            "data_mode": "CACHED_OFFICIAL",
        }
        weather = {
            "valid_from": "2026-09-11T00:00:00Z",
            "valid_to": "2026-09-13T00:00:00Z",
            "retrieved_at": "2026-09-11T04:00:00Z",
            "wind_speed_ms": 3.0,
            "warning_level": "NONE",
            "source": "IMD",
            "data_mode": "CACHED_OFFICIAL",
        }
        req = PipelineRequest(query="Find safe fishing zone near Kochi")
        res = run_pipeline(
            req,
            marine_record=marine,
            weather_record=weather,
            restricted_zones=[],
            candidates=[self.candidate_a],
            current_time=datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc),
        )

        sources = [ev.get("source") for ev in res.evidence if "source" in ev]
        self.assertTrue("INCOIS" in sources or "IMD" in sources)
        data_modes = [ev.get("data_mode") for ev in res.evidence if "data_mode" in ev]
        self.assertTrue("CACHED_OFFICIAL" in data_modes)

    def test_deterministic_repeated_calls(self):
        """Same input query produces identical results on successive calls."""
        req = PipelineRequest(query="Find a safe fishing zone near Kochi tomorrow morning.")
        res1 = run_pipeline(req, current_time=self.fixed_ref_time)
        res2 = run_pipeline(req, current_time=self.fixed_ref_time)

        self.assertEqual(res1.status, res2.status)
        self.assertEqual(res1.location.name, res2.location.name)
        self.assertEqual(res1.requested_time.valid_from, res2.requested_time.valid_from)
        self.assertEqual(res1.requested_time.valid_to, res2.requested_time.valid_to)


if __name__ == "__main__":
    unittest.main()
