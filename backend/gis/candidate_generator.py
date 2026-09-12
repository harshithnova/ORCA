"""
Candidate zone generator for ORCA decision-support system.

Generates / retrieves candidate sea-area patches near a requested location
and time window. For MVP, loads validated candidate fixtures (labelled SIMULATED_MVP)
and filters/ranks them by Haversine distance from the query coordinates.

IMPORTANT:
- Candidate zones are ORCA-evaluated sea patches, NOT automatically official INCOIS PFZs.
- Architecture is location-independent (region-driven).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import DEFAULT_SEARCH_RADIUS_KM, KOCHI_CENTER_LAT, KOCHI_CENTER_LON
from backend.gis.distance import filter_by_radius


def load_candidate_fixtures(region: str) -> List[Dict[str, Any]]:
    """
    Load candidate zone fixtures for the specified region.

    Returns an empty list if no fixture file exists for the requested region.
    Does NOT fall back to another region's fixtures — a Mumbai request must
    never receive Kochi candidates.
    """
    fixture_dir = Path(__file__).parents[2] / "data" / "fixtures"
    fixture_path = fixture_dir / f"{region.lower()}_candidates.json"

    if not fixture_path.exists():
        return []

    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_candidates(
    location: Optional[Dict[str, Any]] = None,
    time_window: Optional[Dict[str, Any]] = None,
    max_radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate candidate zones for the given query location and time window.

    Args:
        location: Dict with keys 'latitude', 'longitude', and optional 'name'/'region'.
                  'region' is used first, then 'name', to identify the fixture file.
                  If neither yields a known region fixture, returns [].
        time_window: Dict with 'valid_from' and 'valid_to' ISO datetime strings.
        max_radius_km: Maximum search radius in kilometers.
        config: Optional configuration overrides.

    Returns:
        List of candidate zone dictionaries sorted by distance_km ascending.
        Empty list if no fixture exists for the resolved region.
    """
    loc = location or {}
    center_lat = float(loc.get("latitude", KOCHI_CENTER_LAT))
    center_lon = float(loc.get("longitude", KOCHI_CENTER_LON))
    region = loc.get("region") or loc.get("name") or "Kochi"

    # 1. Load available candidates for the region
    all_candidates = load_candidate_fixtures(region=region)

    # 2. Filter active candidates
    active_candidates = [c for c in all_candidates if c.get("active", True)]

    # 3. Filter candidates within max search radius using Haversine distance
    nearby_candidates = filter_by_radius(
        center_lat=center_lat,
        center_lon=center_lon,
        items=active_candidates,
        max_km=max_radius_km,
        lat_key="latitude",
        lon_key="longitude",
    )

    # 4. Sort by proximity (closest first)
    nearby_candidates.sort(key=lambda x: x.get("distance_km", float("inf")))

    # 5. Attach requested time window if provided (copy dict to avoid mutating fixtures)
    if time_window:
        nearby_candidates = [
            {**cand, "time_window": dict(time_window)}
            for cand in nearby_candidates
        ]

    return nearby_candidates
