"""
Deterministic cached-data loading service for ORCA MVP.

Loads normalized marine and weather data, and restricted zone fixtures.

PRINCIPLES (AGENTS.md, DATA_CONTRACT.md):
- Loads cached official data without inventing marine/weather measurements.
- Preserves missing / null values exactly as stored (never converts None to 0).
- Does not calculate suitability, risk, or safety.
- Raises explicit FileNotFoundError / RuntimeError if requested data is missing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Path relative to repository root
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"


def load_marine_record(
    region: str = "Kochi",
    data_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Load normalized marine data for the specified region (e.g. INCOIS forecast).

    Args:
        region: Geographic region name (default: "Kochi").
        data_dir: Optional custom data directory path for testing or overrides.

    Returns:
        Dict containing normalized marine fields matching DATA_CONTRACT.md.

    Raises:
        FileNotFoundError: If the normalized marine data file does not exist.
    """
    base_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    region_key = region.strip().lower()
    file_path = base_dir / "normalized" / f"{region_key}_incois.json"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Normalized marine dataset not found for region '{region}': {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict for marine record, got {type(data).__name__}")

    return data


def load_weather_record(
    region: str = "Kochi",
    data_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Load normalized weather data for the specified region (e.g. IMD forecast).

    Args:
        region: Geographic region name (default: "Kochi").
        data_dir: Optional custom data directory path for testing or overrides.

    Returns:
        Dict containing normalized weather fields matching DATA_CONTRACT.md.

    Raises:
        FileNotFoundError: If the normalized weather data file does not exist.
    """
    base_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    region_key = region.strip().lower()
    file_path = base_dir / "normalized" / f"{region_key}_imd.json"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Normalized weather dataset not found for region '{region}': {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict for weather record, got {type(data).__name__}")

    return data


def load_restricted_zones(
    file_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    Load restricted zone fixtures for spatial safety filtering.

    Args:
        file_path: Optional custom path to restricted zones JSON file.

    Returns:
        List of restricted zone dictionaries containing id, geometry, and restriction_type.

    Raises:
        FileNotFoundError: If the restricted zones fixture file does not exist.
    """
    path = (
        Path(file_path)
        if file_path
        else DEFAULT_DATA_DIR / "fixtures" / "restricted_zones.json"
    )

    if not path.exists():
        raise FileNotFoundError(f"Restricted zones fixture file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list for restricted zones, got {type(data).__name__}")

    return data


# Re-export freshness helpers for service convenience
from backend.services.freshness import (
    check_forecast_validity,
    check_marine_and_weather_freshness,
    check_record_freshness,
    check_retrieval_freshness,
    is_data_fresh,
    parse_iso_datetime,
)
