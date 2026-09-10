"""
GIS distance calculation module using the Haversine formula.

Calculates great-circle distance between two points on the Earth's surface
specified in decimal degrees (latitude and longitude).
"""

import math
from typing import Any, Dict, List

# Earth's mean radius in kilometers
EARTH_RADIUS_KM: float = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in kilometers between two points
    on Earth using the Haversine formula.

    Args:
        lat1: Latitude of first point in decimal degrees.
        lon1: Longitude of first point in decimal degrees.
        lat2: Latitude of second point in decimal degrees.
        lon2: Longitude of second point in decimal degrees.

    Returns:
        Distance in kilometers (clamped to >= 0.0).
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Numerical tolerance clamp for floating point inaccuracies
    c = 2.0 * math.atan2(math.sqrt(min(1.0, a)), math.sqrt(max(0.0, 1.0 - a)))

    return max(0.0, EARTH_RADIUS_KM * c)


def filter_by_radius(
    center_lat: float,
    center_lon: float,
    items: List[Dict[str, Any]],
    max_km: float,
    lat_key: str = "latitude",
    lon_key: str = "longitude",
) -> List[Dict[str, Any]]:
    """
    Filter a list of spatial dictionary items to only those within max_km
    of the given center coordinates. Adds 'distance_km' to each matching item.

    Args:
        center_lat: Center latitude.
        center_lon: Center longitude.
        items: List of dictionary records containing lat_key and lon_key.
        max_km: Maximum search radius in kilometers.
        lat_key: Dictionary key for latitude.
        lon_key: Dictionary key for longitude.

    Returns:
        List of matching items within radius, each augmented with 'distance_km'.
    """
    filtered = []
    for item in items:
        lat = item.get(lat_key)
        lon = item.get(lon_key)
        if lat is None or lon is None:
            continue

        dist = haversine_km(center_lat, center_lon, float(lat), float(lon))
        if dist <= max_km:
            item_copy = dict(item)
            item_copy["distance_km"] = round(dist, 2)
            filtered.append(item_copy)

    return filtered
