"""
Suitability scoring module for ORCA decision-support system.

Implements the deterministic prototype model from REASONING_SPEC.md:
    Suitability =
        0.35 * PFZ signal
      + 0.20 * chlorophyll
      + 0.15 * SST
      + 0.15 * wave suitability
      + 0.15 * weather suitability
Clamped to integer [0, 100].

NOTE:
- All formulas here are PROTOTYPE HEURISTICS.
- They are NOT official scientific standards or species-specific predictions.
- If PFZ signal is unavailable, it is NOT invented; a conservative fallback (0.0)
  is applied and pfz_fallback_used is flagged True.
"""

from typing import Any, Dict, List, Optional

from backend.config import (
    CHLOROPHYLL_IDEAL_MG_M3,
    CHLOROPHYLL_MIN_MG_M3,
    SST_IDEAL_C,
    SST_TOLERANCE_C,
    SUITABILITY_CLASSES,
    SUITABILITY_WEIGHTS,
    WAVE_HEIGHT_SUITABILITY_IDEAL_M,
    WAVE_HEIGHT_SUITABILITY_WORST_M,
    WIND_SPEED_SUITABILITY_IDEAL_MS,
    WIND_SPEED_SUITABILITY_WORST_MS,
)


def get_suitability_class(score: int) -> str:
    """Classify integer suitability score into qualitative category."""
    for threshold, label in SUITABILITY_CLASSES:
        if score <= threshold:
            return label
    return "EXCELLENT"


def normalize_linear(
    val: Optional[float],
    min_val: float,
    max_val: float,
    invert: bool = False,
) -> float:
    """
    Linear normalization to [0.0, 100.0].
    If invert is True, lower values yield higher scores.
    """
    if val is None:
        return 0.0

    if max_val == min_val:
        return 50.0

    ratio = (val - min_val) / (max_val - min_val)
    ratio = max(0.0, min(1.0, ratio))

    if invert:
        ratio = 1.0 - ratio

    return ratio * 100.0


def normalize_sst(sst_c: Optional[float]) -> float:
    """
    Normalize SST around ideal temperature (e.g. 28.0 C).
    Full score at ideal, decaying to 0 when deviation reaches 2 * tolerance.
    """
    if sst_c is None:
        return 0.0
    deviation = abs(sst_c - SST_IDEAL_C)
    max_dev = SST_TOLERANCE_C * 2.0
    if deviation >= max_dev:
        return 0.0
    return (1.0 - (deviation / max_dev)) * 100.0


def calculate_suitability(
    marine_record: Optional[Dict[str, Any]],
    weather_record: Optional[Dict[str, Any]],
    pfz_signal: Optional[float] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate deterministic suitability score according to REASONING_SPEC.md.

    Args:
        marine_record: Normalized marine dictionary.
        weather_record: Normalized weather dictionary.
        pfz_signal: Official PFZ signal (0-100 or 0-1) if available, or None.
        config: Optional configuration overrides.

    Returns:
        Dictionary with suitability_score (0-100), suitability_class,
        sub-components, missing fields, and metadata.
    """
    weights = (config or {}).get("weights", SUITABILITY_WEIGHTS)
    missing_fields: List[str] = []

    # 1. PFZ Signal component (0-100)
    pfz_fallback_used = False
    if pfz_signal is None:
        pfz_fallback_used = True
        pfz_comp = 0.0
    else:
        # If passed as 0-1 float, scale to 0-100
        val = pfz_signal * 100.0 if pfz_signal <= 1.0 else pfz_signal
        pfz_comp = max(0.0, min(100.0, float(val)))

    # 2. Chlorophyll component
    chl = (marine_record or {}).get("chlorophyll_mg_m3")
    if chl is None:
        missing_fields.append("chlorophyll_mg_m3")
        chl_comp = 0.0
    else:
        chl_comp = normalize_linear(
            chl, CHLOROPHYLL_MIN_MG_M3, CHLOROPHYLL_IDEAL_MG_M3, invert=False
        )

    # 3. SST component
    sst = (marine_record or {}).get("sst_c")
    if sst is None:
        missing_fields.append("sst_c")
        sst_comp = 0.0
    else:
        sst_comp = normalize_sst(sst)

    # 4. Wave suitability component (lower wave is better)
    wave_h = (marine_record or {}).get("wave_height_m")
    if wave_h is None:
        missing_fields.append("wave_height_m")
        wave_comp = 0.0
    else:
        wave_comp = normalize_linear(
            wave_h,
            WAVE_HEIGHT_SUITABILITY_IDEAL_M,
            WAVE_HEIGHT_SUITABILITY_WORST_M,
            invert=True,
        )

    # 5. Weather suitability component (lower wind is better)
    wind_spd = (weather_record or {}).get("wind_speed_ms")
    if wind_spd is None:
        # Fallback to marine wind if available
        wind_spd = (marine_record or {}).get("wind_speed_ms")

    if wind_spd is None:
        missing_fields.append("wind_speed_ms")
        weather_comp = 0.0
    else:
        weather_comp = normalize_linear(
            wind_spd,
            WIND_SPEED_SUITABILITY_IDEAL_MS,
            WIND_SPEED_SUITABILITY_WORST_MS,
            invert=True,
        )

    # Weighted sum
    w_pfz = weights.get("pfz_signal", 0.35)
    w_chl = weights.get("chlorophyll", 0.20)
    w_sst = weights.get("sst", 0.15)
    w_wave = weights.get("wave_suitability", 0.15)
    w_weather = weights.get("weather_suitability", 0.15)

    raw_sum = (
        w_pfz * pfz_comp
        + w_chl * chl_comp
        + w_sst * sst_comp
        + w_wave * wave_comp
        + w_weather * weather_comp
    )

    clamped_score = int(max(0, min(100, round(raw_sum))))
    suit_class = get_suitability_class(clamped_score)

    return {
        "suitability_score": clamped_score,
        "suitability_class": suit_class,
        "components": {
            "pfz_signal": round(pfz_comp, 2),
            "chlorophyll": round(chl_comp, 2),
            "sst": round(sst_comp, 2),
            "wave_suitability": round(wave_comp, 2),
            "weather_suitability": round(weather_comp, 2),
        },
        "pfz_fallback_used": pfz_fallback_used,
        "missing_fields": missing_fields,
        "is_prototype": True,
    }
