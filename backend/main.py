"""
ORCA FastAPI application entry point.

Importable as: backend.main:app
Run with:      uvicorn backend.main:app --reload
"""

from fastapi import FastAPI

from backend.api.routes import router

app = FastAPI(
    title="ORCA - Marine EcOsystem Reasoning with Collaborative Agents",
    description=(
        "SIH 2026 Problem Statement SIH26176.\n\n"
        "API surface is defined in API_CONTRACT.md. "
        "Do not add endpoints without updating the contract and notifying affected owners."
    ),
    version="0.1.0-mvp",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router)
