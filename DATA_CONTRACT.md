# DATA CONTRACT

This document defines the common data language between provider, agent, reasoning and backend teams.

## Common metadata

Every external data record should preserve:

- `source`
- `source_url` when available
- `data_mode`
- `data_type`
- `retrieved_at`
- `issued_at` when available
- `valid_from`
- `valid_to`

### Allowed data modes

- `CACHED_OFFICIAL`
- `SIMULATED_MVP`

### Data types

- `OBSERVATION`
- `FORECAST`
- `WARNING`
- `REFERENCE`

## Marine record example

```json
{
  "latitude": 9.90,
  "longitude": 76.10,
  "issued_at": "2026-09-07T00:00:00Z",
  "valid_from": "2026-09-08T06:00:00Z",
  "valid_to": "2026-09-08T12:00:00Z",
  "wave_height_m": 1.2,
  "wave_period_s": 7.5,
  "wind_speed_ms": 5.8,
  "wind_direction_deg": 240,
  "current_speed_ms": 0.4,
  "current_direction_deg": 180,
  "sst_c": 28.4,
  "chlorophyll_mg_m3": 0.35,
  "source": "INCOIS",
  "data_mode": "CACHED_OFFICIAL",
  "data_type": "FORECAST"
}
```

## Weather record example

```json
{
  "latitude": 9.90,
  "longitude": 76.10,
  "issued_at": "2026-09-07T00:00:00Z",
  "valid_from": "2026-09-08T06:00:00Z",
  "valid_to": "2026-09-08T12:00:00Z",
  "wind_speed_ms": 6.0,
  "wind_direction_deg": 230,
  "rainfall_mm": 1.5,
  "visibility_km": 8,
  "weather_condition": "Partly cloudy",
  "warning_level": "NONE",
  "source": "IMD",
  "data_mode": "CACHED_OFFICIAL",
  "data_type": "FORECAST"
}
```

The values above are schema examples, not claimed live measurements.

## Observation vs forecast

Observation:
- describes observed/current/historical state.

Forecast:
- describes expected future conditions and must have validity information.

Never convert observation data into forecast by changing a label.

## Candidate zone

```json
{
  "id": "KOC-A",
  "name": "Candidate A",
  "latitude": 9.90,
  "longitude": 76.10,
  "geometry": "GeoJSON geometry",
  "region": "Kochi",
  "active": true
}
```

Candidate zones are ORCA-generated/evaluated patches and are not automatically official PFZs.

## Evidence

Evidence should identify:
- source
- parameter
- value
- unit
- validity period
- underlying record/reference

## Missing values

Missing critical safety data must remain missing/null.

Do not replace missing values with zero and then call the result safe.
