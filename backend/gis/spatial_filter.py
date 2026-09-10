"""
Spatial filtering module for ORCA decision-support system.

Performs deterministic geometry intersection checks between candidate zones
and restricted / geofenced maritime zones using Shapely.

RULE (SAFETY_SPEC.md):
- Any candidate geometry that intersects or touches a restricted zone is HARD BLOCKED.
- Provenance and restriction details are preserved in the blocking reason.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry


def parse_geometry(geom_data: Any) -> Optional[BaseGeometry]:
    """Parse a GeoJSON geometry dict or Shapely geometry into a Shapely BaseGeometry."""
    if isinstance(geom_data, BaseGeometry):
        return geom_data
    if isinstance(geom_data, dict):
        try:
            return shape(geom_data)
        except Exception:
            return None
    return None


def check_candidate_intersection(
    candidate_geom: Any,
    restricted_geom: Any,
) -> bool:
    """
    Return True if the candidate geometry intersects or touches the restricted zone.
    Conservative safety policy: any spatial overlap or boundary touch triggers True.
    """
    c_shape = parse_geometry(candidate_geom)
    r_shape = parse_geometry(restricted_geom)

    if c_shape is None or r_shape is None:
        return False

    return c_shape.intersects(r_shape)


def apply_spatial_filter(
    candidates: List[Dict[str, Any]],
    restricted_zones: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Apply hard spatial filtering against a list of restricted zones.

    Args:
        candidates: List of candidate zone dictionaries containing 'geometry'.
        restricted_zones: List of restricted zone dictionaries containing 'geometry'.

    Returns:
        A tuple of (passed_candidates, blocked_candidates).
        Blocked candidates include 'spatial_blocked': True, 'status': 'BLOCK',
        'blocking_reason', and 'zone_source'.
    """
    passed: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []

    # Pre-parse restricted geometries
    parsed_zones = []
    for rz in restricted_zones:
        r_shape = parse_geometry(rz.get("geometry"))
        if r_shape is not None:
            parsed_zones.append((rz, r_shape))

    for cand in candidates:
        cand_shape = parse_geometry(cand.get("geometry"))
        if cand_shape is None:
            # Malformed geometry fail-safe block
            blocked_cand = dict(cand)
            blocked_cand["spatial_blocked"] = True
            blocked_cand["status"] = "BLOCK"
            blocked_cand["blocking_reason"] = "Invalid or missing candidate geometry"
            blocked_cand["zone_source"] = cand.get("data_mode", "UNKNOWN")
            blocked.append(blocked_cand)
            continue

        is_blocked = False
        blocking_info = None

        for rz_dict, r_shape in parsed_zones:
            if cand_shape.intersects(r_shape):
                is_blocked = True
                blocking_info = {
                    "zone_id": rz_dict.get("id", "UNKNOWN"),
                    "zone_name": rz_dict.get("name", "Restricted Area"),
                    "source": rz_dict.get("source", "UNKNOWN"),
                    "restriction_type": rz_dict.get("restriction_type", "RESTRICTED"),
                }
                break

        if is_blocked and blocking_info:
            blocked_cand = dict(cand)
            blocked_cand["spatial_blocked"] = True
            blocked_cand["status"] = "BLOCK"
            blocked_cand["blocking_reason"] = (
                f"Candidate intersects restricted zone {blocking_info['zone_id']} "
                f"({blocking_info['zone_name']})"
            )
            blocked_cand["zone_source"] = blocking_info["source"]
            blocked.append(blocked_cand)
        else:
            passed_cand = dict(cand)
            passed_cand["spatial_blocked"] = False
            passed.append(passed_cand)

    return passed, blocked


def load_restricted_zones(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Helper to load restricted zones from GeoJSON / JSON fixture file."""
    path = Path(file_path) if file_path else Path(__file__).parents[2] / "data" / "fixtures" / "restricted_zones.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
