"""
Pydantic request / response schemas for ORCA API.

Follows API_CONTRACT.md exactly.
Do NOT add fields without updating API_CONTRACT.md and notifying all owners.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Request ──────────────────────────────────────────────────────────────────

class ReasonRequest(BaseModel):
    """POST /api/v1/reason request body per API_CONTRACT.md."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language query from the user.",
        examples=["Find a suitable and safe fishing zone near Kochi tomorrow morning."],
    )

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query must not be empty or whitespace only")
        return v


# ── Health response ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """GET /health response per API_CONTRACT.md."""

    status: str = "ok"


# ── Reason response ───────────────────────────────────────────────────────────

class LocationModel(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RequestedTimeModel(BaseModel):
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class RecommendationModel(BaseModel):
    zone_id: Optional[str] = None
    suitability_score: Optional[int] = None
    risk_score: Optional[int] = None
    confidence_score: Optional[float] = None
    reason: Optional[str] = None


class MapModel(BaseModel):
    geojson: Optional[Dict[str, Any]] = None


class ReasonResponse(BaseModel):
    """
    POST /api/v1/reason response per API_CONTRACT.md.

    IMPORTANT: status must be one of the contracted values only AFTER
    the full reasoning pipeline has run. The MVP placeholder uses
    "PIPELINE_NOT_CONNECTED" to prevent false safety claims.

    Contracted final statuses (API_CONTRACT.md):
        SAFE | CAUTION | BLOCK | NO_SAFE_RECOMMENDATION
    """

    status: str
    query: str
    location: Optional[LocationModel] = None
    requested_time: Optional[RequestedTimeModel] = None
    recommendation: Optional[RecommendationModel] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    map: Optional[MapModel] = None
