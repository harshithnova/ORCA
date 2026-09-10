# MVP SCOPE

## Must build

### Query understanding
- natural-language query
- location
- future time window
- intent

### Agents
- Planner
- Marine
- Weather
- Geo

### Deterministic engines
- spatial checks
- suitability
- risk
- confidence

### Safety
- hard constraints
- official warning handling where integrated
- fail-safe missing/stale critical data
- replan
- final safety gate

### Data
- cached official data
- common normalized schema
- PostgreSQL/PostGIS
- provenance

### UI
- query input
- map
- candidate zones
- recommended zone
- risk/suitability/confidence
- evidence

## Should not build for first MVP

- national-scale live satellite processing
- raw satellite image processing
- species-specific ML prediction
- full route optimization
- production safety certification
- unnecessary ML models
- huge agent count
- unsupported live-provider claims
- broad language support unless separately agreed

## Success criterion

A judge can enter a primary query and see:

1. planner interpretation
2. relevant data retrieval
3. candidate zones
4. deterministic scores
5. safety validation
6. recommendation or safe refusal
7. evidence
8. map visualization

The result must be explainable and reproducible for the same cached dataset.
