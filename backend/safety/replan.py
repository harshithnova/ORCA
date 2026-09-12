"""
Deterministic replanning module for ORCA Safety Engine.

Provides candidate iteration and audit trail tracking when candidates
are BLOCKED by safety checks.

RULES (SAFETY_SPEC.md, AGENTS.md):
- Deterministic candidate progression (preserves candidate ranking order).
- Never retries a candidate that has already been evaluated.
- Never mutates candidate objects unexpectedly.
- When all candidates are exhausted, returns None (triggering NO_SAFE_RECOMMENDATION).
- Contains zero LLM logic, zero scoring formulas, and zero API code.
"""

from typing import Any, Dict, List, Optional, Set


def select_next_candidate(
    candidates: List[Dict[str, Any]],
    evaluated_ids: Set[str],
) -> Optional[Dict[str, Any]]:
    """
    Select the next un-evaluated candidate preserving the original ranking order.

    Args:
        candidates: Ordered list of candidate zone dictionaries.
        evaluated_ids: Set of candidate IDs already evaluated.

    Returns:
        A copy of the next un-evaluated candidate dict, or None if all are exhausted.
    """
    for cand in candidates:
        cid = cand.get("id")
        if cid is not None and cid not in evaluated_ids:
            return dict(cand)
    return None


class ReplanManager:
    """
    Manager for iterating candidate zones during safety replanning.
    """

    def __init__(self, candidates: List[Dict[str, Any]]):
        # Store a copy to prevent external list mutations from affecting iteration
        self._candidates: List[Dict[str, Any]] = [dict(c) for c in candidates]
        self._evaluated_ids: Set[str] = set()
        self._audit_log: List[Dict[str, Any]] = []

    def get_next_candidate(self) -> Optional[Dict[str, Any]]:
        """
        Return a copy of the next un-evaluated candidate in original ranking order.
        Returns None when all candidates have been evaluated.
        """
        return select_next_candidate(self._candidates, self._evaluated_ids)

    def record_evaluation(
        self,
        candidate_id: str,
        safety_status: str,
        blocking_reason: Optional[str] = None,
        blocking_evidence: Optional[List[Dict[str, Any]]] = None,
        reason: Optional[str] = None,
    ) -> None:
        """
        Record the evaluation result for a candidate.
        Marks candidate_id as evaluated so it is never selected again.
        """
        effective_reason = blocking_reason if blocking_reason is not None else reason
        self._evaluated_ids.add(candidate_id)
        self._audit_log.append({
            "candidate_id": candidate_id,
            "safety_status": safety_status,
            "blocking_reason": effective_reason,
            "blocking_evidence": list(blocking_evidence or []),
        })

    def is_exhausted(self) -> bool:
        """True if all candidates have been evaluated or candidate list was empty."""
        return self.get_next_candidate() is None

    @property
    def evaluated_ids(self) -> Set[str]:
        """Set of candidate IDs evaluated so far."""
        return set(self._evaluated_ids)

    @property
    def audit_log(self) -> List[Dict[str, Any]]:
        """Copy of evaluation audit log entries for all tried candidates."""
        return [dict(entry) for entry in self._audit_log]

    @property
    def remaining_count(self) -> int:
        """Count of candidates remaining to be evaluated."""
        return sum(
            1 for c in self._candidates
            if c.get("id") is not None and c.get("id") not in self._evaluated_ids
        )
