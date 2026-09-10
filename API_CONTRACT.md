# API CONTRACT

## Health

`GET /health`

Example:

```json
{
  "status": "ok"
}
```

## Main reasoning endpoint

`POST /api/v1/reason`

### Request

```json
{
  "query": "Find a suitable and safe fishing zone near Kochi tomorrow morning."
}
```

Optional structured fields may be added only after agreement between Planner and Backend owners.

### Response concept

```json
{
  "status": "SAFE",
  "query": "Find a suitable and safe fishing zone near Kochi tomorrow morning.",
  "location": {
    "name": "Kochi",
    "latitude": 9.93,
    "longitude": 76.27
  },
  "requested_time": {
    "valid_from": "2026-09-08T06:00:00Z",
    "valid_to": "2026-09-08T12:00:00Z"
  },
  "recommendation": {
    "zone_id": "KOC-A",
    "suitability_score": 82,
    "risk_score": 24,
    "confidence_score": 0.89,
    "reason": "Candidate passes spatial and safety checks."
  },
  "evidence": [],
  "map": {
    "geojson": {}
  }
}
```

## Status values

- `SAFE`
- `CAUTION`
- `BLOCK`
- `NO_SAFE_RECOMMENDATION`

## Contract rule

The exact implementation schema must be agreed before frontend/backend integration.

Any breaking change requires:
- contract update
- affected-owner review
- tests
- changelog entry
