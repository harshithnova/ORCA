from __future__ import annotations

from typing import Any, List

import pytest

from ai.agents.planner import PlannerAgent, PlannerOutput


class _FakeStructuredRunnable:
    def __init__(
        self,
        output: Any = None,
        error: Exception | None = None,
    ) -> None:
        self.output = output
        self.error = error
        self.last_messages: List[Any] = []
        self.invoke_count = 0

    def invoke(self, messages: List[Any]) -> Any:
        self.invoke_count += 1
        self.last_messages = messages

        if self.error is not None:
            raise self.error

        return self.output


class _FakeChatModel:
    def __init__(
        self,
        output: Any = None,
        error: Exception | None = None,
    ) -> None:
        self.structured = _FakeStructuredRunnable(
            output=output,
            error=error,
        )
        self.requested_schema = None

    def with_structured_output(self, schema):
        self.requested_schema = schema
        return self.structured


def _planner_output(
    *,
    intent: str,
    location: str | None = None,
    time_window: str | None = None,
    capabilities: list[str] | None = None,
    requires_context: bool = False,
    confidence: float | None = None,
    raw_query: str = "LLM supplied query",
) -> PlannerOutput:
    return PlannerOutput(
        intent=intent,
        location_text=location,
        time_window_text=time_window,
        required_capabilities=capabilities or [],
        requires_context=requires_context,
        raw_query=raw_query,
        confidence_of_understanding=confidence,
    )


def test_find_zone_preserves_interpretation():
    model = _FakeChatModel(
        output=_planner_output(
            intent="find_zone",
            location="near Kochi",
            time_window="tomorrow morning",
            capabilities=["marine", "weather", "geo", "safety"],
            confidence=0.9,
        )
    )
    agent = PlannerAgent(llm=model)

    query = "Where should I fish tomorrow morning near Kochi?"
    result = agent.plan(query)

    assert result.intent == "find_zone"
    assert result.location_text == "near Kochi"
    assert result.time_window_text == "tomorrow morning"
    assert result.required_capabilities == [
        "marine",
        "weather",
        "geo",
        "safety",
    ]
    assert result.requires_context is False
    assert result.confidence_of_understanding == 0.9


def test_safety_check_preserves_interpretation():
    model = _FakeChatModel(
        output=_planner_output(
            intent="safety_check",
            time_window="tomorrow morning",
            capabilities=["marine", "weather", "safety"],
        )
    )
    agent = PlannerAgent(llm=model)

    result = agent.plan("Is it safe to go fishing tomorrow morning?")

    assert result.intent == "safety_check"
    assert result.location_text is None
    assert result.time_window_text == "tomorrow morning"
    assert result.required_capabilities == [
        "marine",
        "weather",
        "safety",
    ]
    assert result.requires_context is False


def test_explain_previous_requires_context():
    model = _FakeChatModel(
        output=_planner_output(
            intent="explain_previous",
            requires_context=True,
        )
    )
    agent = PlannerAgent(llm=model)

    result = agent.plan("Why this recommendation?")

    assert result.intent == "explain_previous"
    assert result.requires_context is True


def test_unknown_is_valid_structured_intent():
    model = _FakeChatModel(
        output=_planner_output(
            intent="unknown",
        )
    )
    agent = PlannerAgent(llm=model)

    query = "Tell me something unrelated."
    result = agent.plan(query)

    assert result.intent == "unknown"
    assert result.raw_query == query
    assert result.required_capabilities == []
    assert result.requires_context is False


def test_location_and_time_remain_unresolved_text():
    model = _FakeChatModel(
        output=_planner_output(
            intent="find_zone",
            location="near Kochi",
            time_window="tomorrow morning",
        )
    )
    agent = PlannerAgent(llm=model)

    result = agent.plan("Find a fishing zone near Kochi tomorrow morning.")

    assert result.location_text == "near Kochi"
    assert result.time_window_text == "tomorrow morning"


def test_structured_output_schema_is_injected():
    model = _FakeChatModel(
        output=_planner_output(intent="find_zone")
    )

    PlannerAgent(llm=model)

    assert model.requested_schema is PlannerOutput


def test_original_query_reaches_structured_model():
    model = _FakeChatModel(
        output=_planner_output(intent="find_zone")
    )
    agent = PlannerAgent(llm=model)

    query = "Find a fishing zone near Kochi tomorrow."
    agent.plan(query)

    messages = model.structured.last_messages

    assert len(messages) == 2
    assert messages[1].content == query


def test_raw_query_is_always_original_query():
    model = _FakeChatModel(
        output=_planner_output(
            intent="find_zone",
            raw_query="LLM attempted to replace this",
        )
    )
    agent = PlannerAgent(llm=model)

    query = "Actual user query"
    result = agent.plan(query)

    assert result.raw_query == query


def test_dict_structured_output_is_normalized():
    class _DictModel:
        def with_structured_output(self, schema):
            assert schema is PlannerOutput

            class Runnable:
                def invoke(self, messages):
                    return {
                        "intent": "find_zone",
                        "location_text": "near Kochi",
                        "time_window_text": "tomorrow morning",
                        "required_capabilities": ["marine", "geo"],
                        "requires_context": False,
                        "raw_query": "wrong value",
                    }

            return Runnable()

    agent = PlannerAgent(llm=_DictModel())

    result = agent.plan("actual query")

    assert isinstance(result, PlannerOutput)
    assert result.intent == "find_zone"
    assert result.location_text == "near Kochi"
    assert result.time_window_text == "tomorrow morning"
    assert result.required_capabilities == ["marine", "geo"]
    assert result.raw_query == "actual query"


def test_malformed_structured_output_returns_unknown():
    class _MalformedModel:
        def with_structured_output(self, schema):
            assert schema is PlannerOutput

            class Runnable:
                def invoke(self, messages):
                    return {
                        "intent": "not_a_valid_intent",
                        "location_text": "near Kochi",
                    }

            return Runnable()

    agent = PlannerAgent(llm=_MalformedModel())

    query = "Find a fishing zone near Kochi"
    result = agent.plan(query)

    assert result.intent == "unknown"
    assert result.raw_query == query


def test_invalid_capability_returns_unknown():
    class _MalformedModel:
        def with_structured_output(self, schema):
            assert schema is PlannerOutput

            class Runnable:
                def invoke(self, messages):
                    return {
                        "intent": "find_zone",
                        "required_capabilities": ["marine", "not_a_capability"],
                    }

            return Runnable()

    agent = PlannerAgent(llm=_MalformedModel())

    query = "Find a fishing zone"
    result = agent.plan(query)

    assert result.intent == "unknown"
    assert result.raw_query == query


def test_unsupported_structured_response_returns_unknown():
    model = _FakeChatModel(output="not structured output")
    agent = PlannerAgent(llm=model)

    query = "Find a fishing zone"
    result = agent.plan(query)

    assert result.intent == "unknown"
    assert result.raw_query == query


def test_model_failure_returns_unknown_without_raising():
    model = _FakeChatModel(
        error=RuntimeError("simulated provider failure")
    )
    agent = PlannerAgent(llm=model)

    query = "Find a fishing zone near Kochi"
    result = agent.plan(query)

    assert result.intent == "unknown"
    assert result.raw_query == query
    assert result.location_text is None
    assert result.time_window_text is None
    assert result.required_capabilities == []
    assert result.requires_context is False


def test_injected_provider_is_used_directly():
    model = _FakeChatModel(
        output=_planner_output(intent="find_zone")
    )
    agent = PlannerAgent(llm=model)

    agent.plan("Find a fishing zone")

    assert model.structured.invoke_count == 1


def test_planner_output_contains_no_downstream_business_fields():
    forbidden = {
        "risk",
        "risk_score",
        "suitability",
        "suitability_score",
        "distance",
        "distance_km",
        "safety_decision",
        "coordinates",
        "latitude",
        "longitude",
        "resolved_time",
        "timestamp",
        "safety_confidence",
        "risk_confidence",
        "suitability_confidence",
    }

    field_names = set(PlannerOutput.model_fields)

    assert not field_names.intersection(forbidden)


def test_confidence_is_planner_understanding_only():
    fields = set(PlannerOutput.model_fields)

    assert "confidence_of_understanding" in fields
    assert "confidence" not in fields
    assert "safety_confidence" not in fields


def test_confidence_value_is_preserved():
    model = _FakeChatModel(
        output=_planner_output(
            intent="find_zone",
            confidence=0.73,
        )
    )
    agent = PlannerAgent(llm=model)

    result = agent.plan("Find a fishing zone")

    assert result.confidence_of_understanding == 0.73


def test_empty_query_returns_unknown_without_calling_model():
    model = _FakeChatModel(
        output=_planner_output(intent="find_zone")
    )
    agent = PlannerAgent(llm=model)

    result = agent.plan("   ")

    assert result.intent == "unknown"
    assert result.raw_query == "   "
    assert model.structured.invoke_count == 0


def test_non_string_query_is_rejected():
    model = _FakeChatModel(
        output=_planner_output(intent="unknown")
    )
    agent = PlannerAgent(llm=model)

    with pytest.raises(TypeError):
        agent.plan(None)  # type: ignore[arg-type]


def test_none_llm_is_rejected():
    with pytest.raises(ValueError):
        PlannerAgent(llm=None)  # type: ignore[arg-type]