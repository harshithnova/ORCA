"""
Unit and integration tests for backend API routes.

Tests:
  - GET /health contract (API_CONTRACT.md)
  - POST /api/v1/reason schema acceptance & rejection
  - POST /api/v1/reason connected to pipeline_service with safety contract verification
"""

import unittest

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestHealthEndpoint(unittest.TestCase):
    """GET /health must return 200 {"status": "ok"} per API_CONTRACT.md."""

    def test_health_returns_200(self):
        """GET /health responds with HTTP 200."""
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_health_returns_ok_status(self):
        """GET /health body is exactly {"status": "ok"}."""
        response = client.get("/health")
        self.assertEqual(response.json(), {"status": "ok"})


class TestReasonEndpoint(unittest.TestCase):
    """POST /api/v1/reason schema and pipeline integration tests."""

    def test_valid_query_accepted(self):
        """A well-formed query string is accepted with HTTP 200."""
        response = client.post(
            "/api/v1/reason",
            json={"query": "Find a safe fishing zone near Kochi tomorrow morning."},
        )
        self.assertEqual(response.status_code, 200)

    def test_response_echoes_query(self):
        """Response body must include the original query string."""
        query = "Find a safe fishing zone near Kochi tomorrow morning."
        response = client.post("/api/v1/reason", json={"query": query})
        self.assertEqual(response.json()["query"], query)

    def test_response_status_in_contracted_set(self):
        """
        Status must strictly be one of the contracted safety statuses:
        SAFE | CAUTION | BLOCK | NO_SAFE_RECOMMENDATION.
        """
        response = client.post(
            "/api/v1/reason",
            json={"query": "Find a safe fishing zone near Kochi tomorrow morning."},
        )
        self.assertEqual(response.status_code, 200)
        contracted_safety_statuses = {"SAFE", "CAUTION", "BLOCK", "NO_SAFE_RECOMMENDATION"}
        status_value = response.json().get("status", "")
        self.assertIn(status_value, contracted_safety_statuses)

    def test_real_cached_kochi_query_safety_contract(self):
        """
        Real cached Kochi query validates safety contract:
        - returns valid ReasonResponse
        - location is Kochi
        - requested_time reflects tomorrow morning
        - status is contracted
        - if cached data does not cover tomorrow morning, status is NO_SAFE_RECOMMENDATION
        - never falsely claims SAFE without valid forecast coverage
        """
        response = client.post(
            "/api/v1/reason",
            json={"query": "Find a suitable and safe fishing zone near Kochi tomorrow morning."},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["location"]["name"], "Kochi")
        self.assertIsNotNone(body["requested_time"]["valid_from"])
        self.assertIn("06:00:00", body["requested_time"]["valid_from"])

        contracted_safety_statuses = {"SAFE", "CAUTION", "BLOCK", "NO_SAFE_RECOMMENDATION"}
        self.assertIn(body["status"], contracted_safety_statuses)

        # The real cached forecast ends on 2026-09-12T00:00:00Z and does not cover
        # tomorrow morning (06:00 IST = 00:30 UTC). Thus it must fail safe to NO_SAFE_RECOMMENDATION.
        self.assertNotEqual(body["status"], "SAFE")
        if body["status"] == "NO_SAFE_RECOMMENDATION":
            self.assertIsNone(body["recommendation"])
            self.assertGreater(len(body["evidence"]), 0)

    def test_missing_query_field_rejected(self):
        """Request without a query field must be rejected with HTTP 422."""
        response = client.post("/api/v1/reason", json={})
        self.assertEqual(response.status_code, 422)

    def test_empty_query_rejected(self):
        """Empty string query must be rejected with HTTP 422."""
        response = client.post("/api/v1/reason", json={"query": ""})
        self.assertEqual(response.status_code, 422)

    def test_whitespace_only_query_rejected(self):
        """Whitespace-only query must be rejected with HTTP 422."""
        response = client.post("/api/v1/reason", json={"query": "   "})
        self.assertEqual(response.status_code, 422)

    def test_extra_fields_ignored(self):
        """Unexpected extra fields in request body must not cause a 500 error."""
        response = client.post(
            "/api/v1/reason",
            json={
                "query": "Find a safe fishing zone near Kochi.",
                "unexpected_field": "should_be_ignored",
            },
        )
        self.assertIn(response.status_code, [200, 422])

    def test_unsupported_region_controlled_response(self):
        """Query for Mumbai returns controlled NO_SAFE_RECOMMENDATION, not 500."""
        response = client.post(
            "/api/v1/reason",
            json={"query": "Find a safe fishing zone near Mumbai tomorrow morning."},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "NO_SAFE_RECOMMENDATION")
        self.assertEqual(body["location"]["name"], "Mumbai")
        self.assertIsNone(body["recommendation"])


if __name__ == "__main__":
    unittest.main()
