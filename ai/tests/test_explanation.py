"""
Deterministic tests for ai.agents.explanation.ExplanationAgent.

No real LLM providers or external services are used.
These tests verify evidence handling and explanation behavior only.
"""

from __future__ import annotations

from typing import Any, List

from ai.agents.explanation import EvidenceInput, ExplanationAgent


class _FakeAIMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChatModel:
    def __init__(
        self,
        response_text: str = "",
        *,
        raise_error: bool = False,
    ) -> None:
        self.response_text = response_text
        self.raise_error = raise_error
        self.received_messages: List[Any] = []
        self.call_count = 0

    def invoke(self, messages: List[Any]) -> _FakeAIMessage:
        self.call_count += 1
        self.received_messages = messages

        if self.raise_error:
            raise RuntimeError("simulated provider failure")

        return _FakeAIMessage(self.response_text)


def test_normal_explanation_uses_supplied_evidence():
    evidence = {
        "safety_output": {
            "decision": "SAFE",
            "factors": ["calm_seas", "good_visibility"],
            "confidence": 0.85,
        },
        "reasoning_output": {
            "decision": "recommended_zone_A",
        },
        "errors": [],
    }

    text = ExplanationAgent().explain(evidence)

    assert "SAFE" in text
    assert "calm_seas" in text
    assert "good_visibility" in text
    assert "0.85" in text


def test_missing_decision_returns_deterministic_fallback():
    text = ExplanationAgent().explain(
        {
            "safety_output": {},
            "reasoning_output": {},
            "errors": [],
        }
    )

    assert text == "No decision is available yet to explain."


def test_missing_evidence_does_not_fabricate_decision():
    text = ExplanationAgent().explain({})

    assert "No decision is available yet to explain." == text
    assert "SAFE" not in text
    assert "AVOID" not in text


def test_none_evidence_sections_are_handled_without_fabrication():
    text = ExplanationAgent().explain(
        {
            "marine_data": None,
            "weather_data": None,
            "geo_data": None,
            "reasoning_output": None,
            "safety_output": None,
            "errors": [],
        }
    )

    assert text == "No decision is available yet to explain."


def test_upstream_errors_are_reported():
    error = "safety engine unavailable"

    text = ExplanationAgent().explain(
        {
            "reasoning_output": None,
            "safety_output": None,
            "errors": [error],
        }
    )

    assert error in text
    assert "complete explanation" in text


def test_upstream_errors_take_precedence_over_missing_decision():
    text = ExplanationAgent().explain(
        {
            "reasoning_output": {},
            "safety_output": {},
            "errors": ["weather data unavailable"],
        }
    )

    assert "weather data unavailable" in text
    assert "No decision is available yet to explain." not in text


def test_safety_decision_takes_precedence_over_reasoning_decision():
    evidence = {
        "reasoning_output": {
            "decision": "recommended_zone_A",
            "factors": ["reasoning_factor"],
            "confidence": 0.60,
        },
        "safety_output": {
            "decision": "AVOID",
            "factors": ["unsafe_conditions"],
            "confidence": 0.95,
        },
        "errors": [],
    }

    parsed = EvidenceInput.from_graph_evidence(evidence)

    assert parsed.decision == "AVOID"
    assert parsed.factors == ["unsafe_conditions"]
    assert parsed.confidence == 0.95


def test_safety_fields_override_matching_reasoning_fields():
    evidence = {
        "reasoning_output": {
            "decision": "SAFE",
            "factors": ["reasoning_factor"],
            "confidence": 0.40,
        },
        "safety_output": {
            "decision": "AVOID",
            "factors": ["safety_factor"],
            "confidence": 0.90,
        },
        "errors": [],
    }

    parsed = EvidenceInput.from_graph_evidence(evidence)

    assert parsed.decision == "AVOID"
    assert parsed.factors == ["safety_factor"]
    assert parsed.confidence == 0.90


def test_reasoning_evidence_is_used_when_safety_is_absent():
    evidence = {
        "reasoning_output": {
            "decision": "recommended_zone_A",
            "factors": ["calm_seas"],
            "confidence": 0.75,
        },
        "safety_output": None,
        "errors": [],
    }

    parsed = EvidenceInput.from_graph_evidence(evidence)

    assert parsed.decision == "recommended_zone_A"
    assert parsed.factors == ["calm_seas"]
    assert parsed.confidence == 0.75


def test_marine_weather_geo_data_is_preserved_as_opaque_evidence():
    evidence = {
        "marine_data": {"wave_state": "calm"},
        "weather_data": {"visibility": "good"},
        "geo_data": {"zone": "A"},
        "safety_output": {"decision": "SAFE"},
        "errors": [],
    }

    parsed = EvidenceInput.from_graph_evidence(evidence)

    assert parsed.raw["marine_data"] == {"wave_state": "calm"}
    assert parsed.raw["weather_data"] == {"visibility": "good"}
    assert parsed.raw["geo_data"] == {"zone": "A"}


def test_evidence_input_preserves_original_graph_evidence():
    evidence = {
        "marine_data": {"value": "marine"},
        "weather_data": {"value": "weather"},
        "geo_data": {"value": "geo"},
        "reasoning_output": {"decision": "SAFE"},
        "safety_output": {"decision": "SAFE"},
        "errors": [],
        "extra_field": {"opaque": True},
    }

    parsed = EvidenceInput.from_graph_evidence(evidence)

    assert parsed.raw == evidence
    assert parsed.raw["extra_field"] == {"opaque": True}


def test_invalid_factor_shape_does_not_create_fabricated_factors():
    evidence = {
        "safety_output": {
            "decision": "SAFE",
            "factors": "not-a-list",
        },
        "errors": [],
    }

    parsed = EvidenceInput.from_graph_evidence(evidence)

    assert parsed.decision == "SAFE"
    assert parsed.factors == []


def test_invalid_error_shape_does_not_create_fabricated_errors():
    evidence = {
        "safety_output": {"decision": "SAFE"},
        "errors": "not-a-list",
    }

    parsed = EvidenceInput.from_graph_evidence(evidence)

    assert parsed.errors == []


def test_llm_success_returns_provider_text():
    expected = "The supplied evidence supports the recommendation."

    llm = _FakeChatModel(expected)
    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "safety_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
                "confidence": 0.9,
            },
            "errors": [],
        }
    )

    assert text == expected
    assert llm.call_count == 1
    assert len(llm.received_messages) == 2


def test_provider_receives_authoritative_evidence():
    llm = _FakeChatModel("Evidence-based explanation.")

    agent = ExplanationAgent(llm=llm)

    agent.explain(
        {
            "reasoning_output": {
                "decision": "recommended_zone_A",
                "factors": ["calm_seas"],
            },
            "safety_output": {
                "decision": "SAFE",
                "factors": ["safe_conditions"],
                "confidence": 0.9,
            },
            "errors": [],
        }
    )

    assert llm.call_count == 1

    messages = llm.received_messages
    human_content = messages[1].content

    assert "Authoritative decision: SAFE" in human_content
    assert "safe_conditions" in human_content
    assert "0.9" in human_content


def test_llm_failure_falls_back_to_deterministic_template():
    llm = _FakeChatModel(
        "unused",
        raise_error=True,
    )

    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "safety_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
            },
            "errors": [],
        }
    )

    assert "SAFE" in text
    assert "calm_seas" in text
    assert llm.call_count == 1


def test_empty_llm_response_falls_back_to_template():
    llm = _FakeChatModel("   ")
    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "safety_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
            },
            "errors": [],
        }
    )

    assert "SAFE" in text
    assert "calm_seas" in text


def test_non_string_llm_response_content_falls_back():
    class _InvalidResponseLLM:
        def __init__(self) -> None:
            self.call_count = 0

        def invoke(self, messages: List[Any]) -> Any:
            self.call_count += 1
            return _FakeAIMessage(None)  # type: ignore[arg-type]

    llm = _InvalidResponseLLM()
    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "safety_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
            },
            "errors": [],
        }
    )

    assert "SAFE" in text
    assert "calm_seas" in text
    assert llm.call_count == 1


def test_no_fabricated_evidence_when_only_decision_exists():
    text = ExplanationAgent().explain(
        {
            "safety_output": {
                "decision": "SAFE",
            },
            "errors": [],
        }
    )

    assert "SAFE" in text
    assert "calm_seas" not in text
    assert "weather" not in text.lower()
    assert "distance" not in text.lower()


def test_no_fabricated_confidence_when_not_supplied():
    text = ExplanationAgent().explain(
        {
            "safety_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
            },
            "errors": [],
        }
    )

    assert "SAFE" in text
    assert "calm_seas" in text
    assert "Confidence:" not in text


def test_avoid_uses_authoritative_deterministic_path():
    llm = _FakeChatModel(
        "The conditions are safe. GO."
    )

    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "reasoning_output": {
                "decision": "recommended_zone_A",
                "factors": ["calm_seas"],
            },
            "safety_output": {
                "decision": "AVOID",
                "factors": ["rough_seas"],
            },
            "errors": [],
        }
    )

    assert text.startswith("The recommendation is: AVOID.")
    assert llm.call_count == 0
    assert "safe" not in text.lower()
    assert "go" not in text.lower()


def test_avoid_is_case_insensitive_and_still_blocks_llm():
    llm = _FakeChatModel(
        "The conditions are safe. GO."
    )

    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "safety_output": {
                "decision": "avoid",
                "factors": ["rough_seas"],
            },
            "errors": [],
        }
    )

    assert "avoid" in text.lower()
    assert llm.call_count == 0


def test_avoid_remains_authoritative_against_adversarial_llm():
    """
    Critical safety-boundary test.

    The fake LLM attempts to contradict the authoritative Safety result.
    ExplanationAgent must not expose the LLM response for an AVOID decision.
    """

    llm = _FakeChatModel(
        "The conditions are safe. GO."
    )

    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "reasoning_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
            },
            "safety_output": {
                "decision": "AVOID",
                "factors": ["unsafe_conditions"],
            },
            "errors": [],
        }
    )

    assert text.startswith("The recommendation is: AVOID.")
    assert "The conditions are safe. GO." not in text
    assert llm.call_count == 0


def test_provider_injection_is_used_without_creating_provider_internally():
    llm = _FakeChatModel("Provider supplied explanation.")

    agent = ExplanationAgent(llm=llm)

    text = agent.explain(
        {
            "safety_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
            },
            "errors": [],
        }
    )

    assert text == "Provider supplied explanation."
    assert llm.call_count == 1


def test_without_provider_agent_uses_deterministic_fallback():
    agent = ExplanationAgent()

    text = agent.explain(
        {
            "safety_output": {
                "decision": "SAFE",
                "factors": ["calm_seas"],
            },
            "errors": [],
        }
    )

    assert "SAFE" in text
    assert "calm_seas" in text

