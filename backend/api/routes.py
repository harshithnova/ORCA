"""
ORCA API route definitions.

Endpoints defined here must match API_CONTRACT.md exactly.
Do NOT add routes without updating API_CONTRACT.md.
"""

from fastapi import APIRouter

from backend.api.schemas import HealthResponse, ReasonRequest, ReasonResponse
from backend.services.pipeline_service import PipelineRequest, run_pipeline

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

    Accepts a natural-language query and returns the ORCA reasoning result
    executed deterministically through the reasoning and safety pipeline.
    """
    pipeline_request = PipelineRequest(query=request.query)
    return run_pipeline(pipeline_request)
