"""
Deterministic data freshness and validity helper for ORCA decision-support system.

Distinguishes between:
1. Forecast Validity: whether target query_time falls within [valid_from, valid_to].
2. Retrieval Freshness: whether the record age (retrieved_at / issued_at) is within max_age_hours.

SAFETY RULES (SAFETY_SPEC.md, DATA_CONTRACT.md):
- Timezone-aware UTC datetimes everywhere.
- Missing critical validity/timestamp metadata FAILS SAFE (never assumed fresh).
- Forecast not yet started (future valid_from) or past valid_to is NOT valid.
- Naive timestamps (e.g. from cached INCOIS fixtures) are safely localized to UTC.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from backend.config import CONFIDENCE_MAX_AGE_HOURS


def parse_iso_datetime(dt_val: Any) -> Optional[datetime]:
    """
    Parse ISO 8601 string or datetime into a timezone-aware UTC datetime.
    
    Handles:
    - Already-aware datetimes (normalized to UTC).
    - Naive datetimes (localized to UTC).
    - ISO strings with 'Z'.
    - ISO strings with timezone offset (+00:00, +05:30).
    - Naive ISO strings without timezone (localized to UTC).
    - Returns None if unparseable or None.
    """
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc)
        return dt_val.astimezone(timezone.utc)
    if isinstance(dt_val, str):
        cleaned = dt_val.strip()
        if not cleaned:
            return None
        try:
            # Handle standard ISO and 'Z'
            cleaned = cleaned.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            return None
    return None


def check_forecast_validity(
    record: Optional[Dict[str, Any]],
    target_time: Optional[datetime] = None,
    max_window_hours: float = CONFIDENCE_MAX_AGE_HOURS,
) -> Tuple[bool, str]:
    """
    Verify that the forecast covers the requested target_time.

    Args:
        record: Data record dict with 'valid_from' and optional 'valid_to'.
        target_time: Query target time (UTC). Defaults to now (UTC).
        max_window_hours: Maximum validity window if valid_to is not specified.

    Returns:
        (is_valid, reason) tuple.
    """
    if not record or not isinstance(record, dict):
        return False, "Record is missing or invalid"

    target = parse_iso_datetime(target_time) or datetime.now(timezone.utc)

    valid_from = parse_iso_datetime(record.get("valid_from"))
    valid_to = parse_iso_datetime(record.get("valid_to"))

    if valid_from is None and valid_to is None:
        return False, "Missing critical validity metadata (both valid_from and valid_to are missing)"

    if valid_from is not None and target < valid_from:
        return (
            False,
            f"Forecast not yet valid: target {target.isoformat()} is before valid_from {valid_from.isoformat()}",
        )

    if valid_to is not None:
        if target > valid_to:
            return (
                False,
                f"Forecast expired: target {target.isoformat()} is after valid_to {valid_to.isoformat()}",
            )
    elif valid_from is not None:
        # Fallback: if valid_to is missing, assume validity for max_window_hours from valid_from
        window_end = valid_from + timedelta(hours=max_window_hours)
        if target > window_end:
            return (
                False,
                f"Forecast validity window exceeded: target {target.isoformat()} is after assumed end {window_end.isoformat()}",
            )

    return True, "Forecast is valid for requested time"


def check_retrieval_freshness(
    record: Optional[Dict[str, Any]],
    current_time: Optional[datetime] = None,
    max_age_hours: float = CONFIDENCE_MAX_AGE_HOURS,
) -> Tuple[bool, str]:
    """
    Verify that the record was retrieved or issued recently enough to be trusted.

    Args:
        record: Data record dict with 'retrieved_at', 'issued_at', or 'valid_from'.
        current_time: Reference current time (UTC). Defaults to now (UTC).
        max_age_hours: Maximum age threshold before data is considered stale.

    Returns:
        (is_fresh, reason) tuple.
    """
    if not record or not isinstance(record, dict):
        return False, "Record is missing or invalid"

    now = parse_iso_datetime(current_time) or datetime.now(timezone.utc)

    ref_time = (
        parse_iso_datetime(record.get("retrieved_at"))
        or parse_iso_datetime(record.get("issued_at"))
        or parse_iso_datetime(record.get("valid_from"))
    )

    if ref_time is None:
        return False, "Missing critical timestamp metadata (no retrieved_at, issued_at, or valid_from)"

    diff_seconds = (now - ref_time).total_seconds()
    age_hours = diff_seconds / 3600.0

    if age_hours > max_age_hours:
        return (
            False,
            f"Data is stale: age {age_hours:.1f}h exceeds max allowed {max_age_hours:.1f}h",
        )

    return True, f"Data is fresh ({max(0.0, age_hours):.1f}h old)"


def check_record_freshness(
    record: Optional[Dict[str, Any]],
    target_time: Optional[datetime] = None,
    current_time: Optional[datetime] = None,
    max_age_hours: float = CONFIDENCE_MAX_AGE_HOURS,
) -> Tuple[bool, str]:
    """
    Combined check: must satisfy both forecast validity and retrieval freshness.
    """
    val_ok, val_reason = check_forecast_validity(record, target_time=target_time, max_window_hours=max_age_hours)
    if not val_ok:
        return False, val_reason

    fresh_ok, fresh_reason = check_retrieval_freshness(record, current_time=current_time, max_age_hours=max_age_hours)
    if not fresh_ok:
        return False, fresh_reason

    return True, "Data is fresh and valid"


def is_data_fresh(
    marine_record: Optional[Dict[str, Any]],
    weather_record: Optional[Dict[str, Any]],
    target_time: Optional[datetime] = None,
    current_time: Optional[datetime] = None,
    max_age_hours: float = CONFIDENCE_MAX_AGE_HOURS,
) -> bool:
    """
    Deterministic boolean helper for evaluate_safety(data_freshness_ok=...).

    Returns True ONLY if BOTH marine and weather records exist, are valid
    for target_time, and are fresh relative to current_time.
    Fails safe (returns False) on missing records or metadata.
    """
    if not marine_record or not weather_record:
        return False

    marine_ok, _ = check_record_freshness(marine_record, target_time, current_time, max_age_hours)
    weather_ok, _ = check_record_freshness(weather_record, target_time, current_time, max_age_hours)

    return marine_ok and weather_ok


def check_marine_and_weather_freshness(
    marine_record: Optional[Dict[str, Any]],
    weather_record: Optional[Dict[str, Any]],
    target_time: Optional[datetime] = None,
    current_time: Optional[datetime] = None,
    max_age_hours: float = CONFIDENCE_MAX_AGE_HOURS,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Diagnostic helper returning overall freshness boolean and detailed per-domain breakdown.
    """
    marine_ok, marine_msg = check_record_freshness(marine_record, target_time, current_time, max_age_hours)
    weather_ok, weather_msg = check_record_freshness(weather_record, target_time, current_time, max_age_hours)

    is_overall_ok = marine_ok and weather_ok
    details = {
        "is_fresh": is_overall_ok,
        "marine": {"valid": marine_ok, "detail": marine_msg},
        "weather": {"valid": weather_ok, "detail": weather_msg},
    }
    return is_overall_ok, details
