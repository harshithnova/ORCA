"""
Unit tests for backend API routes.

Tests are focused on:
  - GET /health contract (API_CONTRACT.md)
  - POST /api/v1/reason schema acceptance
  - POST /api/v1/reason rejection of invalid/missing query

These tests deliberately do NOT test business logic -- that lives in
the P4 reasoning and safety modules with their own test suites.
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
    """POST /api/v1/reason schema and response contract tests."""

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

    def test_response_does_not_claim_safe(self):
        """
        MVP placeholder must NOT claim SAFE / CAUTION / BLOCK / NO_SAFE_RECOMMENDATION.
        A false safety claim before the pipeline is connected would violate AGENTS.md.
        """
        response = client.post(
            "/api/v1/reason",
            json={"query": "Find a safe fishing zone near Kochi tomorrow morning."},
        )
        contracted_safety_statuses = {"SAFE", "CAUTION", "BLOCK", "NO_SAFE_RECOMMENDATION"}
        status_value = response.json().get("status", "")
        self.assertNotIn(
            status_value,
            contracted_safety_statuses,
            msg=(
                f"Endpoint returned a contracted safety status '{status_value}' "
                "before the reasoning pipeline is connected. "
                "This violates the AGENTS.md principle: LLM Plans, Code Calculates, Safety Validates."
            ),
        )

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


if __name__ == "__main__":
    unittest.main()
