"""
Confidence scoring module for ORCA decision-support system.

Implements the deterministic prototype model from REASONING_SPEC.md:
    Confidence = 0.50 * freshness + 0.40 * completeness + 0.10 * source_score
Clamped to [0.0, 1.0].

IMPORTANT: Confidence indicates confidence in the DATA-SUPPORTED RECOMMENDATION,
NOT the probability of fishing success. High confidence does NOT mean SAFE.

FRESHNESS VS VALIDITY (confirmed by code review -- team discussion required):
Current implementation treats valid_to as the freshness reference for forecasts.
This conflates two distinct concepts:
  - Forecast VALIDITY: does the forecast cover the requested time window?
    (valid_from <= query_time <= valid_to)
  - Data FRESHNESS: how recently was the forecast issued/retrieved?
    (how old is issued_at relative to now?)
For MVP these are handled together. Before production integration:
  Q-P3-1: Will normalized records always have issued_at, valid_from,
           valid_to AND retrieved_at populated for all forecast types?
  Q-P5-1: Should forecast validity (valid_from/valid_to window check) be
           separated from confidence freshness scoring? Recommended: yes.
           Validity belongs in the data normalization/adapter layer (P3).

MISSING RECORD BEHAVIOUR:
  If one domain (marine OR weather) is missing entirely, its freshness
  contribution is halved (conservative). Whether a missing domain should
  BLOCK the recommendation is a Safety Engine question, not a confidence one.

CONFIDENCE DOES NOT OVERRIDE SAFETY:
  confidence_score > 0.8 does NOT mean SAFE.
  confidence_score < 0.5 does NOT automatically mean BLOCK.
  The Safety Engine makes the final decision based on explicit hard rules.

SOURCE_SCORE_MAP DATA CONTRACT:
  SOURCE_SCORE_MAP in config.py must use exactly the same data_mode strings
  that P3 produces in normalized records. Must be verified before integration.
  Q-P3-2: Confirm exact data_mode enum values (CACHED_OFFICIAL, SIMULATED_MVP, etc.)

OPEN QUESTIONS (from code review):
  Q-P3-1: Confirm normalized record fields: issued_at, valid_from, valid_to, retrieved_at.
  Q-P3-2: Confirm exact data_mode enum values for SOURCE_SCORE_MAP alignment.
  Q-P5-1: Separate forecast validity check from freshness scoring?
  Q-P5-2: Should missing an entire data domain (marine/weather) trigger a Safety block?
  Q-P5-3: Should confidence weights be validated (sum=1.0, all>=0) in config layer?
  Q-P6-1: Future: weight critical vs non-critical fields differently in completeness.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.config import (
    CONFIDENCE_MAX_AGE_HOURS,
    CONFIDENCE_WEIGHTS,
    EXPECTED_MARINE_FIELDS,
    EXPECTED_WEATHER_FIELDS,
    SOURCE_SCORE_MAP,
)


def _parse_iso_datetime(dt_val: Any) -> Optional[datetime]:
    """Parse an ISO 8601 string or return datetime directly."""
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc)
        return dt_val
    if isinstance(dt_val, str):
        try:
            # Replace 'Z' with '+00:00' for standard fromisoformat parsing in Python 3.10
            clean_str = dt_val.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_str)
        except (ValueError, TypeError):
            return None
    return None


def calculate_freshness(
    record: Optional[Dict[str, Any]],
    query_time: Optional[datetime] = None,
    max_age_hours: float = CONFIDENCE_MAX_AGE_HOURS,
) -> float:
    """
    Calculate freshness score in [0.0, 1.0] for a data record.

    Uses 'valid_to' as the reference timestamp (end of forecast validity window).
    Falls back to issued_at then retrieved_at if valid_to is absent.

    Freshness = 1.0 when query_time is within or before valid_to.
    Freshness degrades linearly after valid_to expires, reaching 0.0
    at CONFIDENCE_MAX_AGE_HOURS past the reference timestamp.

    IMPORTANT: This implementation currently combines two distinct concepts:
    - Forecast validity (does the forecast cover query_time?)
    - Data freshness (how recently was the data issued/retrieved?)
    For full separation, the validity check (valid_from <= query_time <= valid_to)
    should be handled by the upstream data normalization layer (P3/P5).
    See module docstring Q-P5-1.
    """
    if not record:
        return 0.0

    target_time = query_time or datetime.now(timezone.utc)
    if target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=timezone.utc)

    # Reference timestamp: valid_to is primary for forecasts
    ref_dt = (
        _parse_iso_datetime(record.get("valid_to"))
        or _parse_iso_datetime(record.get("issued_at"))
        or _parse_iso_datetime(record.get("retrieved_at"))
    )

    if ref_dt is None:
        return 0.3  # Unknown timestamp penalty

    diff_seconds = (target_time - ref_dt).total_seconds()
    if diff_seconds <= 0:
        # Forecast is actively valid for target_time or in the future
        return 1.0

    diff_hours = diff_seconds / 3600.0
    if diff_hours >= max_age_hours:
        return 0.0

    return max(0.0, min(1.0, 1.0 - (diff_hours / max_age_hours)))


def calculate_completeness(
    record: Optional[Dict[str, Any]],
    expected_fields: List[str],
) -> tuple[float, List[str]]:
    """
    Calculate the completeness score in [0.0, 1.0] and list missing fields.
    """
    if not record:
        return 0.0, list(expected_fields)

    missing = [f for f in expected_fields if record.get(f) is None]
    present_count = len(expected_fields) - len(missing)
    score = present_count / len(expected_fields) if expected_fields else 1.0
    return max(0.0, min(1.0, score)), missing


def calculate_source_score(
    data_mode: Optional[str],
    source_name: Optional[str] = None,
) -> float:
    """
    Calculate source reliability score in [0.0, 1.0].

    Args:
        data_mode: Data mode string (e.g. CACHED_OFFICIAL, SIMULATED_MVP).
                   Must match keys in SOURCE_SCORE_MAP in config.py.
        source_name: Reserved for future source-specific scoring (e.g. INCOIS vs IMD).
                     Currently unused -- data_mode is sufficient for MVP.
    """
    if not data_mode:
        return 0.3
    return SOURCE_SCORE_MAP.get(data_mode, 0.3)


def calculate_confidence(
    marine_record: Optional[Dict[str, Any]],
    weather_record: Optional[Dict[str, Any]],
    query_time: Optional[datetime] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate deterministic confidence score according to REASONING_SPEC.md.

    Args:
        marine_record: Normalized marine dictionary.
        weather_record: Normalized weather dictionary.
        query_time: Requested target datetime (UTC).
        config: Optional configuration overrides.

    Returns:
        Dictionary containing confidence_score, sub-components, missing fields,
        and simulated data indicator.
    """
    cfg_weights = (config or {}).get("weights", CONFIDENCE_WEIGHTS)
    max_age = (config or {}).get("max_age_hours", CONFIDENCE_MAX_AGE_HOURS)

    # Validate weight configuration: all weights non-negative and sum to ~1.0.
    _w = [
        cfg_weights.get("freshness", 0.50),
        cfg_weights.get("completeness", 0.40),
        cfg_weights.get("source_score", 0.10),
    ]
    if any(w < 0 for w in _w):
        raise ValueError(f"Confidence weights must be non-negative: {_w}")
    _wsum = sum(_w)
    if abs(_wsum - 1.0) > 0.01:
        raise ValueError(
            f"Confidence weights must sum to 1.0 (got {_wsum:.4f}). "
            "Check CONFIDENCE_WEIGHTS in config.py."
        )

    # 1. Freshness (average of marine and weather freshness)
    marine_fresh = calculate_freshness(marine_record, query_time, max_age)
    weather_fresh = calculate_freshness(weather_record, query_time, max_age)
    if marine_record and weather_record:
        avg_freshness = (marine_fresh + weather_fresh) / 2.0
    elif marine_record:
        avg_freshness = marine_fresh * 0.5
    elif weather_record:
        avg_freshness = weather_fresh * 0.5
    else:
        avg_freshness = 0.0

    # 2. Completeness
    marine_comp, marine_missing = calculate_completeness(
        marine_record, EXPECTED_MARINE_FIELDS
    )
    weather_comp, weather_missing = calculate_completeness(
        weather_record, EXPECTED_WEATHER_FIELDS
    )
    all_missing = marine_missing + weather_missing
    avg_completeness = (marine_comp + weather_comp) / 2.0

    # 3. Source Score
    marine_mode = (marine_record or {}).get("data_mode")
    weather_mode = (weather_record or {}).get("data_mode")
    src_marine = calculate_source_score(marine_mode)
    src_weather = calculate_source_score(weather_mode)
    avg_source = (src_marine + src_weather) / 2.0

    is_simulated = (
        marine_mode == "SIMULATED_MVP" or weather_mode == "SIMULATED_MVP"
    )

    # Weighted sum
    w_fresh = cfg_weights.get("freshness", 0.50)
    w_comp = cfg_weights.get("completeness", 0.40)
    w_src = cfg_weights.get("source_score", 0.10)

    raw_score = (
        w_fresh * avg_freshness
        + w_comp * avg_completeness
        + w_src * avg_source
    )
    clamped_score = max(0.0, min(1.0, round(raw_score, 4)))

    return {
        "confidence_score": clamped_score,
        "components": {
            "freshness": round(avg_freshness, 4),
            "completeness": round(avg_completeness, 4),
            "source_score": round(avg_source, 4),
        },
        "missing_fields": all_missing,
        "is_simulated": is_simulated,
    }
