"""
Explanation layer for ORCA.

This component explains already-computed evidence. It does not calculate
suitability, risk, distance, confidence, GIS data, or safety decisions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

try:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:  # pragma: no cover
    BaseChatModel = object  # type: ignore[assignment,misc]
    HumanMessage = None  # type: ignore[assignment]
    SystemMessage = None  # type: ignore[assignment]


class EvidenceInput(BaseModel):
    """Loose view over unfinished downstream evidence schemas."""

    decision: Optional[str] = None
    factors: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_graph_evidence(cls, evidence: Dict[str, Any]) -> "EvidenceInput":
        reasoning = evidence.get("reasoning_output")
        safety = evidence.get("safety_output")

        reasoning = reasoning if isinstance(reasoning, dict) else {}
        safety = safety if isinstance(safety, dict) else {}

        merged = {**reasoning, **safety}

        factors = merged.get("factors", [])
        errors = evidence.get("errors", [])

        return cls(
            decision=merged.get("decision"),
            factors=list(factors) if isinstance(factors, list) else [],
            confidence=merged.get("confidence"),
            errors=list(errors) if isinstance(errors, list) else [],
            raw=evidence,
        )


_SYSTEM_PROMPT = """You are the Explanation component of ORCA.

Explain only evidence already produced by deterministic components.

The Safety decision is authoritative. Never change, reinterpret, or
contradict it.

Do not calculate or invent suitability, risk, distance, confidence,
observations, factors, numbers, or recommendations.

If evidence is incomplete, state that clearly.
"""


class ExplanationAgent:
    """Turns existing ORCA evidence into a user-facing explanation."""

    def __init__(self, llm: Optional["BaseChatModel"] = None) -> None:
        self._llm = llm

    def explain(self, evidence: Dict[str, Any]) -> str:
        parsed = EvidenceInput.from_graph_evidence(evidence)

        if parsed.errors:
            return self._explain_with_missing_data(parsed)

        # AVOID is authoritative. Do not expose it to an LLM that could
        # contradict it. The deterministic template is the guarantee.
        if parsed.decision and parsed.decision.strip().lower() == "avoid":
            return self._explain_with_template(parsed)

        if self._llm is not None:
            text = self._explain_with_llm(parsed)
            if text is not None:
                return text

        return self._explain_with_template(parsed)

    @staticmethod
    def _explain_with_missing_data(evidence: EvidenceInput) -> str:
        return (
            "I can't give a complete explanation yet because some "
            f"components aren't available: {'; '.join(evidence.errors)}."
        )

    @staticmethod
    def _explain_with_template(evidence: EvidenceInput) -> str:
        if evidence.decision is None:
            return "No decision is available yet to explain."

        parts = [f"The recommendation is: {evidence.decision}."]

        if evidence.factors:
            parts.append("This was based on: " + ", ".join(evidence.factors) + ".")

        if evidence.confidence is not None:
            parts.append(f"Confidence: {evidence.confidence}.")

        return " ".join(parts)

    def _explain_with_llm(self, evidence: EvidenceInput) -> Optional[str]:
        content = (
            f"Authoritative decision: {evidence.decision}\n"
            f"Factors: {', '.join(evidence.factors) or 'none provided'}\n"
            f"Confidence: "
            f"{evidence.confidence if evidence.confidence is not None else 'not provided'}\n\n"
            "Explain this evidence in one or two plain-language sentences."
        )

        try:
            response = self._llm.invoke(
                [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=content),
                ]
            )
        except Exception:  # noqa: BLE001
            return None

        text = getattr(response, "content", None)
        return text.strip() if isinstance(text, str) and text.strip() else None