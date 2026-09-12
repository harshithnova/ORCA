from __future__ import annotations

from typing import List, Literal, Mapping, Optional

from pydantic import BaseModel, Field

try:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:  # pragma: no cover
    BaseChatModel = object  # type: ignore[assignment,misc]
    HumanMessage = None  # type: ignore[assignment]
    SystemMessage = None  # type: ignore[assignment,misc]


class PlannerOutput(BaseModel):
    """
    LLM-produced interpretation of a user query.

    This is intentionally an interpretation contract, not a resolved
    execution contract.

    The Planner may identify:
    - user intent
    - location text
    - time-window text
    - required downstream capabilities
    - whether previous context is required

    The Planner must not resolve:
    - coordinates
    - timestamps
    - distance
    - suitability
    - risk
    - safety decisions
    """

    intent: Literal[
        "find_zone",
        "safety_check",
        "explain_previous",
        "unknown",
    ] = Field(
        description="High-level user intent as understood from the query."
    )

    location_text: Optional[str] = Field(
        default=None,
        description=(
            "Location mentioned by the user, preserved as text. "
            "This is not a resolved coordinate or geographic object."
        ),
    )

    time_window_text: Optional[str] = Field(
        default=None,
        description=(
            "Time expression mentioned by the user, preserved as text. "
            "This is not a resolved timestamp or date range."
        ),
    )

    required_capabilities: List[
        Literal["marine", "weather", "geo", "safety"]
    ] = Field(
        default_factory=list,
        description=(
            "Downstream capabilities required to process the request."
        ),
    )

    requires_context: bool = Field(
        default=False,
        description=(
            "Whether the request depends on previous conversation state."
        ),
    )

    raw_query: str = Field(
        description="Original user query, preserved verbatim."
    )

    confidence_of_understanding: Optional[float] = Field(
        default=None,
        description=(
            "Optional confidence in the Planner's own interpretation. "
            "This is not safety, risk, or suitability confidence."
        ),
    )


_SYSTEM_PROMPT = """You are the Planner component of ORCA.

Your only responsibility is to interpret the user's natural-language query
and produce a structured execution plan.

Extract:
- intent
- location mention
- time-window mention
- required downstream capabilities
- whether previous conversation context is required

IMPORTANT BOUNDARY:

You are producing an interpretation, not resolving data.

For locations:
- preserve the location as user-provided text
- do not convert locations into latitude/longitude
- do not perform GIS or distance calculations
- do not guess coordinates

For time:
- preserve the user's time expression as text
- do not convert relative expressions into timestamps
- do not invent dates or times

You must NOT:
- calculate suitability
- calculate risk
- calculate distance
- perform GIS calculations
- invent marine observations
- invent weather observations
- make safety decisions
- produce a safety recommendation

If information is not present in the query, return null/empty values rather
than guessing.

Respond only using the requested structured schema.
"""


class PlannerAgent:
    """
    Converts natural-language user queries into an unvalidated PlannerOutput.

    The LLM is injected by the application composition layer. No provider
    client, API key, or provider-specific SDK is created here.
    """

    def __init__(self, llm: "BaseChatModel") -> None:
        if llm is None:
            raise ValueError("PlannerAgent requires an injected LLM.")

        self._structured_llm = llm.with_structured_output(PlannerOutput)

    def plan(self, query: str) -> PlannerOutput:
        """
        Interpret a user query.

        Planner failures are converted into an explicit unknown plan so that
        the Planner itself does not crash the orchestration layer.

        The original query is always authoritative and is written into
        raw_query by this method rather than trusting the LLM to populate it.
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")

        if not query.strip():
            return PlannerOutput(
                intent="unknown",
                raw_query=query,
                requires_context=False,
            )

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]

        try:
            result = self._structured_llm.invoke(messages)
        except Exception:  # noqa: BLE001
            return self._unknown_plan(query)

        return self._normalize_result(result, query)

    @staticmethod
    def _unknown_plan(query: str) -> PlannerOutput:
        return PlannerOutput(
            intent="unknown",
            raw_query=query,
            requires_context=False,
        )

    def _normalize_result(
        self,
        result: object,
        query: str,
    ) -> PlannerOutput:
        """
        Normalize supported structured-output forms into PlannerOutput.

        The LLM is never allowed to control raw_query; the original query
        supplied to plan() is always used.
        """
        if isinstance(result, PlannerOutput):
            result.raw_query = query
            return result

        if isinstance(result, Mapping):
            try:
                payload = dict(result)
                payload["raw_query"] = query
                return PlannerOutput.model_validate(payload)
            except Exception:  # noqa: BLE001
                return self._unknown_plan(query)

        return self._unknown_plan(query)