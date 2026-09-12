"""
Tests for ai.agents.graph.build_graph.

All dependencies are deterministic fakes.
No real APIs, databases, external services, or LLM providers are used.
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, List

from ai.agents.graph import OrcaDependencies, build_graph
from ai.agents.planner import PlannerOutput


class _FakePlanner:
    def __init__(self, output: PlannerOutput) -> None:
        self._output = output
        self.calls: List[str] = []

    def plan(self, query: str) -> PlannerOutput:
        self.calls.append(query)
        return self._output.model_copy(update={"raw_query": query})


class _FakeMarine:
    def __init__(self, output: Dict[str, Any] | None = None) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.output = output or {"marine": "fake_marine_data"}

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(context)
        return self.output


class _FakeWeather:
    def __init__(self, output: Dict[str, Any] | None = None) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.output = output or {"weather": "fake_weather_data"}

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(context)
        return self.output


class _FakeGeo:
    def __init__(self, output: Dict[str, Any] | None = None) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.output = output or {"geo": "fake_geo_data"}

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(context)
        return self.output


class _FakeReasoning:
    def __init__(self, output: Dict[str, Any] | None = None) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.output = output or {
            "decision": "recommended_zone_A",
            "factors": ["calm_seas"],
            "confidence": 0.8,
        }

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(context)
        return self.output


class _FakeSafety:
    def __init__(
        self,
        output: Dict[str, Any] | None = None,
    ) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.output = output or {
            "decision": "SAFE",
            "factors": ["calm_seas"],
            "confidence": 0.8,
        }

    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(context)
        return self.output


class _RecordingExplanation:
    def __init__(self, text: str = "recorded explanation") -> None:
        self.received: List[Dict[str, Any]] = []
        self.text = text

    def explain(self, evidence: Dict[str, Any]) -> str:
        self.received.append(evidence)
        return self.text


class _FailingComponent:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        raise RuntimeError(self.message)


class _FailingReasoning:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        raise RuntimeError(self.message)


class _FailingSafety:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        raise RuntimeError(self.message)


def _plan(
    *,
    intent: str = "find_zone",
    capabilities: list[str] | None = None,
    requires_context: bool = False,
) -> PlannerOutput:
    return PlannerOutput(
        intent=intent,
        location_text="near Kochi",
        time_window_text="tomorrow morning",
        required_capabilities=capabilities or [],
        requires_context=requires_context,
        raw_query="placeholder",
    )


def _full_dependencies(
    planner_output: PlannerOutput,
    *,
    explanation: _RecordingExplanation | None = None,
):
    marine = _FakeMarine()
    weather = _FakeWeather()
    geo = _FakeGeo()
    reasoning = _FakeReasoning()
    safety = _FakeSafety()
    explanation = explanation or _RecordingExplanation()

    dependencies = OrcaDependencies(
        planner=_FakePlanner(planner_output),
        explanation=explanation,
        marine=marine,
        weather=weather,
        geo=geo,
        reasoning=reasoning,
        safety=safety,
    )

    return dependencies, marine, weather, geo, reasoning, safety, explanation


def test_complete_pipeline_runs_in_order_and_propagates_data():
    dependencies, marine, weather, geo, reasoning, safety, explanation = (
        _full_dependencies(
            _plan(
                capabilities=["marine", "weather", "geo", "safety"],
            )
        )
    )

    graph = build_graph(dependencies)

    query = "Where should I fish tomorrow morning near Kochi?"
    final_state = graph.invoke({"query": query, "errors": []})

    assert final_state["planner_output"].intent == "find_zone"
    assert final_state["planner_output"].raw_query == query

    assert final_state["marine_data"] == {"marine": "fake_marine_data"}
    assert final_state["weather_data"] == {"weather": "fake_weather_data"}
    assert final_state["geo_data"] == {"geo": "fake_geo_data"}
    assert final_state["reasoning_output"]["decision"] == "recommended_zone_A"
    assert final_state["safety_output"]["decision"] == "SAFE"
    assert final_state["explanation"] == "recorded explanation"
    assert final_state["errors"] == []

    assert len(marine.calls) == 1
    assert len(weather.calls) == 1
    assert len(geo.calls) == 1
    assert len(reasoning.calls) == 1
    assert len(safety.calls) == 1
    assert len(explanation.received) == 1


def test_find_zone_non_context_request_still_uses_normal_pipeline():
    dependencies, marine, weather, geo, reasoning, safety, explanation = (
        _full_dependencies(
            _plan(
                intent="find_zone",
                capabilities=["marine", "weather", "geo", "safety"],
                requires_context=False,
            )
        )
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Find a fishing zone.",
            "errors": [],
        }
    )

    assert len(marine.calls) == 1
    assert len(weather.calls) == 1
    assert len(geo.calls) == 1
    assert len(reasoning.calls) == 1
    assert len(safety.calls) == 1
    assert len(explanation.received) == 1
    assert final_state["safety_output"]["decision"] == "SAFE"


def test_safety_check_non_context_request_still_uses_existing_pipeline():
    dependencies, marine, weather, geo, reasoning, safety, explanation = (
        _full_dependencies(
            _plan(
                intent="safety_check",
                capabilities=["marine", "weather", "geo", "safety"],
                requires_context=False,
            )
        )
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Is it safe to fish?",
            "errors": [],
        }
    )

    assert len(marine.calls) == 1
    assert len(weather.calls) == 1
    assert len(geo.calls) == 1
    assert len(reasoning.calls) == 1
    assert len(safety.calls) == 1
    assert len(explanation.received) == 1
    assert final_state["safety_output"]["decision"] == "SAFE"


def test_unknown_intent_skips_all_downstream_decision_components():
    dependencies, marine, weather, geo, reasoning, safety, explanation = (
        _full_dependencies(
            _plan(
                intent="unknown",
                capabilities=["marine", "weather", "geo", "safety"],
                requires_context=False,
            )
        )
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Something the planner cannot reliably interpret.",
            "errors": [],
        }
    )

    assert marine.calls == []
    assert weather.calls == []
    assert geo.calls == []
    assert reasoning.calls == []
    assert safety.calls == []

    assert final_state.get("marine_data") is None
    assert final_state.get("weather_data") is None
    assert final_state.get("geo_data") is None
    assert final_state.get("reasoning_output") is None
    assert final_state.get("safety_output") is None


def test_unknown_intent_reaches_existing_explanation_path():
    dependencies, marine, weather, geo, reasoning, safety, explanation = (
        _full_dependencies(
            _plan(
                intent="unknown",
                capabilities=["marine", "weather", "geo", "safety"],
            )
        )
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Uninterpretable request.",
            "errors": [],
        }
    )

    assert final_state["explanation"] == "recorded explanation"
    assert len(explanation.received) == 1

    evidence = explanation.received[0]
    assert evidence["marine_data"] is None
    assert evidence["weather_data"] is None
    assert evidence["geo_data"] is None
    assert evidence["reasoning_output"] is None
    assert evidence["safety_output"] is None
    assert evidence["errors"] == []


def test_unknown_intent_does_not_fabricate_recommendation_or_safety_result():
    dependencies, _, _, _, _, _, _ = _full_dependencies(
        _plan(
            intent="unknown",
            capabilities=["marine", "weather", "geo", "safety"],
        )
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Uninterpretable request.",
            "errors": [],
        }
    )

    assert final_state.get("reasoning_output") is None
    assert final_state.get("safety_output") is None
    assert final_state["explanation"] == "recorded explanation"


def test_unknown_intent_preserves_prior_evidence_without_calling_specialists():
    explanation = _RecordingExplanation()

    dependencies, marine, weather, geo, reasoning, safety, _ = _full_dependencies(
        _plan(
            intent="unknown",
            capabilities=["marine", "weather", "geo", "safety"],
        ),
        explanation=explanation,
    )

    prior_evidence = {
        "marine_data": {"marine": "previous"},
        "weather_data": {"weather": "previous"},
        "geo_data": {"geo": "previous"},
        "reasoning_output": {"decision": "previous_decision"},
        "safety_output": {"decision": "SAFE"},
        "errors": [],
    }

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Uninterpretable request.",
            "prior_evidence": prior_evidence,
            "errors": [],
        }
    )

    assert marine.calls == []
    assert weather.calls == []
    assert geo.calls == []
    assert reasoning.calls == []
    assert safety.calls == []

    assert explanation.received[0] == prior_evidence
    assert final_state["explanation"] == "recorded explanation"


def test_planner_output_propagates_to_specialist_context():
    dependencies, marine, _, _, _, _, _ = _full_dependencies(
        _plan(
            capabilities=["marine"],
        )
    )

    graph = build_graph(dependencies)
    query = "Find a fishing zone near Kochi tomorrow morning."

    graph.invoke({"query": query, "errors": []})

    assert len(marine.calls) == 1
    context = marine.calls[0]

    assert context["query"] == query
    assert context["planner_output"]["intent"] == "find_zone"
    assert context["planner_output"]["location_text"] == "near Kochi"
    assert context["planner_output"]["time_window_text"] == "tomorrow morning"


def test_reasoning_receives_marine_weather_and_geo_data():
    dependencies, _, _, _, reasoning, _, _ = _full_dependencies(
        _plan(
            capabilities=["marine", "weather", "geo"],
        )
    )

    graph = build_graph(dependencies)
    graph.invoke({"query": "Find a fishing zone.", "errors": []})

    assert len(reasoning.calls) == 1
    assert reasoning.calls[0] == {
        "marine_data": {"marine": "fake_marine_data"},
        "weather_data": {"weather": "fake_weather_data"},
        "geo_data": {"geo": "fake_geo_data"},
    }


def test_safety_receives_reasoning_output():
    dependencies, _, _, _, _, safety, _ = _full_dependencies(
        _plan(capabilities=["safety"])
    )

    graph = build_graph(dependencies)
    graph.invoke({"query": "Is it safe?", "errors": []})

    assert len(safety.calls) == 1
    assert safety.calls[0] == {
        "reasoning_output": {
            "decision": "recommended_zone_A",
            "factors": ["calm_seas"],
            "confidence": 0.8,
        },
    }


def test_explanation_receives_all_current_evidence():
    dependencies, _, _, _, _, _, explanation = _full_dependencies(
        _plan(
            capabilities=["marine", "weather", "geo", "safety"],
        )
    )

    graph = build_graph(dependencies)
    graph.invoke({"query": "Where should I fish?", "errors": []})

    assert len(explanation.received) == 1
    evidence = explanation.received[0]

    assert evidence["marine_data"] == {"marine": "fake_marine_data"}
    assert evidence["weather_data"] == {"weather": "fake_weather_data"}
    assert evidence["geo_data"] == {"geo": "fake_geo_data"}
    assert evidence["reasoning_output"]["decision"] == "recommended_zone_A"
    assert evidence["safety_output"]["decision"] == "SAFE"


def test_context_route_goes_directly_to_explanation():
    explanation = _RecordingExplanation()
    dependencies, marine, weather, geo, reasoning, safety, _ = _full_dependencies(
        _plan(
            intent="explain_previous",
            requires_context=True,
        ),
        explanation=explanation,
    )

    prior_evidence = {
        "marine_data": {"marine": "previous"},
        "weather_data": {"weather": "previous"},
        "geo_data": {"geo": "previous"},
        "reasoning_output": {"decision": "recommended_zone_A"},
        "safety_output": {"decision": "SAFE"},
        "errors": [],
    }

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Why this recommendation?",
            "prior_evidence": prior_evidence,
            "errors": [],
        }
    )

    assert marine.calls == []
    assert weather.calls == []
    assert geo.calls == []
    assert reasoning.calls == []
    assert safety.calls == []

    assert explanation.received[0] == prior_evidence
    assert final_state["explanation"] == "recorded explanation"


def test_context_route_preserves_prior_errors_and_current_errors():
    explanation = _RecordingExplanation()

    dependencies, _, _, _, _, _, _ = _full_dependencies(
        _plan(
            intent="explain_previous",
            requires_context=True,
        ),
        explanation=explanation,
    )

    prior_evidence = {
        "reasoning_output": {"decision": "recommended_zone_A"},
        "safety_output": {"decision": "SAFE"},
        "errors": ["previous error"],
    }

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Why this recommendation?",
            "prior_evidence": prior_evidence,
            "errors": ["current error"],
        }
    )

    assert explanation.received[0]["errors"] == [
        "previous error",
        "current error",
    ]
    assert final_state["errors"] == ["current error"]


def test_context_without_prior_evidence_does_not_call_specialists():
    explanation = _RecordingExplanation()

    dependencies, marine, weather, geo, reasoning, safety, _ = _full_dependencies(
        _plan(
            intent="explain_previous",
            requires_context=True,
        ),
        explanation=explanation,
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Why this recommendation?",
            "errors": [],
        }
    )

    assert marine.calls == []
    assert weather.calls == []
    assert geo.calls == []
    assert reasoning.calls == []
    assert safety.calls == []

    assert final_state["explanation"] == "recorded explanation"
    assert explanation.received[0]["safety_output"] is None


def test_missing_marine_dependency_records_error_and_continues():
    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan(capabilities=["marine", "weather"])),
        explanation=_RecordingExplanation(),
        marine=None,
        weather=_FakeWeather(),
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {"query": "Find a fishing zone.", "errors": []}
    )

    assert final_state["marine_data"] is None
    assert final_state["weather_data"] == {"weather": "fake_weather_data"}

    assert any(
        "marine agent not yet available" in error
        for error in final_state["errors"]
    )


def test_missing_reasoning_dependency_records_error():
    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan(capabilities=[])),
        explanation=_RecordingExplanation(),
        reasoning=None,
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {"query": "Find a fishing zone.", "errors": []}
    )

    assert final_state["reasoning_output"] is None
    assert any(
        "reasoning engine not yet available" in error
        for error in final_state["errors"]
    )


def test_missing_safety_dependency_records_error_without_inventing_result():
    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan(capabilities=[])),
        explanation=_RecordingExplanation(),
        safety=None,
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {"query": "Is it safe?", "errors": []}
    )

    assert final_state["safety_output"] is None
    assert any(
        "safety engine not yet available" in error
        for error in final_state["errors"]
    )


def test_upstream_failure_is_recorded_without_fabricating_output():
    marine = _FailingComponent("marine service unavailable")

    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan(capabilities=["marine"])),
        explanation=_RecordingExplanation(),
        marine=marine,
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {"query": "Find a fishing zone.", "errors": []}
    )

    assert marine.calls == 1
    assert final_state["marine_data"] is None
    assert any(
        "marine agent failed: marine service unavailable" in error
        for error in final_state["errors"]
    )


def test_reasoning_failure_is_recorded_without_fabricating_output():
    reasoning = _FailingReasoning("reasoning unavailable")

    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan()),
        explanation=_RecordingExplanation(),
        reasoning=reasoning,
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {"query": "Find a fishing zone.", "errors": []}
    )

    assert reasoning.calls == 1
    assert final_state["reasoning_output"] is None
    assert any(
        "reasoning engine failed: reasoning unavailable" in error
        for error in final_state["errors"]
    )


def test_safety_failure_is_recorded_without_fabricating_output():
    safety = _FailingSafety("safety engine unavailable")

    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan()),
        explanation=_RecordingExplanation(),
        safety=safety,
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {"query": "Is it safe?", "errors": []}
    )

    assert safety.calls == 1
    assert final_state["safety_output"] is None
    assert any(
        "safety engine failed: safety engine unavailable" in error
        for error in final_state["errors"]
    )


def test_existing_errors_are_preserved():
    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan()),
        explanation=_RecordingExplanation(),
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Find a fishing zone.",
            "errors": ["upstream error"],
        }
    )

    assert "upstream error" in final_state["errors"]


def test_safety_output_remains_authoritative():
    safety_output = {
        "decision": "AVOID",
        "factors": ["unsafe_conditions"],
    }

    explanation = _RecordingExplanation(
        text="The conditions are safe. GO."
    )

    dependencies = OrcaDependencies(
        planner=_FakePlanner(_plan(capabilities=["safety"])),
        explanation=explanation,
        safety=_FakeSafety(output=safety_output),
    )

    graph = build_graph(dependencies)

    final_state = graph.invoke(
        {
            "query": "Is it safe?",
            "errors": [],
        }
    )

    assert final_state["safety_output"] == safety_output
    assert final_state["safety_output"]["decision"] == "AVOID"

    # The graph transports ExplanationAgent output; it does not replace
    # the authoritative SafetyEngine result with explanation text.
    assert final_state["explanation"] == "The conditions are safe. GO."


def test_graph_routing_has_no_business_threshold_logic():
    from ai.agents.graph import _route_after_planner

    source = inspect.getsource(_route_after_planner).lower()

    forbidden = (
        "risk",
        "suitability",
        "distance",
        "threshold",
        "latitude",
        "longitude",
    )

    assert all(term not in source for term in forbidden)


def test_non_context_route_does_not_depend_on_business_values():
    dependencies, marine, _, _, _, _, _ = _full_dependencies(
        _plan(
            capabilities=["marine"],
            requires_context=False,
        )
    )

    graph = build_graph(dependencies)

    graph.invoke(
        {
            "query": "Find a fishing zone.",
            "errors": [],
        }
    )

    assert len(marine.calls) == 1


def test_context_route_is_selected_only_by_requires_context():
    dependencies, marine, _, _, _, _, explanation = _full_dependencies(
        _plan(
            capabilities=["marine"],
            requires_context=True,
        )
    )

    graph = build_graph(dependencies)

    graph.invoke(
        {
            "query": "Why this recommendation?",
            "errors": [],
        }
    )

    assert marine.calls == []
    assert len(explanation.received) == 1