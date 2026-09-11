"""
ai.agents
=========

Ownership boundary (per ORCA team split):

    LLM PLANS.  CODE CALCULATES.  SAFETY VALIDATES.

This package contains ONLY the Planner / LangGraph orchestration /
Explanation layer. It must never:
    - calculate suitability, risk, confidence, or distance
    - perform GIS calculations
    - make the final safety decision
    - invent marine/weather observations
    - override deterministic safety results
    - talk to backend/, INCOIS, or IMD directly

Everything owned by other teammates (Marine, Weather, Geo, Reasoning,
Safety, Backend/FastAPI) is represented here only as an injectable
interface (see graph.py: MarineAgentInterface, WeatherAgentInterface,
GeoAgentInterface, ReasoningInterface, SafetyInterface) or as an
opaque dict in graph state. Nothing about their real contracts is
assumed or invented.
"""

from ai.agents.planner import PlannerAgent, PlannerOutput
from ai.agents.graph import (
    OrcaGraphState,
    OrcaDependencies,
    MarineAgentInterface,
    WeatherAgentInterface,
    GeoAgentInterface,
    ReasoningInterface,
    SafetyInterface,
    build_graph,
)
from ai.agents.explanation import ExplanationAgent, EvidenceInput

__all__ = [
    "PlannerAgent",
    "PlannerOutput",
    "OrcaGraphState",
    "OrcaDependencies",
    "MarineAgentInterface",
    "WeatherAgentInterface",
    "GeoAgentInterface",
    "ReasoningInterface",
    "SafetyInterface",
    "build_graph",
    "ExplanationAgent",
    "EvidenceInput",
]
