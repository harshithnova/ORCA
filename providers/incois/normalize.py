import json
import math
from datetime import timezone
from pathlib import Path

import xarray as xr


def normalize_kochi_sample(
    raw_file: str,
    output_file: str,
    source_url: str,
) -> dict:
    """Extract the nearest valid INCOIS forecast sample for Kochi."""

    dataset = xr.open_dataset(raw_file, decode_times=True, use_cftime=True)

    target_lat = 9.90
    target_lon = 76.10

    lat_index = abs(dataset.IOYAXIS - target_lat).argmin().item()
    lon_index = abs(dataset.IOXAXIS - target_lon).argmin().item()

    latitude = float(dataset.IOYAXIS[lat_index])
    longitude = float(dataset.IOXAXIS[lon_index])

    time_value = dataset.TIME.values[0]

    if hasattr(time_value, "isoformat"):
        valid_from = time_value.isoformat()
    else:
        valid_from = None

    hs = float(
        dataset.HS.isel(
            TIME=0,
            IOYAXIS=lat_index,
            IOXAXIS=lon_index,
        ).item()
    )

    pwp = float(
        dataset.PWP.isel(
            TIME=0,
            IOYAXIS=lat_index,
            IOXAXIS=lon_index,
        ).item()
    )

    u_wind = float(
        dataset.UWND.isel(
            TIME=0,
            IOYAXIS=lat_index,
            IOXAXIS=lon_index,
        ).item()
    )

    v_wind = float(
        dataset.VWND.isel(
            TIME=0,
            IOYAXIS=lat_index,
            IOXAXIS=lon_index,
        ).item()
    )

    wind_speed = math.sqrt((u_wind ** 2) + (v_wind ** 2))

    wind_direction = (
        math.degrees(math.atan2(-u_wind, -v_wind)) + 360
    ) % 360

    record = {
        "latitude": latitude,
        "longitude": longitude,
        "issued_at": None,
        "valid_from": valid_from,
        "valid_to": None,
        "wave_height_m": hs,
        "wave_period_s": pwp,
        "wind_speed_ms": wind_speed,
        "wind_direction_deg": wind_direction,
        "current_speed_ms": None,
        "current_direction_deg": None,
        "sst_c": None,
        "chlorophyll_mg_m3": None,
        "source": "INCOIS",
        "source_url": source_url,
        "data_mode": "CACHED_OFFICIAL",
        "data_type": "FORECAST",
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(record, file, indent=2)

    dataset.close()

    return record