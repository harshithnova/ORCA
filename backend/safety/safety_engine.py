"""
Safety Engine module for ORCA decision-support system.

Implements deterministic safety gates according to SAFETY_SPEC.md:
- Restricted / geofenced maritime zones
- Authoritative official warnings
- Missing critical data (fail-safe)
- Stale critical data (fail-safe)
- Configured risk score thresholds

NON-NEGOTIABLE RULE:
- The LLM cannot override the Safety Engine.
- Missing critical data never defaults to safe.
"""

from typing import Any, Dict, List, Optional, Tuple

from backend.config import (
    BLOCK_WARNING_LEVELS,
    CAUTION_RISK_SCORE_THRESHOLD,
    CAUTION_WARNING_LEVELS,
    CRITICAL_SAFETY_FIELDS,
    MAX_RISK_SCORE_THRESHOLD,
)


def evaluate_safety(
    candidate: Dict[str, Any],
    risk_result: Dict[str, Any],
    confidence_result: Optional[Dict[str, Any]] = None,
    weather_record: Optional[Dict[str, Any]] = None,
    marine_record: Optional[Dict[str, Any]] = None,
    data_freshness_ok: bool = True,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluate deterministic safety rules for an individual candidate zone.

    Args:
        candidate: Candidate dictionary (may contain 'spatial_blocked' flag).
        risk_result: Output from backend.reasoning.risk.calculate_risk.
        confidence_result: Output from backend.reasoning.confidence.calculate_confidence.
        weather_record: Normalized weather dictionary.
        marine_record: Normalized marine dictionary.
        data_freshness_ok: Boolean indicating if data is within fresh window.
        config: Optional configuration overrides.

    Returns:
        Dictionary containing safety_status ('SAFE', 'CAUTION', 'BLOCK'),
        blocking_reason (if blocked), blocking_evidence list, and checks_performed log.
    """
    cfg = config or {}
    max_risk = cfg.get("max_risk_score", MAX_RISK_SCORE_THRESHOLD)
    caution_risk = cfg.get("caution_risk_score", CAUTION_RISK_SCORE_THRESHOLD)
    block_warnings = cfg.get("block_warnings", BLOCK_WARNING_LEVELS)
    caution_warnings = cfg.get("caution_warnings", CAUTION_WARNING_LEVELS)

    checks_performed: Dict[str, str] = {}
    blocking_evidence: List[Dict[str, Any]] = []

    # 1. Spatial Restriction Check (Hard Override)
    if candidate.get("spatial_blocked", False):
        reason = candidate.get(
            "blocking_reason", "Candidate lies within restricted / geofenced area."
        )
        checks_performed["restricted_zone_check"] = "BLOCK"
        blocking_evidence.append({
            "check": "restricted_zone_check",
            "reason": reason,
            "source": candidate.get("zone_source", "GEOSPATIAL_RESTRICTION"),
        })
        return {
            "safety_status": "BLOCK",
            "blocking_reason": reason,
            "blocking_evidence": blocking_evidence,
            "checks_performed": checks_performed,
        }
    checks_performed["restricted_zone_check"] = "PASS"

    # 2. Official Blocking Warning Check (Hard Override)
    warning_level = (weather_record or {}).get("warning_level")
    if warning_level in block_warnings:
        reason = (
            f"Official blocking warning issued by {weather_record.get('source', 'IMD')}: "
            f"warning_level = {warning_level}."
        )
        checks_performed["official_warning_check"] = "BLOCK"
        blocking_evidence.append({
            "check": "official_warning_check",
            "parameter": "warning_level",
            "value": warning_level,
            "source": weather_record.get("source", "IMD"),
            "data_mode": weather_record.get("data_mode", "CACHED_OFFICIAL"),
        })
        return {
            "safety_status": "BLOCK",
            "blocking_reason": reason,
            "blocking_evidence": blocking_evidence,
            "checks_performed": checks_performed,
        }
    checks_performed["official_warning_check"] = "PASS"

    # 3. Missing Critical Safety Data Check (Fail-Safe)
    missing_critical = risk_result.get("missing_critical_fields", [])
    if missing_critical:
        reason = (
            f"Critical safety data missing: {', '.join(missing_critical)}. "
            "System fails safe and refuses to certify safety."
        )
        checks_performed["missing_critical_data_check"] = "BLOCK"
        blocking_evidence.append({
            "check": "missing_critical_data_check",
            "missing_fields": missing_critical,
            "reason": reason,
        })
        return {
            "safety_status": "BLOCK",
            "blocking_reason": reason,
            "blocking_evidence": blocking_evidence,
            "checks_performed": checks_performed,
        }
    checks_performed["missing_critical_data_check"] = "PASS"

    # 4. Stale Critical Data Check (Fail-Safe)
    if not data_freshness_ok:
        reason = (
            "Critical safety records outside configured freshness window. "
            "System fails safe on stale data."
        )
        checks_performed["stale_data_check"] = "BLOCK"
        blocking_evidence.append({
            "check": "stale_data_check",
            "reason": reason,
        })
        return {
            "safety_status": "BLOCK",
            "blocking_reason": reason,
            "blocking_evidence": blocking_evidence,
            "checks_performed": checks_performed,
        }
    checks_performed["stale_data_check"] = "PASS"

    # 5. Severe Hazard / Severe Risk Class Check
    risk_class = risk_result.get("risk_class", "LOW")
    if risk_class == "SEVERE":
        reason = "Severe marine/weather hazard conditions detected."
        checks_performed["severe_hazard_check"] = "BLOCK"
        blocking_evidence.append({
            "check": "severe_hazard_check",
            "risk_score": risk_result.get("risk_score"),
            "risk_class": "SEVERE",
            "reason": reason,
        })
        return {
            "safety_status": "BLOCK",
            "blocking_reason": reason,
            "blocking_evidence": blocking_evidence,
            "checks_performed": checks_performed,
        }
    checks_performed["severe_hazard_check"] = "PASS"

    # 6. Configured Risk Score Threshold Check
    risk_score = risk_result.get("risk_score", 0)
    if risk_score > max_risk:
        reason = f"Calculated risk score ({risk_score}) exceeds configured limit ({max_risk})."
        checks_performed["risk_threshold_check"] = "BLOCK"
        blocking_evidence.append({
            "check": "risk_threshold_check",
            "risk_score": risk_score,
            "max_risk_threshold": max_risk,
            "reason": reason,
        })
        return {
            "safety_status": "BLOCK",
            "blocking_reason": reason,
            "blocking_evidence": blocking_evidence,
            "checks_performed": checks_performed,
        }
    checks_performed["risk_threshold_check"] = "PASS"

    # 7. Caution Conditions & Unknown Warning Fail-Safe
    caution_evidence: List[Dict[str, Any]] = []

    # Check for unrecognized / unmapped warning level
    is_unknown_warning = (
        bool(warning_level)
        and str(warning_level).strip().upper() not in ("", "NONE")
        and warning_level not in block_warnings
        and warning_level not in caution_warnings
    )
    is_caution_warning = warning_level in caution_warnings
    is_caution_risk = risk_score > caution_risk

    if is_unknown_warning:
        checks_performed["unknown_warning_check"] = "CAUTION"
        caution_evidence.append({
            "check": "unknown_warning_check",
            "parameter": "warning_level",
            "value": warning_level,
            "source": (weather_record or {}).get("source", "IMD"),
            "data_mode": (weather_record or {}).get("data_mode", "CACHED_OFFICIAL"),
            "reason": (
                f"Unrecognized official warning level '{warning_level}'. "
                "Fails safe to CAUTION to prevent unverified safe recommendation."
            ),
        })
    elif is_caution_warning:
        checks_performed["caution_warning_check"] = "CAUTION"
        caution_evidence.append({
            "check": "caution_warning_check",
            "parameter": "warning_level",
            "value": warning_level,
            "source": (weather_record or {}).get("source", "IMD"),
            "data_mode": (weather_record or {}).get("data_mode", "CACHED_OFFICIAL"),
            "reason": f"Official caution warning: warning_level = {warning_level}.",
        })

    if is_caution_risk:
        checks_performed["risk_caution_check"] = "CAUTION"
        caution_evidence.append({
            "check": "risk_caution_check",
            "parameter": "risk_score",
            "value": risk_score,
            "reason": f"Risk score ({risk_score}) is in caution range.",
        })

    is_caution = is_caution_risk or is_caution_warning or is_unknown_warning
    if is_caution:
        checks_performed["overall_safety"] = "CAUTION"
        return {
            "safety_status": "CAUTION",
            "blocking_reason": None,
            "blocking_evidence": caution_evidence,
            "checks_performed": checks_performed,
        }

    # 8. Clean Pass -> SAFE
    checks_performed["overall_safety"] = "SAFE"
    return {
        "safety_status": "SAFE",
        "blocking_reason": None,
        "blocking_evidence": [],
        "checks_performed": checks_performed,
    }
