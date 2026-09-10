"""
Confidence scoring module for ORCA decision-support system.

Implements the deterministic prototype model from REASONING_SPEC.md:
    Confidence = 0.50 * freshness + 0.40 * completeness + 0.10 * source_score
Clamped to [0.0, 1.0].

NOTE: Confidence indicates confidence in the data-supported recommendation,
NOT the probability of fishing success.
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

    Uses 'valid_to' as the reference validity timestamp. If 'valid_to' is missing,
    falls back to 'retrieved_at' or 'issued_at'.

    If query_time falls within or before valid_to, freshness is 1.0.
    If query_time is past valid_to, freshness degrades linearly based on age.
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
