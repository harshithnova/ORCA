"""
ORCA API route definitions.

Endpoints defined here must match API_CONTRACT.md exactly.
Do NOT add routes without updating API_CONTRACT.md.
"""

from fastapi import APIRouter

from backend.api.schemas import HealthResponse, ReasonRequest, ReasonResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """
    GET /health

    Returns application health status per API_CONTRACT.md.
    """
    return HealthResponse(status="ok")


@router.post(
    "/api/v1/reason",
    response_model=ReasonResponse,
    tags=["Reasoning"],
)
async def reason(request: ReasonRequest) -> ReasonResponse:
    """
    POST /api/v1/reason

    Accepts a natural-language query and returns the ORCA reasoning result.

    MVP STATUS: The full reasoning pipeline (Planner → GIS → Safety Engine)
    is not yet connected. This endpoint validates the request schema and
    returns a clearly-marked placeholder.

    IMPORTANT: The placeholder status "PIPELINE_NOT_CONNECTED" is intentional.
    It prevents this skeleton from falsely claiming SAFE / CAUTION / BLOCK /
    NO_SAFE_RECOMMENDATION before the pipeline has actually run.
    Those statuses will replace this placeholder once P2 (Planner), P3 (Data),
    and P4 (Safety) are wired in by P5.
    """
    return ReasonResponse(
        status="PIPELINE_NOT_CONNECTED",
        query=request.query,
        location=None,
        requested_time=None,
        recommendation=None,
        evidence=[],
        map=None,
    )
