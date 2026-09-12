"""
Configuration parameters for ORCA Person 4 modules (GIS, Reasoning, Safety).

IMPORTANT:
- All values here are PROTOTYPE HEURISTICS for MVP.
- They are NOT official scientific or safety standards.
- No magic numbers should be embedded in individual reasoning or safety modules.
"""

from typing import Dict, List

# --- SUITABILITY WEIGHTS & THRESHOLDS (REASONING_SPEC.md) ---
# Suitability = 0.35 * PFZ + 0.20 * Chlorophyll + 0.15 * SST + 0.15 * Wave + 0.15 * Weather
SUITABILITY_WEIGHTS: Dict[str, float] = {
    "pfz_signal": 0.35,
    "chlorophyll": 0.20,
    "sst": 0.15,
    "wave_suitability": 0.15,
    "weather_suitability": 0.15,
}

# Suitability Classes
SUITABILITY_CLASSES = [
    (20, "POOR"),
    (40, "FAIR"),
    (60, "GOOD"),
    (80, "VERY GOOD"),
    (100, "EXCELLENT"),
]

# Normalization ranges for suitability components (Prototype Heuristics)
# Marine / Weather ideal vs worst parameters
WAVE_HEIGHT_SUITABILITY_IDEAL_M: float = 0.8     # calm, safe waters
WAVE_HEIGHT_SUITABILITY_WORST_M: float = 3.0     # rough seas difficult for fishing

WIND_SPEED_SUITABILITY_IDEAL_MS: float = 4.0     # gentle breeze
WIND_SPEED_SUITABILITY_WORST_MS: float = 14.0    # high wind

SST_IDEAL_C: float = 28.0                        # typical tropical optimal SST for Kochi
SST_TOLERANCE_C: float = 2.5                     # within 28 +/- 2.5 C considered favorable

CHLOROPHYLL_IDEAL_MG_M3: float = 0.6             # good phytoplankton indicator
CHLOROPHYLL_MIN_MG_M3: float = 0.05              # oligotrophic / barren


# --- RISK WEIGHTS & THRESHOLDS (REASONING_SPEC.md) ---
# Risk = 0.30 * Wave + 0.25 * Wind + 0.20 * Lightning + 0.15 * Rain + 0.10 * Hazard
RISK_WEIGHTS: Dict[str, float] = {
    "wave_risk": 0.30,
    "wind_risk": 0.25,
    "lightning_risk": 0.20,
    "rain_risk": 0.15,
    "hazard_risk": 0.10,
}

RISK_CLASSES = [
    (20, "LOW"),
    (40, "MODERATE"),
    (60, "ELEVATED"),
    (80, "HIGH"),
    (100, "SEVERE"),
]

# Risk parameter normalization (Prototype Heuristics)
WAVE_HEIGHT_SAFE_M: float = 1.0
WAVE_HEIGHT_DANGEROUS_M: float = 3.5

WIND_SPEED_SAFE_MS: float = 5.0
WIND_SPEED_DANGEROUS_MS: float = 17.0

RAIN_SAFE_MM: float = 2.0
RAIN_DANGEROUS_MM: float = 40.0


# --- CONFIDENCE WEIGHTS & PARAMETERS (REASONING_SPEC.md) ---
# Confidence = 0.50 * Freshness + 0.40 * Completeness + 0.10 * SourceScore
CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "freshness": 0.50,
    "completeness": 0.40,
    "source_score": 0.10,
}

CONFIDENCE_MAX_AGE_HOURS: float = 24.0

SOURCE_SCORE_MAP: Dict[str, float] = {
    "CACHED_OFFICIAL": 1.0,
    "SIMULATED_MVP": 0.5,
}

EXPECTED_MARINE_FIELDS: List[str] = [
    "wave_height_m",
    "wave_period_s",
    "wind_speed_ms",
    "wind_direction_deg",
    "current_speed_ms",
    "sst_c",
    "chlorophyll_mg_m3",
]

EXPECTED_WEATHER_FIELDS: List[str] = [
    "wind_speed_ms",
    "wind_direction_deg",
    "rainfall_mm",
    "visibility_km",
    "warning_level",
]


# --- SAFETY THRESHOLDS (SAFETY_SPEC.md) ---
MAX_RISK_SCORE_THRESHOLD: int = 60      # Above this score -> BLOCK
CAUTION_RISK_SCORE_THRESHOLD: int = 40  # Above this score -> CAUTION

# Critical fields that MUST NOT be missing/null for safety
CRITICAL_SAFETY_FIELDS: List[str] = [
    "wave_height_m",
    "wind_speed_ms",
    "warning_level",
]

# Warning levels (Prototype stub until Person 3 provides complete IMD enum)
BLOCK_WARNING_LEVELS: List[str] = [
    "CYCLONE_WARNING",
    "GALE_WARNING",
    "STORM_WARNING",
    "RED_ALERT",
]

CAUTION_WARNING_LEVELS: List[str] = [
    "ADVISORY",
    "ORANGE_ALERT",
    "YELLOW_ALERT",
]


# --- GIS & REGIONAL SETTINGS ---
DEFAULT_SEARCH_RADIUS_KM: float = 50.0
KOCHI_CENTER_LAT: float = 9.9312
KOCHI_CENTER_LON: float = 76.2673
