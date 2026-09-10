"""
Risk scoring module for ORCA decision-support system.

Implements the deterministic prototype model from REASONING_SPEC.md:
    Risk =
        0.30 * wave risk
      + 0.25 * wind risk
      + 0.20 * lightning risk
      + 0.15 * rain risk
      + 0.10 * hazard risk
Clamped to integer [0, 100].

NOTE:
- All formulas here are PROTOTYPE HEURISTICS for MVP.
- They are NOT official safety standards or official hazard advisories.
- Lightning risk is stubbed to 0.0 with 'lightning_data_missing=True' until
  Person 3 confirms the exact IMD lightning/thunderstorm parameter.
- Hazard risk is derived from the warning_level field.
"""

from typing import Any, Dict, List, Optional

from backend.config import (
    BLOCK_WARNING_LEVELS,
    CAUTION_WARNING_LEVELS,
    RAIN_DANGEROUS_MM,
    RAIN_SAFE_MM,
    RISK_CLASSES,
    RISK_WEIGHTS,
    WAVE_HEIGHT_DANGEROUS_M,
    WAVE_HEIGHT_SAFE_M,
    WIND_SPEED_DANGEROUS_MS,
    WIND_SPEED_SAFE_MS,
)


def get_risk_class(score: int) -> str:
    """Classify integer risk score into qualitative risk category."""
    for threshold, label in RISK_CLASSES:
        if score <= threshold:
            return label
    return "SEVERE"


def normalize_risk_linear(
    val: Optional[float],
    safe_threshold: float,
    dangerous_threshold: float,
) -> float:
    """
    Normalize a physical value to [0.0, 100.0] risk.
    Values <= safe_threshold give 0.0 risk.
    Values >= dangerous_threshold give 100.0 risk.
    """
    if val is None:
        return 0.0
    if dangerous_threshold == safe_threshold:
        return 100.0 if val >= safe_threshold else 0.0

    ratio = (val - safe_threshold) / (dangerous_threshold - safe_threshold)
    ratio = max(0.0, min(1.0, ratio))
    return ratio * 100.0


def calculate_hazard_risk(warning_level: Optional[str]) -> float:
    """
    Derive hazard risk sub-score from warning_level.
    """
    if not warning_level or warning_level == "NONE":
        return 0.0
    if warning_level in BLOCK_WARNING_LEVELS:
        return 100.0
    if warning_level in CAUTION_WARNING_LEVELS:
        return 50.0
    return 25.0  # Generic unclassified warning


def calculate_risk(
    marine_record: Optional[Dict[str, Any]],
    weather_record: Optional[Dict[str, Any]],
    hazard_data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate deterministic risk score according to REASONING_SPEC.md.

    Args:
        marine_record: Normalized marine dictionary.
        weather_record: Normalized weather dictionary.
        hazard_data: Optional explicit hazard layer data.
        config: Optional configuration overrides.

    Returns:
        Dictionary containing risk_score (0-100), risk_class,
        sub-components, missing_fields, missing_critical_fields,
        and lightning_data_missing flag.
    """
    weights = (config or {}).get("weights", RISK_WEIGHTS)
    missing_fields: List[str] = []
    missing_critical_fields: List[str] = []

    # 1. Wave risk component (0.30)
    wave_h = (marine_record or {}).get("wave_height_m")
    if wave_h is None:
        missing_fields.append("wave_height_m")
        missing_critical_fields.append("wave_height_m")
        wave_risk = 0.0
    else:
        wave_risk = normalize_risk_linear(
            wave_h, WAVE_HEIGHT_SAFE_M, WAVE_HEIGHT_DANGEROUS_M
        )

    # 2. Wind risk component (0.25)
    wind_spd = (weather_record or {}).get("wind_speed_ms")
    if wind_spd is None:
        wind_spd = (marine_record or {}).get("wind_speed_ms")

    if wind_spd is None:
        missing_fields.append("wind_speed_ms")
        missing_critical_fields.append("wind_speed_ms")
        wind_risk = 0.0
    else:
        wind_risk = normalize_risk_linear(
            wind_spd, WIND_SPEED_SAFE_MS, WIND_SPEED_DANGEROUS_MS
        )

    # 3. Lightning risk component (0.20) [STUB for Q1]
    # Documented fallback: until IMD lightning field is confirmed by Person 3,
    # set component to 0.0 and flag lightning_data_missing=True.
    lightning_risk = 0.0
    lightning_data_missing = True

    # 4. Rain risk component (0.15)
    rain_mm = (weather_record or {}).get("rainfall_mm")
    if rain_mm is None:
        missing_fields.append("rainfall_mm")
        rain_risk = 0.0
    else:
        rain_risk = normalize_risk_linear(
            rain_mm, RAIN_SAFE_MM, RAIN_DANGEROUS_MM
        )

    # 5. Hazard risk component (0.10) [Q9]
    warning_lvl = (weather_record or {}).get("warning_level")
    if warning_lvl is None:
        missing_fields.append("warning_level")
        missing_critical_fields.append("warning_level")
        hazard_risk = 0.0
    else:
        hazard_risk = calculate_hazard_risk(warning_lvl)

    # Weighted sum
    w_wave = weights.get("wave_risk", 0.30)
    w_wind = weights.get("wind_risk", 0.25)
    w_lightning = weights.get("lightning_risk", 0.20)
    w_rain = weights.get("rain_risk", 0.15)
    w_hazard = weights.get("hazard_risk", 0.10)

    raw_sum = (
        w_wave * wave_risk
        + w_wind * wind_risk
        + w_lightning * lightning_risk
        + w_rain * rain_risk
        + w_hazard * hazard_risk
    )

    clamped_score = int(max(0, min(100, round(raw_sum))))
    r_class = get_risk_class(clamped_score)

    return {
        "risk_score": clamped_score,
        "risk_class": r_class,
        "components": {
            "wave_risk": round(wave_risk, 2),
            "wind_risk": round(wind_risk, 2),
            "lightning_risk": round(lightning_risk, 2),
            "rain_risk": round(rain_risk, 2),
            "hazard_risk": round(hazard_risk, 2),
        },
        "missing_fields": missing_fields,
        "missing_critical_fields": missing_critical_fields,
        "lightning_data_missing": lightning_data_missing,
        "is_prototype": True,
    }
