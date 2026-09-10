# CHANGELOG

## Initial project decisions

### Data
- Cached official data is the primary MVP mode.
- Small synthetic fixtures are allowed only for controlled tests/fallback.
- Synthetic data must be clearly labelled.
- Provider adapters isolate external sources from agents.

### Architecture
- LLM handles planning/orchestration/explanation.
- Deterministic code performs calculations.
- Safety Engine performs final safety validation.
- Replanning occurs after a candidate is blocked.
- PostgreSQL/PostGIS is the shared data/query layer.

### Forecasts
- Future queries require forecast records with validity information.
- Observations must not be relabelled as forecasts.

### GIS
- Leaflet is the frontend map engine.
- Candidate zones are ORCA-evaluated patches, not automatically official PFZs.
- Backend should expose GeoJSON for map overlays.

### Safety
- Restricted zones and authoritative blocking warnings can hard-block.
- Missing/stale critical safety data must fail safe.
- Prototype thresholds are not official standards.

### Scope
- Kochi is the primary demo region.
- Architecture remains location-independent.
- National-scale live processing, species-specific prediction and full route optimization are outside the first MVP.
