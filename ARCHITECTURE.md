# ARCHITECTURE

## End-to-end flow

```text
User Query
    ↓
Planner Agent
    ↓
┌───────────────┬────────────────┬───────────────┐
│ Marine Agent  │ Weather Agent  │ Geo Agent     │
└───────────────┴────────────────┴───────────────┘
    ↓
Validation + Normalization
    ↓
Deterministic Reasoning
    ├── Suitability
    ├── Risk
    ├── Confidence
    └── Spatial checks
    ↓
Safety Engine
    ↓
 ┌───────────────┐
 │ SAFE/CAUTION  │
 │      or       │
 │ BLOCK         │
 └───────────────┘
    ↓
If BLOCK → Replan → Next candidate → Recalculate → Safety again
    ↓
Evidence + Explanation
    ↓
FastAPI
    ↓
React + Leaflet
```

## Data provider architecture

```text
INCOIS / IMD / Geo Sources
          ↓
Provider Adapters
          ↓
Common ORCA Schema
          ↓
Cache + PostgreSQL/PostGIS
          ↓
Agents
```

A synthetic provider may implement the same interface for controlled tests.

## Separation of concerns

### Planner
Understands intent, location and time.

### Agents
Retrieve structured data.

### Deterministic engines
Calculate values.

### Safety Engine
Applies hard rules.

### LLM
Explains results based only on supplied evidence.

## Map

Leaflet is the map engine.

The base map can use an appropriate OpenStreetMap-derived tile provider.

ORCA overlays are application data:
- candidate zones
- recommended zone
- risk zones
- restricted/hazard zones
- optional marine/weather layers

The backend should return GeoJSON where spatial visualization is required.

## Failure handling

- provider unavailable → explicit source failure
- missing critical data → fail safe
- stale critical data → fail safe
- blocked candidate → replan
- all candidates blocked → `NO_SAFE_RECOMMENDATION`
