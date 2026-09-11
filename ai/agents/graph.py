"""
LangGraph orchestration for the ORCA AI layer.

Architecture:

    User Query
        -> Planner Agent
        -> Marine / Weather / Geo Agents
        -> Deterministic Reasoning
        -> Safety Engine
        -> Evidence / Explanation
        -> FastAPI

This module is orchestration only.

It does not:
- import backend/
- calculate suitability
- calculate risk
- calculate distance
- perform GIS
- calculate confidence
- make safety decisions
- define P5-specific interfaces
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, TypedDict, runtime_checkable

from langgraph.graph import END, StateGraph

from ai.agents.explanation import ExplanationAgent
from ai.agents.planner import PlannerAgent, PlannerOutput


# ---------------------------------------------------------------------------
# Injectable interfaces for components outside the AI/Planner layer
# ---------------------------------------------------------------------------


@runtime_checkable
class MarineAgentInterface(Protocol):
    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return opaque marine data for the given planning context."""
        ...


@runtime_checkable
class WeatherAgentInterface(Protocol):
    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return opaque weather data for the given planning context."""
        ...


@runtime_checkable
class GeoAgentInterface(Protocol):
    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return opaque geo/location-resolution data."""
        ...


@runtime_checkable
class ReasoningInterface(Protocol):
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return opaque deterministic reasoning output."""
        ...


@runtime_checkable
class SafetyInterface(Protocol):
    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return opaque safety-validated output."""
        ...


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


@dataclass
class OrcaDependencies:
    """
    Injected components used by the orchestration graph.

    Downstream dependencies remain optional while their contracts are
    finalized. Missing dependencies are recorded as graph errors.
    """

    planner: PlannerAgent
    explanation: ExplanationAgent

    marine: Optional[MarineAgentInterface] = None
    weather: Optional[WeatherAgentInterface] = None
    geo: Optional[GeoAgentInterface] = None
    reasoning: Optional[ReasoningInterface] = None
    safety: Optional[SafetyInterface] = None


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------


class OrcaGraphState(TypedDict, total=False):
    query: str

    # Planner-owned interpretation.
    planner_output: Optional[PlannerOutput]

    # Opaque downstream outputs.
    marine_data: Optional[Dict[str, Any]]
    weather_data: Optional[Dict[str, Any]]
    geo_data: Optional[Dict[str, Any]]
    reasoning_output: Optional[Dict[str, Any]]
    safety_output: Optional[Dict[str, Any]]

    # Evidence supplied from a previous interaction/request.
    #
    # This is deliberately not a memory system. It is simply an optional
    # caller-provided evidence payload used for context-dependent requests
    # such as "Why this recommendation?"
    prior_evidence: Optional[Dict[str, Any]]

    explanation: Optional[str]
    errors: List[str]


def _initial_errors(state: OrcaGraphState) -> List[str]:
    return list(state.get("errors", []))


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _planner_node(
    state: OrcaGraphState,
    deps: OrcaDependencies,
) -> OrcaGraphState:
    plan = deps.planner.plan(state["query"])

    return {
        **state,
        "planner_output": plan,
        "errors": _initial_errors(state),
    }


def _marine_node(
    state: OrcaGraphState,
    deps: OrcaDependencies,
) -> OrcaGraphState:
    plan = state.get("planner_output")
    errors = _initial_errors(state)

    if plan is None or "marine" not in plan.required_capabilities:
        return {
            **state,
            "marine_data": None,
            "errors": errors,
        }

    if deps.marine is None:
        errors.append(
            "marine agent not yet available (contract not finalized)"
        )
        return {
            **state,
            "marine_data": None,
            "errors": errors,
        }

    try:
        data = deps.marine.fetch(
            {
                "query": state["query"],
                "planner_output": plan.model_dump(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"marine agent failed: {exc}")
        return {
            **state,
            "marine_data": None,
            "errors": errors,
        }

    return {
        **state,
        "marine_data": data,
        "errors": errors,
    }


def _weather_node(
    state: OrcaGraphState,
    deps: OrcaDependencies,
) -> OrcaGraphState:
    plan = state.get("planner_output")
    errors = _initial_errors(state)

    if plan is None or "weather" not in plan.required_capabilities:
        return {
            **state,
            "weather_data": None,
            "errors": errors,
        }

    if deps.weather is None:
        errors.append(
            "weather agent not yet available (contract not finalized)"
        )
        return {
            **state,
            "weather_data": None,
            "errors": errors,
        }

    try:
        data = deps.weather.fetch(
            {
                "query": state["query"],
                "planner_output": plan.model_dump(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"weather agent failed: {exc}")
        return {
            **state,
            "weather_data": None,
            "errors": errors,
        }

    return {
        **state,
        "weather_data": data,
        "errors": errors,
    }


def _geo_node(
    state: OrcaGraphState,
    deps: OrcaDependencies,
) -> OrcaGraphState:
    plan = state.get("planner_output")
    errors = _initial_errors(state)

    if plan is None or "geo" not in plan.required_capabilities:
        return {
            **state,
            "geo_data": None,
            "errors": errors,
        }

    if deps.geo is None:
        errors.append(
            "geo agent not yet available (contract not finalized)"
        )
        return {
            **state,
            "geo_data": None,
            "errors": errors,
        }

    try:
        data = deps.geo.fetch(
            {
                "query": state["query"],
                "planner_output": plan.model_dump(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"geo agent failed: {exc}")
        return {
            **state,
            "geo_data": None,
            "errors": errors,
        }

    return {
        **state,
        "geo_data": data,
        "errors": errors,
    }


def _reasoning_node(
    state: OrcaGraphState,
    deps: OrcaDependencies,
) -> OrcaGraphState:
    errors = _initial_errors(state)

    if deps.reasoning is None:
        errors.append(
            "reasoning engine not yet available (contract not finalized)"
        )
        return {
            **state,
            "reasoning_output": None,
            "errors": errors,
        }

    context = {
        "marine_data": state.get("marine_data"),
        "weather_data": state.get("weather_data"),
        "geo_data": state.get("geo_data"),
    }

    try:
        output = deps.reasoning.evaluate(context)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"reasoning engine failed: {exc}")
        return {
            **state,
            "reasoning_output": None,
            "errors": errors,
        }

    return {
        **state,
        "reasoning_output": output,
        "errors": errors,
    }


def _safety_node(
    state: OrcaGraphState,
    deps: OrcaDependencies,
) -> OrcaGraphState:
    errors = _initial_errors(state)

    if deps.safety is None:
        errors.append(
            "safety engine not yet available (contract not finalized)"
        )
        return {
            **state,
            "safety_output": None,
            "errors": errors,
        }

    context = {
        "reasoning_output": state.get("reasoning_output"),
    }

    try:
        output = deps.safety.validate(context)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"safety engine failed: {exc}")
        return {
            **state,
            "safety_output": None,
            "errors": errors,
        }

    # IMPORTANT:
    # The graph does not interpret or modify the Safety output.
    # Whatever Safety returns remains authoritative.
    return {
        **state,
        "safety_output": output,
        "errors": errors,
    }


def _explanation_node(
    state: OrcaGraphState,
    deps: OrcaDependencies,
) -> OrcaGraphState:
    """
    Pass all relevant evidence already present in graph state.

    The graph does not interpret this evidence. It only hands it to the
    ExplanationAgent.
    """

    prior_evidence = state.get("prior_evidence")

    if prior_evidence is not None:
        evidence = dict(prior_evidence)

        # Preserve current graph errors as well.
        evidence["errors"] = list(
            dict.fromkeys(
                [
                    *evidence.get("errors", []),
                    *state.get("errors", []),
                ]
            )
        )
    else:
        evidence = {
            "marine_data": state.get("marine_data"),
            "weather_data": state.get("weather_data"),
            "geo_data": state.get("geo_data"),
            "reasoning_output": state.get("reasoning_output"),
            "safety_output": state.get("safety_output"),
            "errors": state.get("errors", []),
        }

    text = deps.explanation.explain(evidence)

    return {
        **state,
        "explanation": text,
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route_after_planner(state: OrcaGraphState) -> str:
    """
    Orchestration-only routing.

    Context-dependent and uninterpretable requests use the existing
    explanation path instead of starting the specialist pipeline.

    No business decision is made here.
    """

    plan = state.get("planner_output")

    if plan is not None and (
        plan.intent == "unknown" or plan.requires_context
    ):
        return "explanation"

    return "marine"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph(dependencies: OrcaDependencies):
    """
    Build and compile the ORCA AI-layer LangGraph.
    """

    graph = StateGraph(OrcaGraphState)

    graph.add_node(
        "planner",
        lambda state: _planner_node(state, dependencies),
    )
    graph.add_node(
        "marine",
        lambda state: _marine_node(state, dependencies),
    )
    graph.add_node(
        "weather",
        lambda state: _weather_node(state, dependencies),
    )
    graph.add_node(
        "geo",
        lambda state: _geo_node(state, dependencies),
    )
    graph.add_node(
        "reasoning",
        lambda state: _reasoning_node(state, dependencies),
    )
    graph.add_node(
        "safety",
        lambda state: _safety_node(state, dependencies),
    )
    graph.add_node(
        "explanation",
        lambda state: _explanation_node(state, dependencies),
    )

    graph.set_entry_point("planner")

    graph.add_conditional_edges(
        "planner",
        _route_after_planner,
        {
            "marine": "marine",
            "explanation": "explanation",
        },
    )

    graph.add_edge("marine", "weather")
    graph.add_edge("weather", "geo")
    graph.add_edge("geo", "reasoning")
    graph.add_edge("reasoning", "safety")
    graph.add_edge("safety", "explanation")
    graph.add_edge("explanation", END)

    return graph.compile()