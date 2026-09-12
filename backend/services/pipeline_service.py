"""
Deterministic end-to-end reasoning and safety pipeline service for ORCA.

Orchestrates:
1. Query location / time window normalization (MVP parser).
2. Data loading (cached official INCOIS + IMD records, restricted zones).
3. Candidate zone generation (nearest-first ranking).
4. Spatial filtering against restricted zones.
5. Candidate evaluation loop (Suitability + Risk + Confidence + Freshness -> Safety Engine).
6. Deterministic replanning on BLOCK; returns immediately on SAFE or CAUTION.
7. If all candidates are exhausted, returns NO_SAFE_RECOMMENDATION.

NON-NEGOTIABLE PRINCIPLES (AGENTS.md, SAFETY_SPEC.md):
- LLM plans (future), code calculates, Safety Engine validates.
- No LLM calls inside this calculation pipeline.
- CAUTION does not trigger replanning; only BLOCK replans.
- Missing critical data or stale data fails safe to BLOCK / NO_SAFE_RECOMMENDATION.
- Never silently fall back to Kochi when an unknown region is requested.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from backend.api.schemas import (
    LocationModel,
    MapModel,
    RecommendationModel,
    ReasonResponse,
    RequestedTimeModel,
)

from backend.gis.candidate_generator import generate_candidates
from backend.gis.spatial_filter import apply_spatial_filter

from backend.reasoning.confidence import calculate_confidence
from backend.reasoning.risk import calculate_risk
from backend.reasoning.suitability import calculate_suitability

from backend.safety.replan import ReplanManager
from backend.safety.safety_engine import evaluate_safety

from backend.services.data_service import (
    load_marine_record,
    load_restricted_zones,
    load_weather_record,
)

from backend.services.freshness import (
    check_marine_and_weather_freshness,
    parse_iso_datetime,
)


# Timezone constant for Kochi / Indian coastal waters (IST = UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30))


# Known regions for MVP parsing
KNOWN_UNSUPPORTED_REGIONS = [
    "mumbai",
    "chennai",
    "goa",
    "vizag",
    "visakhapatnam",
    "mangalore",
    "kolkata",
    "kandla",
    "gujarat",
]


@dataclass
class PipelineRequest:
    """Internal structured request object for the reasoning pipeline."""

    query: str
    location: Optional[Dict[str, Any]] = None
    requested_time: Optional[Dict[str, Any]] = None
    max_radius_km: float = 50.0


def parse_query_mvp(
    query: str,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Minimal deterministic query parser for MVP until P2 Planner is connected.

    Supported time phrases (resolved in IST UTC+05:30):
    - 'tomorrow morning': next calendar day, 06:00-12:00 IST
    - 'tomorrow': next calendar day, 06:00-12:00 IST
    - 'today morning': current calendar day, 06:00-12:00 IST
    - 'today': current calendar day, 06:00-18:00 IST
    - default: next calendar day morning, 06:00-12:00 IST
    """

    q_lower = query.lower()

    # 1. Location detection
    region = None
    lat = None
    lon = None

    if "kochi" in q_lower or "cochin" in q_lower:
        region = "Kochi"
        lat = 9.9312
        lon = 76.2673
    else:
        for r in KNOWN_UNSUPPORTED_REGIONS:
            if r in q_lower:
                region = r.capitalize()
                break

    if region is None:
        # Default to Kochi for MVP if no region is mentioned
        region = "Kochi"
        lat = 9.9312
        lon = 76.2673

    # 2. Time resolution relative to reference date (IST)
    ref_time = now if now is not None else datetime.now(IST)

    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(
            tzinfo=timezone.utc
        ).astimezone(IST)
    else:
        ref_time = ref_time.astimezone(IST)

    current_date = ref_time.date()

    if "tomorrow morning" in q_lower or "tomorrow" in q_lower:
        target_date = current_date + timedelta(days=1)
        start_hour, end_hour = 6, 12

    elif "today morning" in q_lower:
        target_date = current_date
        start_hour, end_hour = 6, 12

    elif "today" in q_lower:
        target_date = current_date
        start_hour, end_hour = 6, 18

    else:
        # Default MVP expectation: next day morning
        target_date = current_date + timedelta(days=1)
        start_hour, end_hour = 6, 12

    start_dt = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        start_hour,
        0,
        0,
        tzinfo=IST,
    )

    end_dt = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        end_hour,
        0,
        0,
        tzinfo=IST,
    )

    time_window = {
        "valid_from": start_dt.isoformat(),
        "valid_to": end_dt.isoformat(),
    }

    return {
        "region": region,
        "latitude": lat,
        "longitude": lon,
        "time_window": time_window,
    }


def run_pipeline(
    request: PipelineRequest,
    marine_record: Optional[Dict[str, Any]] = None,
    weather_record: Optional[Dict[str, Any]] = None,
    restricted_zones: Optional[List[Dict[str, Any]]] = None,
    candidates: Optional[List[Dict[str, Any]]] = None,
    current_time: Optional[datetime] = None,
) -> ReasonResponse:
    """
    Execute the deterministic ORCA reasoning and safety pipeline.
    """

    # 1. Parse or normalize location and time window
    parsed = parse_query_mvp(
        request.query,
        now=current_time,
    )

    req_loc = request.location or {}

    region = (
        req_loc.get("region")
        or req_loc.get("name")
        or parsed["region"]
    )

    lat = (
        req_loc.get("latitude")
        if req_loc.get("latitude") is not None
        else parsed["latitude"]
    )

    lon = (
        req_loc.get("longitude")
        if req_loc.get("longitude") is not None
        else parsed["longitude"]
    )

    time_window = (
        request.requested_time
        or parsed["time_window"]
    )

    # 2. Safety guard: Unsupported region check
    if region.lower() != "kochi":
        return ReasonResponse(
            status="NO_SAFE_RECOMMENDATION",
            query=request.query,
            location=LocationModel(
                name=region,
                latitude=lat,
                longitude=lon,
            ),
            requested_time=RequestedTimeModel(
                valid_from=time_window.get("valid_from"),
                valid_to=time_window.get("valid_to"),
            ),
            recommendation=None,
            evidence=[
                {
                    "check": "regional_data_availability",
                    "region": region,
                    "reason": (
                        f"No normalized marine/weather data or candidate "
                        f"fixtures available for region '{region}'. "
                        "MVP currently supports Kochi cached official data only."
                    ),
                }
            ],
            map=None,
        )

    # 3. Load data
    try:
        if marine_record is None:
            marine_record = load_marine_record(region)

        if weather_record is None:
            weather_record = load_weather_record(region)

        if restricted_zones is None:
            restricted_zones = load_restricted_zones()

    except FileNotFoundError as e:
        return ReasonResponse(
            status="NO_SAFE_RECOMMENDATION",
            query=request.query,
            location=LocationModel(
                name=region,
                latitude=lat,
                longitude=lon,
            ),
            requested_time=RequestedTimeModel(
                valid_from=time_window.get("valid_from"),
                valid_to=time_window.get("valid_to"),
            ),
            recommendation=None,
            evidence=[
                {
                    "check": "data_loading_error",
                    "error": str(e),
                    "reason": "Required official cached dataset was not found.",
                }
            ],
            map=None,
        )

    # 4. Generate candidate zones
    loc_dict = {
        "name": region,
        "region": region,
        "latitude": lat,
        "longitude": lon,
    }

    if candidates is None:
        raw_candidates = generate_candidates(
            location=loc_dict,
            time_window=time_window,
            max_radius_km=request.max_radius_km,
        )
    else:
        raw_candidates = list(candidates)

    if not raw_candidates:
        return ReasonResponse(
            status="NO_SAFE_RECOMMENDATION",
            query=request.query,
            location=LocationModel(
                name=region,
                latitude=lat,
                longitude=lon,
            ),
            requested_time=RequestedTimeModel(
                valid_from=time_window.get("valid_from"),
                valid_to=time_window.get("valid_to"),
            ),
            recommendation=None,
            evidence=[
                {
                    "check": "candidate_generation",
                    "reason": (
                        "No active candidate zones found within "
                        "the specified search radius."
                    ),
                }
            ],
            map=None,
        )

    # 5. Apply spatial filtering
    passed, blocked = apply_spatial_filter(
        raw_candidates,
        restricted_zones,
    )

    blocked_map = {
        c["id"]: c
        for c in blocked
        if "id" in c
    }

    annotated_candidates = []

    for c in raw_candidates:
        cid = c.get("id")

        if cid in blocked_map:
            annotated_candidates.append(
                blocked_map[cid]
            )
        else:
            c_annotated = dict(c)
            c_annotated["spatial_blocked"] = False
            annotated_candidates.append(
                c_annotated
            )

    # 6. Replan Manager initialization
    replan = ReplanManager(annotated_candidates)

    # 7. Evaluate candidates in ranking order
    target_dt = (
        parse_iso_datetime(
            time_window.get("valid_from")
        )
        or datetime.now(timezone.utc)
    )

    ref_now = (
        current_time
        or datetime.now(timezone.utc)
    )

    # Check forecast validity & retrieval freshness
    fresh_ok, fresh_diag = check_marine_and_weather_freshness(
        marine_record,
        weather_record,
        target_time=target_dt,
        current_time=ref_now,
    )

    while not replan.is_exhausted():

        candidate = replan.get_next_candidate()

        if candidate is None:
            break

        cid = candidate.get(
            "id",
            "UNKNOWN",
        )

        # Deterministic calculations
        suit_res = calculate_suitability(
            marine_record,
            weather_record,
        )

        risk_res = calculate_risk(
            marine_record,
            weather_record,
        )

        conf_res = calculate_confidence(
            marine_record,
            weather_record,
            query_time=target_dt,
        )

        # Safety validation
        safety_res = evaluate_safety(
            candidate=candidate,
            risk_result=risk_res,
            confidence_result=conf_res,
            weather_record=weather_record,
            marine_record=marine_record,
            data_freshness_ok=fresh_ok,
        )

        status = safety_res.get(
            "safety_status",
            "BLOCK",
        )

        if status == "BLOCK":

            replan.record_evaluation(
                candidate_id=cid,
                safety_status="BLOCK",
                blocking_reason=safety_res.get(
                    "blocking_reason"
                ),
                blocking_evidence=safety_res.get(
                    "blocking_evidence",
                    [],
                ),
            )

            continue

        # SAFE or CAUTION -> valid recommendation
        replan.record_evaluation(
            candidate_id=cid,
            safety_status=status,
            blocking_reason=None,
            blocking_evidence=safety_res.get(
                "blocking_evidence",
                [],
            ),
        )

        # ---------------------------------------------------------
        # Construct evidence list
        # ---------------------------------------------------------
        evidence_list: List[Dict[str, Any]] = []

        for ev in safety_res.get(
            "blocking_evidence",
            [],
        ):
            evidence_list.append(ev)

        # Marine evidence
        #
        # IMPORTANT:
        # Frontend expects:
        #   parameter
        #   value
        #   unit
        #
        # Previously the API returned wave_height_m directly,
        # which caused blank parameter/value fields in the UI.
        if marine_record:
            evidence_list.append(
                {
                    "source": marine_record.get(
                        "source",
                        "INCOIS",
                    ),
                    "parameter": "wave_height_m",
                    "value": marine_record.get(
                        "wave_height_m"
                    ),
                    "unit": "m",
                    "valid_from": marine_record.get(
                        "valid_from"
                    ),
                    "valid_to": marine_record.get(
                        "valid_to"
                    ),
                    "data_mode": marine_record.get(
                        "data_mode",
                        "CACHED_OFFICIAL",
                    ),
                    "data_type": marine_record.get(
                        "data_type",
                        "FORECAST",
                    ),
                }
            )

        # Weather evidence
        if weather_record:
            evidence_list.append(
                {
                    "source": weather_record.get(
                        "source",
                        "IMD",
                    ),
                    "parameter": "warning_level",
                    "value": weather_record.get(
                        "warning_level"
                    ),
                    "unit": None,
                    "valid_from": weather_record.get(
                        "valid_from"
                    ),
                    "valid_to": weather_record.get(
                        "valid_to"
                    ),
                    "data_mode": weather_record.get(
                        "data_mode",
                        "CACHED_OFFICIAL",
                    ),
                    "data_type": weather_record.get(
                        "data_type",
                        "FORECAST",
                    ),
                }
            )

        if not fresh_ok:
            evidence_list.append(
                {
                    "check": "freshness_diagnostic",
                    "detail": fresh_diag,
                }
            )

        # Reason text
        if status == "SAFE":

            reason_text = (
                "Candidate passes all spatial, weather, "
                "and safety constraint checks."
            )

        else:

            caution_reasons = [
                ev.get("reason")
                for ev in safety_res.get(
                    "blocking_evidence",
                    [],
                )
                if ev.get("reason")
            ]

            if caution_reasons:
                reason_text = (
                    "Candidate recommended with CAUTION: "
                    + "; ".join(caution_reasons)
                )
            else:
                reason_text = (
                    "Candidate recommended with CAUTION "
                    "based on current environmental advisories."
                )

        # Map GeoJSON
        map_model = None

        geom = candidate.get("geometry")

        if geom:
            map_model = MapModel(
                geojson={
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "zone_id": cid,
                        "name": candidate.get("name"),
                        "status": status,
                        "suitability_score": suit_res[
                            "suitability_score"
                        ],
                        "risk_score": risk_res[
                            "risk_score"
                        ],
                        "confidence_score": conf_res[
                            "confidence_score"
                        ],
                    },
                }
            )

        return ReasonResponse(
            status=status,
            query=request.query,
            location=LocationModel(
                name=region,
                latitude=lat,
                longitude=lon,
            ),
            requested_time=RequestedTimeModel(
                valid_from=time_window.get("valid_from"),
                valid_to=time_window.get("valid_to"),
            ),
            recommendation=RecommendationModel(
                zone_id=cid,
                suitability_score=suit_res[
                    "suitability_score"
                ],
                risk_score=risk_res[
                    "risk_score"
                ],
                confidence_score=conf_res[
                    "confidence_score"
                ],
                reason=reason_text,
            ),
            evidence=evidence_list,
            map=map_model,
        )

    # 8. All candidates blocked / exhausted
    audit_evidence: List[Dict[str, Any]] = []

    for entry in replan.audit_log:
        audit_evidence.append(
            {
                "source": "ORCA Safety Engine",
                "parameter": "safety_status",
                "value": entry[
                    "safety_status"
                ],
                "unit": None,
                "candidate_id": entry[
                    "candidate_id"
                ],
                "status": entry[
                    "safety_status"
                ],
                "reason": entry[
                    "blocking_reason"
                ],
                "evidence": entry[
                    "blocking_evidence"
                ],
            }
        )

    # Add marine evidence in the same schema expected by the frontend.
    if marine_record:
        audit_evidence.append(
            {
                "source": marine_record.get(
                    "source",
                    "INCOIS",
                ),
                "parameter": "wave_height_m",
                "value": marine_record.get(
                    "wave_height_m"
                ),
                "unit": "m",
                "valid_from": marine_record.get(
                    "valid_from"
                ),
                "valid_to": marine_record.get(
                    "valid_to"
                ),
                "data_mode": marine_record.get(
                    "data_mode",
                    "CACHED_OFFICIAL",
                ),
                "data_type": marine_record.get(
                    "data_type",
                    "FORECAST",
                ),
            }
        )

    # Add weather evidence in the same schema expected by the frontend.
    if weather_record:
        audit_evidence.append(
            {
                "source": weather_record.get(
                    "source",
                    "IMD",
                ),
                "parameter": "warning_level",
                "value": weather_record.get(
                    "warning_level"
                ),
                "unit": None,
                "valid_from": weather_record.get(
                    "valid_from"
                ),
                "valid_to": weather_record.get(
                    "valid_to"
                ),
                "data_mode": weather_record.get(
                    "data_mode",
                    "CACHED_OFFICIAL",
                ),
                "data_type": weather_record.get(
                    "data_type",
                    "FORECAST",
                ),
            }
        )

    if not fresh_ok:
        audit_evidence.append(
            {
                "source": "ORCA Freshness Check",
                "parameter": "data_freshness",
                "value": "STALE_OR_OUTSIDE_VALIDITY",
                "unit": None,
                "check": "data_freshness_failure",
                "detail": fresh_diag,
            }
        )

    return ReasonResponse(
        status="NO_SAFE_RECOMMENDATION",
        query=request.query,
        location=LocationModel(
            name=region,
            latitude=lat,
            longitude=lon,
        ),
        requested_time=RequestedTimeModel(
            valid_from=time_window.get("valid_from"),
            valid_to=time_window.get("valid_to"),
        ),
        recommendation=None,
        evidence=audit_evidence,
        map=None,
    )